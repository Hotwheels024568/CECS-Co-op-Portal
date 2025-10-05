from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.functions import execute, get_first_element
from src.database.schema import (
    Accounts,
    Addresses,
    Companies,
    ContactInfo,
    Employers,
    Students,
    Faculty,
)


async def sign_up(
    session: AsyncSession,
    username: str,
    password: str,
    user_type: str,
) -> Optional[int]:
    """
    Signs up a new user account if the username is available.

    Args:
        session (AsyncSession): Database session.
        username (str): Desired username.
        password (str): Hashed password.
        user_type (str): One of: 'Employer', 'Student', 'Faculty'.

    Returns:
        Optional[int]: The newly created Account id, or None on failure (e.g., username taken).
    """
    statement = (
        insert(Accounts)
        .values(
            username=username, password=password, user_type=user_type, profile_id=None
        )
        .on_conflict_do_nothing(index_elements=[Accounts.username])
        .returning(Accounts.id)
    )
    try:
        account_id = await get_first_element(session, statement)
        if account_id is None:  # Username was already in use
            await session.rollback()
            return None

        await session.commit()
        return account_id

    except Exception as e:
        await session.rollback()
        print(f"Error in DB 'sign_up' function:\nStatement: {statement}\nError: {e}")
        return None


async def create_employer_profile(
    session: AsyncSession,
    account_id: int,
    # Contact
    first_name: str,
    middle_name: str,
    last_name: str,
    email: str,
    phone: str,
    # Company
    company_name: str,
    website_link: str,
    # Address
    address_line1: str,
    address_line2: str,
    city: str,
    state_province: str,
    zip_postal: str,
    country: str,
) -> Tuple[bool, str]:
    """
    Atomically creates an employer profile, including address, company, and contact records,
    then links the employer profile to the provided account.
    Uniqueness of the contact email and company name are enforced.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
        account_id (int): The ID of the Account row to link the new profile to.
        first_name (str): Employer contact's first name.
        middle_name (str): Employer contact's middle name.
        last_name (str): Employer contact's last name.
        email (str): Employer contact's email address (must be unique).
        phone (str): Employer contact's phone number.
        company_name (str): The name of the employer's company (must be unique).
        website_link (str): The company's website URL.
        address_line1 (str): The first line of the company address.
        address_line2 (str): The second line of the company address.
        city (str): The city of the company address.
        state_province (str): The state/province of the company address.
        zip_postal (str): The ZIP/postal code of the company address.
        country (str): The country of the company address.

    Returns:
        (Tuple[bool, str]): (True, "Profile created successfully.") on success,
            or (False, reason) if a unique constraint is violated or another error occurs:
            - "Email already in use." if the email exists.
            - "Company name already exists." if the company exists.
            - "A unique constraint was violated." for other unique constraints.
            - "Unexpected error: ..." for unforeseen failures.
    """
    try:
        # 1. Create Address
        address = Addresses(
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            state_province=state_province,
            zip_postal=zip_postal,
            country=country,
        )
        session.add(address)
        await session.flush()  # Populates address.id

        # 2. Create Company (unique on name)
        company = Companies(
            name=company_name, address_id=address.id, website_link=website_link
        )
        session.add(company)
        await session.flush()  # Populates company.id or raises

        # 3. Create ContactInfo (unique on email)
        contact = ContactInfo(
            first=first_name, middle=middle_name, last=last_name, email=email, phone=phone
        )
        session.add(contact)
        await session.flush()  # Populates contact.id or raises

        # 4. Create Employer
        employer = Employers(company_id=company.id, contact_id=contact.id)
        session.add(employer)
        await session.flush()  # Populates employer.id

        # 5. Link profile to account
        statement = (
            update(Accounts)
            .where(Accounts.id == account_id)
            .values(profile_id=employer.id)
        )
        await execute(session, statement)

        # 6. Commit all changes
        await session.commit()
        return True, "Profile created successfully."

    except IntegrityError as e:
        await session.rollback()
        constraint = getattr(getattr(e.orig, "diag", None), "constraint_name", "") or str(
            e
        )
        # TODO: Check violated constraint names for exact string key name
        if "contact_info_email_key" in constraint:
            return False, "Email already in use."
        # TODO: Check violated constraint names for exact string key name
        elif "companies_name_key" in constraint:
            return False, "Company name already exists."
        else:
            return False, "A unique constraint was violated."

    except Exception as e:
        await session.rollback()
        return False, f"Unexpected error in DB 'create_employer_profile' function: {e}"


