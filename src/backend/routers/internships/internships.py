from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, StringConstraints
from typing import Annotated, Optional

from src.backend.globals import DB_MANAGER, AccountInfo, UserType
from src.backend.routers.models import (
    Address,
    AddressCreationDetails,
    Company,
    GeneralRequestResponse,
    Internship,
    InternshipStatus,
    LocationType,
)
from src.backend.routers.utils import assert_user_type, get_current_session
from src.database.internship_insertion import create_internship
from src.database.internship_retrieval import search_internships
from src.database.record_retrieval import get_employer_by_id, get_internship_by_id

router = APIRouter()


"""
Employers
    update
        after setting the status to pending start, create the student summary records for the selected candidates
"""


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


@router.get(
    "/search",
    tags=["Internships"],
    summary="__",
    description=("__. " "__."),
    response_model=InternshipSearchResponse,
)
async def search_internships_endpoint(
    data: InternshipSearchRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> InternshipSearchResponse:
    """
    __

    Args:
        data (InternshipCreationRequest): __
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: Success status and optional message.

    Raises:
        HTTPException (401): If the session is invalid or expired.
    """
    async with DB_MANAGER.session() as db_session:
        internships, count = await search_internships(
            db_session,
            data.company_id,
            data.title,
            data.location_type,
            data.duration_weeks,
            data.weekly_hours,
            data.status,
            data.majors,
            data.required_skills,
            data.preferred_skills,
            data.page,
            data.page_size,
        )

        list = []
        for internship in internships:
            company = internship.company
            address = company.address
            list.append(
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
    return InternshipSearchResponse(internships=list, count=count)


@router.get(
    f"/{id}",
    tags=["Internships"],
    summary="__",
    description=("__. " "__."),
    response_model=Internship,
)
async def get_internship(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> Internship:
    """
    __

    Args:
        data (InternshipCreationRequest): __
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: Success status and optional message.

    Raises:
        HTTPException (400): If the internship does not exist.
        HTTPException (401): If the session is invalid or expired.
    """
    async with DB_MANAGER.session() as db_session:
        internship = await get_internship_by_id(db_session, id)
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
    address: Optional[AddressCreationDetails]


@router.post(
    "/create",
    tags=["Employers"],
    summary="__",
    description=("__. " "__."),
    response_model=GeneralRequestResponse,
)
async def create_internship_endpoint(
    data: InternshipCreationRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    __

    Args:
        data (InternshipCreationRequest): __
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: Success status and optional message.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
        HTTPException (500): If the operation fails.
    """
    assert_user_type(session_data, UserType.EMPLOYER)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        result, msg = await create_internship(
            db_session,
            account_id,
            data.title,
            data.description,
            data.location_type,
            None,
            data.duration_weeks,
            data.weekly_hours,
            data.salary_info,
            data.status,
            data.majors,
            data.required_skills,
            data.preferred_skills,
            data.address.address_line1,
            data.address.address_line2,
            data.address.city,
            data.address.state_province,
            data.address.zip_postal,
            data.address.country,
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


# NOTE: make /{id}
@router.patch(
    f"/update/{id}",
    tags=["Employers"],
    summary="__",
    description=("__. " "__."),
    response_model=GeneralRequestResponse,
)
async def update_internship_endpoint(
    data: InternshipUpdateRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    __

    Args:
        data (InternshipUpdateRequest): __
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: Success status and optional message.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
        HTTPException (500): If the operation fails.
    """
    assert_user_type(session_data, UserType.EMPLOYER)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_employer_by_id(db_session, account_id)
        internship = await get_internship_by_id(db_session, id)
        if internship.company_id != profile.company_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Only __")
    #     result, msg = await update_internship(
    #         db_session,
    #         internship_id,
    #         data.title,
    #         data.description,
    #         data.location_type,
    #         None,
    #         data.duration_weeks,
    #         data.weekly_hours,
    #         data.salary_info,
    #         data.status,
    #         data.majors,
    #         data.required_skills,
    #         data.preferred_skills,
    #         data.address.address_line1,
    #         data.address.address_line2,
    #         data.address.city,
    #         data.address.state_province,
    #         data.address.zip_postal,
    #         data.address.country,
    #     )

    # if not result:
    #     raise HTTPException(
    #         status.HTTP_500_INTERNAL_SERVER_ERROR, f"Internship could not be created. Reason: {msg}"
    #     )
    # return GeneralRequestResponse(success=True, message=msg)


# Could make a delete_internship endpoint
#   Would have to handle dangling FKs
