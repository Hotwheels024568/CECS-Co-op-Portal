from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio.session import AsyncSession

from database.schema import (
    Account,
    Address,
    Company,
    ContactInfo,
    EmployerProfile,
    Department,
    FacultyProfile,
    Major,
    StudentProfile,
    Internship,
    InternshipMajor,
    Skill,
    InternshipReqSkill,
    InternshipPrefSkill,
    InternshipApplication,
    InternshipSummary,
)
from database.crud import add_row
from database.row_retrieval import get_application_by_id, get_application_from_ids


async def add_account(
    session: AsyncSession,
    username: str,
    password: bytes,
    salt: bytes,
    user_type: Optional[str] = None,
) -> Account:
    """
    Adds a new Account record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        username (str): Desired account username (must be unique).
        password (bytes): Pre-hashed password.
        salt (bytes): Password salt for hashing.
        user_type (Optional[str], optional): The type of account, one of: 'Employer', 'Student', or 'Faculty'. Defaults to None.

    Returns:
        Account: The newly created Account object.
    """
    return await add_row(
        session,
        Address,
        username=username,
        password=password,
        salt=salt,
        user_type=user_type,
    )


async def add_address(
    session: AsyncSession,
    address_line1: str,
    address_line2: Optional[str],
    city: str,
    state_province: str,
    zip_postal: str,
    country: str,
) -> Address:
    """
    Adds a new Address record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        address_line1 (str): First line of the address.
        address_line2 (Optional[str]): Second line of the address, if any.
        city (str): City for the address.
        state_province (str): State or province for the address.
        zip_postal (str): ZIP or postal code for the address.
        country (str): Country for the address.

    Returns:
        Address: The newly created Address object.
    """
    return await add_row(
        session,
        Address,
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        state_province=state_province,
        zip_postal=zip_postal,
        country=country,
    )


async def add_company(
    session: AsyncSession,
    name: str,
    address_id: int,
    website_link: Optional[str] = None,
) -> Company:
    """
    Adds a new Company record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        name (str): The name of the company (must be unique).
        address_id (int): The ID of an existing Address to associate with the company.
        website_link (Optional[str], optional): Link to the company's website. Defaults to None.

    Returns:
        Company: The newly created Company object.
    """
    return await add_row(
        session,
        Company,
        name=name,
        address_id=address_id,
        website_link=website_link,
    )


