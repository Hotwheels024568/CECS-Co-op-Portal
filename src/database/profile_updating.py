from typing import Optional
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.schema import Company, EmployerAccount, FacultyAccount, StudentAccount
from src.database.utils import get_constraint_name_from_integrity_error
from src.database.record_retrieval import get_company_by_id
from src.database.record_updating import (
    update_address,
    update_company,
    update_contact,
    update_employer,
    update_student,
    update_faculty,
)
from src.database.record_get_or_create import (
    get_or_create_department,
    get_or_create_major,
)


async def update_company_profile(
    session: AsyncSession,
    company_id: int,
    # Company
    company_name: Optional[str] = None,
    website_link: Optional[str] = None,
    # Address
    address_line1: Optional[str] = None,
    address_line2: Optional[str] = None,
    city: Optional[str] = None,
    state_province: Optional[str] = None,
    zip_postal: Optional[str] = None,
    country: Optional[str] = None,
) -> tuple[Optional[Company], str]:
    """
    Updates a company's profile details and address information.

    Args:
        session (AsyncSession): Active SQLAlchemy async session for database access.
        company_id (int): The ID of the Company to update.
        company_name (Optional[str], optional): Updated company company_name.
        website_link (Optional[str], optional): Updated company website_link.
        address_line1 (Optional[str], optional): Updated company address's address_line1.
        address_line2 (Optional[str], optional): Updated company address's address_line2.
        city (Optional[str], optional): Updated company address's city.
        state_province (Optional[str], optional): Updated company address's state_province.
        zip_postal (Optional[str], optional): Updated company address's zip_postal.
        country (Optional[str], optional): Updated company address's country.

    Returns:
        tuple[Optional[Company], str]:
            - (Company, "Company details updated.") on success.
            - (None, "Company does not exist.") if a company with the provided id does not exist.
            - (None, "Company name already exists.") if the company name already exists.
            - (None, "Unique constraint violated: [constraint_name]") for other unique violations.
            - (None, "Database API error: [message]") for database-layer errors.
            - (None, "Unexpected error: [message]") for all other failures.
    """
    try:
        company = await get_company_by_id(session, company_id)
        if company is None:
            return None, "Company does not exist."

        address_id = company.address.id
        address = await update_address(
            session,
            address_id,
            address_line1,
            address_line2,
            city,
            state_province,
            zip_postal,
            country,
        )

        company = await update_company(
            session,
            company.id,
            company_name,
            None,
            website_link,
        )

        await session.commit()
        return company, "Company details updated."

    except IntegrityError as e:
        await session.rollback()
        constraint = get_constraint_name_from_integrity_error(e)
        if "companies_name_key" in constraint:
            return None, "Company name already exists."

        return (None, f"Unique constraint violated in update_company_profile: {constraint}")

    except DBAPIError as e:
        await session.rollback()
        # These are lower-level errors, can include connection errors, syntax errors, etc.
        return None, f"Database API error in update_company_profile: {e}"

    except Exception as e:
        await session.rollback()
        return None, f"Unexpected error in update_company_profile: {e}"


async def update_employer_profile(
    session: AsyncSession,
    account_id: int,
    # Contact
    first_name: Optional[str] = None,
    middle_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    # Profile
    company_id: Optional[int] = None,
) -> tuple[Optional[EmployerAccount], str]:
    """
    Updates an employer's profile, including associated contact information and company affiliation.

    Args:
        session (AsyncSession): Active SQLAlchemy async session for database access.
        account_id (int): The ID of the Employer account to update.
        first_name (Optional[str], optional): Updated employer contact's first name.
        middle_name (Optional[str], optional): Updated employer contact's middle name.
        last_name (Optional[str], optional): Updated employer contact's last name.
        email (Optional[str], optional): Updated employer contact's unique email address.
        phone (Optional[str], optional): Updated employer contact's phone number.
        company_id (Optional[int], optional): The updated ID of a company to associate with this profile.

    Returns:
        tuple[Optional[EmployerAccount], str]:
            - (EmployerAccount, "Employer profile updated.") on success.
            - (None, "Company does not exist.") if a company with the provided id does not exist.
            - (None, "Unexpected error: [message]") for all other failures.
    """
    try:
        # 1. Update ContactInfo (unique on email)
        contact = await update_contact(
            session, account_id, first_name, middle_name, last_name, email, phone
        )

        # 2. Check Company ID
        company = await get_company_by_id(session, company_id)
        if company is None:
            return None, "Company does not exist."

        # 3. Update EmployerAccount
        employer = await update_employer(session, account_id, company_id)

        # 4. Commit all changes
        await session.commit()
        return employer, "Employer profile updated."

    except Exception as e:
        await session.rollback()
        return None, f"Unexpected error update_employer_profile: {e}"


