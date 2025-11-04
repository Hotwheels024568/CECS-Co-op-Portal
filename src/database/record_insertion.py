from typing import Optional
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.record_retrieval import get_application, get_application_from_internship
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


async def add_account(
    session: AsyncSession,
    username: str,
    password: str,
    user_type: str,
    commit: bool = False,
) -> Optional[Account]:
    """
    Adds a new Account record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        username (str): Desired account username (must be unique).
        password (str): Pre-hashed password (do not pass plaintext).
        user_type (str): The type of account, one of: 'Employer', 'Student', or 'Faculty'.
        commit (bool, optional): If True, commits the transaction after adding.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[Account]: The newly created Account object if successful, or None if insertion fails.
    """
    entry = Account(username=username, password=password, user_type=user_type)
    session.add(entry)
    try:
        await session.flush()  # Tries the insert
        if commit:
            await session.commit()
        return entry

    except IntegrityError as e:
        await session.rollback()
        # Likely a username unique constraint violation
        return None

    except Exception as e:
        await session.rollback()
        print(f"Error in add_account: {e}")
        return None


async def sign_up(
    session: AsyncSession,
    username: str,
    password: str,
    user_type: str,
    commit: bool = False,
) -> Optional[Account]:
    """
    Adds a new Account record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        username (str): Desired account username (must be unique).
        password (str): Pre-hashed password (do not pass plaintext).
        user_type (str): The type of account, one of: 'Employer', 'Student', or 'Faculty'.
        commit (bool, optional): If True, commits the transaction after adding.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[Account]: The newly created Account object if successful, or None if insertion fails.
    """
    return await add_account(session, username, password, user_type, commit)


async def add_address(
    session: AsyncSession,
    address_line1: str,
    address_line2: Optional[str],
    city: str,
    state_province: str,
    zip_postal: str,
    country: str,
    commit: bool = False,
) -> Optional[Address]:
    """
    Adds a new Address record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        address_line1 (str): First line of the address.
        address_line2 (str): Second line of the address, if any.
        city (str): City for the address.
        state_province (str): State or province for the address.
        zip_postal (str): ZIP or postal code for the address.
        country (str): Country for the address.
        commit (bool, optional): If True, commits the transaction after adding.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[Address]: The newly created Address object if successful, or None if insertion fails.
    """
    entry = Address(
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        state_province=state_province,
        zip_postal=zip_postal,
        country=country,
    )
    session.add(entry)
    try:
        await session.flush()
        if commit:
            await session.commit()
        return entry

    except Exception as e:
        await session.rollback()
        print(f"Error in add_address: {e}")
        return None


async def add_company(
    session: AsyncSession,
    name: str,
    address_id: int,
    website_link: Optional[str] = None,
    commit: bool = False,
) -> Optional[Company]:
    """
    Adds a new Company record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        name (str): The name of the company (must be unique).
        address_id (int): The ID of an existing Address to associate with the company.
        website_link (Optional[str], optional): The company's website URL. Defaults to None.
        commit (bool, optional): If True, commits the transaction after adding.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[Company]: The newly created Company object if successful, or None if insertion fails.
    """
    entry = Company(name=name, address_id=address_id, website_link=website_link)
    session.add(entry)
    try:
        await session.flush()
        if commit:
            await session.commit()
        return entry

    except IntegrityError as e:
        await session.rollback()
        # Likely a name or address_id unique constraint violation
        return None

    except Exception as e:
        await session.rollback()
        print(f"Error in add_company: {e}")
        return None


async def add_contact(
    session: AsyncSession,
    account_id: int,
    first_name: str,
    middle_name: Optional[str],
    last_name: str,
    email: str,
    phone: Optional[str] = None,
    commit: bool = False,
) -> Optional[ContactInfo]:
    """
    Adds a new ContactInfo record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        account_id (int): The ID of the associated Account.
        first_name (str): First name of the contact.
        middle_name (Optional[str]): Middle name of the contact, if any.
        last_name (str): Last name of the contact.
        email (str): Email address of the contact (must be unique).
        phone (Optional[str], optional): Phone number of the contact. Defaults to None.
        commit (bool, optional): If True, commits the transaction after adding.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[ContactInfo]: The newly created ContactInfo object if successful, or None if insertion fails.
    """
    entry = ContactInfo(
        id=account_id,
        first=first_name,
        middle=middle_name,
        last=last_name,
        email=email,
        phone=phone,
    )
    session.add(entry)
    try:
        await session.flush()
        if commit:
            await session.commit()
        return entry

    except IntegrityError as e:
        await session.rollback()
        # Likely an email unique constraint violation
        return None

    except Exception as e:
        await session.rollback()
        print(f"Error in add_contact: {e}")
        return None


