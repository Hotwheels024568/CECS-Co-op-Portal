from __future__ import annotations
from collections.abc import Mapping, Sequence
from typing import Any, Optional, overload

from sqlalchemy import ColumnElement
from sqlalchemy.engine import Row
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql import Select
from sqlalchemy.sql.selectable import TypedReturnsRows

from .types import T, TAttr, TModel
from .utils import execute

"""Helpers
Method                  Returns if 0 rows	If 1 row	            If >1 row	        Notes
.scalar()	            None	            first column	        first column	    No error, just first column
.scalar_one_or_none()	None	            first column	        Error	            Raises if more than 1 row; Safest for unique queries

.one()                  Error               first row object        Error               Raises unless exactly 1 row
.one_or_none()          None                first row object        Error               Raises if more than 1 row
.first()	            None	            first row object	    first row object    No error, ignores extras
.fetchone()             None                first row (row/tuple)   next rows           Like DBAPI: call repeatedly for more

.scalars()              ScalarResult (list) of the first column of every row
.fetchmany(size)        Sequence of row objects of size
.all() & .fetchall()    Sequence of all row objects


Method                  Complexity          Syntax                              Example
.filter_by()            Simple checks       Keyword Args                        .filter_by(name='Alice', age=30)
.where & .filter()      Complex Checks      Column expressions & operators      .where(and_(User.name == 'Alice', User.age > 25))
    Supports operators (>, <, ==, >=, <=, !=) and expressions (and_, or_, in_, like_, is_, etc.)
        Operators:      https://docs.sqlalchemy.org/en/20/core/operators.html
        Expressions:    https://docs.sqlalchemy.org/en/20/core/sqlelement.html
"""


@overload
def build_select_statement(
    select: type[TModel],
    *,
    filters: Sequence[ColumnElement[bool]] = (),
    **fields: Any,
) -> Select[tuple[TModel]]: ...


@overload
def build_select_statement(
    select: InstrumentedAttribute[TAttr],
    *,
    filters: Sequence[ColumnElement[bool]] = (),
    **fields: Any,
) -> Select[tuple[TAttr]]: ...


def build_select_statement(
    select: type[TModel] | InstrumentedAttribute[TAttr],
    *,
    filters: Sequence[ColumnElement[bool]] = (),
    **fields: Any,
) -> Select[tuple[TModel | TAttr]]:
    """
    Build a SQLAlchemy `Select` statement from explicit SQL expression filters and/or keyword equality filters.

    This is a helper for composing common `WHERE` clauses:
        - `filters`: an iterable of SQLAlchemy boolean expressions (e.g., `User.email.ilike(...)` ).
        - `**fields`: keyword filters applied to columns on the selected model
            - `field=value` becomes `model.field == value` and `field=None` becomes `model.field IS NULL`.

    Args:
        selected (TModel or TAttr): Either an ORM mapped class (table) or a mapped attribute (table.column).
            If an attribute is provided, `**fields` are resolved against that attribute's owning model.
        filters (Sequence[ColumnElement[bool]]): Additional SQLAlchemy boolean expressions to AND together. Defaults to ().
        **fields (Any): Column filters expressed as keyword arguments.

    Returns:
        Select[tuple[TModel | TAttr]]:
        A SQLAlchemy `Select` statement with all conditions combined
        using `AND`. If no conditions are provided, returns `select(selected)`.

    Raises:
        AttributeError:
            If a key in `fields` is not an attribute on the resolved model.

    Examples:
    - Combine explicit SQL expressions:
    ```
    statement = build_select_from_filters(
        User,
        filters=(
            User.email.ilike("%@umich.edu"),
            or_(User.is_active.is_(True), User.is_admin.is_(True))
        ),
    )
    ```
        - Produces:
        ```
        SELECT ... FROM user
        WHERE user.email ILIKE '%@umich.edu'
            AND (user.is_active IS TRUE OR user.is_admin IS TRUE)
            AND ... (**fields)
        ```

    - Use keyword filters (``None`` => ``IS NULL``):
        ```
        statement = build_select_from_filters(User, deleted_at=None, is_active=True)
        ```

    - Select a single column while still filtering on the owning model:
        ```
        statement = build_select_from_filters(User.email, is_active=True, deleted_at=None)
        ```
    """

    from sqlalchemy import and_, select as select_

    conditions = list(filters)
    model = select.parent.entity if isinstance(select, InstrumentedAttribute) else select

    for name, value in fields.items():
        column = getattr(model, name)
        conditions.append(column.is_(None) if value is None else (column == value))

    return select_(select).where(and_(*conditions)) if conditions else select_(select)


