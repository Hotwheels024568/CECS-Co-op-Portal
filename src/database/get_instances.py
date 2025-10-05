from typing import Optional, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.schema import (
    Account,
    Address,
    Company,
    ContactInfo,
    Employer,
    InternshipOpportunity,
    Student,
    Faculty,
)

from src.database.functions import get_first_element, get_row


async def get_company_by_name(session: AsyncSession, name: str) -> Optional[Company]:
    statement = select(Company).where(Company.name == name)
    return get_first_element(session, statement)


async def get_contact_by_email(
    session: AsyncSession, email: str
) -> Optional[ContactInfo]:
    statement = select(ContactInfo).where(ContactInfo.email == email)
    return get_first_element(session, statement)


async def get_employer_profile_by_id(
    session: AsyncSession, profile_id: int
) -> Optional[Employer]:
    statement = select(Employer).where(Employer.id == profile_id)
    return await get_first_element(session, statement)


async def get_student_profile_by_id(
    session: AsyncSession, profile_id: int
) -> Optional[Student]:
    statement = select(Student).where(Student.id == profile_id)
    return await get_first_element(session, statement)


async def get_faculty_profile_by_id(
    session: AsyncSession, profile_id: int
) -> Optional[Faculty]:
    statement = select(Faculty).where(Faculty.id == profile_id)
    return await get_first_element(session, statement)


async def get_profile_by_account_id(
    session: AsyncSession, account_id: int
) -> Optional[Union[Employer, Student, Faculty]]:
    # 1. Get the account to learn profile_id and user_type
    statement = select(Account.profile_id, Account.user_type).where(
        Account.id == account_id
    )
    result = await get_row(session, statement)
    if result is None:
        return None

    profile_id, user_type = result
    if profile_id is None:
        return None

    # 2. Resolve to the correct profile table
    if user_type == "Employer":
        return await get_employer_profile_by_id(session, profile_id)
    elif user_type == "Student":
        return await get_student_profile_by_id(session, profile_id)
    elif user_type == "Faculty":
        return await get_faculty_profile_by_id(session, profile_id)
    else:
        return None


async def get_internship_by_id(
    session: AsyncSession, id: int
) -> Optional[InternshipOpportunity]:
    statement = select(InternshipOpportunity).where(InternshipOpportunity.id == id)
    return await get_first_element(session, statement)
