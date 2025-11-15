from fastapi import HTTPException
import hashlib
import time

from src.backend.globals import SESSION_STORE


def get_current_session(session_id: str):
    session = SESSION_STORE.get(session_id)
    if not session or session["expires_at"] < time.time():
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return session


def hash_password(password: str, salt: bytes, pepper: str = "") -> bytes:
    pwd_bytes = (password + pepper).encode()
    return hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt, 100_000)  # <-- adjustable iterations
