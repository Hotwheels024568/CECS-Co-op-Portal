from typing import Optional, Tuple
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.schema import EmployerAccount, FacultyAccount, StudentAccount
from src.database.manage import get_constraint_name_from_integrity_error
from src.database.record_insertion import (
    add_address,
    add_company,
    add_contact,
    add_employer,
    add_student,
    add_faculty,
)
from src.database.record_retrieval import get_company_by_name
from src.database.record_get_or_create import (
    get_or_create_department,
    get_or_create_major,
)


async def create_employer_profile(
    session: AsyncSession,
    account_id: int,
    # Contact
    first_name: str,
    middle_name: Optional[str],
    last_name: str,
    email: str,
    phone: Optional[str],
    # Company
    company_name: str,
    website_link: Optional[str] = None,
    # Address
    address_line1: Optional[str] = None,
    address_line2: Optional[str] = None,
    city: Optional[str] = None,
    state_province: Optional[str] = None,
    zip_postal: Optional[str] = None,
    country: Optional[str] = None,
) -> Tuple[Optional[EmployerAccount], str]:
    """
    Atomically creates an employer profile for the specified account.

    If a company with the given name exists, the profile will link to that company and
    ignore all address and website information. If not, a new company (and associated
    address) will be created and linked.

    Uniqueness constraints apply to both contact email and company name.

    Args:
        session (AsyncSession): Active SQLAlchemy async session for database access.
        account_id (int): The ID of the Account row to associate with the employer profile.
        first_name (str): Employer contact's first name.
        middle_name (Optional[str]): Employer contact's middle name.
        last_name (str): Employer contact's last name.
        email (str): Employer contact's unique email address.
        phone (Optional[str]): Employer contact's phone number.
        company_name (str): The name of the employer's company (must be unique if creating).
        website_link (Optional[str]): The company's website (used only if creating company).
        address_line1 (Optional[str]): First line of company address (used only if creating company).
        address_line2 (Optional[str]): Second line of company address (used only if creating company).
        city (Optional[str]): Company address city (used only if creating company).
        state_province (Optional[str]): State/Province of company address (used only if creating company).
        zip_postal (Optional[str]): ZIP/postal code of company address (used only if creating company).
        country (Optional[str]): Country of company address (used only if creating company).

    Returns:
        Tuple[Optional[EmployerAccount], str]:
            - (EmployerAccount, "Profile created successfully.") on success.
            - (None, "Email already in use.") if the contact email already exists.
            - (None, "Company name already exists.") if company exists and cannot be created.
            - (None, "Unique constraint violated: [constraint_name]") for other unique violations.
            - (None, "Database API error: [message]") for database-layer errors.
            - (None, "Unexpected error: [message]") for all other failures.
    """
    try:
        existing_company = await get_company_by_name(session, company_name)
        if existing_company:
            return await create_employer_profile_select_company(
                session,
                account_id,
                first_name,
                middle_name,
                last_name,
                email,
                phone,
                existing_company.id,
            )

        if not all([address_line1, city, state_province, zip_postal, country]):
            return None, "Missing required address fields for new company"

        return await create_employer_profile_create_company(
            session,
            account_id,
            first_name,
            middle_name,
            last_name,
            email,
            phone,
            company_name,
            website_link,
            address_line1,
            address_line2,
            city,
            state_province,
            zip_postal,
            country,
        )

    except Exception as e:
        await session.rollback()
        return None, f"Unexpected error create_employer_profile: {e}"