async def add_employer(
    session: AsyncSession,
    account_id: int,
    company_id: int,
    commit: bool = False,
) -> Optional[EmployerAccount]:
    """
    Adds a new EmployerAccount record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        account_id (int): The ID of the associated Account.
        company_id (int): The ID of the associated Company.
        commit (bool, optional): If True, commits the transaction after adding.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[EmployerAccount]: The newly created EmployerAccount object if successful, or None if insertion fails.
    """
    entry = EmployerAccount(id=account_id, company_id=company_id)
    session.add(entry)
    try:
        await session.flush()
        if commit:
            await session.commit()
        return entry

    except Exception as e:
        await session.rollback()
        print(f"Error in add_employer: {e}")
        return None


async def add_department(
    session: AsyncSession,
    name: str,
    commit: bool = False,
) -> Optional[Department]:
    """
    Adds a new Department record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        name (str): The name of the department (must be unique).
        commit (bool, optional): If True, commits the transaction after adding.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[Department]: The newly created Department object if successful, or None if insertion fails.
    """
    entry = Department(name=name)
    session.add(entry)
    try:
        await session.flush()
        if commit:
            await session.commit()
        return entry

    except IntegrityError as e:
        await session.rollback()
        # Likely a name unique constraint violation
        return None

    except Exception as e:
        await session.rollback()
        print(f"Error in add_department: {e}")
        return None


async def add_major(
    session: AsyncSession,
    name: str,
    commit: bool = False,
) -> Optional[Major]:
    """
    Adds a new Major record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        name (str): The name of the major (must be unique).
        commit (bool, optional): If True, commits the transaction after adding.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[Major]: The newly created Major object if successful, or None if insertion fails.
    """
    entry = Major(name=name)
    session.add(entry)
    try:
        await session.flush()
        if commit:
            await session.commit()
        return entry

    except IntegrityError as e:
        await session.rollback()
        # Likely a name unique constraint violation
        return None

    except Exception as e:
        await session.rollback()
        print(f"Error in add_major: {e}")
        return None


async def add_student(
    session: AsyncSession,
    account_id: int,
    department_id: int,
    major_id: int,
    credit_hours: int,
    gpa: float,
    start_semester: str,
    start_year: int,
    transfer: bool,
    resume_link: Optional[str] = None,
    commit: bool = False,
) -> Optional[StudentAccount]:
    """
    Adds a new StudentAccount record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        account_id (int): The ID of the associated Account.
        department_id (int): The ID of the Department the student belongs to.
        major_id (int): The ID of the Major the student is pursuing.
        credit_hours (int): The number of credit hours completed by the student.
        gpa (float): The student's grade point average.
        start_semester (str): The semester the student started (e.g., 'Winter', 'Summer', or 'Fall').
        start_year (int): The year the student started.
        transfer (bool): Indicates whether the student is a transfer student.
        resume_link (Optional[str], optional): URL link to the student's resume. Defaults to None.
        commit (bool, optional): If True, commits the transaction after adding.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[StudentAccount]: The newly created StudentAccount object if successful, or None if insertion fails.
    """
    entry = StudentAccount(
        id=account_id,
        department_id=department_id,
        major_id=major_id,
        credit_hours=credit_hours,
        gpa=gpa,
        start_semester=start_semester,
        start_year=start_year,
        transfer=transfer,
        resume_link=resume_link,
    )
    session.add(entry)
    try:
        await session.flush()
        if commit:
            await session.commit()
        return entry

    except IntegrityError as e:
        await session.rollback()
        # Likely a check constraint violation
        return None

    except Exception as e:
        await session.rollback()
        print(f"Error in add_student: {e}")
        return None


async def add_faculty(
    session: AsyncSession,
    account_id: int,
    department_id: int,
    commit: bool = False,
) -> Optional[FacultyAccount]:
    """
    Adds a new FacultyAccount record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        account_id (int): The ID of the associated Account.
        department_id (int): The ID of the Department the faculty member belongs to.
        commit (bool, optional): If True, commits the transaction after adding.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[FacultyAccount]: The newly created FacultyAccount object if successful, or None if insertion fails.
    """
    entry = FacultyAccount(id=account_id, department_id=department_id)
    session.add(entry)
    try:
        await session.flush()
        if commit:
            await session.commit()
        return entry

    except Exception as e:
        await session.rollback()
        print(f"Error in add_faculty: {e}")
        return None


