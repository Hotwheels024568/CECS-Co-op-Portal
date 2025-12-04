from typing import Awaitable, Callable, Optional, Protocol, TypeVar
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.backend.routers.models import InternshipStatus
from src.database.internship_insertion import create_summary
from src.database.record_insertion import (
    add_address,
    add_internship_major,
    add_internship_preferred_skill,
    add_internship_required_skill,
)
from src.database.record_updating import (
    update_address,
    update_internship as update_internship_record,
)
from src.database.record_retrieval import (
    get_internship_by_id,
    get_internship_majors_by_id,
    get_internship_preferred_skills_by_id,
    get_internship_required_skills_by_id,
    get_selected_internship_applications,
)
from src.database.record_deletion import (
    delete_record,
    remove_internship_major,
    remove_internship_preferred_skill,
    remove_internship_required_skill,
)
from src.database.record_get_or_create import get_or_create_major, get_or_create_skill
from src.database.utils import get_constraint_name_from_integrity_error
from src.database.schema import Internship


async def update_internship(
    session: AsyncSession,
    internship_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    location_type: Optional[str] = None,
    address_id: Optional[int] = None,
    duration_weeks: Optional[int] = None,
    weekly_hours: Optional[int] = None,
    salary_info: Optional[str] = None,
    status: Optional[str] = None,
    majors: Optional[list[str]] = None,
    required_skills: Optional[list[str]] = None,
    preferred_skills: Optional[list[str]] = None,
    address_line1: Optional[str] = None,
    address_line2: Optional[str] = None,
    city: Optional[str] = None,
    state_province: Optional[str] = None,
    zip_postal: Optional[str] = None,
    country: Optional[str] = None,
) -> tuple[Optional[Internship], str]:
    """
    Updates an Internship record and related address, majors, required & preferred skills.

    Args:
        session (AsyncSession): Active SQLAlchemy async session for database access.
        internship_id (int): The ID Internship to update.
        title (Optional[str], optional): Updated internship title.
        description (Optional[str], optional): Updated internship description.
        location_type (Optional[str], optional): Updated location type ('Remote', 'Company', 'Other').
        address_id (Optional[int], optional): ID for a new address to associate with the internship (used if location_type is 'Other').
        duration_weeks (Optional[int], optional): Updated duration, in weeks.
        weekly_hours (Optional[int], optional): Updated number of weekly work hours.
        salary_info (Optional[str], optional): Updated salary information.
        status (Optional[str], optional): Updated internship status.
        majors (Optional[list[str]], optional): List of updated major fields associated with the internship.
        required_skills (Optional[list[str]], optional): List of updated required skills.
        preferred_skills (Optional[list[str]], optional): List of updated preferred skills.
        address_line1 (Optional[str], optional): Updated company address's address_line1.
        address_line2 (Optional[str], optional): Updated company address's address_line2.
        city (Optional[str], optional): Updated company address's city.
        state_province (Optional[str], optional): Updated company address's state_province.
        zip_postal (Optional[str], optional): Updated company address's zip_postal.
        country (Optional[str], optional): Updated company address's country.

    Returns:
        tuple[Optional[Company], str]:
            - (Internship, "Internship updated.") on success.
            - (None, "Internship not found.") if a company with the provided id does not exist.
            - (None, "Unique constraint violated: [constraint_name]") for other unique violations.
            - (None, "Database API error: [message]") for database-layer errors.
            - (None, "Unexpected error: [message]") for all other failures.
    """
    try:
        # 1. Ensure Internship exists
        internship = await get_internship_by_id(session, internship_id)
        if not internship:
            return None, "Internship not found."

        # 2. Address handling
        current_location_type = internship.location_type
        new_address_id: Optional[int] = None
        update_address_id: bool = False
        if location_type is None and address_id is not None:
            return None, "An updated location_type needs to be provided with an address_id."

        elif location_type not in [status.value for status in InternshipStatus]:
            return None, f"Unknown or unsupported location_type: {location_type}"

        elif location_type == "Other":
            new_address_id = address_id
            update_address_id = True
            if new_address_id is None:
                if not all([address_line1, city, state_province, zip_postal, country]):
                    return None, "Missing address fields for 'Other' location type."

                if current_location_type == "Other":
                    address = await update_address(
                        session,
                        internship.address_id,
                        address_line1,
                        address_line2,
                        city,
                        state_province,
                        zip_postal,
                        country,
                    )
                    new_address_id = address.id
                else:  # current_location_type != "Other"
                    address = await add_address(
                        session,
                        address_line1,
                        address_line2,
                        city,
                        state_province,
                        zip_postal,
                        country,
                    )
                    new_address_id = address.id
            else:  # A new address_id is directly supplied, so delete the old one
                result = await delete_record(session, internship.address)
                if not result:
                    await session.rollback()
                    return (
                        None,
                        "Failed to delete address when a new address_id is directly supplied (Check log)",
                    )

        elif current_location_type != location_type:
            update_address_id = True
            if current_location_type == "Other":
                address = internship.address
                result = await delete_record(session, address)
                if not result:
                    await session.rollback()
                    return (
                        None,
                        "Failed to delete address when changing the location type (Check log)",
                    )

            if location_type == "Company":  # Other or Remote -> Company
                new_address_id = internship.company.address_id
            else:  # location_type == "Remote" # Other or Company -> Remote
                new_address_id = None

        else:  # current_location_type and location_type == Company or Remote: Do nothing
            pass

        # 3. Update Internship record
        internship = await update_internship_record(
            session,
            internship_id,
            None,
            title,
            description,
            location_type,
            new_address_id,
            update_address_id,
            duration_weeks,
            weekly_hours,
            duration_weeks * weekly_hours,
            salary_info,
            status,
        )
        if not internship:
            await session.rollback()
            return None, "Failed to update internship record."

        # 4. Update Majors
        if majors:
            await sync_relationships(
                session,
                internship_id,
                majors,
                get_internship_majors_by_id,
                get_or_create_major,
                add_internship_major,
                remove_internship_major,
            )

        # 5. Update Required Skills
        if required_skills:
            await sync_relationships(
                session,
                internship_id,
                required_skills,
                get_internship_required_skills_by_id,
                get_or_create_skill,
                add_internship_required_skill,
                remove_internship_required_skill,
            )

        # 6. Update Preferred Skills
        if preferred_skills:
            await sync_relationships(
                session,
                internship_id,
                preferred_skills,
                get_internship_preferred_skills_by_id,
                get_or_create_skill,
                add_internship_preferred_skill,
                remove_internship_preferred_skill,
            )

        # 7. Create internship summary records
        if status == InternshipStatus.PENDING_START.value:
            selected_applications = await get_selected_internship_applications(
                session, internship_id
            )
            for application in selected_applications:
                await create_summary(session, application.id)

        # 8. Commit
        await session.commit()
        return internship, "Internship updated."

    except IntegrityError as e:
        await session.rollback()
        constraint = get_constraint_name_from_integrity_error(e)
        return (None, f"Unique constraint violated in update_internship: {constraint}")

    except DBAPIError as e:
        await session.rollback()
        return None, f"Database API error in update_internship: {e}"

    except Exception as e:
        await session.rollback()
        return None, f"Unexpected error in update_internship: {e}"