async def create_employer_profile_select_company(
    session: AsyncSession,
    account_id: int,
    # Contact
    first_name: str,
    middle_name: Optional[str],
    last_name: str,
    email: str,
    phone: Optional[str],
    # Company
    company_id: int,
) -> Tuple[Optional[EmployerAccount], str]:
    """
    Atomically creates an employer profile for the specified account,
    linking to an existing company. A new contact record is created
    and associated with the employer profile.

    Uniqueness of the contact email is enforced.

    Args:
        session (AsyncSession): Active SQLAlchemy async session for database access.
        account_id (int): The ID of the Account row to associate with the employer profile.
        first_name (str): Employer contact's first name.
        middle_name (Optional[str]): Employer contact's middle name.
        last_name (str): Employer contact's last name.
        email (str): Employer contact's unique email address.
        phone (Optional[str]): Employer contact's phone number.
        company_id (int): The ID of the (existing) company to associate with this profile.

    Returns:
        Tuple[Optional[EmployerAccount], str]:
            - (EmployerAccount, "Profile created successfully.") on success.
            - (None, "Email already in use.") if the contact email already exists.
            - (None, "Unique constraint violated: [constraint_name]") for other unique violations.
            - (None, "Database API error: [message]") for database-layer errors.
            - (None, "Unexpected error: [message]") for all other failures.
    """
    try:
        # 1. Create ContactInfo (unique on email)
        contact = await add_contact(
            session, account_id, first_name, middle_name, last_name, email, phone
        )

        # 2. Create EmployerAccount
        employer = await add_employer(session, account_id, company_id)

        # 3. Commit all changes
        await session.commit()
        return employer, "Profile created successfully."

    except IntegrityError as e:
        await session.rollback()
        constraint = get_constraint_name_from_integrity_error(e)
        if "contact_info_email_key" in constraint:
            return None, "Email already in use."

        return (
            None,
            f"Unique constraint violated in create_employer_profile_select_company: {constraint}",
        )

    except DBAPIError as e:
        await session.rollback()
        # These are lower-level errors, can include connection errors, syntax errors, etc.
        return None, f"Database API error in create_employer_profile_select_company: {e}"

    except Exception as e:
        await session.rollback()
        return None, f"Unexpected error in create_employer_profile_select_company: {e}"


async def create_employer_profile_create_company(
    session: AsyncSession,
    account_id: int,
    # Contact
    first_name: str,
    middle_name: Optional[str],
    last_name: str,
    email: str,
    phone: Optional[str],
    # Company
    company_name: str,
    website_link: Optional[str],
    # Address
    address_line1: str,
    address_line2: Optional[str],
    city: str,
    state_province: str,
    zip_postal: str,
    country: str,
) -> Tuple[Optional[EmployerAccount], str]:
    """
    Atomically creates an employer profile for the specified account,
    including a new company (with address), and a new contact record.
    Links the created entities together and enforces uniqueness on both
    contact email and company name.

    Args:
        session (AsyncSession): Active SQLAlchemy async session for database access.
        account_id (int): The ID of the Account row to associate with the employer profile.
        first_name (str): Employer contact's first name.
        middle_name (Optional[str]): Employer contact's middle name.
        last_name (str): Employer contact's last name.
        email (str): Employer contact's unique email address.
        phone (Optional[str]): Employer contact's phone number.
        company_name (str): The name of the employer's company (must be unique).
        website_link (Optional[str]): The company's website.
        address_line1 (str): First line of company address.
        address_line2 (Optional[str]): Second line of company address.
        city (str): City of company address.
        state_province (str): State or province of company address.
        zip_postal (str): ZIP/postal code of company address.
        country (str): Country of company address.

    Returns:
        Tuple[Optional[EmployerAccount], str]:
            - (EmployerAccount, "Profile created successfully.") on success.
            - (None, "Email already in use.") if the contact email already exists.
            - (None, "Company name already exists.") if the company name already exists.
            - (None, "Unique constraint violated: [constraint_name]") for other unique violations.
            - (None, "Database API error: [message]") for database-layer errors.
            - (None, "Unexpected error: [message]") for all other failures.
    """
    try:
        # 1. Create Address
        address = await add_address(
            session,
            address_line1,
            address_line2,
            city,
            state_province,
            zip_postal,
            country,
        )

        # 2. Create Company (unique on name)
        company = await add_company(session, company_name, address.id, website_link)

        # 3. Create ContactInfo (unique on email)
        contact = await add_contact(
            session, account_id, first_name, middle_name, last_name, email, phone
        )

        # 4. Create Employer
        employer = await add_employer(session, account_id, company.id)

        # 5. Commit all changes
        await session.commit()
        return employer, "Profile created successfully."

    except IntegrityError as e:
        await session.rollback()
        constraint = get_constraint_name_from_integrity_error(e)
        if "contact_info_email_key" in constraint:
            return None, "Email already in use."
        elif "companies_name_key" in constraint:
            return None, "Company name already exists."

        return (
            None,
            f"Unique constraint violated in create_employer_profile_create_company: {constraint}",
        )

    except DBAPIError as e:
        await session.rollback()
        # These are lower-level errors, can include connection errors, syntax errors, etc.
        return None, f"Database API error in create_employer_profile_create_company: {e}"

    except Exception as e:
        await session.rollback()
        return None, f"Unexpected error in create_employer_profile_create_company: {e}"


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
