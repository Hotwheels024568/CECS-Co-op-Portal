from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, StringConstraints
from typing import Annotated, Optional

from backend.globals import AccountInfo, UserType, get_db_manager
from backend.routers.internships.internships import InternshipSearchResponse
from backend.routers.models import (
    Address,
    AddressCreationDetails,
    AddressUpdateDetails,
    BriefStudentProfile,
    Company,
    Contact,
    EmployerApplicationSummary,
    EmployerInternshipSummary,
    EmployerSummary,
    GeneralRequestResponse,
    Internship,
    InternshipStatus,
    LocationType,
)
from backend.routers.utils import assert_user_type, get_current_session
from database.internship_retrieval import search_internships
from database.manage import AsyncDBManager
from database.profile_insertion import create_company
from database.profile_updating import update_company_profile
from database.record_retrieval import (
    get_companies,
    get_employer_by_id,
    get_summaries_by_internship_id,
)
from database.sync_retrieval import (
    get_company_address,
    get_contact,
    get_department,
    get_employer_company_internships,
    get_employer_company,
    get_internship_address,
    get_internship_company,
    get_internship_majors,
    get_internship_preferred_skills,
    get_internship_required_skills,
    get_major,
    get_summary_student,
)

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
    db_manager: AsyncDBManager = Depends(get_db_manager),
) -> GeneralRequestResponse:
    """
    Create a new company with information assignment.

    This endpoint can only be called by authenticated employer users.

    Args:
        data (CompanyCreationRequest): An object containing the company's information.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: Indicates success or failure with explanatory message.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
        HTTPException (500): If the operation fails.
    """
    assert_user_type(session_data, UserType.EMPLOYER)

    async with db_manager.session() as db_session:
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
    "/list",
    tags=["Companies"],
    summary="Get a list of companies",
    description="Fetch the list of companies registered in the system.",
    response_model=CompanyListResponse,
)
async def get_company_list(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
    db_manager: AsyncDBManager = Depends(get_db_manager),
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
    results = []
    async with db_manager.session() as db_session:
        companies = await get_companies(db_session)
        for company in companies:
            address = await db_session.run_sync(get_company_address, company)
            results.append(
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
    return CompanyListResponse(companies=results)


class CompanyUpdateDetails(BaseModel):
    name: Optional[Annotated[str, StringConstraints(min_length=2, max_length=100)]] = None
    address: Optional[AddressUpdateDetails] = None
    website_link: Optional[Annotated[str, StringConstraints(min_length=5, max_length=255)]] = None


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
    db_manager: AsyncDBManager = Depends(get_db_manager),
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
        GeneralRequestResponse: Indicates success or failure with explanatory message.

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
    address = company.address if company else None

    account_id = session_data[1]["account_id"]
    async with db_manager.session() as db_session:
        profile = await get_employer_by_id(db_session, account_id)
        company_id = (await db_session.run_sync(get_employer_company, profile)).id
        company, msg = await update_company_profile(
            db_session,
            company_id,
            company.name if company else None,
            company.website_link if company else None,
            address.address_line1 if address else None,
            address.address_line2 if address else None,
            address.city if address else None,
            address.state_province if address else None,
            address.zip_postal if address else None,
            address.country if address else None,
        )

    if not company:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Profile could not be updated. Reason: {msg}"
        )
    return GeneralRequestResponse(success=True, message=msg)


# Could make a delete_company endpoint (Employer's company)
#   Would have to handle dangling FKs and prevent if the company is linked to other employers


class CompanyInternshipSearchRequest(BaseModel):
    title: Optional[Annotated[str, StringConstraints(max_length=255)]] = None
    location_type: Optional[LocationType] = None
    duration_weeks: Optional[int] = None
    weekly_hours: Optional[int] = None
    status: Optional[InternshipStatus] = None
    majors: Optional[list[Annotated[str, StringConstraints(max_length=100)]]] = None
    required_skills: Optional[list[Annotated[str, StringConstraints(max_length=100)]]] = None
    preferred_skills: Optional[list[Annotated[str, StringConstraints(max_length=100)]]] = None
    page: int = 1
    page_size: int = 20


@router.post(
    "/me/internships/summaries",
    tags=["Employers"],
    summary="Search your company's internships by filters and keywords",
    description=(
        "Allows employers to search their company's internships using multiple filters such as title, "
        "location type, duration, hours, status, majors, and skills. Returns a paginated list of matching internships."
    ),
    response_model=InternshipSearchResponse,
)
async def search_company_internships_endpoint(
    data: CompanyInternshipSearchRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
    db_manager: AsyncDBManager = Depends(get_db_manager),
) -> InternshipSearchResponse:
    """
    Search company internships using flexible filters.

    Enables authorized users to perform a filtered search on company internships using criteria such as title,
    location type, duration, status, majors, required and preferred skills. Results are paginated.

    Args:
        data (InternshipSearchRequest): Search filters for internships.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        InternshipSearchResponse: List and count of filtered internships.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
    """
    assert_user_type(session_data, UserType.EMPLOYER)

    account_id = session_data[1]["account_id"]
    async with db_manager.session() as db_session:
        profile = await get_employer_by_id(db_session, account_id)
        internships, count = await search_internships(
            db_session,
            profile.company_id,
            data.title,
            data.location_type.value if data.location_type else None,
            data.duration_weeks,
            data.weekly_hours,
            data.status.value if data.status else None,
            data.majors,
            data.required_skills,
            data.preferred_skills,
            data.page,
            data.page_size,
        )

        results = []
        for internship in internships:
            company = await db_session.run_sync(get_internship_company, internship)
            address = await db_session.run_sync(get_company_address, company)
            majors = await db_session.run_sync(get_internship_majors, internship)
            required_skills = await db_session.run_sync(get_internship_required_skills, internship)
            preferred_skills = await db_session.run_sync(
                get_internship_preferred_skills, internship
            )
            internship_address = await db_session.run_sync(get_internship_address, internship)
            results.append(
                Internship(
                    id=internship.id,
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
                    ),
                    title=internship.title,
                    description=internship.description,
                    location_type=LocationType(internship.location_type),
                    address=(
                        Address(
                            address_line1=internship_address.address_line1,
                            address_line2=internship_address.address_line2,
                            city=internship_address.city,
                            state_province=internship_address.state_province,
                            zip_postal=internship_address.zip_postal,
                            country=internship_address.country,
                        )
                        if internship_address
                        else None
                    ),
                    duration_weeks=internship.duration_weeks,
                    weekly_hours=internship.weekly_hours,
                    total_work_hours=internship.total_work_hours,
                    salary_info=internship.salary_info,
                    status=InternshipStatus(internship.status),
                    majors=[major.name for major in majors],
                    required_skills=[skill.name for skill in required_skills],
                    preferred_skills=[skill.name for skill in preferred_skills],
                )
            )
    return InternshipSearchResponse(internships=results, count=count)


