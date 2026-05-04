from typing import Any, Optional

from sqlalchemy.ext.asyncio.session import AsyncSession

from .types import TModel


async def delete_row_by_pk(
    session: AsyncSession,
    model: type[TModel],
    pk: Any,
    *,
    flush: bool = True,
) -> bool:
    """
    Delete a single ORM row identified by its primary key (supports composite PKs).

    This helper loads the instance via `await session.get(model, pk)`, marks it for deletion
    with `session.delete(...)`, and optionally flushes.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session.
        model (type[TModel]): ORM mapped class (table) to delete from.
        pk (Any): Primary key identifier for the row.
            Common forms:
            - Scalar for single-column primary keys (e.g., 123)
            - Tuple for composite primary keys in PK column order (e.g., (1, 2))
            - Dict mapping primary key attribute names to values (e.g., {"org_id": 1, "user_id": 2})
        flush (bool): If True, flush pending changes after marking the instance for deletion.
            Defaults to True.

    Returns:
        bool: True if a row was found and marked for deletion; False if no row exists for the given PK.

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If the flush triggers a database/ORM error.
    """
    row = await session.get(model, pk)
    if row is None:
        return False

    await session.delete(row)
    if flush:
        await session.flush()
    return True


async def delete_row_instance(
    session: AsyncSession,
    instance: Optional[TModel],
    *,
    flush: bool = True,
) -> bool:
    """
    Delete a single ORM instance.

    If `instance` is None, no action is taken and False is returned. Otherwise the instance
    is marked for deletion via `session.delete(instance)`, and optionally flushes.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session.
        instance (Optional[TModel]): ORM instance (row) to delete, or None.
        flush (bool): If True, flush pending changes after marking the instance for deletion.
            Defaults to True.

    Returns:
        bool: True if an instance was provided and marked for deletion; False if `instance` was None.

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If flushing triggers a database/ORM error.
    """
    if instance is None:
        return False

    await session.delete(instance)
    if flush:
        await session.flush()
    return True


async def bulk_delete_row_by_fields(
    session: AsyncSession,
    model: type[TModel],
    *,
    require_one: bool = False,
    flush: bool = True,
    **fields: Any,
) -> int:
    """
    Bulk delete rows from a table using equality filters.

    Builds and executes a SQL DELETE statement of the form:
        DELETE FROM <model> WHERE <field1>=<value1> AND <field2>=<value2> ...

    This is a bulk operation: it does not load ORM instances into the session and may bypass
    some ORM behaviors (e.g., certain in-Python cascades and ORM delete events).

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session.
        model (type[TModel]): ORM mapped class (table) to delete from.
        require_one (bool): If True, require exactly one row to be deleted; otherwise raise ValueError.
            Defaults to False.
        flush (bool): If True, flush pending changes after marking the instance(s) for deletion.
        **fields (Any): Field/value pairs used as equality predicates. At least one field is required.

    Returns:
        int: The number of rows deleted.

    Raises:
        ValueError: If no fields are provided, or if require_one=True and the number of deleted rows is not 1.
        AttributeError: If a provided field name is not an attribute on the model.
        sqlalchemy.exc.SQLAlchemyError: If statement execution or flushing fails.
    """
    from sqlalchemy import and_, delete

    if not fields:
        raise ValueError("Need at least one field")

    predicate = and_(*(getattr(model, k) == v for k, v in fields.items()))
    statement = delete(model).where(predicate)

    result = await session.execute(statement)
    if flush:
        await session.flush()

    deleted = int(result.rowcount or 0)
    if require_one and deleted != 1:
        raise ValueError(f"Expected to delete 1 row, deleted {deleted}")
    return deleted
