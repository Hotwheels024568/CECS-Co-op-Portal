from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from backend.globals import AccountInfo, UserType, get_db_manager
from backend.routers.models import (
    Address,
    Company,
    Contact,
    ContactCreationDetails,
    ContactUpdateDetails,
    EmployerProfile,
    GeneralRequestResponse,
)
from backend.routers.utils import assert_user_type, get_current_session
from database.manage import AsyncDBManager
from database.profile_insertion import create_employer_profile
from database.profile_updating import update_employer_profile
from database.record_retrieval import get_employer_by_id
from database.sync_retrieval import get_employer_company, get_company_address, get_contact

router = APIRouter()


class EmployerProfileCreationRequest(BaseModel):
    contact: ContactCreationDetails
    profile: EmployerProfile


@router.post(
    "/create",
    tags=["Employers"],
    summary="Create a new employer profile",
    description=(
        "Submit a new employer profile, including contact information and profile details. "
        "Requires authentication. Returns a confirmation of successful profile creation or an error message."
    ),
    response_model=GeneralRequestResponse,
)
async def create_profile(
    data: EmployerProfileCreationRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
    db_manager: AsyncDBManager = Depends(get_db_manager),
) -> GeneralRequestResponse:
    """
    Create a new employer profile with contact information and profile detail assignment.

    This endpoint can only be called by authenticated employer users who have not already created a profile.

    Args:
        data (EmployerProfileCreateRequest): An object containing the employer's contact information and profile details.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: Indicates success or failure with explanatory message.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
        HTTPException (500): If the operation fails.
    """
    assert_user_type(session_data, UserType.EMPLOYER)

    account_id = session_data[1]["account_id"]
    async with db_manager.session() as db_session:
        profile, msg = await create_employer_profile(
            db_session,
            account_id,
            data.contact.first_name,
            data.contact.middle_name,
            data.contact.last_name,
            data.contact.email,
            data.contact.phone,
            data.profile.company_id,
        )

    if not profile:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Profile could not be created. Reason: {msg}"
        )
    return GeneralRequestResponse(success=True, message=msg)


class EmployerCompany(BaseModel):
    company: Company


class EmployerProfileResponse(BaseModel):
    contact: Contact
    profile: EmployerCompany


@router.get(
    "/profile",
    tags=["Employers"],
    summary="Retrieve your employer profile",
    description="Fetch the authenticated employer's contact information and profile details.",
    response_model=EmployerProfileResponse,
)
async def get_profile(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
    db_manager: AsyncDBManager = Depends(get_db_manager),
) -> EmployerProfileResponse:
    """
    Retrieve the authenticated employer's profile information.

    This endpoint returns the employer's contact information and profile details.
    Only callable by authenticated employer users who have an existing profile.

    Args:
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        EmployerProfileResponse: Contains contact information, and profile details.

    Raises:
        HTTPException (400): If the profile does not exist.
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
    """
    assert_user_type(session_data, UserType.EMPLOYER)

    account_id = session_data[1]["account_id"]
    async with db_manager.session() as db_session:
        profile = await get_employer_by_id(db_session, account_id)
        if not profile:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Profile does not exist. Please create a profile first.",
            )

        contact = await db_session.run_sync(get_contact, profile)
        company = await db_session.run_sync(get_employer_company, profile)
        address = await db_session.run_sync(get_company_address, company)

    return EmployerProfileResponse(
        contact=Contact(
            first_name=contact.first,
            middle_name=contact.middle,
            last_name=contact.last,
            email=contact.email,
            phone=contact.phone,
        ),
        profile=EmployerCompany(
            company=Company(
                id=company.id,
                name=company.name,
                address=Address(
                    address_line1=address.address_line1,
                    address_line2=address.address_line2,
                    city=address.city,
                    state_province=address.state_province,
                    zip_postal=address.zip_postal,
                    country=address.country,
                ),
                website_link=company.website_link,
            )
        ),
    )


class EmployerProfileUpdateDetails(BaseModel):
    company_id: Optional[int] = None


class EmployerProfileUpdateRequest(BaseModel):
    contact: Optional[ContactUpdateDetails] = None
    profile: Optional[EmployerProfileUpdateDetails] = None


@router.patch(
    "/update",
    tags=["Employers"],
    summary="Update your employer profile",
    description=(
        "Modify existing employer profile information, such as department, major, gpa and contact info. "
        "Returns a confirmation of the update status. Authentication required."
    ),
    response_model=GeneralRequestResponse,
)
async def update_profile(
    data: EmployerProfileUpdateRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
    db_manager: AsyncDBManager = Depends(get_db_manager),
) -> GeneralRequestResponse:
    """
    Update the authenticated employer's profile information.

    This endpoint allows employer users to modify their contact details or department.
    At least one field must be provided to update.
    Only callable by authenticated employer users who have an existing profile.

    Args:
        data (EmployerProfileUpdateRequest): An object containing the updated contact information and profile details.
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
    assert_user_type(session_data, UserType.EMPLOYER)

    contact = data.contact
    profile = data.profile

    account_id = session_data[1]["account_id"]
    async with db_manager.session() as db_session:
        profile, msg = await update_employer_profile(
            db_session,
            account_id,
            contact.first_name if contact else None,
            contact.middle_name if contact else None,
            contact.last_name if contact else None,
            contact.email if contact else None,
            contact.phone if contact else None,
            company_id=profile.company_id if profile else None,
        )

    if not profile:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Profile could not be updated. Reason: {msg}"
        )
    return GeneralRequestResponse(success=True, message=msg)
