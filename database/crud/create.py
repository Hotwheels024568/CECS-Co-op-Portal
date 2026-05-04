from typing import Any

from sqlalchemy.ext.asyncio.session import AsyncSession

from .types import TModel


async def add_row(
    session: AsyncSession,
    model: type[TModel],
    *,
    flush: bool = True,
    **fields: Any,
) -> type[TModel]:
    """
    Create and add a new ORM instance to the session.

    This helper instantiates `model(**fields)`, adds it to the session, and optionally flushes
    so database-generated values (e.g., primary keys/defaults) are available and constraint
    errors surface early.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session.
        model (type[TModel]): The ORM mapped class (table) to add a new row to.
        flush (bool): If True, flush pending changes after adding the instance. Defaults to True.
        **fields (Any): Field/value pairs passed to the model constructor.
            Keys must be mapped to attribute names on the model.

    Returns:
        type[TModel]: The newly created ORM instance (row).

    Raises:
        TypeError: If `fields` contains invalid constructor keywords.
        sqlalchemy.exc.SQLAlchemyError: If flushing triggers a database/ORM error (e.g., IntegrityError).
    """
    row = model(**fields)
    session.add(row)
    if flush:
        await session.flush()
    return row