async def create_student_profile(
    session: AsyncSession,
    account_id: int,
    # Contact
    first_name: str,
    middle_name: str,
    last_name: str,
    email: str,
    phone: str,
    # Student
    department: str,
    major: str,
    credit_hours: int,
    gpa: float,
    start_semester_year: str,
    transfer: bool,
    resume_link: str,
) -> Tuple[bool, str]:
    """
    Atomically creates a student profile, including a unique contact record,
    a student record, and links the student profile to the provided account.
    Uniqueness of the contact email is enforced.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
        account_id (int): The ID of the Account row to link the new profile to.
        first_name (str): Student's first name.
        middle_name (str): Student's middle name.
        last_name (str): Student's last name.
        email (str): Student's email address (must be unique).
        phone (str): Student's phone number.
        department (str): Student's department.
        major (str): Student's major or field of study.
        credit_hours (int): Number of credit hours the student has completed.
        gpa (float): Student's current GPA.
        start_semester_year (str): Semester and year the student started (e.g., 'Fall 2024').
        transfer (bool): Whether the student has transferred from another institution.
        resume_link (str): URL to the student's resume file.

    Returns:
        Tuple[bool, str]: (True, "Profile created successfully.") on success,
            or (False, reason) if a unique constraint is violated or another error occurs:
                - "Email already in use." if the email exists.
                - "A unique constraint was violated." for other unique constraints.
                - "Unexpected error: ..." for unforeseen failures.
    """
    try:
        # 1. Create ContactInfo (unique on email)
        contact = ContactInfo(
            first=first_name, middle=middle_name, last=last_name, email=email, phone=phone
        )
        session.add(contact)
        await session.flush()  # Populates contact.id or raises

        # 2. Create Student profile
        student = Students(
            contact_id=contact.id,
            department=department,
            major=major,
            credit_hours=credit_hours,
            gpa=gpa,
            start_semester_year=start_semester_year,
            transfer=transfer,
            resume_link=resume_link,
        )
        session.add(student)
        await session.flush()  # Populates student.id

        # 3. Link profile to account
        statement = (
            update(Accounts)
            .where(Accounts.id == account_id)
            .values(profile_id=student.id)
        )
        await execute(session, statement)

        # 4. Commit all
        await session.commit()
        return True, "Profile created successfully."

    except IntegrityError as e:
        await session.rollback()
        constraint = getattr(getattr(e.orig, "diag", None), "constraint_name", "") or str(
            e
        )
        # TODO: Check violated constraint names for exact string key name
        if "contact_info_email_key" in constraint:
            return False, "Email already in use."
        else:
            return False, "A unique constraint was violated."

    except Exception as e:
        await session.rollback()
        return False, f"Unexpected error in DB 'create_student_profile' function: {e}"


async def create_faculty_profile(
    session: AsyncSession,
    account_id: int,
    # Contact
    first_name: str,
    middle_name: str,
    last_name: str,
    email: str,
    phone: str,
    # Faculty
    department: str,
) -> Tuple[bool, str]:
    """
    Atomically creates a faculty profile, including a unique contact record and a faculty record,
    and links the faculty profile to the provided account. Uniqueness of the contact email and
    department is enforced at the database level, making the process safe from race conditions.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
        account_id (int): The ID of the Account row to link the new profile to.
        first_name (str): Faculty member's first name.
        middle_name (str): Faculty member's middle name.
        last_name (str): Faculty member's last name.
        email (str): Faculty member's email address (must be unique).
        phone (str): Faculty member's phone number.
        department (str): Faculty member's department (must be unique).

    Returns:
        Tuple[bool, str]: (True, "Profile created successfully.") on success,
            or (False, reason) if a unique constraint is violated or another error occurs:
                - "Email already in use." if the email exists.
                - "Department already exists." if the department exists.
                - "A unique constraint was violated." for other unique constraints.
                - "Unexpected error: ..." for unforeseen failures.

    Notes:
        - This function is race-condition safe: uniqueness is enforced through database constraints,
          and all inserts are attempted directly. If another process inserts the same email or department
          simultaneously, only one will succeed and the appropriate error message will be returned.
        - The constraint names (e.g., `contact_info_email_key`, `faculty_department_key`)
          may need adjustment to match your actual database schema.
    """
    try:
        # 1. Create ContactInfo (unique on email)
        contact = ContactInfo(
            first=first_name, middle=middle_name, last=last_name, email=email, phone=phone
        )
        session.add(contact)
        await session.flush()  # Populates contact.id or raises

        # 2. Create Faculty profile (unique on department)
        faculty = Faculty(contact_id=contact.id, department=department)
        session.add(faculty)
        await session.flush()  # Populates faculty.id or raises

        # 3. Link profile to account
        statement = (
            update(Accounts)
            .where(Accounts.id == account_id)
            .values(profile_id=faculty.id)
        )
        await execute(session, statement)

        # 4. Commit all
        await session.commit()
        return True, "Profile created successfully."

    except IntegrityError as e:
        await session.rollback()
        constraint = getattr(getattr(e.orig, "diag", None), "constraint_name", "") or str(
            e
        )
        # TODO: Check violated constraint names for exact string key name
        if "contact_info_email_key" in constraint:
            return False, "Email already in use."
        # TODO: Check violated constraint names for exact string key name
        elif "faculty_department_key" in constraint:
            return False, "Department already exists."
        else:
            return False, "A unique constraint was violated."

    except Exception as e:
        await session.rollback()
        return False, f"Unexpected error in DB 'create_faculty_profile' function: {e}"
