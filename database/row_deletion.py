from sqlalchemy.ext.asyncio.session import AsyncSession

from database.schema import InternshipMajor, InternshipReqSkill, InternshipPrefSkill
from database.crud import delete_row_by_pk


async def remove_internship_major(session: AsyncSession, internship_id: int, major_id: int) -> bool:
    return await delete_row_by_pk(
        session, InternshipMajor, {"internship_id": internship_id, "major_id": major_id}
    )


async def remove_internship_required_skill(
    session: AsyncSession, internship_id: int, skill_id: int
) -> bool:
    return await delete_row_by_pk(
        session, InternshipReqSkill, {"internship_id": internship_id, "skill_id": skill_id}
    )


async def remove_internship_preferred_skill(
    session: AsyncSession, internship_id: int, skill_id: int
) -> bool:
    return await delete_row_by_pk(
        session, InternshipPrefSkill, {"internship_id": internship_id, "skill_id": skill_id}
    )
