from typing import Optional, TypedDict
from enum import Enum
import os

from src.database.manage import AsyncDBManager


class UserType(str, Enum):
    EMPLOYER = "Employer"
    STUDENT = "Student"
    FACULTY = "Faculty"


class AccountInfo(TypedDict):
    """
    Session Account Info

    Attributes:
        account_id (int): DB backed account ID
        user_type (Optional[UserType]): A user type of "Employer", "Student", "Faculty", or None
        expires_at (float): When session token times out
    """

    account_id: int
    user_type: Optional[UserType]
    expires_at: float


DB_MANAGER: Optional[AsyncDBManager] = None

# Session storage - use Redis in production
SESSION_STORE: dict[str, AccountInfo] = {}
SESSION_EXPIRE_SECONDS = 3600

USER_SESSION_MAP: dict[int, str] = {}

# Load pepper from environment variable for production, fallback for development.
PEPPER = os.environ.get("APP_PEPPER", "dev-pepper-secret")


def get_db_manager() -> AsyncDBManager:
    if DB_MANAGER is None:
        raise RuntimeError("Database manager not initialized!")
    return DB_MANAGER
