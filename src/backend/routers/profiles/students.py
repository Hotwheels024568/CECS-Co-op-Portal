from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, NonNegativeFloat, NonNegativeInt, StringConstraints
from typing import Annotated, Optional

from src.backend.globals import DB_MANAGER, AccountInfo, UserType
from src.backend.routers.models import (
    ContactCreationRequest,
    ContactResponse,
    ContactUpdateRequest,
    GeneralRequestResponse,
)
from src.backend.routers.utils import assert_user_type, get_current_session
from src.database.profile_insertion import create_student_profile
from src.database.profile_updating import update_student_profile
from src.database.record_retrieval import get_student_by_id
from src.utils.semesters import Semester

router = APIRouter()


class StudentProfileCreateRequest(BaseModel):
    contact: ContactCreationRequest
    # Profile
    department_name: Annotated[str, StringConstraints(max_length=100)]
    major_name: Annotated[str, StringConstraints(max_length=100)]
    credit_hours: Annotated[int, NonNegativeInt]
    gpa: Annotated[float, NonNegativeFloat]
    start_semester: Semester
    start_year: Annotated[int, NonNegativeInt]
    transfer: bool
    resume_link: Optional[Annotated[str, StringConstraints(max_length=255)]] = None


@router.post(
    "/create",
    tags=["Students"],
    summary="Create a new student profile",
    description=(
        "Submit a new student profile, including contact information and profile details. "
        "Requires authentication. Returns a confirmation of successful profile creation or an error message."
    ),
    response_model=GeneralRequestResponse,
)
async def create_profile(
    data: StudentProfileCreateRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    Create a new student profile with contact information and profile detail assignment.

    This endpoint can only be called by authenticated student users who have not already created a profile.

    Args:
        data (StudentProfileCreateRequest): An object containing the student's contact information and profile details.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: {"success": True, "message": "..."} if the profile was created successfully.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
        HTTPException (500): If the operation fails.
    """
    assert_user_type(session_data, UserType.STUDENT)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile, msg = await create_student_profile(
            db_session,
            account_id,
            data.contact.first_name,
            data.contact.middle_name,
            data.contact.last_name,
            data.contact.email,
            data.contact.phone,
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
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Profile could not be created. Reason: {msg}",
        )

    return GeneralRequestResponse(success=True, message=msg)


class StudentProfileResponse(BaseModel):
    contact: ContactResponse
    department_name: str
    major_name: str
    credit_hours: int
    gpa: float
    start_semester: Semester
    start_year: int
    transfer: bool
    resume_link: Optional[str]


@router.get(
    "/profile",
    tags=["Students"],
    summary="Retrieve your student profile",
    description="Fetch the authenticated student's contact information and profile details.",
    response_model=StudentProfileResponse,
)
async def get_profile(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> dict:
    """
    Retrieve the authenticated students's profile information.

    This endpoint returns the students's contact information and profile details.
    Only callable by authenticated students users who have an existing profile.

    Args:
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        StudentProfileResponse: Contains contact information, department name, major name, credit hours,
            gpa, start semester & year, transfer student indication and an optional resume link.

    Raises:
        HTTPException (400): If the profile does not exist or the operation fails.
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
    """
    assert_user_type(session_data, UserType.STUDENT)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_student_by_id(db_session, account_id)
        if not profile:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Faculty profile does not exist. Please create a profile first.",
            )

        contact = profile.contact
        response = ContactResponse(
            first_name=contact.first,
            middle_name=contact.middle,
            last_name=contact.last,
            email=contact.email,
            phone=contact.phone,
        )

    return StudentProfileResponse(
        contact=response,
        department=profile.department.name,
        major_name=profile.major.name,
        credit_hours=profile.credit_hours,
        gpa=profile.gpa,
        start_semester=profile.start_semester,
        start_year=profile.start_year,
        transfer=profile.transfer,
        resume_link=profile.resume_link,
    )


class StudentProfileUpdateRequest(BaseModel):
    contact: ContactUpdateRequest
    # Profile
    department_name: Optional[Annotated[str, StringConstraints(max_length=100)]] = None
    major_name: Optional[Annotated[str, StringConstraints(max_length=100)]] = None
    credit_hours: Optional[Annotated[int, NonNegativeInt]] = None
    gpa: Optional[Annotated[float, NonNegativeFloat]] = None
    start_semester: Optional[Semester] = None
    start_year: Optional[Annotated[int, NonNegativeInt]] = None
    transfer: Optional[bool] = None
    resume_link: Optional[Annotated[str, StringConstraints(max_length=255)]] = None


@router.patch(
    "/update",
    tags=["Students"],
    summary="Update your student profile",
    description=(
        "Modify existing student profile information, such as department, major, gpa and contact info. "
        "Returns a confirmation of the update status. Authentication required."
    ),
    response_model=GeneralRequestResponse,
)
@router.patch("/update", response_model=dict)
async def update_profile(
    data: StudentProfileUpdateRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    Update the authenticated students's profile information.

    This endpoint allows student users to modify their contact details or department.
    Only callable by authenticated student users who have an existing profile.

    Args:
        data (StudentProfileUpdateRequest): An object containing the updated contact information and profile details.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: {"success": True, "message": "..."} if the profile was updated successfully.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
        HTTPException (500): If the operation fails.
    """
    assert_user_type(session_data, UserType.STUDENT)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile, msg = await update_student_profile(
            db_session,
            account_id,
            data.contact.first_name,
            data.contact.middle_name,
            data.contact.last_name,
            data.contact.email,
            data.contact.phone,
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
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Profile could not be updated. Reason: {msg}",
        )

    return GeneralRequestResponse(success=True, message=msg)
