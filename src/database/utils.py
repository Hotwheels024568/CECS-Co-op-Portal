from typing import Any, Optional
from sqlalchemy import Executable, Row, Select
from sqlalchemy.ext.asyncio.session import AsyncSession

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
"""


async def count(session: AsyncSession, model) -> int:
    """
    Returns the count of records in a SQLAlchemy model (table class)

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
        model (Any): The SQLAlchemy model (table class).

    Returns:
        int: Count of the table records
    """
    from sqlalchemy import func, select

    result = await session.scalar(select(func.count()).select_from(model))
    return result if result is not None else 0


async def exists(
    session: AsyncSession, statement: Select, parameters: Optional[dict] = None
) -> bool:
    """
    Executes a SQLAlchemy SELECT query and checks if at least one result was returned.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
        statement (Select): A SQLAlchemy SELECT statement.
        parameters (dict, optional): Optional dictionary of bind parameters for the query. Defaults to {}.

    Returns:
        bool: True if the query returns at least one result, otherwise False.
    """
    from sqlalchemy import select, exists, literal

    parameters = parameters or {}
    try:
        return await session.scalar(
            select(exists(statement.with_only_columns([literal(1)]))), parameters
        )

    except Exception as e:
        print(f"Error in DB 'exists' function:\nStatement: {statement}\nError: {e}")
    return False


async def get_first_column_element(
    session: AsyncSession, statement: Select, parameters: Optional[dict] = None
) -> Optional[Any]:
    """
    Executes a SQLAlchemy SELECT query and returns the first column element (or object) from the first Row.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
        statement (Select): A SQLAlchemy SELECT statement.
        parameters (dict, optional): Optional dictionary of bind parameters for the query. Defaults to {}.

    Returns:
        Optional[Any]: The first column's element of the first row, or None if no result is found.
    """
    parameters = parameters or {}
    try:
        return await session.scalar(statement, parameters)
    except Exception as e:
        print(
            f"Error in DB 'get_first_column_element' function:\nStatement: {statement}\nError: {e}"
        )
    return None


async def get_row(
    session: AsyncSession, statement: Select, parameters: Optional[dict] = None
) -> Optional[Row]:
    """
    Executes a SQLAlchemy SELECT query and returns the first Row.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
        statement (Select): A SQLAlchemy SELECT statement.
        parameters (dict, optional): Optional dictionary of bind parameters for the query. Defaults to {}.

    Returns:
        Optional[Row]: A SQLAlchemy row, or None if no result is found.
    """
    parameters = parameters or {}
    try:
        return (await session.execute(statement, parameters)).first()
    except Exception as e:
        print(f"Error in DB 'get_row' function:\nStatement: {statement}\nError: {e}")
    return None


async def get_first_column_element_of_all_rows(
    session: AsyncSession, statement: Select, parameters: Optional[dict] = None
) -> list[Any]:
    """
    Executes a SQLAlchemy SELECT query and returns a list of the first column's element (or object) from each Row.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
        statement (Select): A SQLAlchemy SELECT statement.
        parameters (dict, optional): Optional dictionary of bind parameters for the query. Defaults to {}.

    Returns:
        list[Any]: A list containing the first column's element of each Row returned.
    """
    parameters = parameters or {}
    try:
        return await session.scalars(statement, parameters).all()
    except Exception as e:
        print(
            f"Error in DB 'get_first_column_element_of_all_rows' function:\nStatement: {statement}\nError: {e}"
        )
        return []


async def get_all_rows(
    session: AsyncSession, statement: Select, parameters: Optional[dict] = None
) -> list[Row]:
    """
    Executes a SQLAlchemy SELECT query and returns all Rows as a list.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
        statement (Select): A SQLAlchemy SELECT statement.
        parameters (dict, optional): Optional dictionary of bind parameters for the query. Defaults to {}.

    Returns:
        list[Row]: List of SQLAlchemy Row objects returned by the query.
    """
    parameters = parameters or {}
    try:
        return (await session.execute(statement, parameters)).all()
    except Exception as e:
        print(f"Error in DB 'get_all_rows' function:\nStatement: {statement}\nError: {e}")
        return []


async def execute(
    session: AsyncSession, statement: Executable, parameters: Optional[dict] = None
) -> None:
    """
    Executes a single SQLAlchemy SQL statement.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
        statement (Executable): A SQLAlchemy SQL statement to execute (e.g., insert, update, delete).
        parameters (dict, optional): Optional dictionary of bind parameters for the statement. Defaults to {}.
    """
    parameters = parameters or {}
    try:
        await session.execute(statement, parameters)
    except Exception as e:
        print(f"Error in DB 'execute' function:\nStatement: {statement}\nError: {e}")


async def execute_many(
    session: AsyncSession, statement: Executable, parameters: Optional[list[dict]] = None
) -> None:
    """
    Executes a SQLAlchemy SQL statement multiple times with a list of parameter sets.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
        statement (Executable): A SQLAlchemy SQL statement to execute (e.g., insert, update, delete).
        parameters (list[dict], optional): List of dictionaries representing parameter sets for each execution. Defaults to [].
    """
    parameters = parameters or []
    try:
        await session.execute(statement, parameters)
    except Exception as e:
        print(f"Error in DB 'execute_many' function:\nStatement: {statement}\nError: {e}")


"""
session.execute(select())
session.execute(insert())
session.execute(update())
session.execute(delete())
session.execute("...") # Raw SQL
"""


def get_constraint_name_from_integrity_error(e) -> str:
    # Handles asyncpg, psycopg2, or most DBAPIs used with SQLAlchemy
    try:
        return getattr(getattr(e.orig, "diag", None), "constraint_name", "") or str(e)
    except Exception:
        return str(e)
