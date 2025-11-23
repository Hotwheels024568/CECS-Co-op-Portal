from fastapi import APIRouter
from pydantic import BaseModel

from src.backend.globals import DB_MANAGER
from src.database.record_retrieval import get_departments, get_majors, get_skills

router = APIRouter()


class DepartmentsResponse(BaseModel):
    departments: list[str]


@router.get(
    "/departments",
    tags=["Catalog"],
    summary="List all available departments",
    description="Returns a list of all departments currently available in the catalog.",
    response_model=DepartmentsResponse,
)
async def get_all_departments() -> DepartmentsResponse:
    """
    Retrieve all department names available in the catalog.

    Args:
        None

    Returns:
        DepartmentsResponse: A dictionary containing a list of department names.
    """
    async with DB_MANAGER.session() as db_session:
        departments = await get_departments(db_session)
        names = [department.name for department in departments]
    return DepartmentsResponse(departments=names)


class MajorsResponse(BaseModel):
    majors: list[str]


@router.get(
    "/majors",
    tags=["Catalog"],
    summary="List all available majors",
    description="Returns a list of all majors currently available in the catalog.",
    response_model=MajorsResponse,
)
async def get_all_majors() -> MajorsResponse:
    """
    Retrieve all major names available in the catalog.

    Args:
        None

    Returns:
        MajorsResponse: A dictionary containing a list of major names.
    """
    async with DB_MANAGER.session() as db_session:
        majors = await get_majors(db_session)
        names = [major.name for major in majors]
    return MajorsResponse(majors=names)


class SkillsResponse(BaseModel):
    skills: list[str]


@router.get(
    "/skills",
    tags=["Catalog"],
    summary="List all available skills",
    description="Returns a list of all skills currently available in the catalog.",
    response_model=SkillsResponse,
)
async def get_all_skills() -> SkillsResponse:
    """
    Retrieve all skill names available in the catalog.

    Args:
        None

    Returns:
        SkillsResponse: A dictionary containing a list of skill names.
    """
    async with DB_MANAGER.session() as db_session:
        skills = await get_skills(db_session)
        names = [skill.name for skill in skills]
    return SkillsResponse(skills=names)
