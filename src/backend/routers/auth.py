from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import secrets
import hmac
import time

from src.backend.globals import DB_MANAGER, SESSION_STORE, SESSION_EXPIRE_SECONDS, PEPPER
from src.backend.utils.auth_utils import hash_password
from src.database.record_insertion import add_account
from src.database.record_retrieval import get_account_by_username

router = APIRouter()


class AuthRequest(BaseModel):
    username: str
    password: str


class LogoutRequest(BaseModel):
    session_id: str


class LoginResponse(BaseModel):
    success: bool
    session_id: str
    user_type: str


@router.post("/register")
async def register(request: AuthRequest) -> dict:
    """
    Register a new account.

    Receives a desired username and plaintext password via HTTPS. Generates a secure, random salt,
    hashes the password using PBKDF2 (with optional pepper), and stores the username, password hash,
    and salt in the database. User type is not required or set at registration.

    Args:
        request (AuthRequest): Contains 'username' and 'password' fields.

    Returns:
        dict: {"success": True} if registration completes, else 400 error on failure.

    Raises:
        HTTPException 400: If username is already taken or registration fails.
    """
    # 1. Generate salt and hash
    salt = secrets.token_bytes(16)
    pw_hash = hash_password(request.password, salt, PEPPER)

    # 2. Insert into DB
    async with DB_MANAGER.session() as session:
        account = await add_account(session, request.username, pw_hash, salt, commit=True)
        if account is not None:
            return {"success": True}

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Username already exists or registration failed",
    )


@router.post("/login", response_model=LoginResponse)
async def login(request: AuthRequest) -> LoginResponse:
    """
    Authenticate a user and create a session.

    Verifies credentials by comparing the provided username and password (hashed with salt and pepper)
    to the stored values in the database using constant-time comparison to prevent timing attacks.
    If successful, generates and stores a secure, opaque session token (session_id).

    Args:
        request (AuthRequest): Contains 'username' and 'password' fields.

    Returns:
        LoginResponse: JSON object with
            - success: authentication result
            - session_id: opaque session token for authenticated requests
            - user_type: account type ("Employer", "Student", "Faculty", or None)

    Raises:
        HTTPException 401: If credentials are invalid.
    """
    # 1. Look up user by username
    async with DB_MANAGER.session() as session:
        account = await get_account_by_username(session, request.username)  # None if not found

    # 2. Prepare for timing-attack-resistant check
    salt: bytes = secrets.token_bytes(16)
    stored_hash: bytes = secrets.token_bytes(32)
    user_type: str = ""

    if account is not None:
        salt = account.salt
        stored_hash = account.password
        user_type = account.user_type

    # 3. Hash the given password + pepper + salt
    attempted_hash = hash_password(request.password, salt, PEPPER)

    # 4. Constant-time comparison
    if not account:
        # Do constant-time compare for dummy, just for timing resistance
        hmac.compare_digest(secrets.token_bytes(32), stored_hash)

    elif hmac.compare_digest(attempted_hash, stored_hash):
        # 5. Session token
        session_id = secrets.token_urlsafe(32)
        expires_at = time.time() + SESSION_EXPIRE_SECONDS
        SESSION_STORE[session_id] = {
            "account_id": account.id,
            "user_type": user_type,
            "expires_at": expires_at,
        }
        return LoginResponse(success=True, session_id=session_id, user_type=user_type)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password"
    )


# --- Helper: hash_and_pepper Example (You can use bcrypt/scrypt/argon2, but here's a basic PBKDF2 example) ---
@router.post("/logout")
async def logout(request: LogoutRequest) -> dict:
    """
    Log out a user by invalidating their session.

    Removes the specified session_id from the session store, ending the user's authenticated session.
    This endpoint requires the session_id (typically sent in JSON, but may also be provided via header/cookie).

    Args:
        request (LogoutRequest): Contains 'session_id' field to be invalidated.

    Returns:
        dict: {"success": True} if logout was successful.

    Raises:
        HTTPException 401: If the session_id does not exist or has already been invalidated.
    """
    session_id = request.session_id
    removed = SESSION_STORE.pop(session_id, None)
    if removed:
        return {"success": True}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session not found or already logged out",
    )