async def add_contact(
    session: AsyncSession,
    account_id: int,
    first_name: str,
    middle_name: Optional[str],
    last_name: str,
    email: str,
    phone: Optional[str] = None,
) -> ContactInfo:
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

    Returns:
        ContactInfo: The newly created ContactInfo.
    """
    return await add_row(
        session,
        ContactInfo,
        id=account_id,
        first=first_name,
        middle=middle_name,
        last=last_name,
        email=email,
        phone=phone,
    )


async def add_employer(
    session: AsyncSession,
    account_id: int,
    company_id: int,
) -> EmployerProfile:
    """
    Adds a new EmployerAccount record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        account_id (int): The ID of the associated Account.
        company_id (int): The ID of the associated Company.

    Returns:
        EmployerProfile: The newly created EmployerAccount object.
    """
    return await add_row(
        session,
        EmployerProfile,
        id=account_id,
        company_id=company_id,
    )


async def add_department(
    session: AsyncSession,
    name: str,
) -> Department:
    """
    Adds a new Department record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        name (str): The name of the department (must be unique).

    Returns:
        Department: The newly created Department object.
    """
    return await add_row(
        session,
        Department,
        name=name,
    )


async def add_major(
    session: AsyncSession,
    name: str,
) -> Major:
    """
    Adds a new Major record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        name (str): The name of the major (must be unique).

    Returns:
        Major: The newly created Major object.
    """
    return await add_row(
        session,
        Major,
        name=name,
    )


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
) -> StudentProfile:
    """
    Adds a new StudentProfile record to the database.

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
        resume_link (Optional[str], optional): Link to the student's resume. Defaults to None.

    Returns:
        StudentProfile: The newly created StudentProfile object
    """
    return await add_row(
        session,
        Account,
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


async def add_faculty(
    session: AsyncSession,
    account_id: int,
    department_id: int,
) -> FacultyProfile:
    """
    Adds a new FacultyProfile record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        account_id (int): The ID of the associated Account.
        department_id (int): The ID of the Department the faculty member belongs to.

    Returns:
        FacultyProfile: The newly created FacultyProfile object.
    """
    return await add_row(
        session,
        FacultyProfile,
        id=account_id,
        department_id=department_id,
    )


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
) -> Internship:
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

    Returns:
        Internship: The newly created Internship object.
    """
    return await add_row(
        session,
        Internship,
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


async def add_internship_major(
    session: AsyncSession,
    internship_id: int,
    major_id: int,
) -> InternshipMajor:
    """
    Adds a new InternshipMajor association record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        internship_id (int): The ID of the Internship to associate with a major.
        major_id (int): The ID of the Major to associate with the internship.

    Returns:
        InternshipMajor: The newly created InternshipMajor association object.
    """
    return await add_row(
        session,
        InternshipMajor,
        internship_id=internship_id,
        major_id=major_id,
    )


async def add_skill(
    session: AsyncSession,
    name: str,
) -> Skill:
    """
    Adds a new Skill record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        name (str): The name of the skill (must be unique).

    Returns:
        Skill: The newly created Skill object.
    """
    return await add_row(
        session,
        Skill,
        name=name,
    )


async def add_internship_required_skill(
    session: AsyncSession,
    internship_id: int,
    skill_id: int,
) -> InternshipReqSkill:
    """
    Adds a new InternshipReqSkill association record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        internship_id (int): The ID of the Internship requiring the skill.
        skill_id (int): The ID of the required Skill to associate with the internship.

    Returns:
        InternshipReqSkill: The newly created InternshipReqSkill association object.
    """
    return await add_row(
        session, InternshipReqSkill, internship_id=internship_id, skill_id=skill_id
    )


async def add_internship_preferred_skill(
    session: AsyncSession,
    internship_id: int,
    skill_id: int,
) -> InternshipPrefSkill:
    """
    Adds a new InternshipPrefSkill association record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        internship_id (int): The ID of the Internship for which the skill is preferred.
        skill_id (int): The ID of the preferred Skill to associate with the internship.

    Returns:
        InternshipPrefSkill: The newly created InternshipPrefSkill association object.
    """
    return await add_row(
        session,
        InternshipPrefSkill,
        internship_id=internship_id,
        skill_id=skill_id,
    )


async def add_application(
    session: AsyncSession,
    student_id: int,
    internship_id: int,
    coop_credit_eligibility: bool,
    note: Optional[str] = None,
    resume_link: Optional[str] = None,
    cover_letter_link: Optional[str] = None,
    selected: bool = False,
) -> InternshipApplication:
    """
    Adds a new InternshipApplication record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        student_id (int): The ID of the Student applying for the internship.
        internship_id (int): The ID of the Internship to which the student is applying.
        coop_credit_eligibility (bool): Indicates whether the application is eligible for co-op credit.
        note (str, optional): Application note or message from the student to the employer. Defaults to None.
        resume_link (str, optional): Application specific resume link. Defaults to None.
        cover_letter_link (str, optional): Application specific cover letter link. Defaults to None.
        selected (bool, optional): Indicates if this application was chosen by the employer for the internship. Defaults to False.

    Returns:
        InternshipApplication: The newly created InternshipApplication object.
    """
    return await add_row(
        session,
        InternshipApplication,
        student_id=student_id,
        internship_id=internship_id,
        application_date=datetime.now(timezone.utc),
        coop_credit_eligibility=coop_credit_eligibility,
        note=note,
        resume_link=resume_link,
        cover_letter_link=cover_letter_link,
        selected=selected,
    )


async def add_summary(
    session: AsyncSession,
    application_id: int,
    summary: str = "",
    file_link: Optional[str] = None,
    employer_approval: bool = False,
    letter_grade: Optional[str] = None,
) -> InternshipSummary:
    """
    Adds a new InternshipSummary record to the database.

    Args:
        session (AsyncSession): An open SQLAlchemy asynchronous session (must be managed externally).
        application_id (int): The ID of the InternshipApplication.
        summary (str, optional): The summary text describing the internship experience. Defaults to "".
        file_link (str, optional): Link to supporting document(s) or file(s). Defaults to None.
        employer_approval (bool, optional): Indicates whether the employer has approved the summary. Defaults to False.
        letter_grade (Optional[str], optional): The letter grade for the internship (e.g., 'A', 'B', 'C'), if assigned. Defaults to None.

    Returns:
        InternshipSummary: The newly created InternshipSummary object.
    """
    return await add_row(
        session,
        InternshipSummary,
        id=application_id,
        summary=summary,
        file_link=file_link,
        employer_approval=employer_approval,
        letter_grade=letter_grade,
    )