async def update_student_profile(
    session: AsyncSession,
    account_id: int,
    # Contact
    first_name: Optional[str] = None,
    middle_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    # Student
    department_name: Optional[str] = None,
    major_name: Optional[str] = None,
    credit_hours: Optional[int] = None,
    gpa: Optional[float] = None,
    start_semester: Optional[str] = None,
    start_year: Optional[int] = None,
    transfer: Optional[bool] = None,
    resume_link: Optional[str] = None,
) -> tuple[Optional[StudentAccount], str]:
    """
    Updates a student's profile, including contact, department, major, and academic details.

    Args:
        session (AsyncSession): Active SQLAlchemy async session for database access.
        account_id (int): The ID of the Student account to update.
        first_name (Optional[str], optional): Updated student contact's first name.
        middle_name (Optional[str], optional): Updated student contact's middle name.
        last_name (Optional[str], optional): Updated student contact's last name.
        email (Optional[str], optional): Updated student contact's unique email address.
        phone (Optional[str], optional): Updated student contact's phone number.
        department_name (Optional[str], optional): Updated student's department_name.
        major_name (Optional[str], optional): Updated student's major_name.
        credit_hours (Optional[int], optional): Updated student's credit_hours.
        gpa (Optional[float], optional): Updated student's gpa.
        start_semester (Optional[str], optional): Updated student's start_semester.
        start_year (Optional[int], optional): Updated student's start_year.
        transfer (Optional[bool], optional): Updated student's transfer.
        resume_link (Optional[str], optional): Updated student's resume_link.

    Returns:
        tuple[Optional[StudentAccount], str]:
            - (StudentAccount, "Student profile updated.") on success.
            - (None, "Email already in use.") if the email already exists.
            - (None, "Unique constraint violated: [constraint_name]") for other unique violations.
            - (None, "Database API error: [message]") for database-layer errors.
            - (None, "Unexpected error: [message]") for all other failures.
    """
    try:
        # 1. Update ContactInfo (unique on email)
        contact = await update_contact(
            session, account_id, first_name, middle_name, last_name, email, phone
        )

        # 2. Get or Create Department
        department = await get_or_create_department(session, department_name)

        # 3. Get or Create Major
        major = await get_or_create_major(session, major_name)

        # 4. Update Student profile
        student = await update_student(
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
        return student, "Student profile updated."

    except IntegrityError as e:
        await session.rollback()
        constraint = get_constraint_name_from_integrity_error(e)
        if "contact_info_email_key" in constraint:
            return None, "Email already in use."

        return (None, f"Unique constraint violated in update_student_profile: {constraint}")

    except DBAPIError as e:
        await session.rollback()
        # These are lower-level errors, can include connection errors, syntax errors, etc.
        return None, f"Database API error in update_student_profile: {e}"

    except Exception as e:
        await session.rollback()
        return None, f"Unexpected error in update_student_profile: {e}"


async def update_faculty_profile(
    session: AsyncSession,
    account_id: int,
    # Contact
    first_name: Optional[str] = None,
    middle_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    # Faculty
    department_name: Optional[str] = None,
) -> tuple[Optional[FacultyAccount], str]:
    """
    Updates a faculty member's profile, including contact information and department affiliation.

    Args:
        session (AsyncSession): Active SQLAlchemy async session for database access.
        account_id (int): The ID of the Faculty account to update.
        first_name (Optional[str], optional): Updated faculty contact's first name.
        middle_name (Optional[str], optional): Updated faculty contact's middle name.
        last_name (Optional[str], optional): Updated faculty contact's last name.
        email (Optional[str], optional): Updated faculty contact's unique email address.
        phone (Optional[str], optional): Updated faculty contact's phone number.
        department_name (Optional[str], optional): Updated faculty's department_name.

    Returns:
        tuple[Optional[FacultyAccount], str]:
            - (FacultyAccount, "Faculty profile updated.") on success.
            - (None, "Email already in use.") if the email already exists.
            - (None, "Unique constraint violated: [constraint_name]") for other unique violations.
            - (None, "Database API error: [message]") for database-layer errors.
            - (None, "Unexpected error: [message]") for all other failures.
    """
    try:
        # 1. Update ContactInfo (unique on email)
        contact = await update_contact(
            session, account_id, first_name, middle_name, last_name, email, phone
        )

        # 2. Get or Create Department
        department = await get_or_create_department(session, department_name)

        # 3. Update Faculty profile
        faculty = await update_faculty(
            session,
            account_id,
            department.id,
        )

        # 4. Commit all
        await session.commit()
        return faculty, "Faculty profile updated."

    except IntegrityError as e:
        await session.rollback()
        constraint = get_constraint_name_from_integrity_error(e)
        if "contact_info_email_key" in constraint:
            return None, "Email already in use."

        return (None, f"Unique constraint violated in update_faculty_profile: {constraint}")

    except DBAPIError as e:
        await session.rollback()
        # These are lower-level errors, can include connection errors, syntax errors, etc.
        return None, f"Database API error in update_faculty_profile: {e}"

    except Exception as e:
        await session.rollback()
        return None, f"Unexpected error in update_faculty_profile: {e}"
