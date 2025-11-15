from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.backend.globals import DB_MANAGER

router = APIRouter()
