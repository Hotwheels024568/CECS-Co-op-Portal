from typing import Optional, Tuple
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.schema import StudentAccount, FacultyAccount
from src.database.manager import get_constraint_name_from_integrity_error
from src.database.record_insertion import add_contact, add_faculty, add_student
from src.database.record_get_or_create import (
    get_or_create_department,
    get_or_create_major,
)


async def create_student_profile(
    session: AsyncSession,
    account_id: int,
    # Contact
    first_name: str,
    middle_name: Optional[str],
    last_name: str,
    email: str,
    phone: Optional[str],
    # Student
    department_name: str,
    major_name: str,
    credit_hours: int,
    gpa: float,
    start_semester: str,
    start_year: int,
    transfer: bool,
    resume_link: Optional[str] = None,
) -> Tuple[Optional[StudentAccount], str]:
    """
    Atomically creates a student profile for the specified account.

    This function inserts a unique contact record for the student,
    ensures existence (or creates) their department and major, and creates
    a StudentAccount profile. All operations are safe against concurrency:
    uniqueness constraints (such as email) are enforced at the database level.
    On failure, an informative message is returned and the transaction is rolled back.

    Args:
        session (AsyncSession): Active SQLAlchemy async session for database access.
        account_id (int): The ID of the Account row to associate with the new student profile.
        first_name (str): Student's first name.
        middle_name (Optional[str]): Student's middle name.
        last_name (str): Student's last name.
        email (str): Student's email address (must be unique).
        phone (Optional[str]): Student's phone number.
        department_name (str): Student's department name.
        major_name (str): Student's major or field of study.
        credit_hours (int): Number of credit hours the student has completed.
        gpa (float): Student's current grade point average.
        start_semester (str): Name of the semester the student started (e.g., 'Fall').
        start_year (int): Year the student started (e.g., 2024).
        transfer (bool): Whether the student transferred from another institution.
        resume_link (Optional[str]): URL/link to the student's resume file.

    Returns:
        Tuple[Optional[StudentAccount], str]:
            - (StudentAccount, "Profile created successfully.") on success.
            - (None, "Email already in use.") if the email exists.
            - (None, "Unique constraint violated: [constraint_name]") for other unique violations.
            - (None, "Database API error: [message]") for low-level errors.
            - (None, "Unexpected error: [message]") for any other failures.
    """
    try:
        # 1. Create ContactInfo (unique on email)
        contact = await add_contact(
            session, account_id, first_name, middle_name, last_name, email, phone
        )

        # 2. Get or Create Department
        department = await get_or_create_department(session, department_name)

        # 3. Get or Create Major
        major = await get_or_create_major(session, major_name)

        # 4. Create Student profile
        student = await add_student(
            session,
            account_id,
            department.id,
            major.id,
            credit_hours,
            gpa,
            start_semester,
            start_year,
            transfer,
            resume_link,
        )

        # 4. Commit all
        await session.commit()
        return student, "Profile created successfully."

    except IntegrityError as e:
        await session.rollback()
        constraint = get_constraint_name_from_integrity_error(e)
        if "contact_info_email_key" in constraint:
            return None, "Email already in use."

        return (
            None,
            f"Unique constraint violated in create_student_profile: {constraint}",
        )

    except DBAPIError as e:
        await session.rollback()
        # These are lower-level errors, can include connection errors, syntax errors, etc.
        return None, f"Database API error in create_student_profile: {e}"

    except Exception as e:
        await session.rollback()
        return None, f"Unexpected error in create_student_profile: {e}"


async def create_faculty_profile(
    session: AsyncSession,
    account_id: int,
    # Contact
    first_name: str,
    middle_name: Optional[str],
    last_name: str,
    email: str,
    phone: Optional[str],
    # Faculty
    department_name: str,
) -> Tuple[Optional[FacultyAccount], str]:
    """
    Atomically creates a faculty profile, including a unique contact record and FacultyAccount,
    and links the faculty profile to the provided account and department.

    Uniqueness of contact email and department assignment is enforced at the database
    level, making this routine safe for concurrent creation.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
        account_id (int): The ID of the Account row to link the new profile to.
        first_name (str): Faculty member's first name.
        middle_name (Optional[str]): Faculty member's middle name.
        last_name (str): Faculty member's last name.
        email (str): Faculty member's email address (must be unique).
        phone (Optional[str]): Faculty member's phone number.
        department_name (str): Name of faculty member's department.

    Returns:
        Tuple[Optional[FacultyAccount], str]:
            - (FacultyAccount, "Profile created successfully.") on success.
            - (None, "Email already in use.") if the email exists.
            - (None, "Unique constraint violated: [constraint_name]") for other unique violations.
            - (None, "Database API error: [message]") for database-layer errors.
            - (None, "Unexpected error: [message]") for any other failures.
    """
    try:
        # 1. Create ContactInfo (unique on email)
        contact = await add_contact(
            session, account_id, first_name, middle_name, last_name, email, phone
        )

        # 2. Get or Create Department
        department = await get_or_create_department(session, department_name)

        # 3. Create Faculty profile
        faculty = await add_faculty(
            session,
            account_id,
            department.id,
        )

        # 4. Commit all
        await session.commit()
        return faculty, "Profile created successfully."

    except IntegrityError as e:
        await session.rollback()
        constraint = get_constraint_name_from_integrity_error(e)
        if "contact_info_email_key" in constraint:
            return None, "Email already in use."

        return (
            None,
            f"Unique constraint violated in create_faculty_profile: {constraint}",
        )

    except DBAPIError as e:
        await session.rollback()
        # These are lower-level errors, can include connection errors, syntax errors, etc.
        return None, f"Database API error in create_faculty_profile: {e}"

    except Exception as e:
        await session.rollback()
        return None, f"Unexpected error in create_faculty_profile: {e}"
