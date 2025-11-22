from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, NonNegativeFloat, NonNegativeInt, StringConstraints
from typing import Annotated, Optional

from src.backend.globals import DB_MANAGER, AccountInfo, UserType
from src.backend.routers.utils import assert_user_type, get_current_session
from src.database.profile_insertion import create_student_profile
from src.database.profile_updating import update_student_profile
from src.database.record_retrieval import get_student_by_id
from src.utils.academics import Semester

router = APIRouter()


class StudentProfileCreateRequest(BaseModel):
    # Contact
    first_name: Annotated[str, StringConstraints(max_length=50)]
    middle_name: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    last_name: Annotated[str, StringConstraints(max_length=50)]
    email: Annotated[EmailStr, StringConstraints(max_length=254)]
    phone: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    # Profile
    department_name: Annotated[str, StringConstraints(max_length=100)]
    major_name: Annotated[str, StringConstraints(max_length=100)]
    credit_hours: Annotated[int, NonNegativeInt]
    gpa: Annotated[int, NonNegativeFloat]
    start_semester: Semester
    start_year: Annotated[int, NonNegativeInt]
    transfer: bool
    resume_link: Optional[Annotated[str, StringConstraints(max_length=255)]] = None


@router.post("/create", response_model=dict)
async def create_profile(
    data: StudentProfileCreateRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> dict:
    """
    Create a student profile (contact info + department).
    Only callable by authenticated student users who haven't yet created their profile.
    """
    assert_user_type(session_data, UserType.STUDENT)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile, msg = await create_student_profile(
            db_session,
            account_id,
            data.first_name,
            data.middle_name,
            data.last_name,
            data.email,
            data.phone,
            data.department_name,
            data.major_name,
            data.credit_hours,
            data.gpa,
            data.start_semester,
            data.start_year,
            data.transfer,
            data.resume_link,
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
    assert_user_type(session_data, UserType.STUDENT)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_student_by_id(db_session, account_id)
        contact = profile.contact

    return {
        "contact": {
            "first_name": contact.first,
            "middle_name": contact.middle,
            "last_name": contact.last,
            "email": contact.email,
            "phone": contact.phone,
        },
        "profile": {
            "department": profile.department.name,
            "major": profile.major.name,
            "credit_hours": profile.credit_hours,
            "gpa": profile.gpa,
            "start_semester": profile.start_semester,
            "start_year": profile.start_year,
            "transfer": profile.transfer,
            "resume_link": profile.resume_link,
        },
    }


class StudentProfileUpdateRequest(BaseModel):
    # Contact
    first_name: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    middle_name: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    last_name: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    email: Optional[Annotated[EmailStr, StringConstraints(max_length=254)]] = None
    phone: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    # Profile
    department_name: Optional[Annotated[str, StringConstraints(max_length=100)]] = None
    major_name: Optional[Annotated[str, StringConstraints(max_length=100)]] = None
    credit_hours: Optional[Annotated[int, NonNegativeInt]] = None
    gpa: Optional[Annotated[int, NonNegativeFloat]] = None
    start_semester: Optional[Semester] = None
    start_year: Optional[Annotated[int, NonNegativeInt]] = None
    transfer: Optional[bool] = None
    resume_link: Optional[Annotated[str, StringConstraints(max_length=255)]] = None


@router.patch("/update", response_model=dict)
async def update_profile(
    data: StudentProfileUpdateRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
):
    """
    __
    """
    assert_user_type(session_data, UserType.STUDENT)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile, msg = await update_student_profile(
            db_session,
            account_id,
            data.first_name,
            data.middle_name,
            data.last_name,
            data.email,
            data.phone,
            data.department_name,
            data.major_name,
            data.credit_hours,
            data.gpa,
            data.start_semester,
            data.start_year,
            data.transfer,
            data.resume_link,
        )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile could not be updated. Reason: {msg}",
        )

    return {"success": True, "message": msg}
