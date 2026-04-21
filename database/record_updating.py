from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import Any, Optional

from database.schema import (
    Account,
    Address,
    Company,
    ContactInfo,
    EmployerProfile,
    FacultyProfile,
    StudentProfile,
    Internship,
    InternshipApplication,
    InternshipSummary,
)
from database.utils import TModel, get_constraint_name_from_integrity_error


async def update_row_by_id(
    session: AsyncSession,
    model: type[TModel],
    id: Any,
    *,
    commit: bool = False,
    skip_none: bool = True,
    **patch: Any,
) -> Optional[TModel]:
    """
    Patch-update a row by primary key.
    - If skip_none=True, fields with value None are ignored (so you can't set NULL via this helper).
    """
    try:
        obj = await session.get(model, id)
        if obj is None:
            return None

        updated = False
        for name, value in patch.items():
            if skip_none and value is None:
                continue
            if not hasattr(obj, name):
                raise AttributeError(f"{model.__name__} has no attribute '{name}'")

            current = getattr(obj, name)
            if current != value:
                setattr(obj, name, value)
                updated = True

        if not updated:
            return obj

        if commit:
            await session.commit()
        else:
            await session.flush()
        return obj

    except IntegrityError as e:
        await session.rollback()
        constraint = get_constraint_name_from_integrity_error(e)
        print(f"DB {constraint} integrity error updating {model.__name__}: {e}")
        return None

    except SQLAlchemyError as e:
        await session.rollback()
        print(f"DB error updating {model.__name__} id={id}: {e}")
        return None

    except Exception as e:
        await session.rollback()
        print(f"Unexpected error updating {model.__name__} id={id}: {e}")
        return None


async def update_account(
    session: AsyncSession,
    id: int,
    username: Optional[str] = None,
    password: Optional[bytes] = None,
    salt: Optional[bytes] = None,
    user_type: Optional[str] = None,
    commit: bool = False,
) -> Optional[Account]:
    """
    Updates the fields of an Account record in the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        id (int): The ID of the Account to update.
        username (Optional[str], optional): Updated username (must be unique).
        password (Optional[bytes], optional): Updated pre-hashed password.
        salt (Optional[bytes], optional): Updated password salt.
        user_type (Optional[str], optional): Updated user type ('Employer', 'Student', 'Faculty').
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[Account]: The updated object if successful, or None if it doesn't exist or an error occurs.
    """
    return await update_row_by_id(
        session,
        Account,
        id,
        username=username,
        password=password,
        salt=salt,
        user_type=user_type,
        commit=commit,
    )


async def update_address(
    session: AsyncSession,
    id: int,
    address_line1: Optional[str] = None,
    address_line2: Optional[str] = None,
    city: Optional[str] = None,
    state_province: Optional[str] = None,
    zip_postal: Optional[str] = None,
    country: Optional[str] = None,
    commit: bool = False,
) -> Optional[Address]:
    """
    Updates the fields of an Address record in the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        address_id (int): The ID of the Address to update.
        address_line1 (Optional[str], optional): Updated first line.
        address_line2 (Optional[str], optional): Updated second line.
        city (Optional[str], optional): Updated city.
        state_province (Optional[str], optional): Updated state or province.
        zip_postal (Optional[str], optional): Updated ZIP or postal code.
        country (Optional[str], optional): Updated country.
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[Address]: The updated object if successful, or None if it doesn't exist or an error occurs.
    """
    return await update_row_by_id(
        session,
        Address,
        id,
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        state_province=state_province,
        zip_postal=zip_postal,
        country=country,
        commit=commit,
    )


async def update_company(
    session: AsyncSession,
    id: int,
    name: Optional[str] = None,
    address_id: Optional[int] = None,
    website_link: Optional[str] = None,
    commit: bool = False,
) -> Optional[Company]:
    """
    Updates the fields of a Company record in the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        id (int): The ID of the Company to update.
        name (Optional[str], optional): Updated company name (must be unique).
        address_id (Optional[int], optional): Updated address ID.
        website_link (Optional[str], optional): Updated website link.
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[Company]: The updated object if successful, or None if it doesn't exist or an error occurs.
    """
    return await update_row_by_id(
        session,
        Address,
        id,
        name=name,
        address_id=address_id,
        website_link=website_link,
        commit=commit,
    )


async def update_contact(
    session: AsyncSession,
    id: int,
    first: Optional[str] = None,
    middle: Optional[str] = None,
    last: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    commit: bool = False,
) -> Optional[ContactInfo]:
    """
    Updates the fields of a ContactInfo record in the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        id (int): The ID of the ContactInfo record to update.
        first (Optional[str], optional): Updated first name.
        middle (Optional[str], optional): Updated middle name.
        last (Optional[str], optional): Updated last name.
        email (Optional[str], optional): Updated email address (must be unique).
        phone (Optional[str], optional): Updated phone number.
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[ContactInfo]: The updated object if successful, or None if it doesn't exist or an error occurs.
    """
    return await update_row_by_id(
        session,
        Address,
        id,
        first=first,
        middle=middle,
        last=last,
        email=email,
        phone=phone,
        commit=commit,
    )


async def update_employer(
    session: AsyncSession,
    id: int,
    company_id: Optional[int] = None,
    commit: bool = False,
) -> Optional[EmployerProfile]:
    """
    Updates the fields of an EmployerAccount record in the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        id (int): The ID of the EmployerAccount to update.
        company_id (Optional[int], optional): Updated company ID.
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[EmployerAccount]: The updated object if successful, or None if it doesn't exist or an error occurs.
    """
    return await update_row_by_id(
        session,
        Address,
        id,
        company_id=company_id,
        commit=commit,
    )


