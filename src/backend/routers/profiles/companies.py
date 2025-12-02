from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, StringConstraints
from typing import Annotated, Optional

from src.backend.globals import DB_MANAGER, AccountInfo, UserType
from src.backend.routers.models import (
    Address,
    AddressCreationDetails,
    AddressUpdateDetails,
    Company,
    GeneralRequestResponse,
)
from src.backend.routers.utils import assert_user_type, get_current_session
from src.database.profile_insertion import create_company
from src.database.profile_updating import update_company_profile
from src.database.record_retrieval import get_companies, get_employer_by_id

router = APIRouter()


class CompanyCreationDetails(BaseModel):
    name: Annotated[str, StringConstraints(min_length=2, max_length=100)]
    address: AddressCreationDetails
    website_link: Optional[Annotated[str, StringConstraints(min_length=5, max_length=255)]]


class CompanyCreationRequest(BaseModel):
    company: CompanyCreationDetails


@router.post(
    "/create",
    tags=["Employers"],
    summary="Create a new company",
    description=(
        "Submit new company information. Requires authentication. "
        "Returns a confirmation of successful creation or an error message."
    ),
    response_model=GeneralRequestResponse,
)
async def create_profile(
    data: CompanyCreationRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    Create a new company with information assignment.

    This endpoint can only be called by authenticated employer users.

    Args:
        data (CompanyCreationRequest): An object containing the company's information.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: {"success": True, "message": "..."} if the company was created successfully.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
        HTTPException (500): If the operation fails.
    """
    assert_user_type(session_data, UserType.EMPLOYER)

    async with DB_MANAGER.session() as db_session:
        profile, msg = await create_company(
            db_session,
            data.company.name,
            data.company.website_link,
            data.company.address.address_line1,
            data.company.address.address_line2,
            data.company.address.city,
            data.company.address.state_province,
            data.company.address.zip_postal,
            data.company.address.country,
        )

    if not profile:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Profile could not be created. Reason: {msg}"
        )
    return GeneralRequestResponse(success=True, message=msg)


class CompanyListResponse(BaseModel):
    companies: list[Company]


@router.get(
    "/companies",
    tags=["Companies"],
    summary="Get a list of companies",
    description="Fetch the list of companies registered in the system.",
    response_model=CompanyListResponse,
)
async def get_company_list(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> CompanyListResponse:
    """
    Retrieve a list of registered companies.

    This endpoint returns a structured list of all companies currently stored in the database.

    Args:
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        CompanyListResponse: List of companies containing its ID, name, address, and (optionally) website link.

    Raises:
        HTTPException (401): If the session is invalid or expired.
    """
    list = []
    async with DB_MANAGER.session() as db_session:
        companies = await get_companies(db_session)
        for company in companies:
            address = company.address
            list.append(
                Company(
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
            )
    return CompanyListResponse(companies=list)


class CompanyUpdateDetails(BaseModel):
    name: Optional[Annotated[str, StringConstraints(min_length=2, max_length=100)]]
    address: Optional[AddressUpdateDetails] = None
    website_link: Optional[Annotated[str, StringConstraints(min_length=5, max_length=255)]]


class CompanyUpdateRequest(BaseModel):
    company: Optional[CompanyUpdateDetails] = None


@router.patch(
    "/update",
    tags=["Employers"],
    summary="Update company information",
    description=(
        "Modify existing company information, such as name, website, and address details. "
        "Returns a confirmation of the update status. Authentication as employer required."
    ),
    response_model=GeneralRequestResponse,
)
async def update_profile(
    data: CompanyUpdateRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    Update company profile information.

    Allows an authenticated employer to update their associated company's details, including
    name, website link, and address. At least one field must be provided to update.
    This endpoint can only be called by authenticated employer users.

    Args:
        data (CompanyUpdateRequest): An object containing the company information.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: {"success": True, "message": "..."} if the company was updated successfully.

    Raises:
        HTTPException (400): If no update details are provided.
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
        HTTPException (500): If the operation fails.
    """
    if data.company is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "You must provide either contact information or profile details to update.",
        )
    assert_user_type(session_data, UserType.EMPLOYER)

    company = data.company
    name = company.name if company else None
    website_link = company.website_link if company else None
    address = company.address if company else None
    address_line1 = address.address_line1 if address else None
    address_line2 = address.address_line2 if address else None
    city = address.city if address else None
    state_province = address.state_province if address else None
    zip_postal = address.zip_postal if address else None
    country = address.country if address else None

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_employer_by_id(db_session, account_id)
        company_id = profile.company.id
        company, msg = await update_company_profile(
            db_session,
            company_id,
            name,
            website_link,
            address_line1,
            address_line2,
            city,
            state_province,
            zip_postal,
            country,
        )

    if not company:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Profile could not be updated. Reason: {msg}"
        )
    return GeneralRequestResponse(success=True, message=msg)


# Could make a delete_company endpoint (Employer's company)
#   Would have to handle dangling FKs and prevent if the company is linked to other employers
