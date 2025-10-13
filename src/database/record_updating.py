from typing import Optional
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.record_retrieval import (
    get_account,
    get_address,
    get_company,
    get_contact,
    get_employer,
    get_student,
    get_faculty,
    get_internship,
    get_application,
    get_summary,
)

from src.database.schema import (
    Account,
    Address,
    Company,
    ContactInfo,
    EmployerAccount,
    StudentAccount,
    FacultyAccount,
    Internship,
    InternshipApplication,
    InternshipSummary,
)


async def update_account(
    session: AsyncSession,
    id: int,
    username: Optional[str] = None,
    password: Optional[str] = None,
    user_type: Optional[str] = None,
    commit: bool = False,
) -> Optional[Account]:
    """
    Updates the fields of an Account record in the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        id (int): The ID of the Account to update.
        username (Optional[str], optional): Updated username (must be unique), if any.
        password (Optional[str], optional): Updated pre-hashed password, if any.
        user_type (Optional[str], optional): Updated user type ('Employer', 'Student', 'Faculty'), if any.
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[Account]: The updated Account object if successful, or None if the account does not exist or if an error occurs.
    """
    try:
        account = await get_account(session, id)
        if not account:
            return None

        updated = False
        if username is not None and account.username != username:
            account.username = username
            updated = True
        if password is not None and account.password != password:
            account.password = password
            updated = True
        if user_type is not None and account.user_type != user_type:
            account.user_type = user_type
            updated = True

        if not updated:
            return account  # Return the (unchanged) instance for transparency

        if commit:
            await session.commit()
        else:
            await session.flush()
        return account

    except IntegrityError as e:
        await session.rollback()
        # Likely a username unique constraint violation
        return None

    except Exception as e:
        await session.rollback()
        print(f"Unexpected error in update_account: {e}")
        return None


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
        address_line1 (Optional[str], optional): Updated first line, if any.
        address_line2 (Optional[str], optional): Updated second line, if any.
        city (Optional[str], optional): Updated city, if any.
        state_province (Optional[str], optional): Updated state or province, if any.
        zip_postal (Optional[str], optional): Updated ZIP or postal code, if any.
        country (Optional[str], optional): Updated country, if any.
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[Address]: The updated Address object if successful, or None if the address does not exist or if an error occurs.
    """
    try:
        address = await get_address(session, id)
        if not address:
            return None

        updated = False
        if address_line1 is not None and address.address_line1 != address_line1:
            address.address_line1 = address_line1
            updated = True
        if address_line2 is not None and address.address_line2 != address_line2:
            address.address_line2 = address_line2
            updated = True
        if city is not None and address.city != city:
            address.city = city
            updated = True
        if state_province is not None and address.state_province != state_province:
            address.state_province = state_province
            updated = True
        if zip_postal is not None and address.zip_postal != zip_postal:
            address.zip_postal = zip_postal
            updated = True
        if country is not None and address.country != country:
            address.country = country
            updated = True

        if not updated:
            return address

        if commit:
            await session.commit()
        else:
            await session.flush()
        return address

    except Exception as e:
        await session.rollback()
        print(f"Unexpected error in update_address: {e}")
        return None


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
        name (Optional[str], optional): Updated company name (must be unique), if any.
        address_id (Optional[int], optional): Updated address ID, if any.
        website_link (Optional[str], optional): Updated website link, if any.
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[Company]: The updated Company object if successful, or None if the company does not exist or if an error occurs.
    """
    try:
        company = await get_company(session, id)
        if not company:
            return None

        updated = False
        if name is not None and company.name != name:
            company.name = name
            updated = True
        if address_id is not None and company.address_id != address_id:
            company.address_id = address_id
            updated = True
        if website_link is not None and company.website_link != website_link:
            company.website_link = website_link
            updated = True

        if not updated:
            return company

        if commit:
            await session.commit()
        else:
            await session.flush()
        return company

    except IntegrityError as e:
        await session.rollback()
        # Likely a name or address_id unique constraint violation
        return None

    except Exception as e:
        await session.rollback()
        print(f"Unexpected error in update_company: {e}")
        return None


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
        first (Optional[str], optional): Updated first name, if any.
        middle (Optional[str], optional): Updated middle name, if any.
        last (Optional[str], optional): Updated last name, if any.
        email (Optional[str], optional): Updated email address (must be unique), if any.
        phone (Optional[str], optional): Updated phone number, if any.
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[ContactInfo]: The updated ContactInfo object if successful, or None if the record does not exist or if an error occurs.
    """
    try:
        contact = await get_contact(session, id)
        if not contact:
            return None

        updated = False
        if first is not None and contact.first != first:
            contact.first = first
            updated = True
        if middle is not None and contact.middle != middle:
            contact.middle = middle
            updated = True
        if last is not None and contact.last != last:
            contact.last = last
            updated = True
        if email is not None and contact.email != email:
            contact.email = email
            updated = True
        if phone is not None and contact.phone != phone:
            contact.phone = phone
            updated = True

        if not updated:
            return contact

        if commit:
            await session.commit()
        else:
            await session.flush()
        return contact

    except IntegrityError as e:
        await session.rollback()
        # Likely an email unique constraint violation
        return None

    except Exception as e:
        await session.rollback()
        print(f"Unexpected error in update_contact: {e}")
        return None


async def update_employer(
    session: AsyncSession,
    id: int,
    company_id: Optional[int] = None,
    commit: bool = False,
) -> Optional[EmployerAccount]:
    """
    Updates the fields of an EmployerAccount record in the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        id (int): The ID of the EmployerAccount to update.
        company_id (Optional[int], optional): Updated company ID, if any.
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[EmployerAccount]: The updated EmployerAccount object if successful, or None if the record does not exist or if an error occurs.
    """
    try:
        employer = await get_employer(session, id)
        if not employer:
            return None

        updated = False
        if company_id is not None and employer.company_id != company_id:
            employer.company_id = company_id
            updated = True

        if not updated:
            return employer

        if commit:
            await session.commit()
        else:
            await session.flush()
        return employer

    except Exception as e:
        await session.rollback()
        print(f"Unexpected error in update_employer: {e}")
        return None


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
) -> Optional[StudentAccount]:
    """
    Updates the fields of a StudentAccount record in the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        id (int): The ID of the StudentAccount to update.
        department_id (Optional[int], optional): Updated department ID, if any.
        major_id (Optional[int], optional): Updated major ID, if any.
        credit_hours (Optional[int], optional): Updated number of credit hours, if any.
        gpa (Optional[float], optional): Updated GPA, if any.
        start_semester (Optional[str], optional): Updated start semester, if any.
        start_year (Optional[int], optional): Updated start year, if any.
        transfer (Optional[bool], optional): Updated transfer status, if any.
        resume_link (Optional[str], optional): Updated resume link, if any.
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[StudentAccount]: The updated StudentAccount object if successful, or None if the record does not exist or if an error occurs.
    """
    try:
        student = await get_student(session, id)
        if not student:
            return None

        updated = False
        if department_id is not None and student.department_id != department_id:
            student.department_id = department_id
            updated = True
        if major_id is not None and student.major_id != major_id:
            student.major_id = major_id
            updated = True
        if credit_hours is not None and student.credit_hours != credit_hours:
            student.credit_hours = credit_hours
            updated = True
        if gpa is not None and student.gpa != gpa:
            student.gpa = gpa
            updated = True
        if start_semester is not None and student.start_semester != start_semester:
            student.start_semester = start_semester
            updated = True
        if start_year is not None and student.start_year != start_year:
            student.start_year = start_year
            updated = True
        if transfer is not None and student.transfer != transfer:
            student.transfer = transfer
            updated = True
        if resume_link is not None and student.resume_link != resume_link:
            student.resume_link = resume_link
            updated = True

        if not updated:
            return student

        if commit:
            await session.commit()
        else:
            await session.flush()
        return student

    except IntegrityError as e:
        await session.rollback()
        # Likely a check constraint violation
        return None

    except Exception as e:
        await session.rollback()
        print(f"Unexpected error in update_student: {e}")
        return None


async def update_faculty(
    session: AsyncSession,
    id: int,
    department_id: Optional[int] = None,
    commit: bool = False,
) -> Optional[FacultyAccount]:
    """
    Updates the fields of a FacultyAccount record in the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        id (int): The ID of the FacultyAccount to update.
        department_id (Optional[int], optional): Updated department ID, if any.
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[FacultyAccount]: The updated FacultyAccount object if successful, or None if the record does not exist or if an error occurs.
    """
    try:
        faculty = await get_faculty(session, id)
        if not faculty:
            return None

        updated = False
        if department_id is not None and faculty.department_id != department_id:
            faculty.department_id = department_id
            updated = True

        if not updated:
            return faculty

        if commit:
            await session.commit()
        else:
            await session.flush()
        return faculty

    except Exception as e:
        await session.rollback()
        print(f"Unexpected error in update_faculty: {e}")
        return None


async def update_internship(
    session: AsyncSession,
    id: int,
    company_id: Optional[int] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    location_type: Optional[str] = None,
    address_id: Optional[int] = None,
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
        company_id (Optional[int], optional): Updated company ID, if any.
        title (Optional[str], optional): Updated title, if any.
        description (Optional[str], optional): Updated description, if any.
        location_type (Optional[str], optional): Updated location type ('Remote', 'Company', 'Other'), if any.
        address_id (Optional[int], optional): Updated address ID, if any.
        duration_weeks (Optional[int], optional): Updated duration in weeks, if any.
        weekly_hours (Optional[int], optional): Updated weekly hours, if any.
        total_work_hours (Optional[int], optional): Updated total work hours, if any.
        salary_info (Optional[str], optional): Updated salary information, if any.
        status (Optional[str], optional): Updated status ('Open', 'Closed', etc.), if any.
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[Internship]: The updated Internship object if successful, or None if the record does not exist or if an error occurs.
    """
    try:
        internship = await get_internship(session, id)
        if not internship:
            return None

        updated = False
        if company_id is not None and internship.company_id != company_id:
            internship.company_id = company_id
            updated = True
        if title is not None and internship.title != title:
            internship.title = title
            updated = True
        if description is not None and internship.description != description:
            internship.description = description
            updated = True
        if location_type is not None and internship.location_type != location_type:
            internship.location_type = location_type
            updated = True
        if address_id is not None and internship.address_id != address_id:
            internship.address_id = address_id
            updated = True
        if duration_weeks is not None and internship.duration_weeks != duration_weeks:
            internship.duration_weeks = duration_weeks
            updated = True
        if weekly_hours is not None and internship.weekly_hours != weekly_hours:
            internship.weekly_hours = weekly_hours
            updated = True
        if (
            total_work_hours is not None
            and internship.total_work_hours != total_work_hours
        ):
            internship.total_work_hours = total_work_hours
            updated = True
        if salary_info is not None and internship.salary_info != salary_info:
            internship.salary_info = salary_info
            updated = True
        if status is not None and internship.status != status:
            internship.status = status
            updated = True

        if not updated:
            return internship

        if commit:
            await session.commit()
        else:
            await session.flush()
        return internship

    except IntegrityError as e:
        await session.rollback()
        # Likely a check constraint violation
        return None

    except Exception as e:
        await session.rollback()
        print(f"Unexpected error in update_internship: {e}")
        return None


