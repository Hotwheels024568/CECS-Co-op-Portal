from typing import Optional, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.schema import (
    Accounts,
    Addresses,
    Companies,
    ContactInfo,
    Employers,
    InternshipOpportunities,
    Students,
    Faculty,
)

from src.database.functions import get_first_element, get_row


async def get_account_by_id(session: AsyncSession, id: int) -> Optional[Accounts]:
    return await session.get(Accounts, id)


async def get_address_by_id(session: AsyncSession, id: int) -> Optional[Addresses]:
    return await session.get(Addresses, id)


async def get_company_by_id(session: AsyncSession, id: int) -> Optional[Companies]:
    return await session.get(Companies, id)


async def get_company_by_name(session: AsyncSession, name: str) -> Optional[Companies]:
    statement = select(Companies).where(Companies.name == name)
    return await get_first_element(session, statement)


async def get_contact_by_id(session: AsyncSession, id: int) -> Optional[ContactInfo]:
    return await session.get(ContactInfo, id)


async def get_contact_by_email(
    session: AsyncSession, email: str
) -> Optional[ContactInfo]:
    statement = select(ContactInfo).where(ContactInfo.email == email)
    return await get_first_element(session, statement)


async def get_employer_profile_by_id(
    session: AsyncSession, profile_id: int
) -> Optional[Employers]:
    return await session.get(Employers, profile_id)


async def get_student_profile_by_id(
    session: AsyncSession, profile_id: int
) -> Optional[Students]:
    return await session.get(Students, profile_id)


async def get_faculty_profile_by_id(
    session: AsyncSession, profile_id: int
) -> Optional[Faculty]:
    return await session.get(Faculty, profile_id)


async def get_profile_by_account_id(
    session: AsyncSession, account_id: int
) -> Optional[Union[Employers, Students, Faculty]]:
    # 1. Get the account to learn profile_id and user_type
    statement = select(Accounts.profile_id, Accounts.user_type).where(
        Accounts.id == account_id
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
) -> Optional[InternshipOpportunities]:
    return await session.get(InternshipOpportunities, id)
