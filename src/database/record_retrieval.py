from typing import Optional
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


async def get_employer_by_id(session: AsyncSession, id: int) -> Optional[EmployerAccount]:
    return await session.get(EmployerAccount, id)


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


async def get_student_by_id(session: AsyncSession, id: int) -> Optional[StudentAccount]:
    return await session.get(StudentAccount, id)


async def get_faculty(session: AsyncSession) -> list[FacultyAccount]:
    return await get_first_column_element_of_all_rows(session, select(FacultyAccount))


async def get_faculty_by_id(session: AsyncSession, id: int) -> Optional[FacultyAccount]:
    return await session.get(FacultyAccount, id)


async def get_internship_by_id(session: AsyncSession, id: int) -> Optional[Internship]:
    return await session.get(Internship, id)


async def get_skills(session: AsyncSession) -> list[Skill]:
    return await get_first_column_element_of_all_rows(session, select(Skill))


async def get_skill_by_id(session: AsyncSession, id: int) -> Optional[Skill]:
    return await session.get(Skill, id)


async def get_skill_by_name(session: AsyncSession, name: str) -> Optional[Skill]:
    statement = select(Skill).filter_by(name=name)
    return await get_first_column_element(session, statement)


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
        .filter(StudentAccount.department_id == department_id)
    )
    return await get_first_column_element_of_all_rows(session, statement)


async def get_summary_by_id(session: AsyncSession, id: int) -> Optional[InternshipSummary]:
    return await session.get(InternshipSummary, id)


async def get_department_summaries(
    session: AsyncSession, department_id: int
) -> list[InternshipSummary]:
    statement = (
        select(InternshipSummary)
        .join(InternshipSummary.application)
        .join(InternshipApplication.student)
        .filter(StudentAccount.department_id == department_id)
    )
    return await get_first_column_element_of_all_rows(session, statement)
