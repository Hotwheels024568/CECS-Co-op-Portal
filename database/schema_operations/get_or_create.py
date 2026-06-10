from typing import Optional

from sqlalchemy.ext.asyncio.session import AsyncSession

from database.schema import Company, Department, Major, Skill
from database.crud import get_or_create_row


async def get_or_create_company(
    session: AsyncSession,
    company_name: str,
    address_id: int,
    website_link: Optional[str] = None,
) -> Optional[Company]:
    """
    Retrieve a Company by name or create it if it does not exist, within the current transaction.

    This function attempts to create a new Company record using the provided name,
    address_id, and optional website_link. If another concurrent transaction has already
    created a Company with the same name, or if a unique constraint violation occurs,
    the existing Company is retrieved and returned. Does not commit the transaction.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        company_name (str): The unique name of the company.
        address_id (int): The ID of an existing address to associate with the company.
        website_link (Optional[str], optional): The company's website URL.

    Returns:
        Optional[Company]: The existing or newly created Company, or None if the operation fails.
    """
    company, _ = await get_or_create_row(
        session,
        Department,
        name=company_name,
        address_id=address_id,
        website_link=website_link,
    )
    return company


async def get_or_create_department(session: AsyncSession, name: str) -> Optional[Department]:
    """
    Retrieve a Department by name or create it if it does not exist, within the current transaction.

    This function attempts to create a new Department with the given name. If a department
    with this name already exists (due to another concurrent transaction or prior entry),
    the existing Department is retrieved and returned. Does not commit the transaction.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        name (str): The unique name of the department.

    Returns:
        Optional[Department]: The existing or newly created Department, or None if the operation fails.
    """
    department, _ = await get_or_create_row(session, Department, name=name)
    return department


async def get_or_create_major(session: AsyncSession, name: str) -> Optional[Major]:
    """
    Retrieve a Major by name or create it if it does not exist, within the current transaction.

    This function attempts to create a new Major with the given name. If a major with this
    name already exists, the existing Major is retrieved and returned.
    Does not commit the transaction.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        name (str): The unique name of the major.

    Returns:
        Optional[Major]: The existing or newly created Major, or None if the operation fails.
    """
    major, _ = await get_or_create_row(session, Major, name=name)
    return major


async def get_or_create_skill(session: AsyncSession, name: str) -> Optional[Skill]:
    """
    Retrieve a Skill by name or create it if it does not exist, within the current transaction.

    This function attempts to create a new Skill with the given name. If a skill with this
    name already exists, the existing Skill is retrieved and returned.
    Does not commit the transaction.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        name (str): The unique name of the skill.

    Returns:
        Optional[Skill]: The existing or newly created Skill, or None if the operation fails.
    """
    skill, _ = await get_or_create_row(session, Skill, name=name)
    return skill
