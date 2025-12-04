from typing import Optional
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.record_retrieval import (
    get_account_by_id,
    get_address_by_id,
    get_company_by_id,
    get_contact_by_id,
    get_employer_by_id,
    get_student_by_id,
    get_faculty_by_id,
    get_internship_by_id,
    get_application_by_id,
    get_summary_by_id,
)

from src.database.schema import (
    Account,
    Address,
    Company,
    ContactInfo,
    EmployerProfile,
    StudentProfile,
    FacultyProfile,
    Internship,
    InternshipApplication,
    InternshipSummary,
)


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
    try:
        account = await get_account_by_id(session, id)
        if not account:
            return None

        updated = False
        if username is not None and account.username != username:
            account.username = username
            updated = True
        if password is not None and account.password != password:
            account.password = password
            updated = True
        if salt is not None and account.salt != salt:
            account.salt = salt
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
    try:
        address = await get_address_by_id(session, id)
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
        name (Optional[str], optional): Updated company name (must be unique).
        address_id (Optional[int], optional): Updated address ID.
        website_link (Optional[str], optional): Updated website link.
        commit (bool, optional): If True, commits the transaction after updating.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[Company]: The updated object if successful, or None if it doesn't exist or an error occurs.
    """
    try:
        company = await get_company_by_id(session, id)
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
    try:
        contact = await get_contact_by_id(session, id)
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
    try:
        employer = await get_employer_by_id(session, id)
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
    try:
        student = await get_student_by_id(session, id)
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
    try:
        faculty = await get_faculty_by_id(session, id)
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
    try:
        internship = await get_internship_by_id(session, id)
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
        if update_address_id and internship.address_id != address_id:
            internship.address_id = address_id
            updated = True
        if duration_weeks is not None and internship.duration_weeks != duration_weeks:
            internship.duration_weeks = duration_weeks
            updated = True
        if weekly_hours is not None and internship.weekly_hours != weekly_hours:
            internship.weekly_hours = weekly_hours
            updated = True
        if total_work_hours is not None and internship.total_work_hours != total_work_hours:
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
    try:
        application = await get_application_by_id(session, id)
        if not application:
            return None

        updated = False
        if (
            coop_credit_eligibility is not None
            and application.coop_credit_eligibility != coop_credit_eligibility
        ):
            application.coop_credit_eligibility = coop_credit_eligibility
            updated = True
        if note is not None and application.note != note:
            application.note = note
            updated = True
        if resume_link is not None and application.resume_link != resume_link:
            application.resume_link = resume_link
            updated = True
        if cover_letter_link is not None and application.cover_letter_link != cover_letter_link:
            application.cover_letter_link = cover_letter_link
            updated = True
        if selected is not None and application.selected != selected:
            application.selected = selected
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
    try:
        summary = await get_summary_by_id(session, id)
        if not summary:
            return None

        updated = False
        if summary_text is not None and summary.summary != summary_text:
            summary.summary = summary_text
            updated = True
        if file_link is not None and summary.file_link != file_link:
            summary.file_link = file_link
            updated = True
        if employer_approval is not None and summary.employer_approval != employer_approval:
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
