from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, StringConstraints
from typing import Annotated, Optional

from src.backend.globals import DB_MANAGER, AccountInfo, UserType
from src.backend.routers.models import (
    Address,
    AddressCreationDetails,
    BriefStudentProfile,
    Company,
    Contact,
    EmployerApplicationInfo,
    GeneralRequestResponse,
    Internship,
    InternshipStatus,
    LocationType,
)
from src.backend.routers.profiles.companies import EmployerSummary
from src.backend.routers.utils import assert_user_type, get_current_session
from src.database.internship_insertion import create_internship
from src.database.internship_retrieval import search_internships
from src.database.internship_updating import update_internship
from src.database.record_retrieval import (
    get_application_by_id,
    get_employer_by_id,
    get_internship_applications,
    get_internship_by_id,
)
from src.database.schema import StudentAccount

router = APIRouter()


class InternshipSearchRequest(BaseModel):
    company_id: Optional[int] = None
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


class InternshipSearchResponse(BaseModel):
    internships: list[Internship]
    count: int


@router.post(
    "/search",
    tags=["Internships"],
    summary="Search internships by filters and keywords",
    description=(
        "Allows faculty and students to search internships using multiple filters such as company, title, "
        "location type, duration, hours, status, majors, and skills. Returns a paginated list of matching internships."
    ),
    response_model=InternshipSearchResponse,
)
async def search_internships_endpoint(
    data: InternshipSearchRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> InternshipSearchResponse:
    """
    Search internships using flexible filters.

    Enables authorized users to perform a filtered search on internships using criteria such as company, title,
    location type, duration, status, majors, required and preferred skills. Results are paginated.

    Args:
        data (InternshipSearchRequest): Search filters for internships.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        InternshipSearchResponse: List and count of filtered internships.

    Raises:
        HTTPException (401): If session is invalid.
    """
    assert_user_type(session_data, {UserType.FACULTY, UserType.STUDENT})

    async with DB_MANAGER.session() as db_session:
        internships, count = await search_internships(
            db_session,
            data.company_id,
            data.title,
            data.location_type.value,
            data.duration_weeks,
            data.weekly_hours,
            data.status.value,
            data.majors,
            data.required_skills,
            data.preferred_skills,
            data.page,
            data.page_size,
        )

        results = []
        for internship in internships:
            company = internship.company
            address = company.address
            results.append(
                Internship(
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
                    location_type=internship.location_type,
                    address=internship.address,
                    duration_weeks=internship.duration_weeks,
                    weekly_hours=internship.weekly_hours,
                    total_work_hours=internship.total_work_hours,
                    salary_info=internship.salary_info,
                    status=internship.status,
                    majors=[major.major.name for major in internship.majors],
                    required_skills=[
                        required_skill.skill.name for required_skill in internship.required_skills
                    ],
                    preferred_skills=[
                        preferred_skill.skill.name
                        for preferred_skill in internship.preferred_skills
                    ],
                )
            )
    return InternshipSearchResponse(internships=results, count=count)


@router.get(
    "/{internship_id}",
    tags=["Internships"],
    summary="Retrieve internship details by ID",
    description=(
        "Fetches complete details for a specific internship, including company information, "
        "address, required and preferred skills, and majors. "
        "Accessible by faculty or student users only; ensures proper authorization."
    ),
    response_model=Internship,
)
async def get_internship(
    internship_id: int, session_data: tuple[str, AccountInfo] = Depends(get_current_session)
) -> Internship:
    """
    Retrieve specific internship details by internship ID.

    Allow authorized users to access internships comprehensive information about a particular
    internship, including company details, address, skills required/preferred, and eligible majors.

    Args:
        internship_id (int): The ID of the internship to be retrieved.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        Internship: The complete internship record if found and authorized.

    Raises:
        HTTPException (400): If the internship does not exist.
        HTTPException (401): If the session is invalid or expired.
    """
    assert_user_type(session_data, {UserType.FACULTY, UserType.STUDENT})

    async with DB_MANAGER.session() as db_session:
        internship = await get_internship_by_id(db_session, internship_id)
        if not internship:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Internship does not exist")

        company = internship.company
        address = company.address
        return Internship(
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
            location_type=internship.location_type,
            address=internship.address,
            duration_weeks=internship.duration_weeks,
            weekly_hours=internship.weekly_hours,
            total_work_hours=internship.total_work_hours,
            salary_info=internship.salary_info,
            status=internship.status,
            majors=[major.major.name for major in internship.majors],
            required_skills=[
                required_skill.skill.name for required_skill in internship.required_skills
            ],
            preferred_skills=[
                preferred_skill.skill.name for preferred_skill in internship.preferred_skills
            ],
        )


class InternshipCreationRequest(BaseModel):
    title: Annotated[str, StringConstraints(max_length=255)]
    description: str
    location_type: LocationType
    address: Optional[AddressCreationDetails]
    duration_weeks: int
    weekly_hours: int
    total_work_hours: int
    salary_info: Optional[Annotated[str, StringConstraints(max_length=255)]]
    status: Optional[InternshipStatus] = InternshipStatus.OPEN
    majors: list[Annotated[str, StringConstraints(max_length=100)]]
    required_skills: list[Annotated[str, StringConstraints(max_length=100)]]
    preferred_skills: list[Annotated[str, StringConstraints(max_length=100)]]


@router.post(
    "/create",
    tags=["Employers"],
    summary="Create a new internship posting",
    description=(
        "Allows authorized employers to create a new internship listing with details such as title, description, "
        "location, duration, majors, and required/preferred skills. Only users with employer accounts can perform this action."
    ),
    response_model=GeneralRequestResponse,
)
async def create_internship_endpoint(
    data: InternshipCreationRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    Create a new internship posting.

    Allows an employer to create a new internship with details on title, description, location,
    duration, skills, and eligible majors.

    Args:
        data (InternshipCreationRequest): Data for the new internship, including title, description, skills, and more.
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
    async with DB_MANAGER.session() as db_session:
        address = data.address
        result, msg = await create_internship(
            db_session,
            account_id,
            data.title,
            data.description,
            data.location_type.value,
            None,  # address_id param, if handled elsewhere
            data.duration_weeks,
            data.weekly_hours,
            data.salary_info,
            data.status.value,
            data.majors,
            data.required_skills,
            data.preferred_skills,
            address.address_line1 if address else None,
            address.address_line2 if address else None,
            address.city if address else None,
            address.state_province if address else None,
            address.zip_postal if address else None,
            address.country if address else None,
        )

    if not result:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Internship could not be created. Reason: {msg}"
        )
    return GeneralRequestResponse(success=True, message=msg)


class InternshipUpdateRequest(BaseModel):
    title: Optional[Annotated[str, StringConstraints(max_length=255)]] = None
    description: Optional[str] = None
    location_type: Optional[LocationType] = None
    address: Optional[AddressCreationDetails]
    duration_weeks: Optional[int] = None
    weekly_hours: Optional[int] = None
    total_work_hours: Optional[int] = None
    salary_info: Optional[Annotated[str, StringConstraints(max_length=255)]] = None
    status: Optional[InternshipStatus] = None
    majors: Optional[list[Annotated[str, StringConstraints(max_length=100)]]] = None
    required_skills: Optional[list[Annotated[str, StringConstraints(max_length=100)]]] = None
    preferred_skills: Optional[list[Annotated[str, StringConstraints(max_length=100)]]] = None
    address: Optional[AddressCreationDetails]


@router.patch(
    "/{internship_id}/update",
    tags=["Employers"],
    summary="Update an internship",
    description="Allows authorized employers to update their company's posted internship details.",
    response_model=GeneralRequestResponse,
)
async def update_internship_endpoint(
    internship_id: int,
    data: InternshipUpdateRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    Update an internship record for an employer account.

    Args:
        internship_id (int): The ID of the internship to be updated.
        data (InternshipUpdateRequest): The fields to update.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: Indicates success or failure with explanatory message.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid, or employer does not own the internship.
        HTTPException (500): If the operation fails.
    """
    assert_user_type(session_data, UserType.EMPLOYER)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_employer_by_id(db_session, account_id)
        internship = await get_internship_by_id(db_session, internship_id)
        if internship.company_id != profile.company_id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "You can only update internships posted by your company."
            )

        address = data.address
        result, msg = await update_internship(
            db_session,
            internship_id,
            data.title,
            data.description,
            data.location_type.value,
            None,  # address_id param, if handled elsewhere
            data.duration_weeks,
            data.weekly_hours,
            data.salary_info,
            data.status.value,
            data.majors,
            data.required_skills,
            data.preferred_skills,
            address.address_line1 if address else None,
            address.address_line2 if address else None,
            address.city if address else None,
            address.state_province if address else None,
            address.zip_postal if address else None,
            address.country if address else None,
        )

    if not result:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Internship could not be updated. Reason: {msg}",
        )
    return GeneralRequestResponse(success=True, message=msg)


# Could make a delete_internship endpoint
#   Would have to handle dangling FKs


class EmployerSelectedApplicationsUpdateRequest(BaseModel):
    selected: list[int]


@router.patch(
    "/{internship_id}/update-candidates",
    tags=["Employers"],
    summary="Update selected candidates for an internship",
    description=(
        "Allows an authenticated employer to update the selection status of applicants to their internship "
        "by adding or removing application IDs from the 'selected candidates' list. Only employers who own "
        "the internship may perform this action."
    ),
    response_model=GeneralRequestResponse,
)
async def update_selected_candidates_for_internship(
    internship_id: int,
    data: EmployerSelectedApplicationsUpdateRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    Update the list of selected student candidates for a specific internship.

    Employers may add or remove student applications to/from the selected list for an internship they own.
    Ownership and application-internship association are strictly validated.

    Args:
        internship_id (int): The ID of the internship to update.
        data (EmployerSelectedApplicationsUpdateRequest): Lists of application IDs selected.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: Indicates success or failure with explanatory message.

    Raises:
        HTTPException (400): If the internship does not exist.
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid or not allowed to preform the action.
        HTTPException (500): If the operation fails.
    """
    assert_user_type(session_data, UserType.EMPLOYER)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_employer_by_id(db_session, account_id)
        internship = await get_internship_by_id(db_session, internship_id)
        if not internship:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Internship does not exist.")

        if internship.company_id != profile.company_id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "You can only update candidate selection for internships you own.",
            )

        applications = await get_internship_applications(db_session, internship_id)
        current_selected = set(app.id for app in applications if app.selected)
        new_selected = set(data.selected)

        to_add = new_selected - current_selected
        to_remove = current_selected - new_selected
        changed = []
        # Handle additions
        for app_id in to_add:
            application = await get_application_by_id(db_session, app_id)
            if not application:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, f"Application {app_id} does not exist."
                )
            if application.internship_id != internship_id:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"Application {app_id} does not belong to this internship.",
                )
            if not application.selected:
                application.selected = True
                db_session.add(application)
                changed.append(app_id)

        # Handle removals
        for app_id in to_remove:
            application = await get_application_by_id(db_session, app_id)
            if not application:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, f"Application {app_id} does not exist."
                )
            if application.internship_id != internship_id:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"Application {app_id} does not belong to this internship.",
                )
            if application.selected:
                application.selected = False
                db_session.add(application)
                changed.append(app_id)

        await db_session.commit()
    return GeneralRequestResponse(
        success=True, message=f"Updated selection status for applications: {changed}"
    )


