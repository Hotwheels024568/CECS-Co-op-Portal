from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.schema import (
    Account,
    Address,
    Company,
    ContactInfo,
    EmployerAccount,
    Department,
    Major,
    StudentAccount,
    FacultyAccount,
    Internship,
    InternshipMajor,
    Skill,
    InternshipReqSkill,
    InternshipPrefSkill,
    InternshipApplication,
    InternshipSummary,
)

from src.database.functions import get_all_rows, get_first_element


"""  Result helpers
Method                  Complexity          Syntax                              Example
.filter_by()            Simple checks       Keyword Args                        .filter_by(name='Alice', age=30)
.where & .filter()      Complex Checks      Column expressions & operators      .where(and_(User.name == 'Alice', User.age > 25))
    Supports operators ((>, <, ==, >=, <=, !=) and expressions (and_, or_, in_, like_, is_, etc.)
        Operators:      https://docs.sqlalchemy.org/en/20/core/operators.html
        Expressions:    https://docs.sqlalchemy.org/en/20/core/sqlelement.html
"""


async def get_account(session: AsyncSession, id: int) -> Optional[Account]:
    return await session.get(Account, id)


async def get_account(
    session: AsyncSession, username: str, password: str
) -> Optional[Account]:
    statement = select(Account).filter_by(username=username, password=password)
    return await get_first_element(session, statement)


async def login(session: AsyncSession, username: str, password: str) -> Optional[Account]:
    return await get_account(session, username, password)


async def get_address(session: AsyncSession, id: int) -> Optional[Address]:
    return await session.get(Address, id)


async def get_company(session: AsyncSession, id: int) -> Optional[Company]:
    return await session.get(Company, id)


async def get_company_by_name(session: AsyncSession, name: str) -> Optional[Company]:
    statement = select(Company).filter_by(name=name)
    return await get_first_element(session, statement)


async def get_contact(session: AsyncSession, id: int) -> Optional[ContactInfo]:
    return await session.get(ContactInfo, id)


async def get_contact_by_email(
    session: AsyncSession, email: str
) -> Optional[ContactInfo]:
    statement = select(ContactInfo).filter_by(email=email)
    return await get_first_element(session, statement)


async def get_employer(session: AsyncSession, id: int) -> Optional[EmployerAccount]:
    return await session.get(EmployerAccount, id)


async def get_department(session: AsyncSession, id: int) -> Optional[Department]:
    return await session.get(Department, id)


async def get_department_by_name(
    session: AsyncSession, name: str
) -> Optional[Department]:
    statement = select(Department).filter_by(name=name)
    return await get_first_element(session, statement)


async def get_major(session: AsyncSession, id: int) -> Optional[Major]:
    return await session.get(Major, id)


async def get_major_by_name(session: AsyncSession, name: str) -> Optional[Major]:
    statement = select(Major).filter_by(name=name)
    return await get_first_element(session, statement)


async def get_student(session: AsyncSession, id: int) -> Optional[StudentAccount]:
    return await session.get(StudentAccount, id)


# TODO: Paginate
async def get_student_by_dept(
    session: AsyncSession, department: str
) -> Optional[List[StudentAccount]]:
    statement = select(StudentAccount).filter_by(department=department)
    return await get_all_rows(session, statement)


async def get_faculty(session: AsyncSession, id: int) -> Optional[FacultyAccount]:
    return await session.get(FacultyAccount, id)


async def get_faculty_by_dept(
    session: AsyncSession, department: str
) -> Optional[FacultyAccount]:
    statement = select(FacultyAccount).filter_by(department=department)
    return await get_first_element(session, statement)


async def get_internship(session: AsyncSession, id: int) -> Optional[Internship]:
    return await session.get(Internship, id)


async def get_internship_majors(session: AsyncSession, id: int) -> Optional[List[str]]:
    statement = select(InternshipMajor.major).filter_by(internship_id=id)
    return await get_all_rows(session, statement)


async def get_internship_required_skills(
    session: AsyncSession, id: int
) -> Optional[List[str]]:
    statement = select(InternshipReqSkill.skill).filter_by(internship_id=id)
    return await get_all_rows(session, statement)


async def get_internship_preferred_skills(
    session: AsyncSession, id: int
) -> Optional[List[str]]:
    statement = select(InternshipPrefSkill.skill).filter_by(internship_id=id)
    return await get_all_rows(session, statement)


async def get_skill(session: AsyncSession, name: str) -> Optional[Skill]:
    statement = select(Skill).filter_by(name=name)
    return await get_first_element(session, statement)


async def get_application(
    session: AsyncSession, internship_id: int, student_id: int
) -> Optional[InternshipApplication]:
    return await session.get(InternshipApplication, (internship_id, student_id))


async def get_summary(session: AsyncSession, id: int) -> Optional[InternshipSummary]:
    return await session.get(InternshipSummary, id)
