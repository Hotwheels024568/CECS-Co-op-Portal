from fastapi import HTTPException, Header, status
import hashlib
import time

from src.backend.globals import SESSION_EXPIRE_SECONDS, SESSION_STORE, AccountInfo, UserType


# --- Helper: hash_and_pepper Example (You can use bcrypt/scrypt/argon2, but here's a basic PBKDF2 example) ---
def hash_password(
    password: str,
    salt: bytes,
    pepper: str = "",
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
        Tuple (str, AccountInfo): The session ID and session data if valid.

    Raises:
        HTTPException (401): If the session is invalid or expired.
    """
    session = SESSION_STORE.get(session_id)
    now = time.time()
    if not session or session["expires_at"] < now:
        SESSION_STORE.pop(session_id, None)
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    session["expires_at"] = now + SESSION_EXPIRE_SECONDS
    return session_id, session


def assert_user_type(session_data: tuple[str, AccountInfo], required_type: UserType) -> None:
    """
    Validates the current user's session user type.

    Args:
        session_data (tuple[str, AccountInfo]): The session info.
        required_type (UserType): The endpoints's required user type.

    Raises:
        HTTPException (403): If the session's user type is invalid.
    """
    if session_data[1]["user_type"] != required_type:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Student accounts may update a student profile.",
        )
