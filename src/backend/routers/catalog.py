from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from src.backend.globals import DB_MANAGER, AccountInfo, UserType

router = APIRouter()

"""
get addresses (maybe)
get departments
get majors
get skills
"""
