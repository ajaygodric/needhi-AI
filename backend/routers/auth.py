import sqlite3
import time
import logging
import re
from fastapi import APIRouter, Depends, HTTPException, status, Header
from core.db import DATABASE_FILE
from core.schemas import UserRegisterRequest, UserLoginRequest, AuthResponse, UserMeResponse
from core.security import hash_password, verify_password, create_session, delete_session, get_current_user

logger = logging.getLogger("needhi.routers.auth")
router = APIRouter()

@router.post("/api/auth/register", response_model=AuthResponse)
def register_user(req: UserRegisterRequest):
    email = req.email.strip().lower()
    name = req.name.strip()
    password = req.password
    
    # Validation
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise HTTPException(status_code=400, detail="Invalid email format.")
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
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered.")
            
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
    
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, password_hash FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=400, detail="Incorrect email or password.")
            
        user_id, name, pwd_hash = row
        if not verify_password(password, pwd_hash):
            raise HTTPException(status_code=400, detail="Incorrect email or password.")
            
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
