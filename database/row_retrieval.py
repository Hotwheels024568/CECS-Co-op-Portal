from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import select
from typing import Optional

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
    build_select_from_filters,
    get_first_element_list,
    get_first_element,
    get_row_by_pk,
)


async def get_account_by_id(session: AsyncSession, id: int) -> Optional[Account]:
    return await get_row_by_pk(session, Account, id)


async def get_account_by_username(session: AsyncSession, username: str) -> Optional[Account]:
    return await get_first_element(session, build_select_from_filters(Account, username=username))


async def get_address_by_id(session: AsyncSession, id: int) -> Optional[Address]:
    return await get_row_by_pk(session, Address, id)


async def get_companies(session: AsyncSession) -> list[Company]:
    return await get_first_element_list(session, build_select_from_filters(Company))


async def get_company_by_id(session: AsyncSession, id: int) -> Optional[Company]:
    return await get_row_by_pk(session, Company, id)


async def get_company_by_name(session: AsyncSession, name: str) -> Optional[Company]:
    return await get_first_element(session, build_select_from_filters(Company, name=name))


async def get_contact_by_id(session: AsyncSession, id: int) -> Optional[ContactInfo]:
    return await get_row_by_pk(session, ContactInfo, id)


async def get_contact_by_email(session: AsyncSession, email: str) -> Optional[ContactInfo]:
    return await get_first_element(session, build_select_from_filters(ContactInfo, email=email))


async def get_employer_by_id(session: AsyncSession, id: int) -> Optional[EmployerProfile]:
    return await get_row_by_pk(session, EmployerProfile, id)


async def get_departments(session: AsyncSession) -> list[Department]:
    return await get_first_element_list(session, build_select_from_filters(Department))


async def get_department_by_id(session: AsyncSession, id: int) -> Optional[Department]:
    return await get_row_by_pk(session, Department, id)


async def get_department_by_name(session: AsyncSession, name: str) -> Optional[Department]:
    return await get_first_element(session, build_select_from_filters(Department, name=name))


async def get_majors(session: AsyncSession) -> list[Major]:
    return await get_first_element_list(session, build_select_from_filters(Major))


async def get_major_by_id(session: AsyncSession, id: int) -> Optional[Major]:
    return await get_row_by_pk(session, Major, id)


async def get_major_by_name(session: AsyncSession, name: str) -> Optional[Major]:
    return await get_first_element(session, build_select_from_filters(Major, name=name))


async def get_student_by_id(session: AsyncSession, id: int) -> Optional[StudentProfile]:
    return await get_row_by_pk(session, StudentProfile, id)


async def get_faculty(session: AsyncSession) -> list[FacultyProfile]:
    return await get_first_element_list(session, build_select_from_filters(FacultyProfile))


async def get_faculty_by_id(session: AsyncSession, id: int) -> Optional[FacultyProfile]:
    return await get_row_by_pk(session, FacultyProfile, id)


async def get_internship_by_id(session: AsyncSession, id: int) -> Optional[Internship]:
    return await get_row_by_pk(session, Internship, id)


async def get_internship_majors_by_id(session: AsyncSession, id: int) -> list[Major]:
    statement = (
        select(Major)
        .join(InternshipMajor, InternshipMajor.major_id == Major.id)
        .filter(InternshipMajor.internship_id == id)
    )
    return await get_first_element_list(session, statement)


async def get_skills(session: AsyncSession) -> list[Skill]:
    return await get_first_element_list(session, build_select_from_filters(Skill))


async def get_skill_by_id(session: AsyncSession, id: int) -> Optional[Skill]:
    return await get_row_by_pk(session, Skill, id)


async def get_skill_by_name(session: AsyncSession, name: str) -> Optional[Skill]:
    return await get_first_element(session, build_select_from_filters(Skill, name=name))


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
    return await get_row_by_pk(session, InternshipApplication, id)


async def get_application_from_ids(
    session: AsyncSession, internship_id: int, student_id: int
) -> Optional[InternshipApplication]:
    statement = build_select_from_filters(
        InternshipApplication, internship_id=internship_id, student_id=student_id
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
    statement = build_select_from_filters(InternshipApplication, internship_id=internship_id)
    return await get_first_element_list(session, statement)


async def get_selected_internship_applications(
    session: AsyncSession, internship_id: int
) -> list[InternshipApplication]:
    statement = build_select_from_filters(
        InternshipApplication, internship_id=internship_id, selected=True
    )
    return await get_first_element_list(session, statement)


async def get_summary_by_id(session: AsyncSession, id: int) -> Optional[InternshipSummary]:
    return await get_row_by_pk(session, InternshipSummary, id)


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
