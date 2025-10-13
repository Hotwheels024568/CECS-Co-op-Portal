from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base

Base = declarative_base()


class Account(Base):
    """
    Base user account model for all users in the system.
    User type is an enum: Employer, Student, or Faculty.
    Passwords should be hashed and compared securely, per application security requirements.
    Each account is associated with contact info (one-to-one).
    """

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    # Require POST HTTPS request to server
    # Hash, Salt & (Optional before hashing) Pepper on server and store
    #   If a username does not exist, perform a fake hash computation with a dummy password hash so the time spent matches an existing user’s check.
    #   Hash password comparisons should always use constant-time algorithms.
    #       Compare hashes using hmac.compare_digest
    user_type: Mapped[str] = mapped_column(
        Enum("Employer", "Student", "Faculty", name="user_type"), nullable=False
    )

    # 1-to-1 with ContactInfo
    contact: Mapped["ContactInfo"] = relationship(
        "ContactInfo",
        back_populates="account",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __mapper_args__ = {"polymorphic_identity": "account", "polymorphic_on": user_type}


class Address(Base):
    """
    Stores postal addresses for companies and internships.
    Allows for an optional second address line.
    """

    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    address_line1: Mapped[str] = mapped_column(String(100), nullable=False)
    # Nullable
    address_line2: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    state_province: Mapped[str] = mapped_column(String(50), nullable=False)
    zip_postal: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(50), nullable=False)


class Company(Base):
    """
    Represents a company that offers internships.
    Each company has a unique name, is associated with a unique address, and may have an optional website.
    """

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    address_id: Mapped[int] = mapped_column(
        ForeignKey("addresses.id"), unique=True, nullable=False
    )
    # Nullable
    website_link: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # 1-to-1 with Address
    address: Mapped["Address"] = relationship("Address", uselist=False)

    employees: Mapped[list["EmployerAccount"]] = relationship(
        "EmployerAccount", back_populates="company"
    )
    internships: Mapped[list["Internship"]] = relationship(
        "Internship", back_populates="company"
    )


class ContactInfo(Base):
    """
    Stores personal contact information for an account, including name, email, and optional middle name and phone number.
    Each account has exactly one associated contact info entry.
    """

    __tablename__ = "contact_info"

    id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True
    )
    first: Mapped[str] = mapped_column(String(30), nullable=False)
    middle: Mapped[str | None] = mapped_column(String(30), nullable=True)  # Nullable
    last: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)  # Nullable

    # 1-to-1 with Account
    account: Mapped["Account"] = relationship(
        "Account", back_populates="contact", uselist=False
    )


class EmployerAccount(Account):
    """
    Specialized user account for employers.
    Each employer is associated with a company and inherits login credentials and contact info from Account.
    """

    __tablename__ = "employer_accounts"

    id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    company: Mapped["Company"] = relationship("Company", back_populates="employees")

    __mapper_args__ = {"polymorphic_identity": "Employer"}


class Department(Base):
    """
    Represents an academic department within the system.
    Used to group students and faculty members by their field or area of study.
    """

    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    students: Mapped[list["StudentAccount"]] = relationship(
        "StudentAccount", back_populates="department"
    )
    faculty: Mapped[list["FacultyAccount"]] = relationship(
        "FacultyAccount", back_populates="department"
    )


class Major(Base):
    """
    Represents a field of study (major) that students can be enrolled in.
    Each major has a unique name, and is associated with students and relevant internships.
    """

    __tablename__ = "majors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    students: Mapped[list["StudentAccount"]] = relationship(
        "StudentAccount", back_populates="major"
    )
    internships: Mapped[list["InternshipMajor"]] = relationship(
        "InternshipMajor", back_populates="major"
    )


