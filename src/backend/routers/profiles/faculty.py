from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, StringConstraints
from typing import Annotated, Optional

from src.backend.globals import DB_MANAGER, AccountInfo, UserType
from src.backend.routers.utils import assert_user_type, get_current_session
from src.database.profile_insertion import create_faculty_profile
from src.database.profile_updating import update_faculty_profile
from src.database.record_retrieval import get_faculty_by_id

router = APIRouter()


class FacultyProfileCreateRequest(BaseModel):
    # Contact
    first_name: Annotated[str, StringConstraints(max_length=50)]
    middle_name: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    last_name: Annotated[str, StringConstraints(max_length=50)]
    email: Annotated[EmailStr, StringConstraints(max_length=254)]
    phone: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    # Profile
    department_name: Annotated[str, StringConstraints(max_length=100)]


@router.post("/create", response_model=dict)
async def create_profile(
    data: FacultyProfileCreateRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> dict:
    """
    Create a faculty profile (contact info + department).
    Only callable by authenticated faculty users who haven't yet created their profile.
    """
    assert_user_type(session_data, UserType.FACULTY)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile, msg = await create_faculty_profile(
            db_session,
            account_id,
            data.first_name,
            data.middle_name,
            data.last_name,
            data.email,
            data.phone,
            data.department_name,
        )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile could not be created. Reason: {msg}",
        )

    return {"success": True, "message": msg}


@router.get("/profile", response_model=dict)
async def get_profile(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> dict:
    """
    __
    """
    assert_user_type(session_data, UserType.FACULTY)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_faculty_by_id(db_session, account_id)
        contact = profile.contact
        department = profile.department.name

    return {
        "contact": {
            "first_name": contact.first,
            "middle_name": contact.middle,
            "last_name": contact.last,
            "email": contact.email,
            "phone": contact.phone,
        },
        "profile": {"department": department},
    }


class FacultyProfileUpdateRequest(BaseModel):
    # Contact
    first_name: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    middle_name: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    last_name: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    email: Optional[Annotated[EmailStr, StringConstraints(max_length=254)]] = None
    phone: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    # Profile
    department_name: Optional[Annotated[str, StringConstraints(max_length=100)]] = None


@router.patch("/update", response_model=dict)
async def update_profile(
    data: FacultyProfileUpdateRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> dict:
    """
    __
    """
    assert_user_type(session_data, UserType.FACULTY)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile, msg = await update_faculty_profile(
            db_session,
            account_id,
            data.first_name,
            data.middle_name,
            data.last_name,
            data.email,
            data.phone,
            data.department_name,
        )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile could not be updated. Reason: {msg}",
        )

    return {"success": True, "message": msg}
