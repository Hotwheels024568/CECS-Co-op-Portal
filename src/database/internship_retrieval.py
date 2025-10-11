from typing import List, Optional
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.schema import Internship


# Paginate
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
) -> Optional[Internship]:
    pass
