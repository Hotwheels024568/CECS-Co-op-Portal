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
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func

from datetime import datetime

Base = declarative_base()


class Account(Base):
    """
    Base user account model.

    Attributes:
        id (int): Auto-incrementing primary key.
        username (str): Unique username.
        password (str): Hashed user password. Should be securely hashed and compared per security best practices.
        user_type (str, optional): User type; one of 'Employer', 'Student', or 'Faculty'.
        contact (ContactInfo): Associated Contact Info (one-to-one).

    Security Considerations:
        - Passwords are required to be sent via POST over HTTPS only.
        - All passwords should be hashed, salted, and, optionally, peppered on the server before storage.
        - If a username does not exist, the system should perform a fake hash to mitigate timing attacks.
        - Hash comparisons must be done in constant time using methods like hmac.compare_digest.
    """

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    user_type: Mapped[str | None] = mapped_column(Enum("Employer", "Student", "Faculty", name="user_type"))
    # An Admin user type could be useful

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
    Stores postal address information for companies and internships.

    Attributes:
        id (int): Auto-incrementing primary key.
        address_line1 (str): First line of the street address.
        address_line2 (str, optional): Second line of the street address. Defaults to None.
        city (str): City name.
        state_province (str): State or province.
        zip_postal (str): ZIP or postal code.
        country (str): Country.
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
    Represents a company offering internships.

    Attributes:
        id (int): Auto-incrementing primary key.
        name (str): Unique company name.
        address_id (int): Foreign key to the Address.
        website_link (str, optional): Company website. Defaults to None.
        address (Address): Associated Address (one-to-one).
        employees (list[EmployerAccount]): Employer accounts associated with the company.
        internships (list[Internship]): Internships offered by the company.
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
    Stores contact details for an account.

    Attributes:
        id (int): Primary key and foreign key to the Account (one-to-one).
        first (str): First name.
        middle (str, optional): Middle name. Defaults to None.
        last (str): Last name.
        email (str): Unique email address.
        phone (str, optional): Phone number. Defaults to None.
        account (Account): Associated Account (one-to-one).
    """

    __tablename__ = "contact_info"

    id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True
    )
    first: Mapped[str] = mapped_column(String(50), nullable=False)
    middle: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Nullable
    last: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Nullable

    # 1-to-1 with Account
    account: Mapped["Account"] = relationship(
        "Account", back_populates="contact", uselist=False
    )


class EmployerAccount(Account):
    """
    Employer user account.

    Inherits login credentials and contact info from Account.

    Attributes:
        id (int): Primary key and foreign key to the Account (one-to-one).
        company_id (int): Foreign key to the Company.
        company (Company): Associated Company.
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
    Represents an Academic Department.

    Attributes:
        id (int): Auto-incrementing primary key.
        name (str): Unique Department name.
        faculty (list[FacultyAccount]): Faculty accounts within the Department.
        students (list[StudentAccount]): Student accounts within the Department.
    """

    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    faculty: Mapped[list["FacultyAccount"]] = relationship(
        "FacultyAccount", back_populates="department"
    )
    students: Mapped[list["StudentAccount"]] = relationship(
        "StudentAccount", back_populates="department"
    )


class Major(Base):
    """
    Represents a Major (field of study).

    Attributes:
        id (int): Auto-incrementing primary key.
        name (str): Unique Major name.
        students (list[StudentAccount]): Student accounts enrolled in the Major.
        internships (list[InternshipMajor]): Internships associated with the Major.
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
    Student user account.

    Attributes:
        id (int): Primary key and foreign key to the Account (one-to-one).
        department_id (int): Foreign key to the Department.
        major_id (int): Foreign key to the Major.
        credit_hours (int): Number of credit hours completed (must be non-negative).
        gpa (float): GPA (0 or greater, up to 4 decimal places).
        start_semester (str): The Student's first semester taking classes ('Winter', 'Summer', or 'Fall').
        start_year (int): The year the Student started taking classes (must be non-negative).
        transfer (bool): Whether the student transferred from another institution.
        resume_link (str, optional): Link to the student's resume. Defaults to None.
        department (Department): Associated Department.
        major (Major): Associated Major.
        applications (list[InternshipApplication]): Internship applications submitted by the Student.
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
    # 4.0 (2, 1) up to 4.0000 (5, 4) overkill, but don't want to worry about it
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
    Faculty user account.

    Attributes:
        id (int): Primary key and foreign key to the Account (one-to-one).
        department_id (int): Foreign key to the Department.
        department (Department): Associated Department.
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
    Internship opportunity posted by a Company.

    Attributes:
        id (int): Auto-incrementing primary key.
        company_id (int): Foreign key to the Company.
        title (str): Internship title.
        description (str): Detailed description of the internship.
        location_type (str): Location type ('Remote', 'Company', or 'Other').
        address_id (int, optional): Foreign key to an Address. Nullable if Remote; required otherwise.
        duration_weeks (int): Internship duration in weeks (must be non-negative).
        weekly_hours (int): Number of work hours per week (must be non-negative).
        total_work_hours (int): Total number of work hours (must be non-negative).
        salary_info (str, optional): Salary or compensation information. Defaults to None.
        status (str): Current status ('Open', 'Closed', 'PendingStart', 'InProgress', 'WaitingSummary', 'WaitingGrade', 'Completed').
            Defaults to 'Open'.
        company (Company): Associated Company.
        address (Address): Associated Address, if applicable.
        majors (list[InternshipMajor]): Association objects linking Majors to the internship.
        required_skills (list[InternshipReqSkill]): Association objects linking required Skills to the internship.
        preferred_skills (list[InternshipPrefSkill]): Association objects linking preferred Skills to the internship.
        applications (list[InternshipApplication]): Applications submitted for this internship.

    Notes:
        - To access related Major objects: [imajor.major for imajor in internship.majors]
        - To access related required Skill objects: [iskill.skill for iskill in internship.required_skills]
        - To access related preferred Skill objects: [iskill.skill for iskill in internship.preferred_skills]
    """

    # Fields to store dates for creation, latest update, and latest status update could be useful

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
    Associate an Internship with a Major.

    Implements a many-to-many relationship between Internships and Majors using a composite primary key.

    Attributes:
        internship_id (int): Foreign key to the Internship (part of composite primary key).
        major_id (int): Foreign key to the Major (part of composite primary key).
        internship (Internship): Associated Internship.
        major (Major): Associated Major.
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
    Represents a Skill.

    Attributes:
        id (int): Auto-incrementing primary key.
        name (str): Unique Skill name.
    """

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class InternshipReqSkill(Base):
    """
    Associate a required Skill with an Internship.

    Implements a many-to-many relationship between Internships and Skills using a composite primary key.

    Attributes:
        internship_id (int): Foreign key to the Internship (part of composite primary key).
        skill_id (int): Foreign key to the Skill (part of composite primary key).
        internship (Internship): Associated Internship.
        skill (Skill): Associated required Skill.
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
    Associate a preferred (nice-to-have) Skill with an Internship.

    Implements a many-to-many relationship between Internships and Skills using a composite primary key.

    Attributes:
        internship_id (int): Foreign key to the Internship (part of composite primary key).
        skill_id (int): Foreign key to the Skill (part of composite primary key).
        internship (Internship): Associated Internship.
        skill (Skill): Associated preferred Skill.
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
    Represents a Student's application to a specific Internship.

    Attributes:
        id (int): Auto-incrementing primary key.
        student_id (int): Foreign key to the StudentAccount.
        internship_id (int): Foreign key to the Internship.
        application_date (str): ISO 8601 timestamp of when the application was submitted.
        coop_credit_eligibility (bool): Whether the application is eligible for co-op credit.
        note (str, optional): Note or message from the student to the employer. Defaults to None.
        resume_link (str, optional): Link to the student's application specific resume. Defaults to None.
        cover_letter_link (str, optional): Link to the student's application specific cover letter. Defaults to None.
        selected (bool): Indicates if this application was chosen/hired by the employer for the internship. Defaults to False.
        internship (Internship): Associated Internship.
        student (StudentAccount): Associated Student.
        summary (InternshipSummary): Associated summary for the application (one-to-one).

    Notes:
        - Each student can only apply to a given internship once.
            - Unique constraint on internship_id and student_id
    """

    __tablename__ = "internship_applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("student_accounts.id", ondelete="CASCADE"), nullable=False
    )
    internship_id: Mapped[int] = mapped_column(
        ForeignKey("internships.id", ondelete="CASCADE"), nullable=False
    )
    application_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.timezone('utc', func.now())
    )
    coop_credit_eligibility: Mapped[bool] = mapped_column(Boolean, nullable=False)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cover_letter_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("FALSE"))

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
    Contains the completion summary and the employer's evaluation for a specific InternshipApplication.

    Attributes:
        id (int): Primary key and foreign key to the InternshipApplication (one-to-one).
        summary (str): Completion summary text of the internship experience.
        file_link (str, optional): Link to supporting document(s) or file(s), e.g. additional reports or proof of work. Defaults to ""
        employer_approval (bool): Employer approval status (False = Not Approved by default; True = Approved).
        letter_grade (str, optional): Letter grade (e.g., "A+", "A", "B"). Defaults to None.
        application (InternshipApplication): Associated InternshipApplication (one-to-one).

    Notes:
        Uses a strict one-to-one relationship with InternshipApplication, sharing the same primary key.
    """

    __tablename__ = "internship_summaries"

    id: Mapped[int] = mapped_column(
        ForeignKey("internship_applications.id", ondelete="CASCADE"), primary_key=True
    )
    summary: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=""
    )
    file_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employer_approval: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("FALSE")
    )
    # Nullable, e.g., "A", "B", "C"
    letter_grade: Mapped[str | None] = mapped_column(String(2), nullable=True)

    # 1-to-1 with InternshipApplication
    application: Mapped["InternshipApplication"] = relationship(
        "InternshipApplication", back_populates="summary", uselist=False
    )