class EmployerApplicationResponse(BaseModel):
    application_id: int
    application: EmployerApplicationInfo


class EmployerApplicationListResponse(BaseModel):
    applications: list[EmployerApplicationResponse]


@router.get(
    "/{internship_id}/applications",
    tags=["Employers"],
    summary="List all internship applications for your internship opportunity",
    description=(
        "Returns a list of applications submitted by students for a specified internship opportunity owned by the employer. "
        "Each application includes student profile, contact information, notes, resume and cover letter links. "
        "Access is restricted to authenticated employers who own the related internship."
    ),
    response_model=EmployerApplicationListResponse,
)
async def get_internship_applications_endpoint(
    internship_id: int,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> EmployerApplicationListResponse:
    """
    Retrieve all student internship applications for a specific employer-owned opportunity.

    Only the employer who owns the internship may view these applications. For each application,
    returns student contact and academic details, application note, resume and cover letter links,
    and selected status.

    Args:
        internship_id (int): The unique identifier for the internship opportunity.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        EmployerApplicationListResponse: List of application details and internship context.

    Raises:
        HTTPException (400): If the internship does not exist.
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid or not allowed to preform the action.
        HTTPException (500): If the operation fails.
    """
    assert_user_type(session_data, UserType.EMPLOYER)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_employer_by_id(db_session, account_id)
        internship = await get_internship_by_id(db_session, internship_id)
        if not internship:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Internship does not exist.")
        if internship.company_id != profile.company_id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Only the internship owner can view its applications."
            )
        applications = internship.applications

        results = []
        for application in applications:
            student = application.student
            contact = student.contact
            internship = application.internship
            results.append(
                EmployerApplicationResponse(
                    application_id=application.id,
                    application=EmployerApplicationInfo(
                        student=BriefStudentProfile(
                            contact=Contact(
                                first_name=contact.first,
                                middle_name=contact.middle,
                                last_name=contact.last,
                                email=contact.email,
                                phone=contact.phone,
                            ),
                            department_name=student.department.name,
                            major_name=student.major.name,
                        ),
                        note=application.note,
                        resume_link=application.resume_link,
                        cover_letter_link=application.cover_letter_link,
                        selected=application.selected,
                    ),
                )
            )
    return EmployerApplicationListResponse(applications=results)


