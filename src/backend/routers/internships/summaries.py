from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, StringConstraints
from typing import Annotated, Optional

from src.backend.globals import DB_MANAGER, AccountInfo, UserType
from src.backend.routers.models import (
    BriefApplication,
    BriefInternship,
    BriefStudentProfile,
    CompanyName,
    Contact,
    GeneralRequestResponse,
    Summary,
)
from src.backend.routers.utils import assert_user_type, get_current_session
from src.database.record_retrieval import (
    get_department_summaries,
    get_employer_by_id,
    get_faculty_by_id,
    get_internship_by_id,
    get_student_by_id,
    get_summary_by_id,
)
from src.database.record_updating import update_summary
from src.database.schema import Company, Internship, StudentAccount

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
    application: BriefApplication
    summary: Summary


class FacultySummaryListResponse(BaseModel):
    summaries: list[FacultySummaryResponse]


@router.get(
    "/department-summaries",
    tags=["Faculty"],
    summary="List all internship summaries for your department",
    description=(
        "Returns a list of internship summaries submitted by students in your department for review and grading. "
        "Each summary includes relevant application details. Only accessible by authenticated faculty."
    ),
    response_model=FacultySummaryListResponse,
)
async def get_department_summaries_endpoint(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
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
    async with DB_MANAGER.session() as db_session:
        profile = await get_faculty_by_id(db_session, account_id)
        department = profile.department
        summaries = await get_department_summaries(db_session, department.id)

        list = []
        for summary in summaries:
            student: StudentAccount = summary.student
            contact = student.contact
            internship: Internship = summary.internship
            application = summary.application
            list.append(
                FacultySummaryResponse(
                    summary_id=summary.id,
                    application=BriefApplication(
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
                    summary=Summary(
                        summary=summary.summary,
                        file_link=summary.file_link,
                        employer_approval=summary.employer_approval,
                        letter_grade=summary.letter_grade,
                    ),
                )
            )
    return FacultySummaryListResponse(summaries=list)


class UpdateSummaryGradeRequest(BaseModel):
    summary_id: int
    # Could use an Enum but due to the number of possible grades its not worth it for this assignment
    letter_grade: Annotated[str, StringConstraints(min_length=1, max_length=2)]


@router.patch(
    "/grade",
    tags=["Faculty"],
    summary="Assign or update a letter grade for a student summary",
    description=(
        "Allows department faculty to assign a grade to a student's submitted internship summary. "
        "Only faculty in the same department as the student are authorized to grade the summary."
    ),
    response_model=GeneralRequestResponse,
)
async def update_summary_grade(
    data: UpdateSummaryGradeRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    Submit or update the letter grade for a specific internship summary.

    Args:
        data (UpdateSummaryGradeRequest): The summary ID and desired letter grade.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: Success status and optional message.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
        HTTPException (500): If the operation fails.
    """
    assert_user_type(session_data, UserType.FACULTY)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_faculty_by_id(db_session, account_id)
        faculty_dept = profile.department.id
        summary = await get_summary_by_id(db_session, data.summary_id)
        student: StudentAccount = summary.student
        student_dept = student.department.id
        if student_dept != faculty_dept:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only grade internship summaries for students in your own department.",
            )

        result = await update_summary(
            db_session, data.summary_id, letter_grade=data.letter_grade, commit=True
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Summary grade could not be updated due to a server or database error.",
        )
    return GeneralRequestResponse(success=True, message="")


class StudentSummaryApplication(BaseModel):
    internship: BriefInternship
    coop_credit_eligibility: bool


class StudentSummaryResponse(BaseModel):
    summary_id: int
    application: StudentSummaryApplication
    summary: Summary


class StudentSummaryListResponse(BaseModel):
    summaries: list[StudentSummaryResponse]


@router.get(
    "/my-summaries",
    tags=["Students"],
    summary="Get all internship summaries for the authenticated student",
    description=(
        "Returns all internship summaries submitted by the authenticated student. "
        "Each record includes summary content, grade status, and basic internship context."
    ),
    response_model=StudentSummaryListResponse,
)
async def get_student_summaries(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
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
    async with DB_MANAGER.session() as db_session:
        profile = await get_student_by_id(db_session, account_id)
        summaries = profile.summaries

        list = []
        for summary in summaries:
            internship: Internship = summary.internship
            application = summary.application
            list.append(
                StudentSummaryListResponse(
                    summary_id=summary.id,
                    application=StudentSummaryApplication(
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
                    summary=Summary(
                        summary=summary.summary,
                        file_link=summary.file_link,
                        employer_approval=summary.employer_approval,
                        letter_grade=summary.letter_grade,
                    ),
                )
            )
    return StudentSummaryListResponse(summaries=list)


class UpdateSummaryApprovalRequest(BaseModel):
    summary_id: int
    summary_text: str
    file_link: Optional[Annotated[str, StringConstraints(max_length=255)]]


@router.patch(
    "/update",
    tags=["Students"],
    summary="Update internship summary text or file",
    description=(
        "Allows students to update the text or attached file for an existing internship summary. "
        "Students may update only their own summaries."
    ),
    response_model=GeneralRequestResponse,
)
async def update_summary_text(
    data: UpdateSummaryApprovalRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    Update the text and/or file attachment for a student's internship summary.

    Args:
        data (UpdateSummaryApprovalRequest): Summary ID, new summary text, new file link (optional).
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: Indicates success or failure.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
        HTTPException (500): If the operation fails.
    """
    assert_user_type(session_data, UserType.STUDENT)

    async with DB_MANAGER.session() as db_session:
        summary = await get_summary_by_id(db_session, data.summary_id)
        student: StudentAccount = summary.student
        if student.id != session_data[1]["account_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the student who owns this summary may update its content.",
            )

        result = await update_summary(
            db_session, data.summary_id, data.summary_text, data.file_link, commit=True
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Summary could not be updated due to a server or database error.",
        )
    return GeneralRequestResponse(success=True, message="")


class EmployerSummaryInternship(BaseModel):
    title: str
    description: str
    duration_weeks: int
    weekly_hours: int
    total_work_hours: int


class EmployerSummaryApplication(BaseModel):
    student: BriefStudentProfile
    internship: EmployerSummaryInternship


class EmployerSummary(BaseModel):
    summary: str
    file_link: Optional[str]
    employer_approval: bool


class EmployerSummaryResponse(BaseModel):
    summary_id: int
    application: EmployerSummaryApplication
    summary: EmployerSummary


class EmployerSummaryListResponse(BaseModel):
    summaries: list[EmployerSummaryResponse]


@router.get(
    "/internship-summaries",
    tags=["Employers"],
    summary="Retrieve all internship summaries for the employer's company",
    description=(
        "Returns internship summaries submitted by students associated with any internships at the employer's company. "
        "Only accessible by authenticated employers."
    ),
    response_model=EmployerSummaryListResponse,
)
async def get_internship_summaries(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
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
    async with DB_MANAGER.session() as db_session:
        profile = await get_employer_by_id(db_session, account_id)
        company = profile.company
        internships = company.internships

        list = []
        for internship in internships:
            summaries = internship.summaries
            for summary in summaries:
                student: StudentAccount = summary.student
                contact = student.contact
                list.append(
                    EmployerSummaryResponse(
                        summary_id=summary.id,
                        application=EmployerSummaryApplication(
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
                            internship=EmployerSummaryInternship(
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
    return EmployerSummaryListResponse(summaries=list)


class EmployerSpecificSummaryRequest(BaseModel):
    internship_id: int


class EmployerSpecificSummaryApplication(BaseModel):
    student: BriefStudentProfile


class EmployerSpecificSummaryResponse(BaseModel):
    summary_id: int
    application: EmployerSpecificSummaryApplication
    summary: EmployerSummary


class EmployerSpecificSummaryListResponse(BaseModel):
    summaries: list[EmployerSpecificSummaryResponse]


@router.get(
    "/internship-summaries",
    tags=["Employers"],
    summary="Retrieve internship summaries for a specific internship",
    description=(
        "Returns all summaries for a specified internship owned by the authenticated employer."
    ),
    response_model=EmployerSpecificSummaryListResponse,
)
async def get_internship_summaries(
    data: EmployerSpecificSummaryRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> EmployerSpecificSummaryListResponse:
    """
    Retrieve all summary submissions for a particular internship owned by the employer.

    Args:
        data (EmployerSpecificSummaryRequest): Internship ID.
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
        internship = await get_internship_by_id(db_session, data.internship_id)
        if internship.company_id != company.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view summaries for internships owned by another company.",
            )

        summaries = internship.summaries
        list = []
        for summary in summaries:
            student: StudentAccount = summary.student
            contact = student.contact
            list.append(
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
    return EmployerSpecificSummaryListResponse(summaries=list)


class UpdateSummaryApprovalRequest(BaseModel):
    summary_id: int
    approval: bool


@router.patch(
    "/approval",
    tags=["Employers"],
    summary="Update employer approval status for an internship summary",
    description=(
        "Allows an employer to approve or reject a student's summary for their internship. "
        "Only available to the internship's owner (employer)."
    ),
    response_model=GeneralRequestResponse,
)
async def update_summary_approval(
    data: UpdateSummaryApprovalRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    Change the approval status of a summary associated with an internship you own.

    Args:
        data (UpdateSummaryApprovalRequest): Summary ID and new approval status (bool).
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: Indicates result of the update.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
        HTTPException (500): If the operation fails.
    """
    assert_user_type(session_data, UserType.EMPLOYER)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_employer_by_id(db_session, account_id)
        company = profile.company
        summary = await get_summary_by_id(db_session, data.summary_id)
        intern_company: Company = summary.application.company

        if intern_company.id != company.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only employers of internship's company may update an internship summary's employer approval status.",
            )

        result = await update_summary(
            db_session, data.summary_id, employer_approval=data.approval, commit=True
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Employer approval status could not be updated due to a server or database error.",
        )
    return GeneralRequestResponse(success=True, message="")
