from collections.abc import Mapping, Sequence
from typing import Any, Optional

from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Executable


async def execute(
    session: AsyncSession,
    statement: Executable,
    parameters: Optional[Mapping[str, Any] | Sequence[Mapping[str, Any]]] = None,
) -> Result[Any]:
    """
    Executes a SQLAlchemy SQL statement a single or multiple times with optional bound parameters.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous session.
        statement (Executable): A SQLAlchemy SQL statement to execute (e.g., select, insert, update, delete, or "..." (Raw SQL)).
        parameters (dict | list[dict], optional): An optional dictionary or list of dictionaries of bind parameters for the query. Defaults to {}.
    """
    if parameters is None:
        return await session.execute(statement)
    return await session.execute(statement, parameters)


def get_constraint_name_from_integrity_error(e) -> str:
    """
    Best-effort extraction of a violated constraint name from a SQLAlchemy IntegrityError.
    Returns "" if not found.
    """
    original_exception = getattr(e, "orig", None)

    # psycopg2/psycopg (Postgres)
    diagnostics = getattr(original_exception, "diag", None)
    name = getattr(diagnostics, "constraint_name", None)
    if name:
        return str(name)

    # asyncpg (Postgres) and some other drivers
    for attr in ("constraint_name", "constraint", "constraintName"):
        name = getattr(original_exception, attr, None)
        if name:
            return str(name)

    return ""
