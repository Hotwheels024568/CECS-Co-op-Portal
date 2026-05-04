from typing import Any, Optional

from sqlalchemy.ext.asyncio.session import AsyncSession

from .types import TModel


async def update_row_by_pk(
    session: AsyncSession,
    model: type[TModel],
    pk: Any,
    *,
    skip_none: bool = True,
    flush: bool = True,
    **patch_fields: Any,
) -> Optional[TModel]:
    """
    Patch-update a single ORM row identified by its primary key (supports composite PKs).

    This helper loads the instance with `await session.get(model, pk)`, applies the provided
    field/value pairs to mapped attributes, and optionally flushes.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session.
        model (type[TModel]): The ORM mapped class (table) to update.
        pk (Any): Primary key identifier for the row.
            Common forms:
            - Scalar for single-column primary keys (e.g., 123)
            - Tuple for composite primary keys in PK column order (e.g., (1, 2))
            - Dict mapping primary key attribute names to values (e.g., {"org_id": 1, "user_id": 2})
        skip_none (bool): If True, patch items with value None are ignored (cannot set NULL).
            If False, None values are applied (may set columns to NULL if nullable). Defaults to True.
        flush (bool): If True, flush pending changes after applying updates. Defaults to True.
        **patch (Any): Field/value pairs to update on the ORM instance.
            Keys must be mapped to attribute names on the model.

    Returns:
        Optional[TModel]: The updated ORM instance, or None if no row exists for the given PK.

    Raises:
        AttributeError: If a patch key is not a mapped attribute on the model.
        sqlalchemy.exc.SQLAlchemyError: If flushing triggers a database/ORM error (e.g., IntegrityError).
    """
    from sqlalchemy import inspect

    row = await session.get(model, pk)
    if row is None:
        return None

    # Only allow mapped non-PK attributes
    mapper = inspect(model)
    mapped_names = {attr.key for attr in mapper.column_attrs}
    pk_names = {col.key for col in mapper.primary_key}
    mapped_names -= pk_names

    updated = False
    for name, value in patch_fields.items():
        if skip_none and value is None:
            continue
        if name not in mapped_names:
            raise AttributeError(f"{model.__name__} has no mapped attribute '{name}'")

        current = getattr(row, name)
        if current != value:
            setattr(row, name, value)
            updated = True

    if updated and flush:
        await session.flush()

    return row
