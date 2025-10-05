from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.get_instances import (
    get_account_by_id,
    get_address_by_id,
    get_company_by_id,
    get_contact_by_id,
    get_employer_profile_by_id,
    get_faculty_profile_by_id,
    get_student_profile_by_id,
)


async def update_employer_profile_from_account(
    session: AsyncSession,
    account_id: int,
    # Contact
    first_name: Optional[str] = None,
    middle_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    # Company
    company_name: Optional[str] = None,
    website_link: Optional[str] = None,
    # Address
    address_line1: Optional[str] = None,
    address_line2: Optional[str] = None,
    city: Optional[str] = None,
    state_province: Optional[str] = None,
    zip_postal: Optional[str] = None,
    country: Optional[str] = None,
) -> Tuple[bool, str]:
    try:
        account = await get_account_by_id(session, account_id)
        if not account or account.user_type != "Employer" or not account.profile_id:
            return False, "Account not linked to an employer profile."

    except Exception as e:
        await session.rollback()
        return (
            False,
            f"Unexpected error in DB 'update_employer_profile_from_account' function: {e}",
        )

    return await update_employer_profile(
        session,
        account.profile_id,
        first_name,
        middle_name,
        last_name,
        email,
        phone,
        company_name,
        website_link,
        address_line1,
        address_line2,
        city,
        state_province,
        zip_postal,
        country,
    )


