from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.schema import (
    Account,
    Address,
    Company,
    ContactInfo,
    Employer,
    Student,
    Faculty,
)
