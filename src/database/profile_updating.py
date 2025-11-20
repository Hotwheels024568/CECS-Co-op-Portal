from typing import Optional, Tuple
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.schema import EmployerAccount, FacultyAccount, StudentAccount
from src.database.manage import get_constraint_name_from_integrity_error
from src.database.record_updating import (
    update_address,
    update_company,
    update_contact,
    update_employer,
    update_student,
    update_faculty,
)
from src.database.record_retrieval import get_company_by_name
from src.database.record_get_or_create import (
    get_or_create_department,
    get_or_create_major,
)


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
        # 1. Create ContactInfo (unique on email)
        contact = await update_contact(
            session, account_id, first_name, middle_name, last_name, email, phone
        )

        # 2. Get or Create Department
        department = await get_or_create_department(session, department_name)

        # 3. Create Faculty profile
        faculty = await update_faculty(
            session,
            account_id,
            department.id,
        )

        # 4. Commit all
        await session.commit()
        return faculty, "Profile updated successfully."

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
