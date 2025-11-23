from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, StringConstraints
from typing import Annotated, Optional

from src.backend.globals import DB_MANAGER, AccountInfo, UserType
from src.backend.routers.models import Application, Summary
from src.backend.routers.utils import assert_user_type, get_current_session
from src.database.record_retrieval import (
    get_department_summaries,
    get_employer_by_id,
    get_faculty_by_id,
    get_student_by_id,
    get_summary_by_id,
)
from src.database.record_updating import update_summary
from src.database.schema import Company, Department, StudentAccount

router = APIRouter()


@router.get("/department-summaries", response_model=dict)
async def get_department_summaries_endpoint(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> dict:
    """
    __
    """
    assert_user_type(session_data, UserType.FACULTY)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_faculty_by_id(db_session, account_id)
        department = profile.department
        summaries = await get_department_summaries(db_session, department.id)

        list = []
        for summary in summaries:
            list.append(
                {
                    "summary": summary.summary,
                    "file_link": summary.file_link,
                    "employer_approval": summary.employer_approval,
                    "letter_grade": summary.letter_grade,
                }
            )

    # TODO: What do we return? The summary info and maybe company and/or student and/or internship info
    return {}


class UpdateSummaryGradeRequest(BaseModel):
    summary_id: int
    # Could use an Enum but due to the number of possible grades its not worth it for this assignment
    letter_grade: Annotated[str, StringConstraints(min_length=1, max_length=2)]


@router.patch("/grade", response_model=dict)
async def update_summary_grade(
    data: UpdateSummaryGradeRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> dict:
    """
    __
    """
    assert_user_type(session_data, UserType.FACULTY)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_faculty_by_id(db_session, account_id)
        faculty_dept = profile.department
        summary = await get_summary_by_id(db_session, data.summary_id)
        student_dept: Department = summary.student.department
        if student_dept != faculty_dept:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Only faculty of the student's department may grade this summary.",
            )

        _ = await update_summary(
            db_session, data.summary_id, letter_grade=data.letter_grade, commit=True
        )

    return {"success": True}


@router.get("/my-summaries", response_model=dict)
async def get_student_summaries(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> dict:
    """
    __
    """
    assert_user_type(session_data, UserType.STUDENT)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_student_by_id(db_session, account_id)
        summaries = profile.summaries

        list = []
        for summary in summaries:
            list.append(
                {
                    "summary": summary.summary,
                    "file_link": summary.file_link,
                    "employer_approval": summary.employer_approval,
                    "letter_grade": summary.letter_grade,
                }
            )

    # TODO: What do we return? The summary info and maybe company and/or internship info
    return {}


class UpdateSummaryApprovalRequest(BaseModel):
    summary_id: int
    summary_text: str
    file_link: Optional[Annotated[str, StringConstraints(max_length=255)]]


@router.patch("/update", response_model=dict)
async def update_summary_text(
    data: UpdateSummaryApprovalRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> dict:
    """
    __
    """
    assert_user_type(session_data, UserType.STUDENT)

    async with DB_MANAGER.session() as db_session:
        summary = await get_summary_by_id(db_session, data.summary_id)
        student: StudentAccount = summary.student
        if student.id != session_data[1]["account_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the owner of the summary can update this summary.",
            )

        _ = await update_summary(
            db_session, data.summary_id, data.summary_text, data.file_link, commit=True
        )

    return {"success": True}


# TODO: get summaries of specific internship or all own internships?
@router.get("/internship-summaries", response_model=dict)
async def get_internship_summaries(
    internship_id: Optional[int] = None,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> dict:
    """
    __
    """
    assert_user_type(session_data, UserType.EMPLOYER)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_employer_by_id(db_session, account_id)
        internships = profile.company.internships

        list = []
        for internship in internships:
            summaries = internship.summaries
            for summary in summaries:
                list.append(
                    {
                        "summary": summary.summary,
                        "file_link": summary.file_link,
                        "employer_approval": summary.employer_approval,
                    }
                )

    # TODO: What do we return? The summary info and maybe student and/or internship info
    return {}


class UpdateSummaryApprovalRequest(BaseModel):
    summary_id: int
    approval: bool


@router.patch("/approval", response_model=dict)
async def update_summary_approval(
    data: UpdateSummaryApprovalRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> dict:
    """
    __
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
                detail="Only the owner of the internship can update this summary's employer approval.",
            )

        _ = await update_summary(
            db_session, data.summary_id, employer_approval=data.approval, commit=True
        )

    return {"success": True}
