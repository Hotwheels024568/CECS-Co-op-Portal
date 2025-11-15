import os
from src.database.manage import AsyncDBManager

DB_MANAGER: AsyncDBManager | None = None

# Session storage - use Redis in production
SESSION_STORE = {}  # {session_id: #, account: { account_id, user_type, expires_at }}
SESSION_EXPIRE_SECONDS = 3600

# Load pepper from environment variable for production, fallback for development.
PEPPER = os.environ.get("APP_PEPPER", "dev-pepper-secret")