class EmployerSpecificSummaryApplication(BaseModel):
    student: BriefStudentProfile


class EmployerSpecificSummaryResponse(BaseModel):
    summary_id: int
    application: EmployerSpecificSummaryApplication
    summary: EmployerSummary


class EmployerSpecificSummaryListResponse(BaseModel):
    summaries: list[EmployerSpecificSummaryResponse]


@router.get(
    "/{internship_id}/summaries",
    tags=["Employers"],
    summary="Retrieve internship summaries for a specific internship",
    description=(
        "Returns all summaries for a specified internship owned by the authenticated employer."
    ),
    response_model=EmployerSpecificSummaryListResponse,
)
async def get_internship_summaries(
    internship_id: int,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> EmployerSpecificSummaryListResponse:
    """
    Retrieve all summary submissions for a particular internship owned by the employer.

    Args:
        internship_id (int): The ID of the Internship.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        EmployerSpecificSummaryListResponse: List of summaries for the specified internship.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
    """
    assert_user_type(session_data, UserType.EMPLOYER)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_employer_by_id(db_session, account_id)
        company = profile.company
        internship = await get_internship_by_id(db_session, internship_id)
        if internship.company_id != company.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view summaries for internships owned by another company.",
            )

        summaries = internship.summaries
        results = []
        for summary in summaries:
            student: StudentAccount = summary.student
            contact = student.contact
            results.append(
                EmployerSpecificSummaryResponse(
                    summary_id=summary.id,
                    application=EmployerSpecificSummaryApplication(
                        student=BriefStudentProfile(
                            contact=Contact(
                                first_name=contact.first,
                                middle_name=contact.middle,
                                last_name=contact.last,
                                email=contact.email,
                                phone=contact.phone,
                            ),
                            department_name=student.department.name,
                            major_name=student.major.name,
                        ),
                    ),
                    summary=EmployerSummary(
                        summary=summary.summary,
                        file_link=summary.file_link,
                        employer_approval=summary.employer_approval,
                    ),
                )
            )
    return EmployerSpecificSummaryListResponse(summaries=results)
