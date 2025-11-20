from typing import List, Optional, Tuple
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.ext.asyncio.session import AsyncSession

from datetime import datetime

from src.database.manage import get_constraint_name_from_integrity_error
from src.database.record_get_or_create import get_or_create_major, get_or_create_skill
from src.database.record_insertion import (
    add_address,
    add_application,
    add_internship,
    add_internship_major,
    add_internship_preferred_skill,
    add_internship_required_skill,
    add_summary,
)
from src.database.record_retrieval import (
    get_address,
    get_application,
    get_application_from_internship,
    get_company,
    get_employer,
    get_internship,
    get_student,
)
from src.database.schema import (
    Internship,
    InternshipApplication,
    InternshipSummary,
)


async def create_internship(
    session: AsyncSession,
    account_id: int,
    title: str,
    description: str,
    location_type: str,
    address_id: Optional[int],
    duration_weeks: int,
    weekly_hours: int,
    salary_info: Optional[str],
    status: str = "Open",
    # Majors & Skills
    majors: Optional[List[str]] = None,
    required_skills: Optional[List[str]] = None,
    preferred_skills: Optional[List[str]] = None,
    # Address (for Other)
    address_line1: Optional[str] = None,
    address_line2: Optional[str] = None,
    city: Optional[str] = None,
    state_province: Optional[str] = None,
    zip_postal: Optional[str] = None,
    country: Optional[str] = None,
) -> Tuple[Optional[Internship], str]:
    """
    Atomically creates a new Internship for the employer associated with the provided account.

    Args:
        session (AsyncSession): Active SQLAlchemy async session.
        account_id (int): The EmployerAccount's account ID.
        title (str): Internship title.
        description (str): Internship description.
        location_type (str): 'Other', 'Company', or 'Remote'.
        address_id (Optional[int]): Address to use (if location_type != 'Remote' or directly supplied).
        duration_weeks (int): Number of weeks.
        weekly_hours (int): Hours/week.
        salary_info (Optional[str]): Salary/compensation details.
        status (str): One of: 'Open', 'Closed', 'PendingStart', 'InProgress', 'WaitingSummary', 'WaitingGrade', or 'Completed'
        majors (List[str], optional): List of major names related to this internship.
        required_skills (List[str], optional): List of required skill names.
        preferred_skills (List[str], optional): List of preferred skill names.
        address_line1~country: Address fields for 'Other' locations.

    Returns:
        Tuple[Optional[Internship], str]:
            (Internship, "Internship created successfully.") on success.
            (None, "Reason") with a descriptive message on failure.
    """
    try:
        # 1. Ensure EmployerAccount exists
        employer = await get_employer(session, account_id)
        if not employer:
            return None, "Account is not associated with an employer account."

        # 2. Get the Company object
        company = await get_company(session, employer.company_id)
        if not company:
            return None, "Employer's company not found."

        # 3. Determine address based on location_type
        address_id = None

        if location_type == "Other":
            address = None
            if address_id is not None:
                address = await get_address(session, id)
                if not address:
                    return None, f"Address of ID {address_id} not found."

            else:
                if not all([address_line1, city, state_province, zip_postal, country]):
                    return None, "Missing address fields for 'Other' location type."

                address = await add_address(
                    session,
                    address_line1,
                    address_line2,
                    city,
                    state_province,
                    zip_postal,
                    country,
                )
                if address is None:
                    return None, "Failed to create address for internship."

            address_id = address.id

        elif location_type == "Company":
            address_id = company.address_id

        elif location_type == "Remote":
            address_id = None

        else:
            return None, f"Unknown or unsupported location_type: {location_type}"

        # 4. Create the Internship
        internship = await add_internship(
            session,
            company.id,
            title,
            description,
            location_type,
            address_id,
            duration_weeks,
            weekly_hours,
            duration_weeks * weekly_hours,
            salary_info,
            status,
        )
        if internship is None:
            await session.rollback()
            return None, "Failed to create internship."

        # 5. Link majors
        if majors:
            for major_name in majors:
                major = await get_or_create_major(session, major_name)
                if not major:
                    await session.rollback()
                    return None, f"Failed to find or create major: {major_name}"
                await add_internship_major(session, internship.id, major.id)

        # 6. Link required skills
        if required_skills:
            for skill_name in required_skills:
                skill = await get_or_create_skill(session, skill_name)
                if not skill:
                    await session.rollback()
                    return None, f"Failed to find or create required skill: {skill_name}"
                await add_internship_required_skill(session, internship.id, skill.id)

        # 7. Link preferred skills
        if preferred_skills:
            for skill_name in preferred_skills:
                skill = await get_or_create_skill(session, skill_name)
                if not skill:
                    await session.rollback()
                    return None, f"Failed to find or create preferred skill: {skill_name}"
                await add_internship_preferred_skill(session, internship.id, skill.id)

        # 8. Commit
        await session.commit()
        return internship, "Internship created successfully."

    except IntegrityError as e:
        await session.rollback()
        return None, f"Unique constraint violated in create_internship: {e}"

    except DBAPIError as e:
        await session.rollback()
        return None, f"Database API error in create_internship: {e}"

    except Exception as e:
        await session.rollback()
        return None, f"Unexpected error in create_internship: {e}"


