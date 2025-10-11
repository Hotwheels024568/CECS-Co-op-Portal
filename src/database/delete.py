from typing import Any, Optional
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio.session import AsyncSession


async def delete_instance(
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
