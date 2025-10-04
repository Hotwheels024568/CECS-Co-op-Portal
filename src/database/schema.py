from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    user_type = Column(
        Enum("Employer", "Student", "Faculty", name="user_type"), nullable=False
    )
    # Must be enforced by logic to point to correct profile table!
    profile_id = Column(Integer)  # Nullable


class Address(Base):
    __tablename__ = "address"
    id = Column(Integer, primary_key=True)
    address_line1 = Column(String(100), nullable=False)
    address_line2 = Column(String(100))  # Nullable
    city = Column(String(50), nullable=False)
    state_province = Column(String(50), nullable=False)
    zip_postal = Column(String(20), nullable=False)
    country = Column(String(50), nullable=False)


class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    address_id = Column(Integer, ForeignKey("address.id"), nullable=False)
    website_link = Column(String(255))
    address = relationship("Address")


class ContactInfo(Base):
    __tablename__ = "contact_info"
    id = Column(Integer, primary_key=True)
    first = Column(String(30), nullable=False)
    middle = Column(String(30))  # Nullable
    last = Column(String(30), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    phone = Column(String(30))  # Nullable


class Employer(Base):
    __tablename__ = "employers"
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey("contact_info.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    company = relationship("Company")
    contact = relationship("ContactInfo")


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey("contact_info.id"), nullable=False)
    department = Column(String(100), nullable=False)
    major = Column(String(100), nullable=False)
    credit_hours = Column(Integer, nullable=False)
    gpa = Column(Float(2), nullable=False)  # precision hints for floating point types
    start_semester_year = Column(String(20), nullable=False)
    transfer = Column(Boolean, nullable=False)
    resume_link = Column(String(255))
    contact = relationship("ContactInfo")


class Faculty(Base):
    __tablename__ = "faculty"
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey("contact_info.id"), nullable=False)
    department = Column(String(100), nullable=False, unique=True)
    contact = relationship("ContactInfo")


class InternshipLocation(Base):
    __tablename__ = "internship_location"
    id = Column(Integer, primary_key=True)
    type = Column(
        Enum("Remote", "Company", "Other", name="location_type"), nullable=False
    )
    address_id = Column(Integer, ForeignKey("address.id"))  # Nullable
    address = relationship("Address")


class InternshipOpportunity(Base):
    __tablename__ = "internship_opportunities"
    id = Column(Integer, primary_key=True)
    employer_id = Column(Integer, ForeignKey("employers.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    location_id = Column(Integer, ForeignKey("internship_location.id"), nullable=False)
    duration_weeks = Column(Integer, nullable=False)
    weekly_hours = Column(Integer, nullable=False)
    total_work_hours = Column(Integer, nullable=False)  # Calculated!
    # For full normalization: use association table
    majors_of_interest = Column(String(255))  # Nullable
    required_skills = Column(String(255))  # Nullable
    preferred_skills = Column(String(255))  # Nullable
    salary_info = Column(String(255))  # Nullable
    status = Column(
        Enum(
            "Open",  # Accepting Applications
            "Closed",  # Applications Closed
            "PendingStart",  # Student is selected/Opportunity is filled
            "InProgress",
            "WaitingSummary",
            "WaitingGrade",
            "Completed",
            name="internship_status_enum",
        ),
        nullable=False,
        default="Open",
    )
    employer = relationship("Employer")
    location = relationship("InternshipLocation")


class InternshipApplication(Base):
    __tablename__ = "internship_applications"
    id = Column(Integer, primary_key=True)
    internship_id = Column(
        Integer, ForeignKey("internship_opportunities.id"), nullable=False
    )
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    coop_credit_eligibility = Column(Boolean, nullable=False)
    internship = relationship("InternshipOpportunity")
    student = relationship("Student")

    __table_args__ = (
        UniqueConstraint("internship_id", "student_id", name="_internship_student_uc"),
    )


class InternshipSummary(Base):
    __tablename__ = "internship_summaries"
    id = Column(Integer, primary_key=True)
    application_id = Column(
        Integer, ForeignKey("internship_applications.id"), unique=True, nullable=False
    )
    summary = Column(Text, nullable=False)
    employer_approval = Column(
        Enum("Approved", "Not Approved", name="employer_approval_enum"),
        default="Not Approved",
        nullable=False,
    )
    letter_grade = Column(String(2))  # E.g., A, B, C, etc.  # Nullable
    application = relationship("InternshipApplication")


"""
# Optionally, you can add Major, Skill, and junction tables for full normalization.
class Major(Base):
    __tablename__ = "majors"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)


class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
"""