async def add_internship(
    session: AsyncSession,
    company_id: int,
    title: str,
    description: str,
    location_type: str,
    address_id: Optional[int],
    duration_weeks: int,
    weekly_hours: int,
    total_work_hours: int,
    salary_info: Optional[str],
    status: str = "Open",
    commit: bool = False,
) -> Optional[Internship]:
    """
    Adds a new Internship record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        company_id (int): The ID of the Company offering the internship.
        title (str): The title or position name for the internship.
        description (str): A detailed description of the internship role.
        location_type (str): The type of location ('Remote', 'Company', or 'Other').
        address_id (int): The ID of the Address associated with the internship location.
        duration_weeks (int): The duration of the internship in weeks.
        weekly_hours (int): The expected number of work hours per week.
        total_work_hours (int): The total number of work hours for the internship.
        salary_info (str): Information regarding internship compensation (may be empty).
        status (str, optional): The current status of the internship
            (e.g., 'Open', 'Closed', 'PendingStart', etc.). Defaults to 'Open'.
        commit (bool, optional): If True, commits the transaction after adding.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[Internship]: The newly created Internship object if successful, or None if insertion fails.
    """
    entry = Internship(
        company_id=company_id,
        title=title,
        description=description,
        location_type=location_type,
        address_id=address_id,
        duration_weeks=duration_weeks,
        weekly_hours=weekly_hours,
        total_work_hours=total_work_hours,
        salary_info=salary_info,
        status=status,
    )
    session.add(entry)
    try:
        await session.flush()
        if commit:
            await session.commit()
        return entry

    except IntegrityError as e:
        await session.rollback()
        # Likely a check constraint violation
        return None

    except Exception as e:
        await session.rollback()
        print(f"Error in add_internship: {e}")
        return None


async def add_internship_major(
    session: AsyncSession,
    internship_id: int,
    major_id: int,
    commit: bool = False,
) -> Optional[InternshipMajor]:
    """
    Adds a new InternshipMajor association record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        internship_id (int): The ID of the Internship to associate with a major.
        major_id (int): The ID of the Major to associate with the internship.
        commit (bool, optional): If True, commits the transaction after adding.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[InternshipMajor]: The newly created InternshipMajor association object if successful, or None if insertion fails.
    """
    entry = InternshipMajor(internship_id=internship_id, major_id=major_id)
    session.add(entry)
    try:
        await session.flush()
        if commit:
            await session.commit()
        return entry

    except Exception as e:
        await session.rollback()
        print(f"Error in add_internship_major: {e}")
        return None


async def add_skill(
    session: AsyncSession,
    name: str,
    commit: bool = False,
) -> Optional[Skill]:
    """
    Adds a new Skill record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        name (str): The name of the skill (must be unique).
        commit (bool, optional): If True, commits the transaction after adding.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[Skill]: The newly created Skill object if successful, or None if insertion fails.
    """
    entry = Skill(name=name)
    session.add(entry)
    try:
        await session.flush()
        if commit:
            await session.commit()
        return entry

    except IntegrityError as e:
        await session.rollback()
        # Likely a name unique constraint violation
        return None

    except Exception as e:
        await session.rollback()
        print(f"Error in add_skill: {e}")
        return None


async def add_internship_required_skill(
    session: AsyncSession,
    internship_id: int,
    skill_id: int,
    commit: bool = False,
) -> Optional[InternshipReqSkill]:
    """
    Adds a new InternshipReqSkill association record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        internship_id (int): The ID of the Internship requiring the skill.
        skill_id (int): The ID of the required Skill to associate with the internship.
        commit (bool, optional): If True, commits the transaction after adding.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[InternshipReqSkill]: The newly created InternshipReqSkill association object if successful, or None if insertion fails.
    """
    entry = InternshipReqSkill(internship_id=internship_id, skill_id=skill_id)
    session.add(entry)
    try:
        await session.flush()
        if commit:
            await session.commit()
        return entry

    except Exception as e:
        await session.rollback()
        print(f"Error in add_internship_required_skill: {e}")
        return None