class IdentifiableNamed(Protocol):
    id: int
    name: str


T_IdentifiableNamed = TypeVar("T_IdentifiableNamed", bound=IdentifiableNamed)


async def sync_relationships(
    session: AsyncSession,
    internship_id: int,
    new_item_names: list[str],
    get_current_items: Callable[[AsyncSession, int], Awaitable[list[T_IdentifiableNamed]]],
    get_or_create_item: Callable[[AsyncSession, str], Awaitable[T_IdentifiableNamed]],
    # (session, internship_id, item_id)
    add_func: Callable[[AsyncSession, int, int], Awaitable[None]],
    # (session, internship_id, item_id)
    remove_func: Callable[[AsyncSession, int, int], Awaitable[None]],
) -> None:
    """
    Generic function to sync relationship tables (majors, required skills, preferred skills).

    Args:
        session: AsyncSession
        internship_id: The internship to update
        new_names: List of names to sync to
        get_current_items: async function(session, internship_id) -> List of objects with .name and .id
        get_or_create_item: async function(session, name) -> object with .id
        add_func: async function(session, internship_id, item_id) -> None
        remove_func: async function(session, internship_id, item_id) -> None
    """
    current_items = await get_current_items(session, internship_id)
    current_name_to_id = {item.name: item.id for item in current_items}
    current_names = set(current_name_to_id.keys())
    new_names_set = set(new_item_names)

    # Determine differences
    to_add = new_names_set - current_names
    to_remove = current_names - new_names_set

    # Add new items
    for name in to_add:
        item = await get_or_create_item(session, name)
        await add_func(session, internship_id, item.id)

    # Remove those not in new list
    for name in to_remove:
        item_id = current_name_to_id[name]
        await remove_func(session, internship_id, item_id)
