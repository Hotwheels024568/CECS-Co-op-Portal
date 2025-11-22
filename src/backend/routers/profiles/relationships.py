from fastapi import APIRouter, Depends

from src.backend.globals import DB_MANAGER, AccountInfo, UserType
from src.backend.routers.profiles.faculty import router
from src.backend.routers.profiles.students import router
from src.backend.routers.utils import assert_user_type, get_current_session
from src.database.record_retrieval import (
    get_faculty,
    get_faculty_by_id,
    get_faculty_by_department_id,
    get_student_by_id,
    get_students_by_department_id,
)

router = APIRouter()


@router.get("/students", response_model=dict)
async def get_dept_students(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> dict:
    """
    __
    """
    assert_user_type(session_data, UserType.FACULTY)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_faculty_by_id(db_session, account_id)
        students = await get_students_by_department_id(db_session, profile.department)

        student_list = []
        for student in students:
            contact = student.contact

            student_list.append(
                {
                    "contact": {
                        "first_name": contact.first,
                        "middle_name": contact.middle,
                        "last_name": contact.last,
                        "email": contact.email,
                        "phone": contact.phone,
                    },
                    "profile": {
                        "department": student.department.name,
                        "major": student.major.name,
                        "credit_hours": student.credit_hours,
                        "gpa": student.gpa,
                        "start_semester": student.start_semester,
                        "start_year": student.start_year,
                        "transfer": student.transfer,
                        "resume_link": student.resume_link,
                    },
                }
            )

    return {
        "success": True,
        "students": student_list,
    }


@router.get("/faculty", response_model=dict)
async def get_dept_faculty(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> dict:
    """
    __
    """
    assert_user_type(session_data, UserType.FACULTY)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_student_by_id(db_session, account_id)
        faculty = await get_faculty_by_department_id(db_session, profile.department)

        faculty_list = []
        for staff in faculty:
            contact = staff.contact

            faculty_list.append(
                {
                    "contact": {
                        "first_name": contact.first,
                        "middle_name": contact.middle,
                        "last_name": contact.last,
                        "email": contact.email,
                        "phone": contact.phone,
                    },
                    "profile": {"department": staff.department.name},
                }
            )

    return {
        "success": True,
        "students": faculty_list,
    }


@router.get("/faculty", response_model=dict)
async def get_all_faculty(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> dict:
    """
    __
    """
    assert_user_type(session_data, UserType.EMPLOYER)

    async with DB_MANAGER.session() as db_session:
        faculty = await get_faculty(db_session)

        faculty_list = []
        for staff in faculty:
            contact = staff.contact

            faculty_list.append(
                {
                    "contact": {
                        "first_name": contact.first,
                        "middle_name": contact.middle,
                        "last_name": contact.last,
                        "email": contact.email,
                        "phone": contact.phone,
                    },
                    "profile": {"department": staff.department.name},
                }
            )

    return {
        "success": True,
        "students": faculty_list,
    }