class StudentAccount(Account):
    """
    Specialized user account for students.
    Stores enrollment information, academic details (GPA, credit hours, major, department, transfer status), and an optional resume link.
    """

    __tablename__ = "student_accounts"

    id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True
    )
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id"), nullable=False
    )
    major_id: Mapped[int] = mapped_column(ForeignKey("majors.id"), nullable=False)

    credit_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    # 4.0 (2, 1) up to 4.0000 (5, 4) overkill but don't want to worry about it
    gpa: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    start_semester: Mapped[str] = mapped_column(
        Enum("Winter", "Summer", "Fall", name="start_semester_enum"), nullable=False
    )
    start_year: Mapped[int] = mapped_column(Integer, nullable=False)
    transfer: Mapped[bool] = mapped_column(Boolean, nullable=False)
    resume_link: Mapped[str | None] = mapped_column(String(255), nullable=True)

    department: Mapped["Department"] = relationship(
        "Department", back_populates="students"
    )
    major: Mapped["Major"] = relationship("Major", back_populates="students")

    applications: Mapped[list["InternshipApplication"]] = relationship(
        "InternshipApplication", back_populates="student"
    )

    __table_args__ = (
        CheckConstraint("credit_hours >= 0", name="_check_credit_hours_non_negative"),
        CheckConstraint("gpa >= 0", name="_check_gpa_non_negative"),
        CheckConstraint("start_year >= 0", name="_check_start_year_non_negative"),
    )

    __mapper_args__ = {"polymorphic_identity": "Student"}


class FacultyAccount(Account):
    """
    Specialized user account for faculty members.
    Each faculty member is associated with a single academic department and inherits login credentials and contact info from Account.
    """

    __tablename__ = "faculty_accounts"

    id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True
    )
    # Should be Unique according to assignment directions
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id"), nullable=False
    )

    department: Mapped["Department"] = relationship(
        "Department", back_populates="faculty"
    )
    # 1-to-1 with Department
    # department: Mapped["Department"] = relationship("Department", back_populates="faculty", uselist=False)

    __mapper_args__ = {"polymorphic_identity": "Faculty"}


class Internship(Base):
    """
    Represents an internship opportunity posted by a company.
    Includes details such as title, description, location, duration, work hours, salary info,
    and current status (as an enumerated set of states in the application process).
    May be associated with specific majors and skill requirements.
    """

    __tablename__ = "internships"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location_type: Mapped[str] = mapped_column(
        Enum("Remote", "Company", "Other", name="location_type"), nullable=False
    )
    # Nullable if Remote, else required (Company: companies.address_id; Other: Unique address.id)
    address_id: Mapped[int | None] = mapped_column(
        ForeignKey("addresses.id"), nullable=True
    )
    duration_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    weekly_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    # Calculated externally
    total_work_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    salary_info: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "Open",  # Accepting Applications
            "Closed",  # Applications Closed
            "PendingStart",  # Student selected, opportunity is filled
            "InProgress",  # Currently ongoing
            "WaitingSummary",  # Awaiting completion summary
            "WaitingGrade",  # Awaiting grade input
            "Completed",  # Finished
            name="internship_status_enum",
        ),
        nullable=False,
        default="Open",
        server_default="Open",
    )

    company: Mapped["Company"] = relationship("Company", back_populates="internships")
    address: Mapped["Address"] = relationship("Address")
    majors: Mapped[list["InternshipMajor"]] = relationship(
        "InternshipMajor", back_populates="internship"
    )
    required_skills: Mapped[list["InternshipReqSkill"]] = relationship(
        "InternshipReqSkill", back_populates="internship"
    )
    preferred_skills: Mapped[list["InternshipPrefSkill"]] = relationship(
        "InternshipPrefSkill", back_populates="internship"
    )
    applications: Mapped[list["InternshipApplication"]] = relationship(
        "InternshipApplication", back_populates="internship"
    )

    __table_args__ = (
        CheckConstraint("duration_weeks >= 0", name="_check_duration_weeks_non_negative"),
        CheckConstraint("weekly_hours >= 0", name="_check_weekly_hours_non_negative"),
        CheckConstraint(
            "total_work_hours >= 0", name="_check_total_work_hours_non_negative"
        ),
        CheckConstraint(
            "location_type != 'Remote' OR address_id IS NULL",
            name="_location_type_address_ck",
        ),
    )


