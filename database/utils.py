from __future__ import annotations

from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import ColumnElement, Executable, Result, Row, Select, Sequence, and_
from sqlalchemy.orm import InstrumentedAttribute
from typing import Any, Mapping, Optional, TypeVar, overload

from database.schema import Base

TModel = TypeVar("TModel", bound=Base)
TAttr = TypeVar("TAttr")
T = TypeVar("T")

# Create Read Update Delete (CRUD)
# Missing a "Get or Create" helper (concurrency helper)


# region Create (Insertion, Insert)
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


# endregion


# region Read (Retrieval, Read, Select)
"""  Result helpers
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
async def build_select_statement(
    select: type[TModel],
    *,
    filters: Sequence[ColumnElement[bool]] = (),
    **fields: Any,
) -> Select[tuple[TModel]]: ...


@overload
async def build_select_statement(
    select: InstrumentedAttribute[TAttr],
    *,
    filters: Sequence[ColumnElement[bool]] = (),
    **fields: Any,
) -> Select[tuple[TAttr]]: ...


async def build_select_statement(
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
                or_(User.is_active.is_(True), User.is_admin.is_(True)
            ),
        )
        ```

    - Use keyword filters (``None`` => ``IS NULL``):
        ```statement = build_select_from_filters(User, deleted_at=None, is_active=True)```

    - Select a single column while still filtering on the owning model:
        ```statement = build_select_from_filters(User.email, is_active=True, deleted_at=None)``
    """
    from sqlalchemy import and_, select as select_

    conditions = list(filters)
    model = select.parent.entity if isinstance(select, InstrumentedAttribute) else select

    for name, value in fields.items():
        column = getattr(model, name)
        conditions.append(column.is_(None) if value is None else (column == value))

    return select_(select).where(and_(*conditions)) if conditions else select_(select)


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

    result = await session.scalar(select(func.count()).select_from(model))
    return result if result is not None else 0


async def exists(
    session: AsyncSession, statement: Select, parameters: Optional[dict] = None
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
    from sqlalchemy import select, exists, literal

    if parameters is None:
        return await session.scalar(select(exists(statement.with_only_columns([literal(1)]))))
    else:
        return await session.scalar(
            select(exists(statement.with_only_columns([literal(1)]))), parameters
        )


async def get_first_element(
    session: AsyncSession, statement: Select[tuple[T]], parameters: Optional[dict] = None
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
    if parameters is None:
        return await session.scalar(statement)
    else:
        return await session.scalar(statement, parameters)


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
    session: AsyncSession, statement: Select, parameters: Optional[dict] = None
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
    if parameters is None:
        return (await session.execute(statement)).first()
    else:
        return (await session.execute(statement, parameters)).first()


async def get_first_element_list(
    session: AsyncSession, statement: Select[tuple[T]], parameters: Optional[dict] = None
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
    if parameters is None:
        return (await session.scalars(statement)).all()
    else:
        return (await session.scalars(statement, parameters)).all()


async def get_all_rows(
    session: AsyncSession, statement: Select, parameters: Optional[dict] = None
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
    if parameters is None:
        return (await session.execute(statement)).all()
    else:
        return (await session.execute(statement, parameters)).all()


async def execute(
    session: AsyncSession,
    statement: Executable,
    parameters: Optional[dict[str, Any] | list[dict[str, Any]]] = None,
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
    else:
        return await session.execute(statement, parameters)


# endregion


# region Update
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


# endregion


# region Delete
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


# endregion


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
