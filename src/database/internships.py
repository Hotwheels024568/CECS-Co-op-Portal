# from typing import Any, Dict, List, Optional, Tuple
# from sqlalchemy import insert, select, update
# from sqlalchemy.exc import IntegrityError
# from sqlalchemy.ext.asyncio.session import AsyncSession

# from src.database.functions import get_first_element
# from src.database.instance_retrieval import (
#     get_internship_by_id,
#     get_student_profile_by_id,
# )
# from src.database.schema import (
#     Accounts,
#     Addresses,
#     Companies,
#     Employers,
#     InternshipLocations,
#     InternshipOpportunities,
#     InternshipApplications,
#     InternshipSummaries,
# )


# async def create_internship_from_account(
#     session: AsyncSession,
#     account_id: int,
#     title: str,
#     description: str,
#     location_type: str,
#     duration_weeks: int,
#     weekly_hours: int,
#     majors_of_interest: str,
#     required_skills: str,
#     preferred_skills: str,
#     salary_info: str,
#     # Address
#     address_line1: Optional[str] = None,
#     address_line2: Optional[str] = None,
#     city: Optional[str] = None,
#     state_province: Optional[str] = None,
#     zip_postal: Optional[str] = None,
#     country: Optional[str] = None,
# ) -> Tuple[bool, str]:
#     """
#     Atomically creates an internship opportunity and its location from an account_id.

#     Args:
#         session (AsyncSession): Async DB session.
#         account_id (int): The account ID (must be an Employer).
#         title (str): Title of the internship.
#         description (str): Description of the internship.
#         location_type (str): One of "Company", "Remote", "Other".
#         duration_weeks (int): Duration in weeks.
#         weekly_hours (int): Expected hours per week.
#         majors_of_interest (str): Majors of interest.
#         required_skills (str): Required skills.
#         preferred_skills (str): Preferred skills.
#         salary_info (str): Salary or stipend information.

#     Returns:
#         (Tuple[bool, str]): (True, "Internship opportunity created successfully")
#             or (False, "Error message")
#     """
#     statement = select(Accounts.profile_id).where(Accounts.id == account_id)
#     employer_id = await get_first_element(session, statement)
#     """
#     # Get account info, confirm it's an employer and has profile_id
#     statement = select(Account.user_type, Account.profile_id).where(Account.id == account_id)
#     result = await get_row(session, statement)
#     if result is None:
#         return False, "Account does not exist."

#     user_type, employer_id = result
#     if user_type != "Employer":
#         return False, "Account is not an employer."
#     if not employer_id:
#         return False, "Account does not have an employer profile."
#     """
#     return await create_internship(
#         session,
#         employer_id,
#         title,
#         description,
#         location_type,
#         duration_weeks,
#         weekly_hours,
#         majors_of_interest,
#         required_skills,
#         preferred_skills,
#         salary_info,
#         address_line1,
#         address_line2,
#         city,
#         state_province,
#         zip_postal,
#         country,
#     )


# async def create_internship(
#     session: AsyncSession,
#     employer_id: int,
#     title: str,
#     description: str,
#     location_type: str,
#     duration_weeks: int,
#     weekly_hours: int,
#     majors_of_interest: str,
#     required_skills: str,
#     preferred_skills: str,
#     salary_info: str,
#     # Address
#     address_line1: Optional[str] = None,
#     address_line2: Optional[str] = None,
#     city: Optional[str] = None,
#     state_province: Optional[str] = None,
#     zip_postal: Optional[str] = None,
#     country: Optional[str] = None,
# ) -> Tuple[bool, str]:
#     """
#     Atomically creates an internship opportunity and its location.

#     Args:
#         session (AsyncSession): Async DB session.
#         employer_id (int): The employer's ID.
#         title (str): Title of the internship.
#         description (str): Description of the internship.
#         location_type (str): One of "Company", "Remote", "Other".
#         duration_weeks (int): Duration in weeks.
#         weekly_hours (int): Expected hours per week.
#         majors_of_interest (str): Majors of interest.
#         required_skills (str): Required skills.
#         preferred_skills (str): Preferred skills.
#         salary_info (str): Salary or stipend information.

#     Returns:
#         (Tuple[bool, str]): (True, "Internship opportunity created successfully")
#             or (False, "Error message")
#     """
#     try:
#         address_id: Optional[int] = None
#         # 1. Create InternshipLocation
#         if location_type == "Other":
#             # Create Address
#             address = Addresses(
#                 address_line1=address_line1,
#                 address_line2=address_line2,
#                 city=city,
#                 state_province=state_province,
#                 zip_postal=zip_postal,
#                 country=country,
#             )
#             session.add(address)
#             await session.flush()  # Populates address.id
#             address_id = address.id

