from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_, select
from typing import Any, Optional

from database.row_retrieval import (
    get_company_by_name,
    get_department_by_name,
    get_major_by_name,
    get_skill_by_name,
)
from database.schema import (
    Company,
    Department,
    Major,
    Skill,
)
from database.utils import TModel


async def get_or_create_row(
    session: AsyncSession,
    model: type[TModel],
    *,
    commit_savepoint: bool = True,
    **unique_fields: Any,
) -> Optional[TModel]:
    """
    Generic get-or-create for 1+ unique fields (passed as keyword args).
    Example: await get_or_create(session, Department, org_id=1, name="Cardiology")

    - Requires a UNIQUE constraint matching unique_fields (or a superset) for correctness under concurrency.
    - Does not commit the outer transaction.
    """
    if not unique_fields:
        raise ValueError("get_or_create requires at least one unique field")

    # 1) Try to get first (fast path)
    try:
        where_clause = and_(*(getattr(model, k) == v for k, v in unique_fields.items()))
        existing = await session.scalar(select(model).where(where_clause))
        if existing is not None:
            return existing

    except SQLAlchemyError as e:
        print(f"Error querying {model.__name__}:\n{e}\n")
        return None

    # 2) Try to create inside a SAVEPOINT
    savepoint = await session.begin_nested()
    obj = model(**unique_fields)
    session.add(obj)

    try:
        await session.flush()
        if commit_savepoint:
            await savepoint.commit()
        return obj

    except IntegrityError:
        await savepoint.rollback()
        # Another transaction likely inserted it; fetch it
        try:
            return await session.scalar(select(model).where(where_clause))

        except SQLAlchemyError as e:
            print(f"Error re-querying {model.__name__}:\n{e}\n")
            return None

    except SQLAlchemyError as e:
        await savepoint.rollback()
        print(f"Error creating {model.__name__}:\n{e}\n")
        return None


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
    return await get_or_create_row(
        session,
        Department,
        name=company_name,
        address_id=address_id,
        website_link=website_link,
    )


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
    return await get_or_create_row(session, Department, name=name)


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
    return await get_or_create_row(session, Major, name=name)


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
    return await get_or_create_row(session, Skill, name=name)
