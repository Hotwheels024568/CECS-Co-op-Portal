from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from src.backend.globals import DB_MANAGER, AccountInfo, UserType

router = APIRouter()

"""
Faculty
    get dept
    update (grade) dept

Students
    (automatic db entry creation hopefully)
    get personal
    update summary

Employers
    get summaries of apps
    update approval
"""
