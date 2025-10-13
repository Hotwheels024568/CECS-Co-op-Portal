from typing import List, Optional, Tuple
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.schema import (
    Internship,
    Company,
    InternshipMajor,
    Major,
    InternshipReqSkill,
    InternshipPrefSkill,
    Skill,
)


async def search_internships(
    session: AsyncSession,
    employer_id: Optional[int] = None,
    title: Optional[str] = None,
    location_type: Optional[str] = None,
    duration_weeks: Optional[int] = None,
    weekly_hours: Optional[int] = None,
    majors_of_interest: Optional[List[str]] = None,
    required_skills: Optional[List[str]] = None,
    preferred_skills: Optional[List[str]] = None,
    status: Optional[str] = None,
    page: int = 1,  # Starts at 1
    page_size: int = 20,
) -> Tuple[List[Internship], int]:
    """
    Search internships with filters and pagination, also returning total count.

    Args:
        session (AsyncSession): SQLAlchemy async session.
        employer_id (Optional[int]): Filter by employer (company) ID.
        title (Optional[str]): Title keyword (substring).
        location_type (Optional[str]): Location type.
        duration_weeks (Optional[int]): Minimum duration in weeks.
        weekly_hours (Optional[int]): Minimum weekly hours.
        majors_of_interest (Optional[List[str]]): Majors.
        required_skills (Optional[List[str]]): Required skills (must have all).
        preferred_skills (Optional[List[str]]): Preferred skills (must have all).
        status (Optional[str]): Status filter.
        page (int): 1-based page number (Starts at 1).
        page_size (int): Items per page.

    Returns:
        List[Internship]: List of matching objects for the requested page.
        int: Total number of results matching the search (ignoring pagination).
    """
    statement = select(Internship).distinct()
    filters = []

    if employer_id is not None:
        statement = statement.join(Company, Internship.company_id == Company.id)
        filters.append(Company.id == employer_id)

    if title:
        filters.append(Internship.title.ilike(f"%{title}%"))
    if location_type:
        filters.append(Internship.location_type == location_type)
    if duration_weeks is not None:
        filters.append(Internship.duration_weeks >= duration_weeks)
    if weekly_hours is not None:
        filters.append(Internship.weekly_hours >= weekly_hours)
    if status is not None:
        filters.append(Internship.status == status)

    if majors_of_interest:
        statement = statement.join(
            InternshipMajor, Internship.id == InternshipMajor.internship_id
        )
        statement = statement.join(Major, InternshipMajor.major_id == Major.id)
        filters.append(Major.name.in_(majors_of_interest))

    if required_skills:
        for skill in required_skills:
            skill_alias = Skill.__table__.alias()
            req_alias = InternshipReqSkill.__table__.alias()

            statement = statement.join(
                req_alias, Internship.id == req_alias.c.internship_id
            ).join(skill_alias, req_alias.c.skill_id == skill_alias.c.id)
            filters.append(skill_alias.c.name == skill)

    if preferred_skills:
        for skill in preferred_skills:
            skill_alias = Skill.__table__.alias()
            pref_alias = InternshipPrefSkill.__table__.alias()

            statement = statement.join(
                pref_alias, Internship.id == pref_alias.c.internship_id
            ).join(skill_alias, pref_alias.c.skill_id == skill_alias.c.id)
            filters.append(skill_alias.c.name == skill)

    if filters:
        statement = statement.where(and_(*filters))

    # ---- TOTAL COUNT ---
    # It's important to construct the COUNT query using the *same joins and filters* so that the count matches the filter
    count_stmt = statement.with_only_columns(
        func.count(Internship.id).distinct()
    ).order_by(None)
    count_result = await session.execute(count_stmt)
    total_count = count_result.scalar_one() or 0

    # ---- PAGINATION ---
    offset = max((page - 1), 0) * page_size
    paginated_stmt = statement.offset(offset).limit(page_size)
    result = await session.execute(paginated_stmt)
    internships = result.scalars().all()
    return internships, total_count
