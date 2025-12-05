from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, StringConstraints
from typing import Annotated, Optional
import hmac, secrets, time

from src.backend.globals import (
    SESSION_STORE,
    SESSION_EXPIRE_SECONDS,
    USER_SESSION_MAP,
    AccountInfo,
    UserType,
    get_db_manager,
)
from src.backend.routers.models import GeneralRequestResponse
from src.backend.routers.utils import get_current_session, hash_password
from src.database.manage import AsyncDBManager
from src.database.record_insertion import add_account
from src.database.record_retrieval import get_account_by_username

router = APIRouter()


class AuthRequest(BaseModel):
    username: Annotated[str, StringConstraints(max_length=150)]
    password: Annotated[str, StringConstraints(min_length=8, max_length=128)]


class LoginResponse(BaseModel):
    success: bool
    session_id: str
    user_type: Optional[UserType]


@router.post(
    "/register",
    tags=["Authentication"],
    summary="Register a new user and log them in.",
    description=(
        "Registers a new user account and immediately logs the user in. "
        "Receives a username and plaintext password, securely stores the credentials, "
        "and creates a session token for subsequent authenticated requests."
    ),
    response_model=LoginResponse,
)
async def register(
    request: AuthRequest, db_manager: AsyncDBManager = Depends(get_db_manager)
) -> LoginResponse:
    """
    Registers a new user account and logs the user in.

    Receives a desired username and plaintext password via HTTPS. Generates a secure, random salt,
    hashes the password using PBKDF2 (with an optional pepper), and stores the username, password hash,
    and salt in the database. User type is not required or set at registration. Upon successful registration,
    automatically creates a session for the user and returns a session token.

    Args:
        request (AuthRequest): Contains 'username' and 'password' fields.

    Returns:
        LoginResponse: JSON object with
            - success: True if registration and session creation were successful.
            - session_id: The session token for authenticated requests.
            - user_type: The account type if assigned, or None before profile creation.

    Raises:
        HTTPException (400): If the username is already taken or registration fails.
    """
    global SESSION_STORE, USER_SESSION_MAP
    # 1. Generate salt and hash
    salt = secrets.token_bytes(16)
    pw_hash = hash_password(request.password, salt)

    # 2. Insert into DB
    async with db_manager.session() as db_session:
        account = await add_account(db_session, request.username, pw_hash, salt, commit=True)
        if account is not None:
            # Instant login: create session
            session_id = secrets.token_urlsafe(32)
            expires_at = time.time() + SESSION_EXPIRE_SECONDS
            user_type = account.user_type or None
            SESSION_STORE[session_id] = {
                "account_id": account.id,
                "user_type": user_type,
                "expires_at": expires_at,
            }
            USER_SESSION_MAP[account.id] = session_id
            return LoginResponse(success=True, session_id=session_id, user_type=user_type)

    raise HTTPException(
        status.HTTP_400_BAD_REQUEST,
        "Username already exists or registration failed",
    )


@router.post(
    "/login",
    tags=["Authentication"],
    summary="Authenticate and obtain a session token.",
    description=(
        "Logs a user in using their username and password. If credentials are valid, "
        "a secure session token for use in authenticated requests is returned."
    ),
    response_model=LoginResponse,
)
async def login(
    request: AuthRequest, db_manager: AsyncDBManager = Depends(get_db_manager)
) -> LoginResponse:
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
            - session_id: The session token for authenticated requests.
            - user_type: account type ("Employer", "Student", "Faculty", or None)

    Raises:
        HTTPException (401): If credentials are invalid.
    """
    global SESSION_STORE, USER_SESSION_MAP
    # 1. Look up user by username
    async with db_manager.session() as db_session:
        account = await get_account_by_username(db_session, request.username)

    # 2. Prepare for timing-attack-resistant check
    salt = secrets.token_bytes(16)
    stored_hash = secrets.token_bytes(32)
    user_type = None

    if account is not None:
        salt = account.salt
        stored_hash = account.password
        user_type = account.user_type

    # 3. Hash the given password + pepper + salt & Constant-time comparison
    password_match = hmac.compare_digest(hash_password(request.password, salt), stored_hash)

    # 5. Session management
    if account is not None and password_match:
        if account.id in USER_SESSION_MAP:
            SESSION_STORE.pop(USER_SESSION_MAP.get(account.id), None)

        # Generate session token, store login info
        session_id = secrets.token_urlsafe(32)
        expires_at = time.time() + SESSION_EXPIRE_SECONDS
        SESSION_STORE[session_id] = {
            "account_id": account.id,
            "user_type": user_type,
            "expires_at": expires_at,
        }
        USER_SESSION_MAP[account.id] = session_id
        return LoginResponse(success=True, session_id=session_id, user_type=user_type)

    raise HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Incorrect username or password",
    )


@router.post(
    "/logout",
    tags=["Authentication"],
    summary="Logout and invalidate session.",
    description=(
        "Logs out the current user by invalidating the session token. "
        "Session token must be supplied in the request body."
    ),
    response_model=GeneralRequestResponse,
)
async def logout(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    Log out a user by invalidating their session.

    Removes the specified session_id from the session store, ending the user's authenticated session.

    Args:
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: Indicates success or failure with explanatory message.

    Raises:
        HTTPException (401): If the session is invalid or already expired.
    """
    global SESSION_STORE

    session_id = session_data[0]
    removed = SESSION_STORE.pop(session_id, None)
    if removed is not None:
        USER_SESSION_MAP.pop(removed["account_id"], None)
        return GeneralRequestResponse(success=True, message="Logged out")

    raise HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Session not found or already logged out",
    )