class EmployerSummaryResponse(BaseModel):
    summary_id: int
    application: EmployerApplicationSummary
    summary: EmployerSummary


class EmployerSummaryListResponse(BaseModel):
    summaries: list[EmployerSummaryResponse]


@router.get(
    "/me/internships/summaries",
    tags=["Employers"],
    summary="Retrieve all internship summaries for the employer's company",
    description=(
        "Returns internship summaries submitted by students associated with any internships at the employer's company. "
        "Only accessible by authenticated employers."
    ),
    response_model=EmployerSummaryListResponse,
)
async def get_company_internship_summaries(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
    db_manager: AsyncDBManager = Depends(get_db_manager),
) -> EmployerSummaryListResponse:
    """
    Retrieve all internship summaries across all internships owned by this employer.

    Args:
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        EmployerSummaryListResponse: List of summaries with basic student/internship context.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
    """
    assert_user_type(session_data, UserType.EMPLOYER)

    account_id = session_data[1]["account_id"]
    async with db_manager.session() as db_session:
        profile = await get_employer_by_id(db_session, account_id)
        internships = await db_session.run_sync(get_employer_company_internships, profile)

        results = []
        for internship in internships:
            summaries = await get_summaries_by_internship_id(db_session, internship.id)
            for summary in summaries:
                student = await db_session.run_sync(get_summary_student, summary)
                contact = await db_session.run_sync(get_contact, profile)
                department = await db_session.run_sync(get_department, student)
                major = await db_session.run_sync(get_major, student)
                results.append(
                    EmployerSummaryResponse(
                        summary_id=summary.id,
                        application=EmployerApplicationSummary(
                            student=BriefStudentProfile(
                                contact=Contact(
                                    first_name=contact.first,
                                    middle_name=contact.middle,
                                    last_name=contact.last,
                                    email=contact.email,
                                    phone=contact.phone,
                                ),
                                department_name=department.name,
                                major_name=major.name,
                            ),
                            internship=EmployerInternshipSummary(
                                title=internship.title,
                                description=internship.description,
                                duration_weeks=internship.duration_weeks,
                                weekly_hours=internship.weekly_hours,
                                total_work_hours=internship.total_work_hours,
                            ),
                        ),
                        summary=EmployerSummary(
                            summary=summary.summary,
                            file_link=summary.file_link,
                            employer_approval=summary.employer_approval,
                        ),
                    )
                )
    return EmployerSummaryListResponse(summaries=results)
