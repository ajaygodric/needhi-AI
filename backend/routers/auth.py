import sqlite3
import time
import logging
import re
import json
import secrets
import urllib.request
import urllib.error
from fastapi import APIRouter, Depends, HTTPException, status, Header
from core.db import DATABASE_FILE
from core.config import GOOGLE_CLIENT_ID
from core.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    GoogleAuthRequest,
    AuthConfigResponse,
    AuthResponse,
    UserMeResponse,
    SendOtpRequest,
    VerifyOtpRequest,
    SendOtpResponse
)
from core.security import hash_password, verify_password, create_session, delete_session, get_current_user
from core.utils import send_otp_email

logger = logging.getLogger("needhi.routers.auth")
router = APIRouter()

def is_valid_gmail(email: str) -> bool:
    """
    Validates that the email is an official Google @gmail.com or @googlemail.com address.
    Strictly rejects example.com, test.com, disposable addresses, or non-Gmail domains.
    """
    if not email:
        return False
    email_clean = email.strip().lower()
    
    # Must have @ and end with @gmail.com or @googlemail.com
    if not (email_clean.endswith("@gmail.com") or email_clean.endswith("@googlemail.com")):
        return False
        
    # Check username portion before @
    parts = email_clean.split("@")
    if len(parts) != 2:
        return False
    username = parts[0]
    
    # Gmail usernames must be 4-30 chars and contain valid characters
    if len(username) < 3 or len(username) > 30:
        return False
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9._%+-]*$", username):
        return False
        
    return True

@router.get("/api/auth/config", response_model=AuthConfigResponse)
def get_auth_config():
    return AuthConfigResponse(google_client_id=GOOGLE_CLIENT_ID)

