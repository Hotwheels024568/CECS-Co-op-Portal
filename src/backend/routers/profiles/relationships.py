from fastapi import APIRouter, Depends

from src.backend.globals import DB_MANAGER, AccountInfo, UserType
from src.backend.routers.profiles.faculty import router
from src.backend.routers.profiles.students import router
from src.backend.routers.utils import assert_user_type, get_current_session
from src.database.record_retrieval import (
    get_faculty,
    get_faculty_by_id,
    get_student_by_id,
)

router = APIRouter()


@router.get("/department-students", response_model=dict)
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
        students = profile.department.students

        list = []
        for student in students:
            contact = student.contact

            list.append(
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

    return {"students": list}


@router.get("/department-faculty", response_model=dict)
async def get_dept_faculty(
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> dict:
    """
    __
    """
    assert_user_type(session_data, UserType.STUDENT)

    account_id = session_data[1]["account_id"]
    async with DB_MANAGER.session() as db_session:
        profile = await get_student_by_id(db_session, account_id)
        faculty = profile.department.faculty

        list = []
        for staff in faculty:
            contact = staff.contact

            list.append(
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

    return {"faculty": list}


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

        list = []
        for staff in faculty:
            contact = staff.contact

            list.append(
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

    return {"faculty": list}
