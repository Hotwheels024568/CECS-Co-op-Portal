from fastapi import HTTPException, Header, status
from typing import Collection, Optional, Union
import hashlib
import time

from src.backend.globals import (
    PEPPER,
    SESSION_EXPIRE_SECONDS,
    SESSION_STORE,
    USER_SESSION_MAP,
    AccountInfo,
    UserType,
)


# --- Helper: hash_and_pepper Example (You can use bcrypt/scrypt/argon2, but here's a basic PBKDF2 example) ---
def hash_password(
    password: str,
    salt: bytes,
    pepper: Optional[str] = None,
    iterations: int = 100_000,  # adjustable iterations
    algorithm: str = "sha256",
) -> bytes:
    """
    Returns a PBKDF2-HMAC hash of the given password+pepper and salt.

    Args:
        password: The plaintext user password.
        salt: Per-user random salt, bytes.
        pepper: Application-wide secret loaded from environment.
        iterations: PBKDF2 iterations (default: 100,000).
        algorithm: Hashing algorithm (default: sha256).

    Returns:
        hash: bytes suitable for storage in a BLOB field.
    """
    if pepper is None:
        pepper = PEPPER
    pwd_bytes = (password + pepper).encode()
    return hashlib.pbkdf2_hmac(algorithm, pwd_bytes, salt, iterations)


def get_current_session(
    session_id: str = Header(..., alias="session-id", description="Session token from login")
) -> tuple[str, AccountInfo]:
    """
    Validates the current user's session via the session-id HTTP header.

    Args:
        session_id (str): The session ID provided in the request header.

    Returns:
        tuple (str, AccountInfo): The session ID and session data if valid.

    Raises:
        HTTPException (401): If the session is invalid or expired.
    """
    session = SESSION_STORE.get(session_id)
    now = time.time()
    if not session or session["expires_at"] < now:
        removed = SESSION_STORE.pop(session_id, None)
        if removed is not None:
            USER_SESSION_MAP.pop(removed["account_id"], None)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired or invalid")

    session["expires_at"] = now + SESSION_EXPIRE_SECONDS
    return session_id, session


def assert_user_type(
    session_data: tuple[str, AccountInfo], allowed_types: Union[UserType, Collection[UserType]]
) -> None:
    """
    Validates the current user's session user type.

    Args:
        session_data (tuple[str, AccountInfo]): The session info.
        allowed_types (Union[UserType, Collection[UserType]]): The endpoint's allowed user types.

    Raises:
        HTTPException (403): If the session's user type is invalid.
    """
    if isinstance(allowed_types, UserType):
        allowed_types = [allowed_types]

    user_type = session_data[1]["user_type"]
    if user_type not in allowed_types:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Only {_allowed_types_phrase(allowed_types)} accounts may access this endpoint.",
        )


def _allowed_types_phrase(types) -> str:
    names = [type.value if hasattr(type, "value") else str(type) for type in types]
    if len(names) == 1:
        return names[0]
    elif len(names) == 2:
        return f"{names[0]} or {names[1]}"
    else:
        return f"{', '.join(names[:-1])} or {names[-1]}"
