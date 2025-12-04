from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import delete
from typing import Any, Optional

from src.database.schema import InternshipMajor, InternshipReqSkill, InternshipPrefSkill


async def delete_record(
    session: AsyncSession, instance: Optional[Any], commit: bool = False
) -> bool:
    """
    Deletes the specified ORM instance from the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        instance (Any or None): The SQLAlchemy ORM object to delete, or None.
        commit (bool, optional): If True, commits the transaction after deleting.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        bool: True if the instance was deleted; False if not found or an error occurred.
    """
    if instance is None:
        return False

    try:
        await session.delete(instance)
        if commit:
            await session.commit()
        else:
            await session.flush()
        return True

    except SQLAlchemyError as e:
        await session.rollback()
        print(f"SQLAlchemy error in delete_instance: {e}")
        return False


async def remove_internship_major(
    session: AsyncSession, internship_id: int, major_id: int, commit: bool = False
) -> bool:
    statement = delete(InternshipMajor).where(
        InternshipMajor.internship_id == internship_id, InternshipMajor.major_id == major_id
    )
    try:
        await session.execute(statement)
        if commit:
            await session.commit()
        else:
            await session.flush()
        return True

    except SQLAlchemyError as e:
        await session.rollback()
        print(f"SQLAlchemy error in remove_internship_major: {e}")
        return False


async def remove_internship_required_skill(
    session: AsyncSession, internship_id: int, skill_id: int, commit: bool = False
) -> bool:
    statement = delete(InternshipReqSkill).where(
        InternshipReqSkill.internship_id == internship_id, InternshipReqSkill.skill_id == skill_id
    )
    try:
        await session.execute(statement)
        if commit:
            await session.commit()
        else:
            await session.flush()
        return True

    except SQLAlchemyError as e:
        await session.rollback()
        print(f"SQLAlchemy error in remove_internship_required_skill: {e}")
        return False


async def remove_internship_preferred_skill(
    session: AsyncSession, internship_id: int, skill_id: int, commit: bool = False
) -> bool:
    statement = delete(InternshipPrefSkill).where(
        InternshipPrefSkill.internship_id == internship_id, InternshipPrefSkill.skill_id == skill_id
    )
    try:
        await session.execute(statement)
        if commit:
            await session.commit()
        else:
            await session.flush()
        return True

    except SQLAlchemyError as e:
        await session.rollback()
        print(f"SQLAlchemy error in remove_internship_preferred_skill: {e}")
        return False
