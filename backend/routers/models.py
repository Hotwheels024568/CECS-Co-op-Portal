from pydantic import BaseModel, StringConstraints  # , EmailStr
from typing import Annotated, Optional
from datetime import datetime
from enum import Enum

from utils_semesters import Semester


class GeneralRequestResponse(BaseModel):
    success: bool
    message: Optional[str]


class Address(BaseModel):
    address_line1: str
    address_line2: Optional[str]
    city: str
    state_province: str
    zip_postal: str
    country: str


class AddressCreationDetails(BaseModel):
    address_line1: Annotated[str, StringConstraints(min_length=5, max_length=100)]
    address_line2: Optional[Annotated[str, StringConstraints(min_length=5, max_length=100)]] = None
    city: Annotated[str, StringConstraints(min_length=2, max_length=50)]
    state_province: Annotated[str, StringConstraints(min_length=2, max_length=50)]
    zip_postal: Annotated[str, StringConstraints(min_length=2, max_length=50)]
    country: Annotated[str, StringConstraints(min_length=2, max_length=50)]


class AddressUpdateDetails(BaseModel):
    address_line1: Optional[Annotated[str, StringConstraints(min_length=5, max_length=100)]] = None
    address_line2: Optional[Annotated[str, StringConstraints(min_length=5, max_length=100)]] = None
    city: Optional[Annotated[str, StringConstraints(min_length=2, max_length=50)]] = None
    state_province: Optional[Annotated[str, StringConstraints(min_length=2, max_length=50)]] = None
    zip_postal: Optional[Annotated[str, StringConstraints(min_length=2, max_length=50)]] = None
    country: Optional[Annotated[str, StringConstraints(min_length=2, max_length=50)]] = None


class Company(BaseModel):
    id: int
    name: str
    address: Address
    website_link: Optional[str]


class CompanyName(BaseModel):
    name: str


class Contact(BaseModel):
    first_name: str
    middle_name: Optional[str]
    last_name: str
    email: str
    phone: Optional[str]


class ContactCreationDetails(BaseModel):
    first_name: Annotated[str, StringConstraints(max_length=50)]
    middle_name: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    last_name: Annotated[str, StringConstraints(max_length=50)]
    email: Annotated[str, StringConstraints(max_length=254)]
    # email: Annotated[EmailStr, StringConstraints(max_length=254)]
    phone: Optional[Annotated[str, StringConstraints(max_length=50)]] = None


class ContactUpdateDetails(BaseModel):
    first_name: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    middle_name: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    last_name: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    email: Optional[Annotated[str, StringConstraints(max_length=254)]] = None
    # email: Optional[Annotated[EmailStr, StringConstraints(max_length=254)]] = None
    phone: Optional[Annotated[str, StringConstraints(max_length=50)]] = None


class EmployerProfile(BaseModel):
    company_id: int


class FacultyProfile(BaseModel):
    department: str


class StudentProfile(BaseModel):
    department_name: str
    major_name: str
    credit_hours: int
    gpa: float
    start_semester: Semester
    start_year: int
    transfer: bool
    resume_link: Optional[str]


class BriefStudentProfile(BaseModel):
    contact: Contact
    department_name: str
    major_name: str


class LocationType(Enum):
    REMOTE = "Remote"
    COMPANY = "Company"
    OTHER = "Other"


class InternshipStatus(Enum):
    OPEN = "Open"
    CLOSED = "Closed"
    PENDING_START = "PendingStart"
    IN_PROGRESS = "InProgress"
    PENDING_SUMMARY = "PendingSummary"
    PENDING_GRADE = "PendingGrade"
    COMPLETED = "Completed"


class Internship(BaseModel):
    id: int
    company: Company
    title: str
    description: str
    location_type: LocationType
    address: Optional[Address]
    duration_weeks: int
    weekly_hours: int
    total_work_hours: int
    salary_info: Optional[str]
    status: InternshipStatus
    majors: list[str]
    required_skills: list[str]
    preferred_skills: list[str]


class BriefInternship(BaseModel):
    company: CompanyName
    title: str
    description: str
    duration_weeks: int
    weekly_hours: int
    total_work_hours: int


class EmployerInternshipSummary(BaseModel):
    title: str
    description: str
    duration_weeks: int
    weekly_hours: int
    total_work_hours: int


class Application(BaseModel):
    application_date: datetime
    coop_credit_eligibility: bool
    note: Optional[str]
    resume_link: Optional[str]
    cover_letter_link: Optional[str]
    selected: bool


class EmployerApplicationInfo(BaseModel):
    student: BriefStudentProfile
    note: Optional[str]
    resume_link: Optional[str]
    cover_letter_link: Optional[str]
    selected: bool


class FacultyApplicationInfo(BaseModel):
    student: BriefStudentProfile
    internship: BriefInternship
    coop_credit_eligibility: bool


class StudentApplicationInfo(BaseModel):
    internship: BriefInternship
    coop_credit_eligibility: bool
    note: Optional[str]
    resume_link: Optional[str]
    cover_letter_link: Optional[str]


class EmployerApplicationSummary(BaseModel):
    student: BriefStudentProfile
    internship: EmployerInternshipSummary


class StudentApplicationSummary(BaseModel):
    internship: BriefInternship
    coop_credit_eligibility: bool


class Summary(BaseModel):
    summary: str
    file_link: Optional[str]
    employer_approval: bool
    letter_grade: Optional[str]


class EmployerSummary(BaseModel):
    summary: str
    file_link: Optional[str]
    employer_approval: bool
