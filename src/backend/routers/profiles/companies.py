from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional

from src.backend.globals import DB_MANAGER, AccountInfo, UserType

router = APIRouter()

"""
Employers:
    create
    update
    delete

Students & Faculty:
    get (search?) + attach employer list
"""
