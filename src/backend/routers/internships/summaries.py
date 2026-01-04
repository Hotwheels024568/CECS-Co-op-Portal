from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, StringConstraints
from typing import Annotated, Optional

from src.backend.globals import AccountInfo, UserType, get_db_manager
from src.backend.routers.models import (
    BriefInternship,
    BriefStudentProfile,
    CompanyName,
    Contact,
    FacultyApplicationInfo,
    GeneralRequestResponse,
    StudentApplicationSummary,
    Summary,
)
from src.backend.routers.utils import assert_user_type, get_current_session
from src.database.manage import AsyncDBManager
from src.database.record_retrieval import (
    get_department_summaries,
    get_employer_by_id,
    get_faculty_by_id,
    get_summaries_by_student_id,
    get_summary_by_id,
)
from src.database.record_updating import update_summary
from src.database.sync_retrieval import (
    get_contact,
    get_department,
    get_employer_company,
    get_internship_company,
    get_major,
    get_summary_application,
    get_summary_company,
    get_summary_internship,
    get_summary_student,
)


router = APIRouter()

"""
1. “Should I create data expansion endpoints?”
Short answer: Only if your users (faculty, employers, students) actually need additional/minutely detailed data when interacting with summaries.
If most info is available elsewhere (on dedicated pages), and summaries only need context for grading/validation:
    You're already following a clean “minimal API” pattern—this is great.
Expansion endpoints (e.g., /summary/{id}/details) are only needed for “on-demand detail loading” in the UI when viewing a list is not enough.
You can always add these later if user feedback calls for it—your current separation of schemas and endpoints by role is solid and maintainable.
"""


class FacultySummaryResponse(BaseModel):
    summary_id: int
    application: FacultyApplicationInfo
    summary: Summary


class FacultySummaryListResponse(BaseModel):
    summaries: list[FacultySummaryResponse]


@router.get(
    "/department",
    tags=["Faculty"],
    summary="List all internship summaries for your department",
    description=(
        "Returns a list of internship summaries submitted by students in your department for review and grading. "
        "Each summary includes relevant details. Only accessible by authenticated faculty."
    ),
    response_model=FacultySummaryListResponse,
)
async def get_department_summaries_endpoint(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
    db_manager: AsyncDBManager = Depends(get_db_manager),
) -> FacultySummaryListResponse:
    """
    Retrieve all student internship summaries associated with the faculty member's department.

    Only authenticated faculty can access summaries. Each item provides student and internship info
    plus the summary and grade/approval status.

    Args:
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        FacultySummaryListResponse: List of summaries with minimal student and internship context.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
    """
    assert_user_type(session_data, UserType.FACULTY)

    account_id = session_data[1]["account_id"]
    async with db_manager.session() as db_session:
        profile = await get_faculty_by_id(db_session, account_id)
        department = await db_session.run_sync(get_department, profile)
        summaries = await get_department_summaries(db_session, department.id)

        results = []
        for summary in summaries:
            student = await db_session.run_sync(get_summary_student, summary)
            contact = await db_session.run_sync(get_contact, student)
            major = await db_session.run_sync(get_major, student)
            department = await db_session.run_sync(get_department, student)
            internship = await db_session.run_sync(get_summary_internship, summary)
            company = await db_session.run_sync(get_internship_company, internship)
            application = await db_session.run_sync(get_summary_application, summary)
            results.append(
                FacultySummaryResponse(
                    summary_id=summary.id,
                    application=FacultyApplicationInfo(
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
                        internship=BriefInternship(
                            company=CompanyName(name=company.name),
                            title=internship.title,
                            description=internship.description,
                            duration_weeks=internship.duration_weeks,
                            weekly_hours=internship.weekly_hours,
                            total_work_hours=internship.total_work_hours,
                        ),
                        coop_credit_eligibility=application.coop_credit_eligibility,
                    ),
                    summary=Summary(
                        summary=summary.summary,
                        file_link=summary.file_link,
                        employer_approval=summary.employer_approval,
                        letter_grade=summary.letter_grade,
                    ),
                )
            )
    return FacultySummaryListResponse(summaries=results)


class UpdateSummaryGradeRequest(BaseModel):
    # Could use an Enum but due to the number of possible grades its not worth it for this assignment
    letter_grade: Annotated[str, StringConstraints(min_length=1, max_length=2)]