#         elif location_type == "Company":
#             # Find the Company address_id for this employer
#             statement = (
#                 select(Companies.address_id)
#                 .join(Employers, Employers.company_id == Companies.id)
#                 .where(Employers.id == employer_id)
#             )
#             address_id = await get_first_element(session, statement)

#         location = InternshipLocations(type=location_type, address_id=address_id)
#         session.add(location)
#         await session.flush()  # Populates location.id

#         # 2. Create InternshipOpportunity
#         opportunity = InternshipOpportunities(
#             employer_id=employer_id,
#             title=title,
#             description=description,
#             location_id=location.id,
#             duration_weeks=duration_weeks,
#             weekly_hours=weekly_hours,
#             total_work_hours=duration_weeks * weekly_hours,
#             majors_of_interest=majors_of_interest,
#             required_skills=required_skills,
#             preferred_skills=preferred_skills,
#             salary_info=salary_info,
#         )
#         session.add(opportunity)

#         # 3. Commit all changes
#         await session.commit()
#         return True, "Internship opportunity created successfully."

#     except Exception as e:
#         await session.rollback()
#         return False, f"Unexpected error in DB 'create_internship' function: {e}"


# async def create_internship_application_from_account(
#     session: AsyncSession,
#     account_id: int,
#     internship_id: int,
# ) -> Tuple[bool, str]:
#     """
#     Docs
#     """
#     statement = select(Accounts.profile_id).where(Accounts.id == account_id)
#     student_id = await get_first_element(session, statement)
#     """
#     # Get account info, confirm it's a student and has profile_id
#     statement = select(Account.user_type, Account.profile_id).where(Account.id == account_id)
#     result = await get_row(session, statement)
#     if result is None:
#         return False, "Account does not exist."

#     user_type, student_id = result
#     if user_type != "Student":
#         return False, "Account is not a student."
#     if not student_id:
#         return False, "Account does not have a student profile."
#     """
#     return await create_internship_application(session, student_id, internship_id)


# async def create_internship_application(
#     session: AsyncSession,
#     student_id: int,
#     internship_id: int,
# ) -> Tuple[bool, str]:
#     """
#     Creates an internship application for a student.

#     Args:
#         session (AsyncSession): Database session.
#         student_id (int): ID of the student profile applying.
#         internship_id (int): ID of the internship opportunity.

#     Returns:
#         Tuple[bool, str]: (True, success message) or (False, error message).
#     """
#     try:
#         student = await get_student_profile_by_id(session, student_id)
#         if not student:
#             return False, "Student profile not found."

#         internship = await get_internship_by_id(session, internship_id)
#         if not internship:
#             return False, "Internship opportunity not found."

#         coop_credit_eligibility = False
#         # TODO: When "semesters completed" is available, use that in eligibility logic.
#         coop_credit_eligibility = False
#         if (
#             student.gpa >= 2
#             and internship.duration_weeks >= 7
#             and internship.total_work_hours >= 140
#             # and Semesters Completed >= 1
#             # if student.transfer
#             # else Semesters Completed >= 2
#         ):
#             coop_credit_eligibility = True

#         application = InternshipApplications(
#             internship_id=internship_id,
#             student_id=student_id,
#             coop_credit_eligibility=coop_credit_eligibility,
#         )
#         session.add(application)
#         await session.commit()
#         return True, "Internship application created successfully."

#     except IntegrityError as e:
#         await session.rollback()
#         # Check if it's due to the unique constraint on (internship_id, student_id)
#         constraint = getattr(getattr(e.orig, "diag", None), "constraint_name", "") or str(
#             e
#         )
#         if "_internship_student_uc" in constraint:
#             return False, "You have already applied to this internship."
#         else:
#             return False, "A database integrity error occurred."

#     except Exception as e:
#         await session.rollback()
#         return (
#             False,
#             f"Unexpected error in DB 'create_internship_application' function: {e}",
#         )


# # Run when a InternshipOpportunity.status is set to "PendingStart"
# async def create_internship_summary(
#     session: AsyncSession,
#     application_id: int,
#     summary: str,
# ) -> Tuple[bool, str]:
#     """
#     Docs
#     """
#     summary = InternshipSummaries(application_id=application_id, summary="")
#     session.add(summary)
#     await session.commit()
#     return True, "Internship summary created successfully."
