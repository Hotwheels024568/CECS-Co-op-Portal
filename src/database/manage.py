import asyncio
import configparser
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Self

from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.database.schema import Base


def get_database_url() -> str:
    config_path = Path(__file__).parent.parent.parent / "config.ini"
    parser = configparser.ConfigParser()
    try:
        with open(config_path, "r") as file:
            parser.read_file(file)

    except FileNotFoundError:
        print(f"Error: File '{config_path}' not found.")
        raise RuntimeError("Configuration file is missing.")

    config = parser["db"]
    username = config.get("Username")
    password = config.get("Password")
    database = config.get("Database")
    return f"postgresql+asyncpg://{username}:{password}@localhost:5432/{database}"
    # 5432 = the default port for Postgres (you can omit if the default)


DATABASE_URL = get_database_url()


class AsyncDBManager:
    """
    Asynchronous singleton manager for database engine, sessions, and schema control.

    This class encapsulates the creation and management of a SQLAlchemy asynchronous database engine,
    session factory, and utility methods for schema initialization and resetting. It provides
    context-managed asynchronous sessions for use with FastAPI or other async frameworks.

    Attributes:
        engine (AsyncEngine): The SQLAlchemy asynchronous database engine.
        SessionMaker (async_sessionmaker): A factory for creating AsyncSession objects.
        metadata (MetaData): The metadata registry for SQLAlchemy models.
        autocommit (bool): If True, sessions auto-commit after transactions; otherwise, manual commit control.
        _session (Optional[AsyncSession]): Internal reference to the currently active session.
        _instance (Optional[AsyncDBManager]): Singleton instance for this class.

    Class Methods:
        create(autocommit: bool = False) -> AsyncDBManager:
            Asynchronously initializes or returns the singleton DB manager instance,
            ensuring the database schema is created (and optionally seeded).

    Instance Methods:
        async def drop_and_create_db() -> None:
            Drops all tables and re-creates the database schema.

        @asynccontextmanager
        async def session() -> AsyncGenerator[AsyncSession, None]:
            Asynchronous context manager yielding a database session.
            Ensures commit or rollback of the transaction on exit.

        async def __aenter__() -> AsyncSession:
            Enter an async context with an open session.
        async def __aexit__(exc_type, exc_val, exc_tb) -> None:
            Exit the async context, committing or rolling back as appropriate.

    Usage:
        # Startup
        manager = await AsyncDBManager.create()
        # Transaction
        async with manager.session() as session:
            # ... use session ...

    Security Considerations:
        - Do not expose the manager directly in public APIs.
        - Always handle exceptions and rollbacks in session contexts.

    Note:
        This class is intended to be used as a singleton. Use 'await AsyncDBManager.create()' to obtain the instance.
    """

    _instance: Optional["AsyncDBManager"] = None

    def __init__(self, autocommit: bool = False) -> None:
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.SessionMaker = async_sessionmaker(self.engine, expire_on_commit=False, autoflush=False)
        self.metadata = Base.metadata
        self.autocommit = autocommit
        self._session = None

    @classmethod
    async def create(cls, autocommit: bool = False) -> Self:
        if cls._instance:
            return cls._instance
        self = cls._instance = cls(autocommit)
        await self._ensure_schema_and_seed()
        return self

    async def _ensure_schema_and_seed(self) -> None:
        await self._create_db()
        # await self._seed_db_from_csv()

    async def _create_db(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(self.metadata.create_all)

    async def _drop_db(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(self.metadata.drop_all)

    """
    async def _ensure_drop_db(self) -> None:
        async with self.engine.begin() as conn:
            # Drop the public schema and recreate it, drops all tables & relationships
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
    """

    async def drop_and_create_db(self) -> None:
        await self._drop_db()
        await self._create_db()

    # --- context manager (manager.session())
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.SessionMaker() as session:
            self._session = session
            try:
                yield session
                if not self.autocommit:
                    await session.commit()

            except Exception:
                await session.rollback()
                raise

            finally:
                self._session = None

    # --- context management `async with manager.session() as session`
    async def __aenter__(self) -> AsyncSession:
        self._session_obj = self.SessionMaker()
        self._session = await self._session_obj.__aenter__()
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._session is not None:
            if not self.autocommit and exc_type is None:
                await self._session.commit()

            # Rollback if auto-committing or an exception occurred
            else:
                await self._session.rollback()
            await self._session_obj.__aexit__(exc_type, exc_val, exc_tb)
            self._session = None

    """
    async def _seed_db_from_csv(self, csv_path: Path = RESEARCHER_CSV) -> None:
        async with self.session() as session:
            # Only seed if no researchers
            result = await session.execute(select(Researchers))
            if result.first() is not None:
                return

            # Insert from CSV (make a sample if missing)
            if not csv_path.exists():
                csv_path.write_text(
                    "uniqname,first_name,middle_name,last_name\njansmith,Jan,,Smith\nbobdoe,Bob,A.,Doe"
                )

            # Insert from CSV
            data = []
            with open(csv_path, "r", newline="") as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                for temp in reader:
                    # Parse according to your previous logic
                    # uniqname, first_name, middle_name, last_name, first_initial, middle_initial, last_initial
                    researcher = {
                        "first_name": temp[1],
                        "first_initial": temp[4][0] if temp[4] else "",
                        "middle_name": temp[2],
                        "middle_initial": temp[5][0] if temp[5] else "",
                        "last_name": temp[3],
                        "last_initial": temp[6][0] if temp[6] else "",
                        "uniqname": temp[0],
                    }
                    data.append(researcher)

            if data:
                await session.execute(Researchers.insert(), data)

            if not self.autocommit:
                await session.commit()
    """


def get_constraint_name_from_integrity_error(e) -> str:
    # Handles asyncpg, psycopg2, or most DBAPIs used with SQLAlchemy
    try:
        return getattr(getattr(e.orig, "diag", None), "constraint_name", "") or str(e)
    except Exception:
        return str(e)


async def count(session: AsyncSession, model) -> int:
    from sqlalchemy import func, select

    result = await session.scalar(select(func.count()).select_from(model))
    return result if result is not None else 0  # return result or 0


async def main(recreate: bool = False) -> None:
    from src.database.schema import (
        Account,
        Address,
        Company,
        ContactInfo,
        EmployerAccount,
        Department,
        Major,
        StudentAccount,
        FacultyAccount,
        Internship,
        InternshipMajor,
        Skill,
        InternshipReqSkill,
        InternshipPrefSkill,
        InternshipApplication,
        InternshipSummary,
    )

    manager = await AsyncDBManager.create()
    async with manager.session() as session:
        if recreate:
            await manager.drop_and_create_db()

        print(
            f"""
            Counts:
            \tAccount                  {await count(session,Account)}
            \tAddress                  {await count(session,Address)}
            \tCompany                  {await count(session,Company)}
            \tContactInfo              {await count(session,ContactInfo)}
            \tEmployerAccount          {await count(session,EmployerAccount)}
            \tDepartment               {await count(session,Department)}
            \tMajor                    {await count(session,Major)}
            \tStudentAccount           {await count(session,StudentAccount)}
            \tFacultyAccount           {await count(session,FacultyAccount)}
            \tInternship               {await count(session,Internship)}
            \tInternshipMajor          {await count(session,InternshipMajor)}
            \tSkill                    {await count(session,Skill)}
            \tInternshipReqSkill       {await count(session,InternshipReqSkill)}
            \tInternshipPrefSkill      {await count(session,InternshipPrefSkill)}
            \tInternshipApplication    {await count(session,InternshipApplication)}
            \tInternshipSummary        {await count(session,InternshipSummary)}
            """.strip()
        )


if __name__ == "__main__":
    asyncio.run(main())

"""
Migration (Schema swap) Instructions
    pip install alembic
        or if you're using Flask:
        pip install Flask-Migrate
            See https://flask-migrate.readthedocs.io/en/latest/

    Set Up Alembic (if not already)
        alembic init migrations

    After changing your models (the schema), run:
        alembic revision --autogenerate -m "Describe changes"
            This detects differences between your models and the current DB and creates a migration script

    Review the generated script in migrations/versions/
    Apply it:
        alembic upgrade head

    ------------------

    Flask Example (with Flask-Migrate)
        In your app setup
            from flask_migrate import Migrate
            migrate = Migrate(app, db)

        Generate migration:
            flask db migrate -m "Describe changes"

        Apply migration:
            flask db upgrade
"""