async def update_application(
    session: AsyncSession,
    id: int,
    coop_credit_eligibility: Optional[bool] = None,
    commit: bool = False,
) -> Optional[InternshipApplication]:
    """
    Updates the fields of an InternshipApplication record in the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        id (int): The ID of the InternshipApplication to update.
        student_id (int): The student ID part of the composite key.
        coop_credit_eligibility (Optional[bool], optional): Updated co-op credit eligibility, if any.
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[InternshipApplication]: The updated InternshipApplication object if successful,
            or None if the record does not exist or if an error occurs.
    """
    try:
        application = await get_application(session, id)
        if not application:
            return None

        updated = False
        if (
            coop_credit_eligibility is not None
            and application.coop_credit_eligibility != coop_credit_eligibility
        ):
            application.coop_credit_eligibility = coop_credit_eligibility
            updated = True

        if not updated:
            return application

        if commit:
            await session.commit()
        else:
            await session.flush()
        return application

    except Exception as e:
        await session.rollback()
        print(f"Unexpected error in update_application: {e}")
        return None


async def update_summary(
    session: AsyncSession,
    id: int,
    summary_text: Optional[str] = None,
    employer_approval: Optional[bool] = None,
    letter_grade: Optional[str] = None,
    commit: bool = False,
) -> Optional[InternshipSummary]:
    """
    Updates the fields of an InternshipSummary record in the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        id (int): The ID of the InternshipSummary to update.
        summary (Optional[str], optional): Updated summary text, if any.
        employer_approval (Optional[bool], optional): Updated employer approval status, if any.
        letter_grade (Optional[str], optional): Updated letter grade, if any.
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[InternshipSummary]: The updated InternshipSummary object if successful, or None if the record does not exist or if an error occurs.
    """
    try:
        summary = await get_summary(session, id)
        if not summary:
            return None

        updated = False
        if summary_text is not None and summary.summary != summary_text:
            summary.summary = summary_text
            updated = True
        if (
            employer_approval is not None
            and summary.employer_approval != employer_approval
        ):
            summary.employer_approval = employer_approval
            updated = True
        if letter_grade is not None and summary.letter_grade != letter_grade:
            summary.letter_grade = letter_grade
            updated = True

        if not updated:
            return summary

        if commit:
            await session.commit()
        else:
            await session.flush()
        return summary

    except Exception as e:
        await session.rollback()
        print(f"Unexpected error in update_summary: {e}")
        return None
