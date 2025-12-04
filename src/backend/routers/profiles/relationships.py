from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.backend.globals import AccountInfo, UserType, get_db_manager
from src.backend.routers.models import Contact, FacultyProfile, StudentProfile
from src.backend.routers.profiles.faculty import FacultyProfileResponse
from src.backend.routers.profiles.students import StudentProfileResponse
from src.backend.routers.utils import assert_user_type, get_current_session
from src.database.manage import AsyncDBManager
from src.database.record_retrieval import get_faculty, get_faculty_by_id, get_student_by_id

router = APIRouter()


class StudentListResponse(BaseModel):
    students: list[StudentProfileResponse]


@router.get(
    "/departments/me/students",
    tags=["Faculty"],
    summary="Retrieve all students in the faculty's department",
    description=(
        "Fetch a list of all student profiles associated with the authenticated faculty member's department. "
        "Only callable by authenticated faculty users."
    ),
    response_model=StudentListResponse,
)
async def get_dept_students(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
    db_manager: AsyncDBManager = Depends(get_db_manager),
) -> StudentListResponse:
    """
    Retrieve all students within the authenticated faculty member's department.

    This endpoint fetches a list of student profiles for the faculty member's department.
    Only callable by authenticated faculty users.

    Args:
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        DepartmentStudentsResponse: Contains a list of students' contact information and profile details
            (e.g., department name, major, credit hours, GPA, semester/year started, transfer status, resume link).

    Raises:
        HTTPException (401): If session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
    """
    assert_user_type(session_data, UserType.FACULTY)

    account_id = session_data[1]["account_id"]
    async with db_manager.session() as db_session:
        profile = await get_faculty_by_id(db_session, account_id)
        students = profile.department.students

        results = []
        for student in students:
            contact = student.contact
            results.append(
                StudentProfileResponse(
                    contact=Contact(
                        first_name=contact.first,
                        middle_name=contact.middle,
                        last_name=contact.last,
                        email=contact.email,
                        phone=contact.phone,
                    ),
                    profile=StudentProfile(
                        department=student.department.name,
                        major_name=student.major.name,
                        credit_hours=student.credit_hours,
                        gpa=student.gpa,
                        start_semester=student.start_semester,
                        start_year=student.start_year,
                        transfer=student.transfer,
                        resume_link=student.resume_link,
                    ),
                )
            )
    return StudentListResponse(students=results)


class FacultyListResponse(BaseModel):
    faculty: list[FacultyProfileResponse]


@router.get(
    "/departments/me/faculty",
    tags=["Students"],
    summary="Retrieve all faculty in the student's department",
    description=(
        "Fetch a list of all faculty profiles associated with the authenticated student's department. "
        "Only callable by authenticated student users."
    ),
    response_model=FacultyListResponse,
)
async def get_dept_faculty(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
    db_manager: AsyncDBManager = Depends(get_db_manager),
) -> FacultyListResponse:
    """
    Retrieve all faculty in the authenticated student's department.

    This endpoint returns a list of faculty profiles for the student's department.
    Only callable by authenticated student users.

    Args:
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        DepartmentFacultyResponse: Contains a list of faculty contact information and profile details
            (e.g., department name).

    Raises:
        HTTPException (401): If session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
    """
    assert_user_type(session_data, UserType.STUDENT)

    account_id = session_data[1]["account_id"]
    async with db_manager.session() as db_session:
        profile = await get_student_by_id(db_session, account_id)
        faculty = profile.department.faculty

        results = []
        for staff in faculty:
            contact = staff.contact
            results.append(
                FacultyProfileResponse(
                    contact=Contact(
                        first_name=contact.first,
                        middle_name=contact.middle,
                        last_name=contact.last,
                        email=contact.email,
                        phone=contact.phone,
                    ),
                    profile=FacultyProfile(department=staff.department.name),
                )
            )
    return FacultyListResponse(faculty=results)


@router.get(
    "/faculty",
    tags=["Employers"],
    summary="Retrieve all faculty across all departments",
    description=(
        "Fetch a list of all faculty profiles across the university. "
        "Only callable by authenticated employer users."
    ),
    response_model=FacultyListResponse,
)
async def get_all_faculty(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
    db_manager: AsyncDBManager = Depends(get_db_manager),
) -> FacultyListResponse:
    """
    Retrieve all faculty across all departments.

    This endpoint returns a list of all faculty profiles within the university,
    accessible only to authenticated employer users.

    Args:
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        DepartmentFacultyResponse: Contains a list of faculty contact information and profile details
            (e.g., department name).

    Raises:
        HTTPException (401): If session is invalid or expired.
        HTTPException (403): If the session's user type is invalid.
    """
    assert_user_type(session_data, UserType.EMPLOYER)

    async with db_manager.session() as db_session:
        faculty = await get_faculty(db_session)

        results = []
        for staff in faculty:
            contact = staff.contact
            results.append(
                FacultyProfileResponse(
                    contact=Contact(
                        first_name=contact.first,
                        middle_name=contact.middle,
                        last_name=contact.last,
                        email=contact.email,
                        phone=contact.phone,
                    ),
                    profile=FacultyProfile(department=staff.department.name),
                )
            )
    return FacultyListResponse(faculty=results)
