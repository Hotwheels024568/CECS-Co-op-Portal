from typing import Union

# from sqlalchemy.ext.asyncio.session import AsyncSession
from src.database.schema import (
    Address,
    Company,
    ContactInfo,
    EmployerProfile,
    Department,
    FacultyProfile,
    Major,
    StudentProfile,
    Internship,
    Skill,
    InternshipApplication,
    InternshipSummary,
)

# All lazy relationship loads occur in sync context here


# address = await db_session.run_sync(get_company_address, company)
def get_company_address(_, company: Company) -> Address:
    return company.address


# company = await db_session.run_sync(get_employer_company, profile)
def get_employer_company(_, profile: EmployerProfile) -> Company:
    return profile.company


# internships = await db_session.run_sync(get_employer_company_internships, profile)
def get_employer_company_internships(_, profile: EmployerProfile) -> list[Internship]:
    return profile.company.internships


# students = await db_session.run_sync(get_faculty_students, profile)
def get_faculty_students(_, profile: FacultyProfile) -> list[StudentProfile]:
    return profile.department.students


# faculty = await db_session.run_sync(get_student_faculty, profile)
def get_student_faculty(_, profile: StudentProfile) -> list[FacultyProfile]:
    return profile.department.faculty


# applications = await db_session.run_sync(get_student_applications, profile)
def get_student_applications(_, profile: StudentProfile) -> list[InternshipApplication]:
    return profile.applications


# summaries = await db_session.run_sync(get_student_summaries, profile)
def get_student_summaries(_, profile: StudentProfile) -> list[InternshipSummary]:
    return profile.summaries


# major = await db_session.run_sync(get_major, profile)
def get_major(_, profile: StudentProfile) -> Major:
    return profile.major


# department = await db_session.run_sync(get_department, profile)
def get_department(_, profile: Union[FacultyProfile, StudentProfile]) -> Department:
    return profile.department


# contact = await db_session.run_sync(get_contact, profile)
def get_contact(_, profile: Union[EmployerProfile, FacultyProfile, StudentProfile]) -> ContactInfo:
    return profile.contact


# company = await db_session.run_sync(get_internship_company, internship)
def get_internship_company(_, internship: Internship) -> Company:
    return internship.company


# majors = await db_session.run_sync(get_internship_majors, internship)
def get_internship_majors(_, internship: Internship) -> list[Major]:
    return [major.major for major in internship.majors]


# required_skills = await db_session.run_sync(get_internship_required_skills, internship)
def get_internship_required_skills(_, internship: Internship) -> list[Skill]:
    return [required_skill.skill for required_skill in internship.required_skills]


# preferred_skills = await db_session.run_sync(get_internship_preferred_skills, internship)
def get_internship_preferred_skills(_, internship: Internship) -> list[Skill]:
    return [preferred_skill.skill for preferred_skill in internship.preferred_skills]


# applications = await db_session.run_sync(get_internship_applications, internship)
def get_internship_applications(_, internship: Internship) -> list[InternshipApplication]:
    return internship.applications


# summaries = await db_session.run_sync(get_internship_summaries, internship)
def get_internship_summaries(_, internship: Internship) -> list[InternshipSummary]:
    return internship.summaries


# internship = await db_session.run_sync(get_application_internship, application)
def get_application_internship(_, application: InternshipApplication) -> Internship:
    return application.internship


# student = await db_session.run_sync(get_application_student, application)
def get_application_student(_, application: InternshipApplication) -> StudentProfile:
    return application.student


# student = await db_session.run_sync(get_summary_student, summary)
def get_summary_student(_, summary: InternshipSummary) -> StudentProfile:
    return summary.student


# internship = await db_session.run_sync(get_summary_internship, summary)
def get_summary_internship(_, summary: InternshipSummary) -> Internship:
    return summary.internship


# company = await db_session.run_sync(get_summary_company, summary)
def get_summary_company(_, summary: InternshipSummary) -> Company:
    return summary.application.company


# application = await db_session.run_sync(get_summary_application, summary)
def get_summary_application(_, summary: InternshipSummary) -> InternshipApplication:
    return summary.application
