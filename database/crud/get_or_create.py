from collections.abc import Mapping
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .types import TModel
from .read import get_first_element


async def get_or_create_row(
    session: AsyncSession,
    model: type[TModel],
    *,
    defaults: Optional[Mapping[str, Any]] = None,
    **unique_fields: Any,
) -> tuple[TModel, bool]:
    """
    Concurrency-safe get-or-create.

    Returns (obj, created) where created=True iff a new row was inserted by this call.

    Correct under concurrency only if the database enforces a UNIQUE constraint/index
    that matches `unique_fields` (or a superset).
    """
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy import and_, select

    if not unique_fields:
        raise ValueError("get_or_create_row requires at least one unique field")

    defaults = dict(defaults or {})
    where_clause = and_(*(getattr(model, k) == v for k, v in unique_fields.items()))
    statement = select(model).where(where_clause)

    # Fast path: fetch existing (optionally avoid autoflush side effects)
    with session.no_autoflush:
        existing = await get_first_element(session, statement)
    if existing is not None:
        return existing, False

    # Try to insert inside a SAVEPOINT so IntegrityError doesn't abort outer transaction
    params = {**defaults, **unique_fields}
    try:
        async with session.begin_nested():
            obj = model(**params)
            session.add(obj)
            await session.flush()  # forces INSERT; may raise IntegrityError
        return obj, True

    except IntegrityError:
        # Someone else inserted concurrently; fetch the winner
        existing = await get_first_element(session, statement)
        if existing is None:
            # Extremely rare: e.g., different unique constraint triggered than the one we query by
            raise
        return existing, False
