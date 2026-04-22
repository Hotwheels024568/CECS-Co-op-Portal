from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import ColumnElement, Select, Sequence, and_, select
from typing import Any, Optional

from database.schema import (
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
from database.utils import (
    TModel,
    get_first_element,
    get_first_element_list,
)


"""  Result helpers
Method                  Complexity          Syntax                              Example
.filter_by()            Simple checks       Keyword Args                        .filter_by(name='Alice', age=30)
.where & .filter()      Complex Checks      Column expressions & operators      .where(and_(User.name == 'Alice', User.age > 25))
    Supports operators (>, <, ==, >=, <=, !=) and expressions (and_, or_, in_, like_, is_, etc.)
        Operators:      https://docs.sqlalchemy.org/en/20/core/operators.html
        Expressions:    https://docs.sqlalchemy.org/en/20/core/sqlelement.html
"""


async def get_row_by_PK(session: AsyncSession, model: type[TModel], PK: Any) -> Optional[TModel]:
    return await session.get(model, PK)


async def _build_select_by_filter_statement(
    session: AsyncSession,
    model: type[TModel],
    *,
    filters: Sequence[ColumnElement[bool]] = (),
    **fields: Any,
) -> Select[tuple[TModel]]:
    """
    __
    """
    conditions: list[ColumnElement[bool]] = list(filters)

    for name, value in fields.items():
        col = getattr(model, name)
        conditions.append(col.is_(None) if value is None else (col == value))

    statement = select(model)
    if conditions:
        statement = statement.where(and_(*conditions))
    return statement


"""
Example:
    await get_first_element_list_by_filter(
        session,
        User,
        filters=(User.email.ilike("%@umich.edu"), or_(User.is_active.is_(True), User.is_admin.is_(True))),
        deleted_at=None,   # keyword fields still work; None => IS NULL
    )
"""


async def get_first_element_by_filter(
    session: AsyncSession,
    model: type[TModel],
    *,
    filters: Sequence[ColumnElement[bool]] = (),
    **fields: Any,
) -> Optional[TModel]:
    return await get_first_element(
        session, _build_select_by_filter_statement(model, filters=filters, **fields)
    )


async def get_first_element_list_by_filter(
    session: AsyncSession,
    model: type[TModel],
    *,
    filters: Sequence[ColumnElement[bool]] = (),
    **fields: Any,
) -> list[TModel]:
    return await get_first_element(
        session, _build_select_by_filter_statement(model, filters=filters, **fields)
    )


async def get_account_by_id(session: AsyncSession, id: int) -> Optional[Account]:
    return await get_row_by_PK(session, Account, id)
    # return await session.get(Account, id)


async def get_account_by_username(session: AsyncSession, username: str) -> Optional[Account]:
    return await get_first_element_by_filter(session, Account, username=username)
    # statement = select(Account).filter_by(username=username)
    # return await get_first_element(session, statement)


async def get_address_by_id(session: AsyncSession, id: int) -> Optional[Address]:
    return await session.get(Address, id)


async def get_companies(session: AsyncSession) -> list[Company]:
    return await get_first_element_list(session, select(Company))


async def get_company_by_id(session: AsyncSession, id: int) -> Optional[Company]:
    return await session.get(Company, id)


async def get_company_by_name(session: AsyncSession, name: str) -> Optional[Company]:
    statement = select(Company).filter_by(name=name)
    return await get_first_element(session, statement)


async def get_contact_by_id(session: AsyncSession, id: int) -> Optional[ContactInfo]:
    return await session.get(ContactInfo, id)


async def get_contact_by_email(session: AsyncSession, email: str) -> Optional[ContactInfo]:
    statement = select(ContactInfo).filter_by(email=email)
    return await get_first_element(session, statement)


async def get_employer_by_id(session: AsyncSession, id: int) -> Optional[EmployerProfile]:
    return await session.get(EmployerProfile, id)


async def get_departments(session: AsyncSession) -> list[Department]:
    return await get_first_element_list(session, select(Department))


async def get_department_by_id(session: AsyncSession, id: int) -> Optional[Department]:
    return await session.get(Department, id)


async def get_department_by_name(session: AsyncSession, name: str) -> Optional[Department]:
    statement = select(Department).filter_by(name=name)
    return await get_first_element(session, statement)


async def get_majors(session: AsyncSession) -> list[Major]:
    return await get_first_element_list(session, select(Major))


async def get_major_by_id(session: AsyncSession, id: int) -> Optional[Major]:
    return await session.get(Major, id)


async def get_major_by_name(session: AsyncSession, name: str) -> Optional[Major]:
    statement = select(Major).filter_by(name=name)
    return await get_first_element(session, statement)


async def get_student_by_id(session: AsyncSession, id: int) -> Optional[StudentProfile]:
    return await session.get(StudentProfile, id)


async def get_faculty(session: AsyncSession) -> list[FacultyProfile]:
    return await get_first_element_list(session, select(FacultyProfile))


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
    return await get_first_element_list(session, statement)


async def get_skills(session: AsyncSession) -> list[Skill]:
    return await get_first_element_list(session, select(Skill))


async def get_skill_by_id(session: AsyncSession, id: int) -> Optional[Skill]:
    return await session.get(Skill, id)


async def get_skill_by_name(session: AsyncSession, name: str) -> Optional[Skill]:
    statement = select(Skill).filter_by(name=name)
    return await get_first_element(session, statement)


async def get_internship_required_skills_by_id(session: AsyncSession, id: int) -> list[Skill]:
    statement = (
        select(Skill)
        .join(InternshipReqSkill, InternshipReqSkill.skill_id == Skill.id)
        .filter(InternshipReqSkill.internship_id == id)
    )
    return await get_first_element_list(session, statement)


async def get_internship_preferred_skills_by_id(session: AsyncSession, id: int) -> list[Skill]:
    statement = (
        select(Skill)
        .join(InternshipPrefSkill, InternshipPrefSkill.skill_id == Skill.id)
        .filter(InternshipPrefSkill.internship_id == id)
    )
    return await get_first_element_list(session, statement)


async def get_application_by_id(session: AsyncSession, id: int) -> Optional[InternshipApplication]:
    return await session.get(InternshipApplication, id)


async def get_application_from_ids(
    session: AsyncSession, internship_id: int, student_id: int
) -> Optional[InternshipApplication]:
    statement = select(InternshipApplication).filter_by(
        internship_id=internship_id, student_id=student_id
    )
    return await get_first_element(session, statement)


async def get_department_applications(
    session: AsyncSession, department_id: int
) -> list[InternshipApplication]:
    statement = (
        select(InternshipApplication)
        .join(InternshipApplication.student)
        .filter(StudentProfile.department_id == department_id)
    )
    return await get_first_element_list(session, statement)


async def get_internship_applications(
    session: AsyncSession, internship_id: int
) -> list[InternshipApplication]:
    statement = select(InternshipApplication).filter_by(internship_id=internship_id)
    return await get_first_element_list(session, statement)


async def get_selected_internship_applications(
    session: AsyncSession, internship_id: int
) -> list[InternshipApplication]:
    statement = select(InternshipApplication).filter_by(internship_id=internship_id, selected=True)
    return await get_first_element_list(session, statement)


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
    return await get_first_element_list(session, statement)


async def get_summaries_by_internship_id(
    session: AsyncSession, internship_id: int
) -> list[InternshipSummary]:
    statement = (
        select(InternshipSummary)
        .join(InternshipSummary.application)
        .filter(InternshipApplication.internship_id == internship_id)
    )
    return await get_first_element_list(session, statement)


async def get_department_summaries(
    session: AsyncSession, department_id: int
) -> list[InternshipSummary]:
    statement = (
        select(InternshipSummary)
        .join(InternshipSummary.application)
        .join(InternshipApplication.student)
        .filter(StudentProfile.department_id == department_id)
    )
    return await get_first_element_list(session, statement)
