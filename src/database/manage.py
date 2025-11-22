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
    session factory, and utility methods for schema initialization, schema resetting, and seeding.
    It provides both direct context-managed asynchronous sessions and async context management for
    use with FastAPI or other async frameworks.

    Attributes:
        engine (AsyncEngine): The SQLAlchemy asynchronous database engine.
        SessionMaker (async_sessionmaker): A factory for creating AsyncSession objects.
        metadata (MetaData): The metadata registry for SQLAlchemy models.
        autocommit (bool): Default autocommit setting for sessions created by this manager.
        _session (Optional[AsyncSession]): Internal reference to the currently active session.
        _instance (Optional[AsyncDBManager]): Singleton instance for this class.

    Class Methods:
        create(rebuild: bool = False, seed: bool = False, autocommit: bool = False) -> AsyncDBManager:
            Asynchronously initializes or returns the singleton DB manager, recreating and/or seeding the database schema as requested.

    Instance Methods:
        @asynccontextmanager
        async def session(autocommit: Optional[bool] = None) -> AsyncGenerator[AsyncSession, None]:
            Asynchronous context manager yielding a database session.
            Commits automatically when autocommit is True, or else expects manual commit.

        async def __aenter__() -> AsyncSession:
            Enter an async context with an open session. Uses manager's default autocommit setting.

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
        """
        Initialize the AsyncDBManager instance.

        Args:
            autocommit (bool): Default session autocommit behavior. If True, sessions commit automatically.
        """
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.SessionMaker = async_sessionmaker(self.engine, expire_on_commit=False, autoflush=False)
        self.metadata = Base.metadata
        self.autocommit = autocommit
        self._session = None

    @classmethod
    async def create(
        cls, rebuild: bool = False, seed: bool = False, autocommit: bool = False
    ) -> Self:
        """
        Create or return the singleton AsyncDBManager.

        Args:
            rebuild (bool): If True, drop existing tables and recreate the schema.
            seed (bool): If True, populate empty tables with initial data from seed JSON.
            autocommit (bool): Default autocommit behavior for sessions.

        Returns:
            AsyncDBManager: The singleton database manager instance.
        """
        if cls._instance:
            return cls._instance

        self = cls._instance = cls(autocommit)

        if rebuild:
            await self._drop_db()
        await self._create_db()
        if seed:
            await self._seed()

        return self

    async def _create_db(self) -> None:
        """Create (initialize) all tables in the database schema."""
        async with self.engine.begin() as conn:
            await conn.run_sync(self.metadata.create_all)

    async def _drop_db(self) -> None:
        """
        Drop all tables from the database schema.

        If standard table drop fails, attempts to drop and recreate the entire 'public' schema (PostgreSQL only).
        """
        async with self.engine.begin() as conn:
            try:
                await conn.run_sync(self.metadata.drop_all)
            except Exception as e:
                from sqlalchemy import text

                print(
                    f"Standard drop_all failed with error: {e}.\n"
                    "Attempting full schema drop and recreation..."
                )
                await conn.execute(text("DROP SCHEMA public CASCADE"))
                await conn.execute(text("CREATE SCHEMA public"))

    async def _seed(self, json_path: Path = Path("seed_data.json")) -> None:
        """
        Seed the database tables with initial data from a JSON file.

        Tables are only seeded if empty.

        Args:
            json_path (Path): File path to the seed JSON data.
        """
        from sqlalchemy import select, func
        import json

        tables = {table.name: table for table in self.metadata.sorted_tables}
        with open(json_path) as file:
            seed_data = json.load(file)

        async with self.engine.begin() as conn:
            for table_name, records in seed_data.items():
                table = tables.get(table_name)
                if not table or not records:
                    continue

                # Check if table is empty
                count_query = select(func.count()).select_from(table)
                result = await conn.execute(count_query)
                table_count = result.scalar()

                if table_count == 0:
                    await conn.execute(table.insert(), records)

    # --- context manager (manager.session())
    @asynccontextmanager
    async def session(
        self, autocommit: Optional[bool] = None
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Provide an asynchronous context-managed database session.

        Args:
            autocommit (Optional[bool]): If provided, overrides the manager's default autocommit for this session.
                - If True, commits automatically after context exit unless an exception occurs.
                - If False, expects manual commit by calling code.

        Yields:
            AsyncSession: An async SQLAlchemy session.
        """
        auto = self.autocommit if autocommit is None else autocommit
        async with self.SessionMaker() as session:
            self._session = session
            try:
                yield session
                if auto:
                    await session.commit()

            except Exception:
                await session.rollback()
                raise

            finally:
                self._session = None

    async def __aenter__(self) -> AsyncSession:
        """Enter async context with an open session. Uses manager's default autocommit setting."""
        self._session_obj = self.SessionMaker()
        self._session = await self._session_obj.__aenter__()
        self._current_autocommit = self.autocommit
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context, committing the session if autocommit is enabled and no exception occurred, or rolling back otherwise."""
        if self._session is not None:
            if self._current_autocommit and exc_type is None:
                await self._session.commit()
            # Rollback if auto-committing or an exception occurred
            else:
                await self._session.rollback()

            await self._session_obj.__aexit__(exc_type, exc_val, exc_tb)
            self._current_autocommit = None
            self._session = None


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
    from src.database.utils import count

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
