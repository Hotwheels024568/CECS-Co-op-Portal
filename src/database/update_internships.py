from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.functions import get_first_element
from src.database.get_instances import get_internship_by_id
from src.database.schema import InternshipApplications


async def update_internship(
    session: AsyncSession,
    internship_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    location_type: Optional[str] = None,
    duration_weeks: Optional[int] = None,
    weekly_hours: Optional[int] = None,
    majors_of_interest: Optional[str] = None,
    required_skills: Optional[str] = None,
    preferred_skills: Optional[str] = None,
    salary_info: Optional[str] = None,
) -> Tuple[bool, str]:
    try:
        internship = await get_internship_by_id(session, internship_id)
        if not internship_id:
            return False, "Internship Opportunity not found."

        # Update InternshipOpportunity fields
        internship_changed = False
        if title is not None:
            internship.title = title
            internship_changed = True
        if description is not None:
            internship.description = description
            internship_changed = True
        if location_type is not None:
            internship.location_type = location_type
            internship_changed = True
        if duration_weeks is not None:
            internship.duration_weeks = duration_weeks
            internship_changed = True
        if weekly_hours is not None:
            internship.weekly_hours = weekly_hours
            internship_changed = True
        if majors_of_interest is not None:
            internship.majors_of_interest = majors_of_interest
            internship_changed = True
        if required_skills is not None:
            internship.required_skills = required_skills
            internship_changed = True
        if preferred_skills is not None:
            internship.preferred_skills = preferred_skills
            internship_changed = True
        if salary_info is not None:
            internship.salary_info = salary_info
            internship_changed = True

        if not internship_changed:
            return True, "No changes made to the internship."

        # if internship_changed
        #     session.add(internship)

        try:
            await session.flush()

        except IntegrityError as e:
            await session.rollback()
            # Check if it's due to the unique constraint on (internship_id, student_id)
            constraint = getattr(
                getattr(e.orig, "diag", None), "constraint_name", ""
            ) or str(e)
            if "_internship_student_uc" in constraint:
                return False, "You have already applied to this internship."
            else:
                return False, "A database integrity error occurred."

    except Exception as e:
        await session.rollback()
        return (
            False,
            f"Unexpected error in DB 'update_internship' function: {e}",
        )


async def delete_internship_application(
    session: AsyncSession,
    student_id: int,
    internship_id: int,
) -> Tuple[bool, str]:
    """
    Deletes a student's application to a specific internship.

    Args:
        session (AsyncSession): The async DB session.
        student_id (int): The student applying.
        internship_id (int): The internship being applied for.

    Returns:
        Tuple[bool, str]: (True, "Deleted successfully") on success, or
            (False, reason) on failure.
    """
    try:
        # Find the application
        statement = select(InternshipApplications).where(
            InternshipApplications.student_id == student_id,
            InternshipApplications.internship_id == internship_id,
        )
        application = await get_first_element(session, statement)

        if not application:
            return False, "Application does not exist."

        await session.delete(application)
        await session.commit()
        return True, "Application deleted successfully."

    except SQLAlchemyError as e:
        await session.rollback()
        return False, f"Database error: {e}"

    except Exception as e:
        await session.rollback()
        return False, f"Unexpected error: {e}"
