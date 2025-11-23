from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from src.backend.globals import DB_MANAGER, AccountInfo, UserType
from src.backend.routers.models import Address, Company

router = APIRouter()

"""
Employers:
    create
    update
    delete

Students & Faculty:
    get (search?) + attach employer list
"""
