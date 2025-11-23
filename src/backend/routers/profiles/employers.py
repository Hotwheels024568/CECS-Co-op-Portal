from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from src.backend.globals import DB_MANAGER, AccountInfo, UserType
from src.backend.routers.models import Employer

router = APIRouter()


"""
Employers:
    create profile
        pick existing or create a new company

    get profile

    update profile
        pick/keep existing or create a new company
"""