async def create_application(
    session: AsyncSession,
    student_id: int,
    internship_id: int,
    coop_credit_eligibility: bool,
    note: Optional[str] = None,
    resume_link: Optional[str] = None,
    cover_letter_link: Optional[str] = None,
) -> Tuple[Optional[InternshipApplication], str]:
    """
    Atomically creates an internship application for a student to a given internship.

    Validates student and internship existence and calculates co-op credit eligibility.
    Handles duplicate applications gracefully with a user-friendly message.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
        student_id (int): The ID of the student applying.
        internship_id (int): The ID of the internship.
        note (Optional[str], optional): Message from student to employer.
        resume_link (Optional[str], optional): Resume link.
        cover_letter_link (Optional[str], optional): Cover letter link.

    Returns:
        Tuple[Optional[InternshipApplication], str]:
            (InternshipApplication, "Success message") on success,
            (None, "Reason for failure") otherwise.
    """
    try:
        # 1. Check student existence
        student = await get_student(session, student_id)
        if not student:
            return None, "Student account not found."

        # 2. Check internship existence
        internship = await get_internship(session, internship_id)
        if not internship:
            return None, "Internship not found."

        # 3. Add the application
        application = await add_application(
            session,
            student_id,
            internship_id,
            coop_credit_eligibility,
            note=note,
            resume_link=resume_link,
            cover_letter_link=cover_letter_link,
            commit=True,
        )
        if not application:
            await session.rollback()
            return None, "Failed to create internship application."

        return application, "Internship application created successfully."

    except IntegrityError as e:
        await session.rollback()
        constraint = get_constraint_name_from_integrity_error(e)
        if "_internship_student_uc" in constraint:
            return None, "You have already applied to this internship."
        return None, f"A database integrity error occurred: {constraint}"

    except DBAPIError as e:
        await session.rollback()
        return None, f"Database API error in create_internship_application: {e}"

    except Exception as e:
        await session.rollback()
        return None, f"Unexpected error in create_internship_application: {e}"


# Run when a Internship.status is set to "PendingStart"
async def create_summary(
    session: AsyncSession,
    application_id: int,
    summary_text: str = "",
    file_link: Optional[str] = None,
    employer_approval: bool = False,
    letter_grade: Optional[str] = None,
) -> Tuple[Optional[InternshipSummary], str]:
    """
    Atomically creates an internship summary for a given internship application.

    Args:
        session (AsyncSession): The database session.
        application_id (int): The ID of the internship application.
        summary_text (str, optional): Summary text, defaults to empty string.
        file_link (Optional[str], optional): Link to supporting document(s).
        employer_approval (bool, optional): Employer approval, defaults to False.
        letter_grade (Optional[str], optional): Letter grade.

    Returns:
        Tuple[Optional[InternshipSummary], str]
            (InternshipSummary, "Internship summary created successfully.") on success.
            (None, "Reason") with a descriptive message on failure.
    """
    application = await get_application(session, application_id)
    if not application:
        return None, "Internship application not found for this internship/student."

    return await _create_summary(
        session, application.id, summary_text, file_link, employer_approval, letter_grade
    )


async def create_summary_from_internship(
    session: AsyncSession,
    internship_id: int,
    student_id: int,
    summary_text: str = "",
    file_link: Optional[str] = None,
    employer_approval: bool = False,
    letter_grade: Optional[str] = None,
) -> Tuple[Optional[InternshipSummary], str]:
    """
    Atomically creates an internship summary for a given internship application.

    Args:
        session (AsyncSession): The database session.
        student_id (int): The ID of the student.
        internship_id (int): The ID of the internship.
        summary_text (str, optional): Summary text, defaults to empty string.
        file_link (Optional[str], optional): Link to supporting document(s).
        employer_approval (bool, optional): Employer approval, defaults to False.
        letter_grade (Optional[str], optional): Letter grade.

    Returns:
        Tuple[Optional[InternshipSummary], str]
            (InternshipSummary, "Internship summary created successfully.") on success.
            (None, "Reason") with a descriptive message on failure.
    """
    application = await get_application_from_internship(session, internship_id, student_id)
    if not application:
        return None, "Internship application not found for this internship/student."

    return await _create_summary(
        session, application.id, summary_text, file_link, employer_approval, letter_grade
    )


async def _create_summary(
    session: AsyncSession,
    application_id: int,
    summary_text: str = "",
    file_link: Optional[str] = None,
    employer_approval: bool = False,
    letter_grade: Optional[str] = None,
) -> Tuple[Optional[InternshipSummary], str]:
    try:
        summary = await add_summary(
            session,
            application_id,
            summary_text,
            file_link,
            employer_approval,
            letter_grade,
            commit=True,
        )
        if not summary:
            await session.rollback()
            return None, "Failed to create internship summary."

        return summary, "Internship summary created successfully."

    except IntegrityError as e:
        await session.rollback()
        constraint = get_constraint_name_from_integrity_error(e)
        if (
            "internship_summaries_pkey" in constraint
            or "internship_summaries_pk" in constraint
            or "internship_summaries_id_key" in constraint
        ):
            return None, "A summary for this application already exists."
        return (
            None,
            f"Database integrity error in create_internship_summary: {constraint}",
        )

    except DBAPIError as e:
        await session.rollback()
        return None, f"Database API error in create_internship_summary: {e}"

    except Exception as e:
        await session.rollback()
        return None, f"Unexpected error in create_internship_summary: {e}"