async def update_student(
    session: AsyncSession,
    id: int,
    department_id: Optional[int] = None,
    major_id: Optional[int] = None,
    credit_hours: Optional[int] = None,
    gpa: Optional[float] = None,
    start_semester: Optional[str] = None,
    start_year: Optional[int] = None,
    transfer: Optional[bool] = None,
    resume_link: Optional[str] = None,
    commit: bool = False,
) -> Optional[StudentProfile]:
    """
    Updates the fields of a StudentAccount record in the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        id (int): The ID of the StudentAccount to update.
        department_id (Optional[int], optional): Updated department ID.
        major_id (Optional[int], optional): Updated major ID.
        credit_hours (Optional[int], optional): Updated number of credit hours.
        gpa (Optional[float], optional): Updated GPA.
        start_semester (Optional[str], optional): Updated start semester.
        start_year (Optional[int], optional): Updated start year.
        transfer (Optional[bool], optional): Updated transfer status.
        resume_link (Optional[str], optional): Updated resume link.
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[StudentAccount]: The updated object if successful, or None if it doesn't exist or an error occurs.
    """
    return await update_row_by_id(
        session,
        Address,
        id,
        department_id=department_id,
        major_id=major_id,
        credit_hours=credit_hours,
        gpa=gpa,
        start_semester=start_semester,
        start_year=start_year,
        transfer=transfer,
        resume_link=resume_link,
        commit=commit,
    )


async def update_faculty(
    session: AsyncSession,
    id: int,
    department_id: Optional[int] = None,
    commit: bool = False,
) -> Optional[FacultyProfile]:
    """
    Updates the fields of a FacultyAccount record in the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        id (int): The ID of the FacultyAccount to update.
        department_id (Optional[int], optional): Updated department ID.
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[FacultyAccount]: The updated object if successful, or None if it doesn't exist or an error occurs.
    """
    return await update_row_by_id(
        session,
        Address,
        id,
        department_id=department_id,
        commit=commit,
    )


async def update_internship(
    session: AsyncSession,
    id: int,
    company_id: Optional[int] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    location_type: Optional[str] = None,
    address_id: Optional[int] = None,
    update_address_id: bool = False,
    duration_weeks: Optional[int] = None,
    weekly_hours: Optional[int] = None,
    total_work_hours: Optional[int] = None,
    salary_info: Optional[str] = None,
    status: Optional[str] = None,
    commit: bool = False,
) -> Optional[Internship]:
    """
    Updates the fields of an Internship record in the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        id (int): The ID of the Internship to update.
        company_id (Optional[int], optional): Updated company ID.
        title (Optional[str], optional): Updated title.
        description (Optional[str], optional): Updated description.
        location_type (Optional[str], optional): Updated location type ('Remote', 'Company', 'Other').
        address_id (Optional[int], optional): Updated address ID to set, or None to clear.
        update_address_id (bool): If True, address_id will be set/cleared. If False, address_id is unchanged.
        duration_weeks (Optional[int], optional): Updated duration in weeks.
        weekly_hours (Optional[int], optional): Updated weekly hours.
        total_work_hours (Optional[int], optional): Updated total work hours.
        salary_info (Optional[str], optional): Updated salary information.
        status (Optional[str], optional): Updated status ('Open', 'Closed', etc.).
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[Internship]: The updated object if successful, or None if it doesn't exist or an error occurs.
    """
    return await update_row_by_id(
        session,
        Address,
        id,
        company_id=company_id,
        title=title,
        description=description,
        location_type=location_type,
        address_id=address_id,
        update_address_id=update_address_id,
        duration_weeks=duration_weeks,
        weekly_hours=weekly_hours,
        total_work_hours=total_work_hours,
        salary_info=salary_info,
        status=status,
        commit=commit,
    )


async def update_application(
    session: AsyncSession,
    id: int,
    coop_credit_eligibility: Optional[bool] = None,
    note: Optional[str] = None,
    resume_link: Optional[str] = None,
    cover_letter_link: Optional[str] = None,
    selected: Optional[bool] = None,
    commit: bool = False,
) -> Optional[InternshipApplication]:
    """
    Updates the fields of an InternshipApplication record in the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        id (int): The ID of the InternshipApplication to update.
        coop_credit_eligibility (Optional[bool], optional): Updated co-op eligibility.
        note (Optional[str], optional): Updated note or message.
        resume_link (Optional[str], optional): Updated resume link.
        cover_letter_link (Optional[str], optional): Updated cover letter link.
        selected (Optional[bool], optional): Updated selection status.
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[InternshipApplication]: The updated object if successful, or None if it doesn't exist or an error occurs.
    """
    return await update_row_by_id(
        session,
        Address,
        id,
        coop_credit_eligibility=coop_credit_eligibility,
        note=note,
        resume_link=resume_link,
        cover_letter_link=cover_letter_link,
        selected=selected,
        commit=commit,
    )


async def update_summary(
    session: AsyncSession,
    id: int,
    summary_text: Optional[str] = None,
    file_link: Optional[str] = None,
    employer_approval: Optional[bool] = None,
    letter_grade: Optional[str] = None,
    commit: bool = False,
) -> Optional[InternshipSummary]:
    """
    Updates the fields of an InternshipSummary record in the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        id (int): The ID of the InternshipSummary to update.
        summary (Optional[str], optional): Updated summary text.
        file_link (Optional[str], optional): Updated file or document link.
        employer_approval (Optional[bool], optional): Updated employer approval status.
        letter_grade (Optional[str], optional): Updated letter grade.
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[InternshipSummary]: The updated object if successful, or None if it doesn't exist or an error occurs.
    """
    return await update_row_by_id(
        session,
        Address,
        id,
        summary_text=summary_text,
        file_link=file_link,
        employer_approval=employer_approval,
        letter_grade=letter_grade,
        commit=commit,
    )