async def add_internship_preferred_skill(
    session: AsyncSession,
    internship_id: int,
    skill_id: int,
    commit: bool = False,
) -> Optional[InternshipPrefSkill]:
    """
    Adds a new InternshipPrefSkill association record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        internship_id (int): The ID of the Internship for which the skill is preferred.
        skill_id (int): The ID of the preferred Skill to associate with the internship.
        commit (bool, optional): If True, commits the transaction after adding.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[InternshipPrefSkill]: The newly created InternshipPrefSkill association object if successful, or None if insertion fails.
    """
    entry = InternshipPrefSkill(internship_id=internship_id, skill_id=skill_id)
    session.add(entry)
    try:
        await session.flush()
        if commit:
            await session.commit()
        return entry

    except Exception as e:
        await session.rollback()
        print(f"Error in add_internship_preferred_skill: {e}")
        return None


# TODO Update to new schema
async def add_application(
    session: AsyncSession,
    internship_id: int,
    student_id: int,
    coop_credit_eligibility: bool,
    commit: bool = False,
) -> Optional[InternshipApplication]:
    """
    Adds a new InternshipApplication record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        internship_id (int): The ID of the Internship to which the student is applying.
        student_id (int): The ID of the Student applying for the internship.
        coop_credit_eligibility (bool): Indicates whether the application is eligible for co-op credit.
        commit (bool, optional): If True, commits the transaction after adding.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[InternshipApplication]: The newly created InternshipApplication object if successful, or None if insertion fails.
    """
    entry = InternshipApplication(
        internship_id=internship_id,
        student_id=student_id,
        coop_credit_eligibility=coop_credit_eligibility,
    )
    session.add(entry)
    try:
        await session.flush()
        if commit:
            await session.commit()
        return entry

    except Exception as e:
        await session.rollback()
        print(f"Error in add_application: {e}")
        return None


# TODO Update to new schema
async def add_summary(
    session: AsyncSession,
    application_id: int,
    summary: str = "",
    employer_approval: bool = False,
    letter_grade: Optional[str] = None,
    commit: bool = False,
) -> Optional[InternshipSummary]:
    """
    Adds a new InternshipSummary record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        application_id (int): The ID of the InternshipApplication.
        summary (str, optional): The summary text describing the internship experience. Defaults to "".
        employer_approval (bool, optional): Indicates whether the employer has approved the summary. Defaults to False.
        letter_grade (Optional[str], optional): The letter grade for the internship (e.g., 'A', 'B', 'C'), if assigned. Defaults to None.
        commit (bool, optional): If True, commits the transaction after adding.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[InternshipSummary]: The newly created InternshipSummary object if successful, or None if insertion fails.
    """

    application = await get_application(session, application_id)
    if application is None:
        print("No InternshipApplication found for provided application_id.")
        return None

    return await _add_summary(
        session, application.id, summary, employer_approval, letter_grade, commit
    )


# TODO Update to new schema
async def add_summary_from_internship(
    session: AsyncSession,
    internship_id: int,
    student_id: int,
    summary: str = "",
    employer_approval: bool = False,
    letter_grade: Optional[str] = None,
    commit: bool = False,
) -> Optional[InternshipSummary]:
    """
    Adds a new InternshipSummary record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        internship_id (int): The ID of the InternshipApplication's internship.
        student_id (int): The ID of the InternshipApplication's student.
        summary (str, optional): The summary text describing the internship experience. Defaults to "".
        employer_approval (bool, optional): Indicates whether the employer has approved the summary. Defaults to False.
        letter_grade (Optional[str], optional): The letter grade for the internship (e.g., 'A', 'B', 'C'), if assigned. Defaults to None.
        commit (bool, optional): If True, commits the transaction after adding.
            If False, commit must be handled externally. Defaults to False.

    Returns:
        Optional[InternshipSummary]: The newly created InternshipSummary object if successful, or None if insertion fails.
    """

    application = await get_application_from_internship(
        session, internship_id, student_id
    )
    if application is None:
        print("No InternshipApplication found for provided internship_id and student_id.")
        return None

    return await _add_summary(
        session, application.id, summary, employer_approval, letter_grade, commit
    )


# TODO Update to new schema
async def _add_summary(
    session: AsyncSession,
    application_id: int,
    summary: str = "",
    employer_approval: bool = False,
    letter_grade: Optional[str] = None,
    commit: bool = False,
) -> Optional[InternshipSummary]:
    entry = InternshipSummary(
        id=application_id,
        summary=summary,
        employer_approval=employer_approval,
        letter_grade=letter_grade,
    )
    session.add(entry)
    try:
        await session.flush()
        if commit:
            await session.commit()
        return entry

    except Exception as e:
        await session.rollback()
        print(f"Error in add_summary: {e}")
        return None
