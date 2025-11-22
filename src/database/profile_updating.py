from typing import Optional, Tuple
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


async def update_employer_profile(
    session: AsyncSession,
    account_id: int,
    # Contact
    first_name: Optional[str] = None,
    middle_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> Tuple[Optional[EmployerAccount], str]:
    """
    __
    """
    try:
        # 1. Update ContactInfo (unique on email)
        contact = await update_contact(
            session, account_id, first_name, middle_name, last_name, email, phone
        )
        # TODO: either update or create a new company

        employer = await update_employer(session, account_id, None)

        await session.commit()
        return employer, "Employer profile updated."

    except Exception as e:
        await session.rollback()
        return None, f"Unexpected error update_employer_profile: {e}"


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
) -> Tuple[Optional[Company], str]:
    """
    __
    """
    try:
        company = await get_company_by_id(session, company_id)
        address = company.address

        address = await update_address(
            session,
            address.id,
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
            website_link=website_link,
        )

        await session.commit()
        return company, "Company profile updated."

    except IntegrityError as e:
        await session.rollback()
        constraint = get_constraint_name_from_integrity_error(e)
        if "companies_name_key" in constraint:
            return None, "Company name already exists."

        return (
            None,
            f"Unique constraint violated in update_company_profile: {constraint}",
        )

    except DBAPIError as e:
        await session.rollback()
        # These are lower-level errors, can include connection errors, syntax errors, etc.
        return None, f"Database API error in update_company_profile: {e}"

    except Exception as e:
        await session.rollback()
        return None, f"Unexpected error in update_company_profile: {e}"


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
) -> Tuple[Optional[StudentAccount], str]:
    """
    __
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

        return (
            None,
            f"Unique constraint violated in update_student_profile: {constraint}",
        )

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
) -> Tuple[Optional[FacultyAccount], str]:
    """
    __
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

        return (
            None,
            f"Unique constraint violated in update_faculty_profile: {constraint}",
        )

    except DBAPIError as e:
        await session.rollback()
        # These are lower-level errors, can include connection errors, syntax errors, etc.
        return None, f"Database API error in update_faculty_profile: {e}"

    except Exception as e:
        await session.rollback()
        return None, f"Unexpected error in update_faculty_profile: {e}"
