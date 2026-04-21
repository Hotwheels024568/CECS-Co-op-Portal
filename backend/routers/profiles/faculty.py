from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, StringConstraints
from typing import Annotated, Optional

from backend.globals import AccountInfo, UserType, get_db_manager
from backend.routers.models import (
    Contact,
    ContactCreationDetails,
    ContactUpdateDetails,
    GeneralRequestResponse,
)
from backend.routers.models import FacultyProfile
from backend.routers.utils import assert_user_type, get_current_session
from database.manage import AsyncDBManager
from database.profile_insertion import create_faculty_profile
from database.profile_updating import update_faculty_profile
from database.record_retrieval import get_faculty_by_id
from database.sync_retrieval import get_contact, get_department

router = APIRouter()


class FacultyProfileCreationDetails(BaseModel):
    department_name: Annotated[str, StringConstraints(max_length=100)]


class FacultyProfileCreationRequest(BaseModel):
    contact: ContactCreationDetails
    profile: FacultyProfileCreationDetails


@router.post(
    "/create",
    tags=["Faculty"],
    summary="Create a new faculty profile",
    description=(
        "Submit a new faculty profile, including contact information and profile details. "
        "Requires authentication. Returns a confirmation of successful profile creation or an error message."
    ),
    response_model=GeneralRequestResponse,
)
async def create_profile(
    data: FacultyProfileCreationRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
    db_manager: AsyncDBManager = Depends(get_db_manager),
) -> GeneralRequestResponse:
    """
    Create a new faculty profile with contact information and profile detail assignment.

    This endpoint can only be called by authenticated faculty users who have not already created a profile.

    Args:
        data (FacultyProfileCreateRequest): An object containing the faculty member's contact information and profile details.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: Indicates success or failure with explanatory message.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
        HTTPException (500): If the operation fails.
    """
    assert_user_type(session_data, UserType.FACULTY)

    account_id = session_data[1]["account_id"]
    async with db_manager.session() as db_session:
        profile, msg = await create_faculty_profile(
            db_session,
            account_id,
            data.contact.first_name,
            data.contact.middle_name,
            data.contact.last_name,
            data.contact.email,
            data.contact.phone,
            data.profile.department_name,
        )

    if not profile:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Profile could not be created. Reason: {msg}"
        )
    return GeneralRequestResponse(success=True, message=msg)


class FacultyProfileResponse(BaseModel):
    contact: Contact
    profile: FacultyProfile


@router.get(
    "/profile",
    tags=["Faculty"],
    summary="Retrieve your faculty profile",
    description="Fetch the authenticated faculty member's contact information and profile details.",
    response_model=FacultyProfileResponse,
)
async def get_profile(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
    db_manager: AsyncDBManager = Depends(get_db_manager),
) -> FacultyProfileResponse:
    """
    Retrieve the authenticated faculty member's profile information.

    This endpoint returns the faculty member's contact information and profile details.
    Only callable by authenticated faculty users who have an existing profile.

    Args:
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        FacultyProfileResponse: Contains contact information and department name.

    Raises:
        HTTPException (400): If the profile does not exist.
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
    """
    assert_user_type(session_data, UserType.FACULTY)

    account_id = session_data[1]["account_id"]
    async with db_manager.session() as db_session:
        profile = await get_faculty_by_id(db_session, account_id)
        if not profile:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Profile does not exist. Please create a profile first.",
            )

        contact = await db_session.run_sync(get_contact, profile)
        department = await db_session.run_sync(get_department, profile)

    return FacultyProfileResponse(
        contact=Contact(
            first_name=contact.first,
            middle_name=contact.middle,
            last_name=contact.last,
            email=contact.email,
            phone=contact.phone,
        ),
        profile=FacultyProfile(department=department.name),
    )


class FacultyProfileUpdateDetails(BaseModel):
    department_name: Optional[Annotated[str, StringConstraints(max_length=100)]] = None


class FacultyProfileUpdateRequest(BaseModel):
    contact: Optional[ContactUpdateDetails] = None
    profile: Optional[FacultyProfileUpdateDetails] = None


@router.patch(
    "/update",
    tags=["Faculty"],
    summary="Update your faculty profile",
    description=(
        "Modify existing faculty profile information, such as department and contact info. "
        "Returns a confirmation of the update status. Authentication required."
    ),
    response_model=GeneralRequestResponse,
)
async def update_profile(
    data: FacultyProfileUpdateRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
    db_manager: AsyncDBManager = Depends(get_db_manager),
) -> GeneralRequestResponse:
    """
    Update the authenticated faculty member's profile information.

    This endpoint allows faculty users to modify their contact details or department.
    At least one field must be provided to update.
    Only callable by authenticated faculty users who have an existing profile.

    Args:
        data (FacultyProfileUpdateRequest): An object containing the updated contact details or department name.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: Indicates success or failure with explanatory message.

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
    assert_user_type(session_data, UserType.FACULTY)

    contact = data.contact
    profile = data.profile

    account_id = session_data[1]["account_id"]
    async with db_manager.session() as db_session:
        profile, msg = await update_faculty_profile(
            db_session,
            account_id,
            contact.first_name if contact else None,
            contact.middle_name if contact else None,
            contact.last_name if contact else None,
            contact.email if contact else None,
            contact.phone if contact else None,
            profile.department_name if profile else None,
        )

    if not profile:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Profile could not be updated. Reason: {msg}"
        )
    return GeneralRequestResponse(success=True, message=msg)
