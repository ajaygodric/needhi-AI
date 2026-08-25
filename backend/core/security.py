import os
import time
import logging
import sqlite3
import threading
import hashlib
import secrets
from typing import Optional
from collections import defaultdict
from fastapi import HTTPException, Request
from cryptography.fernet import Fernet
from core.config import DATABASE_FILE, DATA_DIR

logger = logging.getLogger("needhi.security")

# Backup in-memory rate limiter cache
BACKUP_LIMITS = defaultdict(list)
BACKUP_LIMITS_LOCK = threading.Lock()

def sanitize_input_dict(input_dict: Optional[dict], allowed_keys: set) -> dict:
    if not input_dict:
        return {}
    
    sanitized = {}
    jailbreak_phrases = [
        "ignore above",
        "ignore previous",
        "system override",
        "you are now",
        "bypass",
        "ignore the instructions",
        "ignore all instructions"
    ]
    
    for k, v in input_dict.items():
        if k not in allowed_keys:
            continue
            
        if isinstance(v, str):
            val_lower = v.lower()
            if any(phrase in val_lower for phrase in jailbreak_phrases):
                sanitized[k] = "[CLEANED]"
            else:
                # Truncate value to a safe length (1000 characters)
                sanitized[k] = v[:1000]
        else:
            sanitized[k] = v
            
    return sanitized

def get_fernet():
    key_str = os.environ.get("PII_ENCRYPTION_KEY")
    if key_str:
        try:
            return Fernet(key_str.encode())
        except Exception as e:
            logger.error(f"Invalid PII_ENCRYPTION_KEY format: {e}. Trying persistent key file.")
            
    # Dynamic persistent key strategy:
    # Attempt to read/write a dynamically generated unique key in DATA_DIR
    key_file = os.path.join(DATA_DIR, ".pii_key.key")
    if os.path.exists(key_file):
        try:
            with open(key_file, "rb") as f:
                persistent_key = f.read().strip()
            if persistent_key:
                return Fernet(persistent_key)
        except Exception as e:
            logger.error(f"Failed to read persistent PII key from {key_file}: {e}")
            
    # Try generating a new persistent key
    try:
        new_key = Fernet.generate_key()
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(key_file, "wb") as f:
            f.write(new_key)
        logger.info(f"Generated a new unique persistent PII encryption key at: {key_file}")
        return Fernet(new_key)
    except Exception as e:
        raise RuntimeError(
            f"FATAL: Cannot initialize PII encryption. Set the PII_ENCRYPTION_KEY environment variable "
            f"or ensure DATA_DIR ({DATA_DIR}) is writable so a persistent key can be generated. "
            f"Original error: {e}"
        )

# Fail-fast check on module load to guarantee encryption keys are active
get_fernet()

def encrypt_field(value: str) -> str:
    if not value:
        return value
    try:
        return get_fernet().encrypt(value.encode()).decode()
    except Exception as e:
        logger.error(f"Field encryption failed: {e}")
        return value

def decrypt_field(value: str) -> str:
    if not value:
        return value
    try:
        return get_fernet().decrypt(value.encode()).decode()
    except Exception as e:
        logger.error(f"Field decryption failed: {e}")
        return value

def check_backup_rate_limit(client_ip: str, endpoint: str, limit: int, window: int) -> bool:
    """In-memory fallback rate limiter."""
    now = time.time()
    with BACKUP_LIMITS_LOCK:
        timestamps = BACKUP_LIMITS[(client_ip, endpoint)]
        timestamps = [t for t in timestamps if now - t < window]
        if len(timestamps) >= limit:
            BACKUP_LIMITS[(client_ip, endpoint)] = timestamps
            return False
        timestamps.append(now)
        BACKUP_LIMITS[(client_ip, endpoint)] = timestamps
        return True

def check_db_rate_limit(client_ip: str, endpoint: str, limit: int, window: int) -> bool:
    """SQLite-backed rate limiter."""
    now = time.time()
    cutoff = now - window
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rate_limits WHERE ip = ? AND endpoint = ? AND timestamp < ?", (client_ip, endpoint, cutoff))
        
        cursor.execute("SELECT COUNT(*) FROM rate_limits WHERE ip = ? AND endpoint = ?", (client_ip, endpoint))
        count = cursor.fetchone()[0]
        
        if count >= limit:
            conn.commit()
            conn.close()
            return False
            
        cursor.execute("INSERT INTO rate_limits (ip, endpoint, timestamp) VALUES (?, ?, ?)", (client_ip, endpoint, now))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error checking rate limits in SQLite: {e}. Falling back to in-memory rate limiter.")
        return check_backup_rate_limit(client_ip, endpoint, limit, window)

def check_rate_limit_ai(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not check_db_rate_limit(client_ip, "ai", limit=5, window=60):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again in a minute.")

def check_rate_limit_data(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not check_db_rate_limit(client_ip, "data", limit=20, window=60):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again in a minute.")

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}:{pwd_hash.hex()}"

def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, stored_hash = password_hash.split(":")
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return new_hash.hex() == stored_hash
    except Exception:
        return False

def create_session(user_id: int) -> str:
    token = secrets.token_hex(32)
    expires_at = time.time() + 86400  # 24 hours
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)", (token, user_id, expires_at))
        conn.commit()
    finally:
        conn.close()
    return token

def verify_session(token: str) -> Optional[int]:
    if not token:
        return None
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, expires_at FROM sessions WHERE token = ?", (token,))
        row = cursor.fetchone()
        if not row:
            return None
        user_id, expires_at = row
        if time.time() > expires_at:
            cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            return None
        return user_id
    except Exception:
        return None
    finally:
        conn.close()

def delete_session(token: str):
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
    finally:
        conn.close()

def get_current_user(request: Request) -> int:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header.")
    token = auth_header.split(" ")[1]
    user_id = verify_session(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Session expired or invalid. Please login again.")
    return user_id

def get_optional_user(request: Request) -> Optional[int]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    return verify_session(token)