@router.patch(
    "/{summary_id}/grade",
    tags=["Faculty"],
    summary="Assign or update a letter grade for a student summary",
    description=(
        "Allows department faculty to assign a grade to a student's submitted internship summary. "
        "Only faculty in the same department as the student are authorized to grade the summary."
    ),
    response_model=GeneralRequestResponse,
)
async def update_summary_grade(
    summary_id: int,
    data: UpdateSummaryGradeRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
    db_manager: AsyncDBManager = Depends(get_db_manager),
) -> GeneralRequestResponse:
    """
    Submit or update the letter grade for a specific internship summary.

    Args:
        summary_id (int): The ID of the summary to be graded.
        data (UpdateSummaryGradeRequest): The desired letter grade.
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
        profile = await get_faculty_by_id(db_session, account_id)
        faculty_dept = await db_session.run_sync(get_department, profile)
        summary = await get_summary_by_id(db_session, summary_id)
        student = await db_session.run_sync(get_summary_student, summary)
        student_dept = await db_session.run_sync(get_department, student)
        if student_dept.id != faculty_dept.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only grade internship summaries for students in your own department.",
            )

        result = await update_summary(
            db_session, summary_id, letter_grade=data.letter_grade, commit=True
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Summary grade could not be updated due to a server or database error.",
        )
    return GeneralRequestResponse(success=True, message="Summary graded")


class StudentSummaryResponse(BaseModel):
    summary_id: int
    application: StudentApplicationSummary
    summary: Summary


class StudentSummaryListResponse(BaseModel):
    summaries: list[StudentSummaryResponse]


@router.get(
    "/me",
    tags=["Students"],
    summary="Get all internship summaries for the authenticated student",
    description=(
        "Returns all internship summaries submitted by the authenticated student. "
        "Each record includes summary content, grade status, and basic internship context."
    ),
    response_model=StudentSummaryListResponse,
)
async def get_student_summaries_endpoint(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
    db_manager: AsyncDBManager = Depends(get_db_manager),
) -> StudentSummaryListResponse:
    """
    Retrieve all internship summaries submitted by the currently authenticated student.

    Args:
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        StudentSummaryListResponse: List of student summaries with internship details.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
    """
    assert_user_type(session_data, UserType.STUDENT)

    account_id = session_data[1]["account_id"]
    async with db_manager.session() as db_session:
        summaries = await get_summaries_by_student_id(db_session, account_id)

        results = []
        for summary in summaries:
            internship = await db_session.run_sync(get_summary_internship, summary)
            application = await db_session.run_sync(get_summary_application, summary)
            company = await db_session.run_sync(get_internship_company, internship)
            results.append(
                StudentSummaryResponse(
                    summary_id=summary.id,
                    application=StudentApplicationSummary(
                        internship=BriefInternship(
                            company=CompanyName(name=company.name),
                            title=internship.title,
                            description=internship.description,
                            duration_weeks=internship.duration_weeks,
                            weekly_hours=internship.weekly_hours,
                            total_work_hours=internship.total_work_hours,
                        ),
                        coop_credit_eligibility=application.coop_credit_eligibility,
                    ),
                    summary=Summary(
                        summary=summary.summary,
                        file_link=summary.file_link,
                        employer_approval=summary.employer_approval,
                        letter_grade=summary.letter_grade,
                    ),
                )
            )
    return StudentSummaryListResponse(summaries=results)


class UpdateSummaryRequest(BaseModel):
    summary_text: str
    file_link: Optional[Annotated[str, StringConstraints(max_length=255)]]


@router.patch(
    "/{summary_id}/update",
    tags=["Students"],
    summary="Update internship summary text or file",
    description=(
        "Allows students to update the text or attached file for an existing internship summary. "
        "Students may update only their own summaries."
    ),
    response_model=GeneralRequestResponse,
)
async def update_summary_text(
    summary_id: int,
    data: UpdateSummaryRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
    db_manager: AsyncDBManager = Depends(get_db_manager),
) -> GeneralRequestResponse:
    """
    Update the text and/or file attachment for a student's internship summary.

    Args:
        summary_id (int): The ID of the summary to update.
        data (UpdateSummaryRequest): The updated summary text and optional updated file link.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: Indicates success or failure with explanatory message.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
        HTTPException (500): If the operation fails.
    """
    assert_user_type(session_data, UserType.STUDENT)

    async with db_manager.session() as db_session:
        summary = await get_summary_by_id(db_session, summary_id)
        student = await db_session.run_sync(get_summary_student, summary)
        if student.id != session_data[1]["account_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the student who owns this summary may update its contents.",
            )

        result = await update_summary(
            db_session, summary_id, data.summary_text, data.file_link, commit=True
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Summary could not be updated due to a server or database error.",
        )
    return GeneralRequestResponse(success=True, message="Summary updated")


class UpdateSummaryApprovalRequest(BaseModel):
    approval: bool


@router.patch(
    "/{summary_id}/approval",
    tags=["Employers"],
    summary="Update employer approval status for an internship summary",
    description=(
        "Allows an employer to approve or reject a student's summary for their internship. "
        "Only available to the internship's owner (employer)."
    ),
    response_model=GeneralRequestResponse,
)
async def update_summary_approval(
    summary_id: int,
    data: UpdateSummaryApprovalRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
    db_manager: AsyncDBManager = Depends(get_db_manager),
) -> GeneralRequestResponse:
    """
    Change the approval status of a summary associated with an internship you own.

    Args:
        summary_id (int): The ID of the summary to approve.
        data (UpdateSummaryApprovalRequest): The updated boolean approval status.
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
        profile = await get_employer_by_id(db_session, account_id)
        company = await db_session.run_sync(get_employer_company, profile)
        summary = await get_summary_by_id(db_session, summary_id)
        intern_company = await db_session.run_sync(get_summary_company, summary)

        if intern_company.id != company.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only employers of internship's company may update an internship summary's employer approval status.",
            )

        result = await update_summary(
            db_session, summary_id, employer_approval=data.approval, commit=True
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Employer approval status could not be updated.",
        )
    return GeneralRequestResponse(success=True, message="Employer approval status updated")
