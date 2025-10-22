from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
import hashlib
import hmac
import os

from src.database.record_retrieval import get_account_by_username

router = APIRouter()

active_connections = []


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register():
    pass


"""
POST /login
Request JSON:
{
    "username": "student1",
    "password": "plaintext-password"
}
Response:
{
    "success": true,
    "account_id": 42,
    "user_type": "student"
}
"""


@router.post("/login")
async def login(
    request: Request, login_req: LoginRequest, active_connections=active_connections
) -> dict:
    """
    Authenticate a user using a constant-time password check.
    If username not found, computes dummy hash for timing attack resistance.
    Returns account info or error.
    """
    username = login_req.username
    password = login_req.password

    # -- Lookup user in DB  --
    user = await get_account_by_username(username)  # None if not found

    # -- Password verification process --
    # (the PEPPER would be a server-side secret, if used)
    # PEPPER = os.environ.get("PEPPER", "")
    PEPPER = "PEPPER"  # TODO: REPLACE

    # All password records should have: password_hash, salt, [pepper]
    if user:
        salt = user.salt
        stored_hash = user.password_hash
        # Hash submitted password
        hash_val = hash_and_pepper(password, salt, PEPPER)
    else:
        # Use dummy values for timing-resistance
        salt = os.urandom(16)  # dummy
        stored_hash = b"DUMMY_HASH_VALUE"
        hash_val = hash_and_pepper(password, salt, PEPPER)

    # -- Constant-time comparison --
    if user and hmac.compare_digest(hash_val, stored_hash):
        # Update active connections (optional: use websocket, or session_id/cookie)
        connection = request.client.host  # or custom session token
        active_connections.append((connection, user.id))
        return {"success": True, "account_id": user.id, "user_type": user.user_type}
    else:
        # Add unauthenticated connection
        connection = request.client.host
        active_connections.append((connection, None))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )


# --- Helper: hash_and_pepper Example (You can use bcrypt/scrypt/argon2, but here's a basic PBKDF2 example) ---
def hash_and_pepper(password: str, salt: bytes, pepper: str) -> bytes:
    pwd_bytes = (password + pepper).encode()
    return hashlib.pbkdf2_hmac(
        "sha256", pwd_bytes, salt, 100_000
    )  # <-- adjustable iterations


@router.post("/logout")
async def login():
    pass
