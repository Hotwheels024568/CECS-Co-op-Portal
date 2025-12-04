from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, StringConstraints
from typing import Annotated, Optional

from src.backend.globals import AccountInfo, UserType

router = APIRouter()
