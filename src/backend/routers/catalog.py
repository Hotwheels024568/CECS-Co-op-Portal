from fastapi import APIRouter

from src.backend.globals import DB_MANAGER
from src.database.record_retrieval import get_departments, get_majors, get_skills

router = APIRouter()


@router.get("/departments", response_model=dict)
async def get_all_departments() -> dict:
    """
    __
    """
    async with DB_MANAGER.session() as db_session:
        departments = await get_departments(db_session)

        list = []
        for department in departments:
            list.append({department.name})

    return {"departments": list}


@router.get("/majors", response_model=dict)
async def get_all_departments() -> dict:
    """
    __
    """
    async with DB_MANAGER.session() as db_session:
        majors = await get_majors(db_session)

        list = []
        for major in majors:
            list.append({major.name})

    return {"majors": list}


@router.get("/skills", response_model=dict)
async def get_all_departments() -> dict:
    """
    __
    """
    async with DB_MANAGER.session() as db_session:
        skills = await get_skills(db_session)

        list = []
        for skill in skills:
            list.append({skill.name})

    return {"skills": list}
