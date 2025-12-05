from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import select
from typing import Optional

from src.database.schema import (
    Account,
    Address,
    Company,
    ContactInfo,
    EmployerProfile,
    Department,
    FacultyProfile,
    Major,
    StudentProfile,
    Internship,
    InternshipMajor,
    Skill,
    InternshipReqSkill,
    InternshipPrefSkill,
    InternshipApplication,
    InternshipSummary,
)
from src.database.utils import (
    get_first_column_element,
    get_first_column_element_of_all_rows,
)


"""  Result helpers
Method                  Complexity          Syntax                              Example
.filter_by()            Simple checks       Keyword Args                        .filter_by(name='Alice', age=30)
.where & .filter()      Complex Checks      Column expressions & operators      .where(and_(User.name == 'Alice', User.age > 25))
    Supports operators (>, <, ==, >=, <=, !=) and expressions (and_, or_, in_, like_, is_, etc.)
        Operators:      https://docs.sqlalchemy.org/en/20/core/operators.html
        Expressions:    https://docs.sqlalchemy.org/en/20/core/sqlelement.html
"""


async def get_account_by_id(session: AsyncSession, id: int) -> Optional[Account]:
    return await session.get(Account, id)


async def get_account_by_username(session: AsyncSession, username: str) -> Optional[Account]:
    statement = select(Account).filter_by(username=username)
    return await get_first_column_element(session, statement)


async def get_address_by_id(session: AsyncSession, id: int) -> Optional[Address]:
    return await session.get(Address, id)


async def get_companies(session: AsyncSession) -> list[Company]:
    return await get_first_column_element_of_all_rows(session, select(Company))


async def get_company_by_id(session: AsyncSession, id: int) -> Optional[Company]:
    return await session.get(Company, id)


async def get_company_by_name(session: AsyncSession, name: str) -> Optional[Company]:
    statement = select(Company).filter_by(name=name)
    return await get_first_column_element(session, statement)


async def get_contact_by_id(session: AsyncSession, id: int) -> Optional[ContactInfo]:
    return await session.get(ContactInfo, id)


async def get_contact_by_email(session: AsyncSession, email: str) -> Optional[ContactInfo]:
    statement = select(ContactInfo).filter_by(email=email)
    return await get_first_column_element(session, statement)


async def get_employer_by_id(session: AsyncSession, id: int) -> Optional[EmployerProfile]:
    return await session.get(EmployerProfile, id)


async def get_departments(session: AsyncSession) -> list[Department]:
    return await get_first_column_element_of_all_rows(session, select(Department))


async def get_department_by_id(session: AsyncSession, id: int) -> Optional[Department]:
    return await session.get(Department, id)


async def get_department_by_name(session: AsyncSession, name: str) -> Optional[Department]:
    statement = select(Department).filter_by(name=name)
    return await get_first_column_element(session, statement)


async def get_majors(session: AsyncSession) -> list[Major]:
    return await get_first_column_element_of_all_rows(session, select(Major))


async def get_major_by_id(session: AsyncSession, id: int) -> Optional[Major]:
    return await session.get(Major, id)


async def get_major_by_name(session: AsyncSession, name: str) -> Optional[Major]:
    statement = select(Major).filter_by(name=name)
    return await get_first_column_element(session, statement)


async def get_student_by_id(session: AsyncSession, id: int) -> Optional[StudentProfile]:
    return await session.get(StudentProfile, id)


async def get_faculty(session: AsyncSession) -> list[FacultyProfile]:
    return await get_first_column_element_of_all_rows(session, select(FacultyProfile))


async def get_faculty_by_id(session: AsyncSession, id: int) -> Optional[FacultyProfile]:
    return await session.get(FacultyProfile, id)


async def get_internship_by_id(session: AsyncSession, id: int) -> Optional[Internship]:
    return await session.get(Internship, id)


async def get_internship_majors_by_id(session: AsyncSession, id: int) -> list[Major]:
    statement = (
        select(Major)
        .join(InternshipMajor, InternshipMajor.major_id == Major.id)
        .filter(InternshipMajor.internship_id == id)
    )
    return await get_first_column_element_of_all_rows(session, statement)


async def get_skills(session: AsyncSession) -> list[Skill]:
    return await get_first_column_element_of_all_rows(session, select(Skill))


async def get_skill_by_id(session: AsyncSession, id: int) -> Optional[Skill]:
    return await session.get(Skill, id)


async def get_skill_by_name(session: AsyncSession, name: str) -> Optional[Skill]:
    statement = select(Skill).filter_by(name=name)
    return await get_first_column_element(session, statement)


async def get_internship_required_skills_by_id(session: AsyncSession, id: int) -> list[Skill]:
    statement = (
        select(Skill)
        .join(InternshipReqSkill, InternshipReqSkill.skill_id == Skill.id)
        .filter(InternshipReqSkill.internship_id == id)
    )
    return await get_first_column_element_of_all_rows(session, statement)


async def get_internship_preferred_skills_by_id(session: AsyncSession, id: int) -> list[Skill]:
    statement = (
        select(Skill)
        .join(InternshipPrefSkill, InternshipPrefSkill.skill_id == Skill.id)
        .filter(InternshipPrefSkill.internship_id == id)
    )
    return await get_first_column_element_of_all_rows(session, statement)


async def get_application_by_id(session: AsyncSession, id: int) -> Optional[InternshipApplication]:
    return await session.get(InternshipApplication, id)


async def get_application_from_ids(
    session: AsyncSession, internship_id: int, student_id: int
) -> Optional[InternshipApplication]:
    statement = select(InternshipApplication).filter_by(
        internship_id=internship_id, student_id=student_id
    )
    return await get_first_column_element(session, statement)


async def get_department_applications(
    session: AsyncSession, department_id: int
) -> list[InternshipApplication]:
    statement = (
        select(InternshipApplication)
        .join(InternshipApplication.student)
        .filter(StudentProfile.department_id == department_id)
    )
    return await get_first_column_element_of_all_rows(session, statement)


async def get_internship_applications(
    session: AsyncSession, internship_id: int
) -> list[InternshipApplication]:
    statement = select(InternshipApplication).filter_by(internship_id=internship_id)
    return await get_first_column_element_of_all_rows(session, statement)


async def get_selected_internship_applications(
    session: AsyncSession, internship_id: int
) -> list[InternshipApplication]:
    statement = select(InternshipApplication).filter_by(internship_id=internship_id, selected=True)
    return await get_first_column_element_of_all_rows(session, statement)


async def get_summary_by_id(session: AsyncSession, id: int) -> Optional[InternshipSummary]:
    return await session.get(InternshipSummary, id)


async def get_summaries_by_student_id(
    session: AsyncSession, student_id: int
) -> list[InternshipSummary]:
    statement = (
        select(InternshipSummary)
        .join(InternshipSummary.application)
        .join(InternshipApplication.student)
        .filter(StudentProfile.id == student_id)
    )
    return await get_first_column_element_of_all_rows(session, statement)


async def get_summaries_by_internship_id(
    session: AsyncSession, internship_id: int
) -> list[InternshipSummary]:
    statement = (
        select(InternshipSummary)
        .join(InternshipSummary.application)
        .filter(InternshipApplication.internship_id == internship_id)
    )
    return await get_first_column_element_of_all_rows(session, statement)


async def get_department_summaries(
    session: AsyncSession, department_id: int
) -> list[InternshipSummary]:
    statement = (
        select(InternshipSummary)
        .join(InternshipSummary.application)
        .join(InternshipApplication.student)
        .filter(StudentProfile.department_id == department_id)
    )
    return await get_first_column_element_of_all_rows(session, statement)
