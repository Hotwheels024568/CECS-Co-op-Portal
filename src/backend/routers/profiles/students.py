from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, NonNegativeFloat, NonNegativeInt, StringConstraints
from typing import Annotated, Optional

from src.backend.globals import DB_MANAGER, AccountInfo, UserType
from src.backend.routers.models import (
    Contact,
    ContactCreationDetails,
    ContactUpdateDetails,
    GeneralRequestResponse,
    StudentProfile,
)
from src.backend.routers.utils import assert_user_type, get_current_session
from src.database.profile_insertion import create_student_profile
from src.database.profile_updating import update_student_profile
from src.database.record_retrieval import get_student_by_id
from src.utils_semesters import Semester

router = APIRouter()


class StudentProfileCreationDetails(BaseModel):
    department_name: Annotated[str, StringConstraints(max_length=100)]
    major_name: Annotated[str, StringConstraints(max_length=100)]
    credit_hours: Annotated[int, NonNegativeInt]
    gpa: Annotated[float, NonNegativeFloat]
    start_semester: Semester
    start_year: Annotated[int, NonNegativeInt]
    transfer: bool
    resume_link: Optional[Annotated[str, StringConstraints(max_length=255)]] = None


class StudentProfileCreationRequest(BaseModel):
    contact: ContactCreationDetails
    profile: StudentProfileCreationDetails


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
    data: StudentProfileCreationRequest,
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
            data.profile.department_name,
            data.profile.major_name,
            data.profile.credit_hours,
            data.profile.gpa,
            data.profile.start_semester,
            data.profile.start_year,
            data.profile.transfer,
            data.profile.resume_link,
        )

    if not profile:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Profile could not be created. Reason: {msg}",
        )
    return GeneralRequestResponse(success=True, message=msg)


class StudentProfileResponse(BaseModel):
    contact: Contact
    profile: StudentProfile


@router.get(
    "/profile",
    tags=["Students"],
    summary="Retrieve your student profile",
    description="Fetch the authenticated student's contact information and profile details.",
    response_model=StudentProfileResponse,
)
async def get_profile(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> StudentProfileResponse:
    """
    Retrieve the authenticated students's profile information.

    This endpoint returns the students's contact information and profile details.
    Only callable by authenticated students users who have an existing profile.

    Args:
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        StudentProfileResponse: Contains contact information, and profile details
            (e.g., department name, major, credit hours, GPA, semester/year started, transfer status, resume link).

    Raises:
        HTTPException (400): If the profile does not exist.
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
                "Profile does not exist. Please create a profile first.",
            )

        contact = profile.contact

    return StudentProfileResponse(
        contact=Contact(
            first_name=contact.first,
            middle_name=contact.middle,
            last_name=contact.last,
            email=contact.email,
            phone=contact.phone,
        ),
        profile=StudentProfile(
            department=profile.department.name,
            major_name=profile.major.name,
            credit_hours=profile.credit_hours,
            gpa=profile.gpa,
            start_semester=profile.start_semester,
            start_year=profile.start_year,
            transfer=profile.transfer,
            resume_link=profile.resume_link,
        ),
    )


class StudentProfileUpdateDetails(BaseModel):
    department_name: Optional[Annotated[str, StringConstraints(max_length=100)]] = None
    major_name: Optional[Annotated[str, StringConstraints(max_length=100)]] = None
    credit_hours: Optional[Annotated[int, NonNegativeInt]] = None
    gpa: Optional[Annotated[float, NonNegativeFloat]] = None
    start_semester: Optional[Semester] = None
    start_year: Optional[Annotated[int, NonNegativeInt]] = None
    transfer: Optional[bool] = None
    resume_link: Optional[Annotated[str, StringConstraints(max_length=255)]] = None


class StudentProfileUpdateRequest(BaseModel):
    contact: Optional[ContactUpdateDetails] = None
    profile: Optional[StudentProfileUpdateDetails] = None


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
async def update_profile(
    data: StudentProfileUpdateRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    Update the authenticated students's profile information.

    This endpoint allows student users to modify their contact details or department.
    At least one field must be provided to update.
    Only callable by authenticated student users who have an existing profile.

    Args:
        data (StudentProfileUpdateRequest): An object containing the updated contact information and profile details.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: {"success": True, "message": "..."} if the profile was updated successfully.

    Raises:
        HTTPException (400): If no update details are provided.
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
        HTTPException (500): If the operation fails.
    """
    if data.contact is None and data.profile is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must provide either contact information or profile details to update.",
        )
    assert_user_type(session_data, UserType.STUDENT)

    contact = data.contact
    first_name = contact.first_name if contact else None
    middle_name = contact.middle_name if contact else None
    last_name = contact.last_name if contact else None
    email = contact.email if contact else None
    phone = contact.phone if contact else None
    profile = data.profile
    department_name = profile.department_name if profile else None
    major_name = profile.major_name if profile else None
    credit_hours = profile.credit_hours if profile else None
    gpa = profile.gpa if profile else None
    start_semester = profile.start_semester if profile else None
    start_year = profile.start_year if profile else None
    transfer = profile.transfer if profile else None
    resume_link = profile.resume_link if profile else None

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile, msg = await update_student_profile(
            db_session,
            account_id,
            first_name,
            middle_name,
            last_name,
            email,
            phone,
            department_name,
            major_name,
            credit_hours,
            gpa,
            start_semester,
            start_year,
            transfer,
            resume_link,
        )

    if not profile:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Profile could not be updated. Reason: {msg}",
        )
    return GeneralRequestResponse(success=True, message=msg)