async def _scalar(
    session: AsyncSession,
    statement: TypedReturnsRows[tuple[T]],
    parameters: Optional[Mapping[str, Any]] = None,
) -> Optional[T]:
    if parameters is None:
        return await session.scalar(statement)
    return await session.scalar(statement, parameters)


async def _scalars(
    session: AsyncSession,
    statement: TypedReturnsRows[tuple[T]],
    parameters: Optional[Mapping[str, Any]] = None,
) -> ScalarResult[T]:
    if parameters is None:
        return await session.scalars(statement)
    return await session.scalars(statement, parameters)


async def count(session: AsyncSession, model: type[TModel]) -> int:
    """
    Count the records in a ORM mapped class (table).

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session.
        model (type[TModel]): ORM mapped class (table) to load.

    Returns:
        int: Count of records in the table
    """
    from sqlalchemy import func, select

    return await _scalar(session, select(func.count()).select_from(model)) or 0


async def exists(
    session: AsyncSession,
    stmt: Select[Any],
    parameters: Optional[Mapping[str, Any]] = None,
) -> bool:
    """
    Determine if at least one result is returned a SQLAlchemy SELECT query.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session.
        statement (Select): A SQLAlchemy SELECT statement.
        parameters (dict, optional): Optional dictionary of bind parameters for the query. Defaults to {}.

    Returns:
        bool: True if the query returns at least one result, otherwise False.
    """
    from sqlalchemy import select, exists as exists_, literal

    stmt: Select[tuple[bool]] = select(exists_(stmt.with_only_columns(literal(1)).order_by(None)))
    return bool(await _scalar(session, stmt, parameters))


async def get_first_element(
    session: AsyncSession,
    statement: Select[tuple[T]],
    parameters: Optional[Mapping[str, Any]] = None,
) -> Optional[T]:
    """
    Retrieve the first element (scalar) or object from the first column's first Row of an SQLAlchemy SELECT query result.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous session.
        statement (Select[tuple[T]]): A SQLAlchemy SELECT statement.
        parameters (dict, optional): Optional dictionary of bind parameters for the query. Defaults to {}.

    Returns:
        Optional[T]: The element of the first column's first row, or None if no result is found.
    """
    return await _scalar(session, statement, parameters)


async def get_row_by_pk(session: AsyncSession, model: type[TModel], pk: Any) -> Optional[TModel]:
    """
    Retrieve a single ORM instance (row) by primary key (supports composite PKs).

    This helper delegates to `await session.get(model, pk)`.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session.
        model (type[TModel]): ORM mapped class (table) to load.
        pk (Any): Primary key identifier for the row.
            Common forms:
            - Scalar for single-column primary keys (e.g., 123)
            - Tuple for composite primary keys in PK column order (e.g., (1, 2))
            - Dict mapping primary key attribute names to values (e.g., {"org_id": 1, "user_id": 2})

    Returns:
        Optional[TModel]: The ORM instance (row) if found; otherwise None.

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If the load operation fails.
    """
    return await session.get(model, pk)


async def get_row(
    session: AsyncSession,
    statement: Select,
    parameters: Optional[Mapping[str, Any]] = None,
) -> Optional[Row]:
    """
    Retrieve the first Row of an SQLAlchemy SELECT query result.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous session.
        statement (Select): A SQLAlchemy SELECT statement.
        parameters (dict, optional): Optional dictionary of bind parameters for the query. Defaults to {}.

    Returns:
        Optional[Row]: A SQLAlchemy Row, or None if no result is found.
    """
    return (await execute(session, statement, parameters)).first()


async def get_first_element_list(
    session: AsyncSession,
    statement: Select[tuple[T]],
    parameters: Optional[Mapping[str, Any]] = None,
) -> list[T]:
    """
    Retrieve a list of the first elements (scalars) or objects from the first column of each Row of an SQLAlchemy SELECT query result.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous session.
        statement (Select[tuple[T]]): A SQLAlchemy SELECT statement.
        parameters (dict, optional): Optional dictionary of bind parameters for the query. Defaults to {}.

    Returns:
        list[T]: A list containing the first column's element of each Row returned.
    """
    return (await _scalars(session, statement, parameters)).all()


async def get_all_rows(
    session: AsyncSession,
    statement: Select,
    parameters: Optional[Mapping[str, Any]] = None,
) -> list[Row]:
    """
    Retrieve a list of Rows from an SQLAlchemy SELECT query result.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous session.
        statement (Select): A SQLAlchemy SELECT statement.
        parameters (dict, optional): Optional dictionary of bind parameters for the query. Defaults to {}.

    Returns:
        list[Row]: List of SQLAlchemy Row objects returned by the query.
    """
    return (await execute(session, statement, parameters)).all()
