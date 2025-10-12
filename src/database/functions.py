from typing import Any, Dict, List, Optional
from sqlalchemy import Executable, Row, Select, Sequence
from sqlalchemy.ext.asyncio.session import AsyncSession

"""  Result helpers
Method                  Returns if 0 rows	If 1 row	            If >1 row	        Notes
.scalar()	            None	            first column	        first column	    No error, just first column
.scalar_one_or_none()	None	            first column	        Error	            Raises if more than 1 row; Safest for unique queries

.one()                  Error               first row object        Error               Raises unless exactly 1 row
.one_or_none()          None                first row object        Error               Raises if more than 1 row
.first()	            None	            first row object	    first row object    No error, ignores extras
.fetchone()             None                first row (row/tuple)   next rows           Like DBAPI: call repeatedly for more

.fetchmany(size)        Sequence of row objects of size
.all() & .fetchall()    Sequence of all row objects
"""


async def exists(
    session: AsyncSession, statement: Select, parameters: Optional[Dict] = None
) -> bool:
    """
    Checks if a SQLAlchemy SELECT statement returns at least one result.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
        statement (Select): A SQLAlchemy Core or ORM select statement.
        parameters (Dict, optional): Optional dictionary of bind parameters for the query. Defaults to {}.

    Returns:
        bool: True if the query returns at least one result, otherwise False.
    """
    parameters = parameters or {}
    try:
        return (await session.execute(statement, parameters)).fetchone() is not None

    except Exception as e:
        print(f"Error in DB 'exists' function:\nStatement: {statement}\nError: {e}")
    return False


async def get_first_element(
    session: AsyncSession, statement: Select, parameters: Optional[Dict] = None
) -> Optional[Any]:
    """
    Returns the first element (or object) from the first SQLAlchemy Row of a SELECT query.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
        statement (Select): A SQLAlchemy SELECT statement.
        parameters (Dict, optional): Optional dictionary of bind parameters for the query. Defaults to {}.

    Returns:
        Optional[Any]: The first element of the first row, or None if no result is found.
    """
    parameters = parameters or {}
    try:
        return (await session.execute(statement, parameters)).scalar_one_or_none()
    except Exception as e:
        print(
            f"Error in DB 'get_first_element' function:\nStatement: {statement}\nError: {e}"
        )
    return None


async def get_row(
    session: AsyncSession, statement: Select, parameters: Optional[Dict] = None
) -> Optional[Row]:
    """
    Returns a single SQLAlchemy row from a SELECT query.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
        statement (Select): A SQLAlchemy SELECT statement.
        parameters (Dict, optional): Optional dictionary of bind parameters for the query. Defaults to {}.

    Returns:
        Optional[Row]: A SQLAlchemy row, or None if no result is found.
    """
    parameters = parameters or {}
    try:
        return (await session.execute(statement, parameters)).first()
    except Exception as e:
        print(f"Error in DB 'get_row' function:\nStatement: {statement}\nError: {e}")
    return None


async def get_all_rows(
    session: AsyncSession, statement: Select, parameters: Optional[Dict] = None
) -> Sequence[Row]:
    """
    Returns a SQLAlchemy Sequence of all Rows from a SELECT query.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
        statement (Select): A SQLAlchemy SELECT statement.
        parameters (Dict, optional): Optional dictionary of bind parameters for the query. Defaults to {}.

    Returns:
        Sequence[Row]: A Sequence of SQLAlchemy Rows.
    """
    parameters = parameters or {}
    try:
        return (await session.execute(statement, parameters)).all()
    except Exception as e:
        print(f"Error in DB 'get_all_rows' function:\nStatement: {statement}\nError: {e}")
    return []


async def execute(
    session: AsyncSession, statement: Executable, parameters: Optional[Dict] = None
) -> None:
    """
    Executes a single SQL statement using SQLAlchemy.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
        statement (Executable): A SQLAlchemy SQL statement to execute (e.g., insert, update, delete).
        parameters (Dict, optional): Optional dictionary of bind parameters for the statement. Defaults to {}.
    """
    parameters = parameters or {}
    try:
        await session.execute(statement, parameters)
    except Exception as e:
        print(f"Error in DB 'execute' function:\nStatement: {statement}\nError: {e}")


async def execute_many(
    session: AsyncSession, statement: Executable, parameters: Optional[List[Dict]] = None
) -> None:
    """
    Executes a SQL statement multiple times with a list of parameter sets using SQLAlchemy.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
        statement (Executable): A SQLAlchemy SQL statement to execute (e.g., insert, update, delete).
        parameters (List[Dict], optional): List of dictionaries representing parameter sets for each execution. Defaults to [].
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
