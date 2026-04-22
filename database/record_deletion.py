from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, delete
from typing import Any, Optional

from database.schema import InternshipMajor, InternshipReqSkill, InternshipPrefSkill
from database.utils import TModel


async def delete_record(
    session: AsyncSession,
    instance: Optional[TModel],
    *,
    commit: bool = False,
) -> bool:
    """
    Deletes the specified ORM instance from the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        instance (T or None): The SQLAlchemy ORM-mapped instance (a subclass of Base) to delete, or None.
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
        print(f"Error deleting {type(instance).__name__}:\n{e}\n")
        return False


async def delete_record_by_fields(
    session: AsyncSession,
    model: type[TModel],
    *,
    commit: bool = False,
    **fields: Any,
) -> bool:
    """
    Deletes specified ORM instance from the database via the model and specified fields.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        model (TModel): The SQLAlchemy ORM-mapped instance (a subclass of Base) to delete from.
        commit (bool, optional): If True, commits the transaction after deleting.
            If False, commit must be handled externally. Defaults to False.
        **fields (): __

    Returns:
        bool: True if the instance was deleted; False if not found or an error occurred.
    """
    if not fields:
        raise ValueError("Need at least one field")

    predicate = and_(*(getattr(model, k) == v for k, v in fields.items()))

    # Return something cheap (typically the PK column). If you don't know the PK,
    # you can return literal 1, but returning a column is common.
    pk_columns = list(model.__mapper__.primary_key)
    returning_column = pk_columns[0] if pk_columns else None

    statement = delete(model).where(predicate)
    if returning_column is not None:
        statement = statement.returning(returning_column)

    try:
        if returning_column is not None:
            deleted_ids = (await session.scalars(statement)).all()
            deleted = len(deleted_ids)
        else:
            # fallback if model has no PK mapping (rare)
            result = await session.execute(statement)
            deleted = result.rowcount or 0

        if commit:
            await session.commit()
        else:
            await session.flush()

        return deleted > 0

    except SQLAlchemyError as e:
        await session.rollback()
        print(f"Error deleting {model.__name__} with {fields}:\n{e}\n")
        return False


async def remove_internship_major(
    session: AsyncSession, internship_id: int, major_id: int, commit: bool = False
) -> bool:
    return await delete_record_by_fields(
        session,
        InternshipMajor,
        internship_id=internship_id,
        major_id=major_id,
        commit=commit,
    )


async def remove_internship_required_skill(
    session: AsyncSession, internship_id: int, skill_id: int, commit: bool = False
) -> bool:
    return await delete_record_by_fields(
        session,
        InternshipReqSkill,
        internship_id=internship_id,
        skill_id=skill_id,
        commit=commit,
    )


async def remove_internship_preferred_skill(
    session: AsyncSession, internship_id: int, skill_id: int, commit: bool = False
) -> bool:
    return await delete_record_by_fields(
        session,
        InternshipPrefSkill,
        internship_id=internship_id,
        skill_id=skill_id,
        commit=commit,
    )
