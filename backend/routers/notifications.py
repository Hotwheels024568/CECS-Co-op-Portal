from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, StringConstraints
from typing import Annotated, Optional

from backend.globals import AccountInfo, UserType

router = APIRouter()
