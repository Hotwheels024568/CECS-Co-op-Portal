from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional

from src.backend.globals import DB_MANAGER, AccountInfo
from src.backend.routers.utils import get_current_session
from src.database.profile_insertion import create_faculty_profile
from src.database.profile_updating import update_faculty_profile

router = APIRouter()


class FacultyProfileUpdateRequest(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    department_name: str


@router.post("/create_profile", response_model=dict)
async def create_faculty_profile_endpoint(
    data: FacultyProfileUpdateRequest,
    session: tuple[str, AccountInfo] = Depends(get_current_session),
):
    """
    Create a faculty profile (contact info + department).
    Only callable by authenticated faculty users who haven't yet created their profile.
    """
    user_type = session[1]["user_type"]
    # 1. Auth check
    if user_type != "Faculty":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Faculty accounts may create a faculty profile.",
        )

    # 2. Create profile
    account_id = session[1]["account_id"]
    async with DB_MANAGER.session() as session:
        faculty, msg = await create_faculty_profile(
            session=session,
            account_id=account_id,
            first_name=data.first_name,
            middle_name=data.middle_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            department_name=data.department_name,
        )

    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile could not be created. Reason: {msg}",
        )

    return {
        "success": True,
        "faculty_id": faculty.id,
        "department": faculty.department.name,
        "message": msg or "Faculty profile created successfully.",
    }


class FacultyProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department_name: Optional[str] = None


@router.post("/update_profile", response_model=dict)
async def update_faculty_profile_endpoint(
    data: FacultyProfileUpdateRequest,
    session: tuple[str, AccountInfo] = Depends(get_current_session),
):
    """
    __
    """
    user_type = session[1]["user_type"]
    # 1. Auth check
    if user_type != "Faculty":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Faculty accounts may create a faculty profile.",
        )

    # 2. Create profile
    account_id = session[1]["account_id"]
    async with DB_MANAGER.session() as session:
        faculty, msg = await update_faculty_profile(
            session=session,
            account_id=account_id,
            first_name=data.first_name,
            middle_name=data.middle_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            department_name=data.department_name,
        )

    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile could not be created. Reason: {msg}",
        )

    return {
        "success": True,
        "faculty_id": faculty.id,
        "department": faculty.department.name,
        "message": msg or "Faculty profile created successfully.",
    }