@router.post("/api/auth/send-otp", response_model=SendOtpResponse)
def send_otp(req: SendOtpRequest):
    email = req.email.strip().lower()
    purpose = req.purpose.lower().strip() # 'login' or 'register'
    name = (req.name or "").strip()
    
    if not is_valid_gmail(email):
        raise HTTPException(
            status_code=400, 
            detail="Only valid official @gmail.com addresses are permitted for registration and sign-in."
        )
        
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT id, name FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()
        
        if purpose == "register" and existing_user:
            raise HTTPException(
                status_code=400, 
                detail="This Gmail is already registered. Please switch to Login tab."
            )
            
        is_new_user = existing_user is None
        display_name = (existing_user[1] if existing_user else name) or "Citizen"
        
        # Rate limit: check if an OTP was sent in the last 45 seconds
        now = time.time()
        cursor.execute("SELECT created_at FROM email_otps WHERE email = ?", (email,))
        prev_otp = cursor.fetchone()
        if prev_otp and (now - prev_otp[0]) < 45:
            wait_sec = int(45 - (now - prev_otp[0]))
            raise HTTPException(
                status_code=429, 
                detail=f"Please wait {wait_sec} seconds before requesting a new OTP."
            )
            
        # Generate 6-digit cryptographically secure OTP
        otp_code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = now + 600  # 10 minutes expiry
        
        # Upsert OTP in SQLite
        cursor.execute("""
            INSERT OR REPLACE INTO email_otps (email, otp_code, purpose, name, created_at, expires_at, attempts)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (email, otp_code, purpose, display_name, now, expires_at))
        conn.commit()
        
        # Dispatch email
        success, msg = send_otp_email(email, display_name, otp_code, purpose)
        logger.info(f"OTP generated for {email}: {otp_code} (Status: {msg})")
        
        return SendOtpResponse(
            success=True, 
            message=f"Verification code sent to {email}. Please check your inbox or spam folder.",
            is_new_user=is_new_user
        )
    finally:
        conn.close()

@router.post("/api/auth/verify-otp", response_model=AuthResponse)
def verify_otp(req: VerifyOtpRequest):
    email = req.email.strip().lower()
    entered_otp = req.otp.strip()
    name = (req.name or "").strip()
    
    if not is_valid_gmail(email):
        raise HTTPException(status_code=400, detail="Invalid Gmail address format.")
        
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        now = time.time()
        
        cursor.execute(
            "SELECT otp_code, purpose, name, expires_at, attempts FROM email_otps WHERE email = ?", 
            (email,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=400, 
                detail="No verification code found. Please click 'Send OTP' to request a new code."
            )
            
        saved_otp, purpose, saved_name, expires_at, attempts = row
        
        if now > expires_at:
            cursor.execute("DELETE FROM email_otps WHERE email = ?", (email,))
            conn.commit()
            raise HTTPException(
                status_code=400, 
                detail="Verification code has expired. Please request a new OTP."
            )
            
        if attempts >= 5:
            cursor.execute("DELETE FROM email_otps WHERE email = ?", (email,))
            conn.commit()
            raise HTTPException(
                status_code=400, 
                detail="Too many incorrect attempts. Please request a new OTP."
            )
            
        if entered_otp != saved_otp:
            cursor.execute("UPDATE email_otps SET attempts = attempts + 1 WHERE email = ?", (email,))
            conn.commit()
            raise HTTPException(
                status_code=400, 
                detail="Incorrect verification code. Please check your Gmail and try again."
            )
            
        # OTP is verified! Delete OTP record
        cursor.execute("DELETE FROM email_otps WHERE email = ?", (email,))
        
        # Check if user exists or create new user
        cursor.execute("SELECT id, name FROM users WHERE email = ?", (email,))
        user_row = cursor.fetchone()
        
        final_name = name or saved_name or "Needhi User"
        if user_row:
            user_id, existing_name = user_row
            final_name = existing_name or final_name
        else:
            # Create user account automatically
            cursor.execute(
                "INSERT INTO users (email, password_hash, name, created_at) VALUES (?, ?, ?, ?)",
                (email, "otp_verified_user", final_name, now)
            )
            user_id = cursor.lastrowid
            
        conn.commit()
        token = create_session(user_id)
        return AuthResponse(token=token, name=final_name, email=email)
    finally:
        conn.close()

@router.post("/api/auth/google", response_model=AuthResponse)
def google_auth(req: GoogleAuthRequest):
    credential = req.credential.strip()
    if not credential:
        raise HTTPException(status_code=400, detail="Missing Google ID token credential.")
        
    # Verify token with Google OAuth2 tokeninfo endpoint
    token_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
    try:
        req_google = urllib.request.Request(token_url, headers={"User-Agent": "NeedhiAI-Backend/1.0"})
        with urllib.request.urlopen(req_google, timeout=10) as response:
            if response.status != 200:
                raise HTTPException(status_code=401, detail="Google authentication failed: Invalid token status.")
            token_info = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        logger.warning(f"Google token validation failed with HTTP {e.code}")
        raise HTTPException(status_code=401, detail="Invalid Google token: Fake or unverified Google accounts are not permitted.")
    except Exception as e:
        logger.exception("Error during Google tokeninfo verification")
        raise HTTPException(status_code=401, detail="Could not verify Google account with Google servers. Please try again.")

    # Validate essential fields verified by Google
    email = token_info.get("email")
    email_verified = token_info.get("email_verified")
    name = token_info.get("name") or token_info.get("given_name") or "Google User"
    
    if not email or (isinstance(email_verified, str) and email_verified.lower() != "true") or (isinstance(email_verified, bool) and not email_verified):
        raise HTTPException(status_code=401, detail="Unverified Google email address. Only verified official Google accounts can log in.")
        
    email = email.strip().lower()
    name = name.strip()
    
    if not is_valid_gmail(email):
        raise HTTPException(status_code=400, detail="Only official @gmail.com accounts are permitted to sign in.")
    
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        
        now = time.time()
        if row:
            user_id, existing_name = row
            name = existing_name or name
        else:
            # Create new user for this verified official Google account
            cursor.execute(
                "INSERT INTO users (email, password_hash, name, created_at) VALUES (?, ?, ?, ?)",
                (email, "oauth_google_verified", name, now)
            )
            user_id = cursor.lastrowid
            conn.commit()
            
        token = create_session(user_id)
        return AuthResponse(token=token, name=name, email=email)
    finally:
        conn.close()

@router.post("/api/auth/register", response_model=AuthResponse)
def register_user(req: UserRegisterRequest):
    email = req.email.strip().lower()
    name = req.name.strip()
    password = req.password
    
    # Strict Gmail Validation
    if not is_valid_gmail(email):
        raise HTTPException(
            status_code=400, 
            detail="Registration is restricted to valid @gmail.com accounts only."
        )
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Name must be at least 2 characters long.")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")
        
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This Gmail is already registered. Please login.")
            
        # Hash password and insert user
        pwd_hash = hash_password(password)
        now = time.time()
        cursor.execute(
            "INSERT INTO users (email, password_hash, name, created_at) VALUES (?, ?, ?, ?)",
            (email, pwd_hash, name, now)
        )
        user_id = cursor.lastrowid
        conn.commit()
        
        # Automatically create session upon successful registration
        token = create_session(user_id)
        return AuthResponse(token=token, name=name, email=email)
    finally:
        conn.close()

@router.post("/api/auth/login", response_model=AuthResponse)
def login_user(req: UserLoginRequest):
    email = req.email.strip().lower()
    password = req.password
    
    # Strict Gmail Validation
    if not is_valid_gmail(email):
        raise HTTPException(
            status_code=400, 
            detail="Sign-in is restricted to valid @gmail.com accounts only."
        )
    
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, password_hash FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=400, detail="Incorrect email or password. You can also sign in via Gmail OTP.")
            
        user_id, name, pwd_hash = row
        if not verify_password(password, pwd_hash):
            raise HTTPException(status_code=400, detail="Incorrect email or password. You can also sign in via Gmail OTP.")
            
        # Create session
        token = create_session(user_id)
        return AuthResponse(token=token, name=name, email=email)
    finally:
        conn.close()

@router.post("/api/auth/logout")
def logout_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token.")
    token = authorization.split(" ")[1]
    delete_session(token)
    return {"detail": "Logged out successfully."}

@router.get("/api/auth/me", response_model=UserMeResponse)
def get_me(user_id: int = Depends(get_current_user)):
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name, email FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found.")
        name, email = row
        return UserMeResponse(name=name, email=email)
    finally:
        conn.close()

