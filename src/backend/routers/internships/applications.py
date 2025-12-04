from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, StringConstraints
from typing import Annotated, Optional

from src.backend.globals import DB_MANAGER, AccountInfo, UserType
from src.backend.routers.models import (
    FacultyApplicationInfo,
    BriefInternship,
    BriefStudentProfile,
    CompanyName,
    Contact,
    GeneralRequestResponse,
    InternshipStatus,
    StudentApplicationInfo,
)
from src.backend.routers.utils import assert_user_type, get_current_session
from src.database.internship_insertion import create_application
from src.database.record_deletion import delete_record
from src.database.record_retrieval import (
    get_application_by_id,
    get_department_applications,
    get_faculty_by_id,
    get_internship_by_id,
    get_student_by_id,
)
from src.database.record_updating import update_application
from src.utils_semesters import semesters_since_enrollment

router = APIRouter()


class FacultyApplicationResponse(BaseModel):
    application_id: int
    application: FacultyApplicationInfo


class FacultyApplicationListResponse(BaseModel):
    applications: list[FacultyApplicationResponse]


@router.get(
    "/department",
    tags=["Faculty"],
    summary="List all internship applications for your department",
    description=(
        "Returns a list of internship applications submitted by students in your department for review and grading. "
        "Each application includes relevant details. Only accessible by authenticated faculty."
    ),
    response_model=FacultyApplicationListResponse,
)
async def get_department_applications_endpoint(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> FacultyApplicationListResponse:
    """
    Retrieve all student internship applications associated with the faculty member's department.

    Only authenticated faculty can access applications. Each item provides student and internship info
    plus the application and credit eligibility status.

    Args:
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        FacultyApplicationListResponse: List of applications with minimal student and internship context.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
    """
    assert_user_type(session_data, UserType.FACULTY)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_faculty_by_id(db_session, account_id)
        department = profile.department
        applications = await get_department_applications(db_session, department.id)

        results = []
        for application in applications:
            student = application.student
            contact = student.contact
            internship = application.internship
            results.append(
                FacultyApplicationResponse(
                    application_id=application.id,
                    application=FacultyApplicationInfo(
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
                        internship=BriefInternship(
                            company=CompanyName(name=internship.company.name),
                            title=internship.title,
                            description=internship.description,
                            duration_weeks=internship.duration_weeks,
                            weekly_hours=internship.weekly_hours,
                            total_work_hours=internship.total_work_hours,
                        ),
                        coop_credit_eligibility=application.coop_credit_eligibility,
                    ),
                )
            )
    return FacultyApplicationListResponse(applications=results)


class StudentApplicationCreationRequest(BaseModel):
    internship_id: int
    note: Optional[Annotated[str, StringConstraints(max_length=255)]] = None
    resume_link: Optional[Annotated[str, StringConstraints(max_length=255)]] = None
    cover_letter_link: Optional[Annotated[str, StringConstraints(max_length=255)]] = None


@router.post(
    "/create",
    tags=["Students"],
    summary="Submit a new application for an internship",
    description=(
        "Allows an authorized student to apply for an internship. Students must provide the internship ID and "
        "may optionally include a note, resume link, and cover letter link."
    ),
    response_model=GeneralRequestResponse,
)
async def create_application_endpoint(
    data: StudentApplicationCreationRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    Submit a new internship application as a student.

    This endpoint lets an authenticated student apply for an internship by submitting required and optional materials.
    Co-op credit eligibility is checked based on the student's profile and the internship details.

    Args:
        data (StudentApplicationCreationRequest): Details for the application, including internship ID and optional documents.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: Indicates success or failure with explanatory message.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
        HTTPException (500): If the operation fails.
    """
    assert_user_type(session_data, UserType.STUDENT)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_student_by_id(db_session, account_id)
        internship = await get_internship_by_id(db_session, data.internship_id)
        application, msg = await create_application(
            db_session,
            account_id,
            data.internship_id,
            (
                profile.gpa >= 2
                and internship.duration_weeks >= 7
                and internship.total_work_hours >= 140
                and semesters_since_enrollment(profile.start_semester, profile.start_year)
                >= (1 if profile.transfer else 2)
            ),
            data.note,
            data.resume_link,
            data.cover_letter_link,
        )

    if not application:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Application could not be created. Reason: {msg}",
        )
    return GeneralRequestResponse(success=True, message=msg)


class StudentApplicationResponse(BaseModel):
    application_id: int
    application: StudentApplicationInfo


class StudentApplicationListResponse(BaseModel):
    applications: list[StudentApplicationResponse]


@router.get(
    "/me",
    tags=["Students"],
    summary="Get all internship applications for the authenticated student",
    description=(
        "Returns all internship applications submitted by the authenticated student. "
        "Each record includes application details and basic internship context."
    ),
    response_model=StudentApplicationListResponse,
)
async def get_student_applications(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> StudentApplicationListResponse:
    """
    Retrieve all internship applications submitted by the currently authenticated student.

    Args:
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        StudentApplicationListResponse: List of applications application details and internship context.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
    """
    assert_user_type(session_data, UserType.STUDENT)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_student_by_id(db_session, account_id)
        applications = profile.applications

        results = []
        for application in applications:
            internship = application.internship
            results.append(
                StudentApplicationResponse(
                    application_id=application.id,
                    application=StudentApplicationInfo(
                        internship=BriefInternship(
                            company=CompanyName(name=internship.company.name),
                            title=internship.title,
                            description=internship.description,
                            duration_weeks=internship.duration_weeks,
                            weekly_hours=internship.weekly_hours,
                            total_work_hours=internship.total_work_hours,
                        ),
                        coop_credit_eligibility=application.coop_credit_eligibility,
                        note=application.note,
                        resume_link=application.resume_link,
                        cover_letter_link=application.cover_letter_link,
                    ),
                )
            )
    return StudentApplicationListResponse(applications=results)


class StudentApplicationDeletionRequest(BaseModel):
    note: Optional[Annotated[str, StringConstraints(max_length=255)]] = None
    resume_link: Optional[Annotated[str, StringConstraints(max_length=255)]] = None
    cover_letter_link: Optional[Annotated[str, StringConstraints(max_length=255)]] = None


@router.patch(
    "/{application_id}/update",
    tags=["Students"],
    summary="Update a student's internship application",
    description="Allows a student to update their internship application details (note, resume link, cover letter link).",
    response_model=GeneralRequestResponse,
)
async def update_application_endpoint(
    application_id: int,
    data: StudentApplicationDeletionRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    Update a student's existing internship application.

    This endpoint enables students to update their submitted application details, such as their note,
    resume link, or cover letter link. Only authorized students that own the application may perform this action.

    Args:
        application_id (int): The ID of the application to be updated.
        data (StudentApplicationDeletionRequest): Updated application fields.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: Indicates success or failure with explanatory message.

    Raises:
        HTTPException (400): If the application does not exist.
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid or not allowed to preform the action.
        HTTPException (500): If the operation fails.
    """
    assert_user_type(session_data, UserType.STUDENT)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_student_by_id(db_session, account_id)
        application = await get_application_by_id(db_session, application_id)
        if not application:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Application does not exist.")
        if application.student_id != account_id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Only the application owner can update an application."
            )
        internship = application.internship

        result = await update_application(
            db_session,
            application_id,
            (
                profile.gpa >= 2
                and internship.duration_weeks >= 7
                and internship.total_work_hours >= 140
                and semesters_since_enrollment(profile.start_semester, profile.start_year)
                >= (1 if profile.transfer else 2)
            ),
            data.note,
            data.resume_link,
            data.cover_letter_link,
        )

    if not result:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Application could not be updated."
        )
    return GeneralRequestResponse(success=True, message="Application updated")