async def update_employer_profile(
    session: AsyncSession,
    profile_id: int,
    # Contact
    first_name: Optional[str] = None,
    middle_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    # Company
    company_name: Optional[str] = None,
    website_link: Optional[str] = None,
    # Address
    address_line1: Optional[str] = None,
    address_line2: Optional[str] = None,
    city: Optional[str] = None,
    state_province: Optional[str] = None,
    zip_postal: Optional[str] = None,
    country: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Partially updates an employer profile. Only fields that are not None are updated.

    Returns:
        (True, "Profile updated successfully") on success;
        (False, reason) on failure.
    """
    try:
        employer = await get_employer_profile_by_id(session, profile_id)
        if not employer:
            return False, "Employer profile not found."

        contact = await get_contact_by_id(session, employer.contact_id)
        company = await get_company_by_id(session, employer.company_id)
        address = await get_address_by_id(session, company.address_id)
        if not contact or not company or not address:
            return False, "Profile is incomplete."

        # Update ContactInfo fields
        contact_changed = False
        if first_name is not None:
            contact.first = first_name
            contact_changed = True
        if middle_name is not None:
            contact.middle = middle_name
            contact_changed = True
        if last_name is not None:
            contact.last = last_name
            contact_changed = True
        if email is not None:
            contact.email = email
            contact_changed = True
        if phone is not None:
            contact.phone = phone
            contact_changed = True

        # Update Company fields
        company_changed = False
        if company_name is not None:
            company.name = company_name
            company_changed = True
        if website_link is not None:
            company.website_link = website_link
            company_changed = True

        # Update Address fields
        address_changed = False
        if address_line1 is not None:
            address.address_line1 = address_line1
            address_changed = True
        if address_line2 is not None:
            address.address_line2 = address_line2
            address_changed = True
        if city is not None:
            address.city = city
            address_changed = True
        if state_province is not None:
            address.state_province = state_province
            address_changed = True
        if zip_postal is not None:
            address.zip_postal = zip_postal
            address_changed = True
        if country is not None:
            address.country = country
            address_changed = True

        if not (contact_changed or company_changed or address_changed):
            return True, "No changes made to profile."

        # if contact_changed:
        #     session.add(contact)
        # if company_changed:
        #     session.add(company)
        # if address_changed:
        #     session.add(address)

        try:
            await session.flush()

        except IntegrityError as e:
            await session.rollback()
            constraint = getattr(
                getattr(e.orig, "diag", None), "constraint_name", ""
            ) or str(e)
            # TODO: Check violated constraint names for exact string key name
            if "contact_info_email_key" in constraint:
                return False, "Email already in use."
            # TODO: Check violated constraint names for exact string key name
            elif "companies_name_key" in constraint:
                return False, "Company name already exists."
            else:
                return False, "A unique constraint was violated."

        await session.commit()
        return True, "Profile updated successfully."

    except Exception as e:
        await session.rollback()
        return False, f"Unexpected error in DB 'update_employer_profile' function: {e}"


async def update_student_profile_from_account(
    session: AsyncSession,
    account_id: int,
    # Contact
    first_name: Optional[str] = None,
    middle_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    # Student
    department: Optional[str] = None,
    major: Optional[str] = None,
    credit_hours: Optional[int] = None,
    gpa: Optional[float] = None,
    start_semester_year: Optional[str] = None,
    transfer: Optional[bool] = None,
    resume_link: Optional[str] = None,
) -> Tuple[bool, str]:
    try:
        account = await get_account_by_id(session, account_id)
        if not account or account.user_type != "Student" or not account.profile_id:
            return False, "Account not linked to a student profile."

    except Exception as e:
        await session.rollback()
        return (
            False,
            f"Unexpected error in DB 'update_student_profile_from_account' function: {e}",
        )

    return await update_student_profile(
        session,
        account.profile_id,
        first_name,
        middle_name,
        last_name,
        email,
        phone,
        department,
        major,
        credit_hours,
        gpa,
        start_semester_year,
        transfer,
        resume_link,
    )


async def update_student_profile(
    session: AsyncSession,
    profile_id: int,
    # Contact
    first_name: Optional[str] = None,
    middle_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    # Student
    department: Optional[str] = None,
    major: Optional[str] = None,
    credit_hours: Optional[int] = None,
    gpa: Optional[float] = None,
    start_semester_year: Optional[str] = None,
    transfer: Optional[bool] = None,
    resume_link: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Partially updates an student profile. Only fields that are not None are updated.

    Returns:
        (True, "Profile updated successfully") on success;
        (False, reason) on failure.
    """
    try:
        student = await get_student_profile_by_id(session, profile_id)
        if not student:
            return False, "Student profile not found."

        contact = await get_contact_by_id(session, student.contact_id)
        if not contact:
            return False, "Profile is incomplete."

        # Update ContactInfo fields
        contact_changed = False
        if first_name is not None:
            contact.first = first_name
            contact_changed = True
        if middle_name is not None:
            contact.middle = middle_name
            contact_changed = True
        if last_name is not None:
            contact.last = last_name
            contact_changed = True
        if email is not None:
            contact.email = email
            contact_changed = True
        if phone is not None:
            contact.phone = phone
            contact_changed = True

        # Update Student fields
        student_changed = False
        if department is not None:
            student.department = department
            student_changed = True
        if major is not None:
            student.major = major
            student_changed = True
        if credit_hours is not None:
            student.credit_hours = credit_hours
            student_changed = True
        if gpa is not None:
            student.gpa = gpa
            student_changed = True
        if start_semester_year is not None:
            student.start_semester_year = start_semester_year
            student_changed = True
        if transfer is not None:
            student.transfer = transfer
            student_changed = True
        if resume_link is not None:
            student.resume_link = resume_link
            student_changed = True

        if not (contact_changed or student_changed):
            return True, "No changes made to profile."

        # if contact_changed:
        #    session.add(contact)
        # if student_changed:
        #    session.add(student)

        try:
            await session.flush()

        except IntegrityError as e:
            await session.rollback()
            constraint = getattr(
                getattr(e.orig, "diag", None), "constraint_name", ""
            ) or str(e)
            # TODO: Check violated constraint names for exact string key name
            if "contact_info_email_key" in constraint:
                return False, "Email already in use."
            else:
                return False, "A unique constraint was violated."

        await session.commit()
        return True, "Profile updated successfully."

    except Exception as e:
        await session.rollback()
        return False, f"Unexpected error in DB 'update_student_profile' function: {e}"


async def update_faculty_profile_from_account(
    session: AsyncSession,
    account_id: int,
    # Contact
    first_name: Optional[str] = None,
    middle_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    # Faculty
    department: Optional[str] = None,
) -> Tuple[bool, str]:
    try:
        account = await get_account_by_id(session, account_id)
        if not account or account.user_type != "Faculty" or not account.profile_id:
            return False, "Account not linked to a faculty profile."

    except Exception as e:
        await session.rollback()
        return (
            False,
            f"Unexpected error in DB 'update_faculty_profile_from_account' function: {e}",
        )

    return await update_faculty_profile(
        session,
        account.profile_id,
        first_name,
        middle_name,
        last_name,
        email,
        phone,
        department,
    )


async def update_faculty_profile(
    session: AsyncSession,
    profile_id: int,
    # Contact
    first_name: Optional[str] = None,
    middle_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    # Faculty
    department: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Partially updates an faculty profile. Only fields that are not None are updated.

    Returns:
        (True, "Profile updated successfully") on success;
        (False, reason) on failure.
    """
    try:
        faculty = await get_faculty_profile_by_id(session, profile_id)
        if not faculty:
            return False, "Faculty profile not found."

        contact = await get_contact_by_id(session, faculty.contact_id)
        if not contact:
            return False, "Profile is incomplete."

        # Update ContactInfo fields
        contact_changed = False
        if first_name is not None:
            contact.first = first_name
            contact_changed = True
        if middle_name is not None:
            contact.middle = middle_name
            contact_changed = True
        if last_name is not None:
            contact.last = last_name
            contact_changed = True
        if email is not None:
            contact.email = email
            contact_changed = True
        if phone is not None:
            contact.phone = phone
            contact_changed = True

        # Update Faculty fields
        faculty_changed = False
        if department is not None:
            faculty.department = department
            faculty_changed = True

        if not (contact_changed or faculty_changed):
            return True, "No changes made to profile."

        # if contact_changed:
        #    session.add(contact)
        # if faculty_changed:
        #    session.add(faculty)

        try:
            await session.flush()

        except IntegrityError as e:
            await session.rollback()
            constraint = getattr(
                getattr(e.orig, "diag", None), "constraint_name", ""
            ) or str(e)
            # TODO: Check violated constraint names for exact string key name
            if "contact_info_email_key" in constraint:
                return False, "Email already in use."
            # TODO: Check violated constraint names for exact string key name
            elif "faculty_department_key" in constraint:
                return False, "Department already exists."
            else:
                return False, "A unique constraint was violated."

        await session.commit()
        return True, "Profile updated successfully."

    except Exception as e:
        await session.rollback()
        return False, f"Unexpected error in DB 'update_faculty_profile' function: {e}"
