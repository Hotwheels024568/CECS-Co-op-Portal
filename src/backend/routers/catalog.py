from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.backend.globals import get_db_manager
from src.database.manage import AsyncDBManager
from src.database.record_retrieval import get_departments, get_majors, get_skills

router = APIRouter()


class CatalogItem(BaseModel):
    id: int
    name: str


class DepartmentsResponse(BaseModel):
    departments: list[CatalogItem]


@router.get(
    "/departments",
    tags=["Catalog"],
    summary="List all available departments",
    description="Returns a list of all departments currently available in the catalog.",
    response_model=DepartmentsResponse,
)
async def get_all_departments(
    db_manager: AsyncDBManager = Depends(get_db_manager),
) -> DepartmentsResponse:
    """
    Retrieve all department names available in the catalog.

    Returns:
        DepartmentsResponse: A dictionary containing a list of department IDs and names.
    """
    async with db_manager.session() as db_session:
        departments = await get_departments(db_session)
        list = [CatalogItem(id=department.id, name=department.name) for department in departments]
    return DepartmentsResponse(departments=list)


class MajorsResponse(BaseModel):
    majors: list[CatalogItem]


@router.get(
    "/majors",
    tags=["Catalog"],
    summary="List all available majors",
    description="Returns a list of all majors currently available in the catalog.",
    response_model=MajorsResponse,
)
async def get_all_majors(db_manager: AsyncDBManager = Depends(get_db_manager)) -> MajorsResponse:
    """
    Retrieve all major names available in the catalog.

    Returns:
        MajorsResponse: A dictionary containing a list of major IDs and names.
    """
    async with db_manager.session() as db_session:
        majors = await get_majors(db_session)
        list = [CatalogItem(id=major.id, name=major.name) for major in majors]
    return MajorsResponse(majors=list)


class SkillsResponse(BaseModel):
    skills: list[CatalogItem]


@router.get(
    "/skills",
    tags=["Catalog"],
    summary="List all available skills",
    description="Returns a list of all skills currently available in the catalog.",
    response_model=SkillsResponse,
)
async def get_all_skills(db_manager: AsyncDBManager = Depends(get_db_manager)) -> SkillsResponse:
    """
    Retrieve all skill names available in the catalog.

    Returns:
        SkillsResponse: A dictionary containing a list of skill IDs and names.
    """
    async with db_manager.session() as db_session:
        skills = await get_skills(db_session)
        list = [CatalogItem(id=skill.id, name=skill.name) for skill in skills]
    return SkillsResponse(skills=list)