@router.delete(
    "/{application_id}/delete",
    tags=["Students"],
    summary="Delete a student's internship application",
    description=(
        "Allows an authorized student to delete their internship application, provided that the associated "
        "internship is still accepting applications. Application ownership and internship status are checked."
    ),
    response_model=GeneralRequestResponse,
)
async def delete_application(
    application_id: int,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    Delete a student's internship application by ID.

    This endpoint enables a student to delete their application for an internship, as long as
    the internship is still open. It enforces ownership and eligibility checks to prevent
    unauthorized actions or deletions when applications are closed.

    Args:
        application_id (int): The unique identifier of the application to delete.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: Indicates success or failure with explanatory message.

    Raises:
        HTTPException (400): If the application does not exist.
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid or not allowed to preform the action.
        HTTPException (500): If the operation fails.
    """
    assert_user_type(session_data, UserType.STUDENT)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        application = await get_application_by_id(db_session, application_id)
        if not application:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Application does not exist.")
        if application.student_id != account_id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Only the application owner can update an application."
            )
        internship = application.internship
        if internship.status != InternshipStatus.OPEN:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Applications can only be deleted while internship applications are open.",
            )

        result = await delete_record(db_session, application, commit=True)

    if not result:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Application could not be deleted."
        )
    return GeneralRequestResponse(success=True, message="Application deleted")