class InternshipMajor(Base):
    """
    Associates an internship with eligible majors.
    Implements a many-to-many relationship between internships and majors using a composite primary key.
    """

    __tablename__ = "internship_majors"

    internship_id: Mapped[int] = mapped_column(
        ForeignKey("internships.id", ondelete="CASCADE"), nullable=False
    )
    major_id: Mapped[int] = mapped_column(
        ForeignKey("majors.id", ondelete="CASCADE"), nullable=False
    )

    internship: Mapped["Internship"] = relationship("Internship", back_populates="majors")
    major: Mapped["Major"] = relationship("Major", back_populates="internships")

    __table_args__ = (
        PrimaryKeyConstraint("internship_id", "major_id", name="_internship_major_pk"),
    )


class Skill(Base):
    """
    Represents a skill that can be required or preferred for internships.
    Each skill has a unique name.
    """

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class InternshipReqSkill(Base):
    """
    Associates required skills with internships.
    Implements a many-to-many relationship between internships and skills via a composite primary key.
    """

    __tablename__ = "internship_required_skills"

    internship_id: Mapped[int] = mapped_column(
        ForeignKey("internships.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )

    internship: Mapped["Internship"] = relationship(
        "Internship", back_populates="required_skills"
    )
    skill: Mapped["Skill"] = relationship("Skill")

    __table_args__ = (
        PrimaryKeyConstraint(
            "internship_id", "skill_id", name="_internship_required_skill_pk"
        ),
    )


class InternshipPrefSkill(Base):
    """
    Associates preferred (nice-to-have) skills with internships.
    Implements a many-to-many relationship between internships and skills via a composite primary key.
    """

    __tablename__ = "internship_preferred_skills"

    internship_id: Mapped[int] = mapped_column(
        ForeignKey("internships.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )

    internship: Mapped["Internship"] = relationship(
        "Internship", back_populates="preferred_skills"
    )
    skill: Mapped["Skill"] = relationship("Skill")

    __table_args__ = (
        PrimaryKeyConstraint(
            "internship_id", "skill_id", name="_internship_preferred_skill_pk"
        ),
    )


class InternshipApplication(Base):
    """
    Represents a student's application to a specific internship.
    Tracks which student applied to which internship and whether the application is eligible for co-op credit.
    Each application is unique per (internship, student) pairing.
    """

    __tablename__ = "internship_applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    internship_id: Mapped[int] = mapped_column(
        ForeignKey("internships.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("student_accounts.id", ondelete="CASCADE"), nullable=False
    )
    coop_credit_eligibility: Mapped[bool] = mapped_column(Boolean, nullable=False)

    internship: Mapped["Internship"] = relationship(
        "Internship", back_populates="applications"
    )
    student: Mapped["StudentAccount"] = relationship(
        "StudentAccount", back_populates="applications"
    )
    # 1-to-1 with InternshipSummary
    summary: Mapped["InternshipSummary"] = relationship(
        "InternshipSummary",
        back_populates="application",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("internship_id", "student_id", name="_internship_student_uc"),
    )


class InternshipSummary(Base):
    """
    Contains the completion summary and employer's evaluation for a specific internship application.
    Employer approval is a boolean (False = Not Approved/Default; True = Approved).
    Letter grade is an optional string (e.g., "A+", "A", "B").
    Strict one-to-one relationship with InternshipApplication; uses the same primary key.
    """

    __tablename__ = "internship_summaries"

    id: Mapped[int] = mapped_column(
        ForeignKey("internship_applications.id", ondelete="CASCADE"), primary_key=True
    )
    summary: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=""
    )
    employer_approval: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("FALSE")
    )
    # Nullable, e.g. "A", "B", "C"
    letter_grade: Mapped[str | None] = mapped_column(String(2), nullable=True)

    # 1-to-1 with InternshipApplication
    application: Mapped["InternshipApplication"] = relationship(
        "InternshipApplication", back_populates="summary", uselist=False
    )
