from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    # Require POST HTTPS request to server
    # Hash, Salt & (Optional before hashing) Pepper on server and store
    #   If a username does not exist, perform a fake hash computation with a dummy password hash so the time spent matches an existing user’s check.
    #   Hash password comparisons should always use constant-time algorithms.
    #       Compare hashes using hmac.compare_digest
    password = Column(String(255), nullable=False)
    user_type = Column(
        Enum("Employer", "Student", "Faculty", name="user_type"), nullable=False
    )

    contact = relationship(
        "ContactInfo",
        back_populates="account",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __mapper_args__ = {"polymorphic_identity": "account", "polymorphic_on": user_type}


class Address(Base):
    __tablename__ = "addresses"
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
    name = Column(String(100), unique=True, nullable=False)
    address_id = Column(Integer, ForeignKey("addresses.id"), unique=True, nullable=False)
    website_link = Column(String(255))  # Nullable

    address = relationship("Address", uselist=False)  # 1-to-1 with Address

    employees = relationship("EmployerAccount", back_populates="company")
    internships = relationship("Internship", back_populates="company")


class ContactInfo(Base):
    __tablename__ = "contact_info"
    id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True)
    first = Column(String(30), nullable=False)
    middle = Column(String(30))  # Nullable
    last = Column(String(30), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    phone = Column(String(30))  # Nullable

    account = relationship("Account", back_populates="contact", uselist=False)


class EmployerAccount(Account):
    __tablename__ = "employer_accounts"
    id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True)
    company_id = Column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    company = relationship("Company", back_populates="employees")

    __mapper_args__ = {"polymorphic_identity": "Employer"}


class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    students = relationship("StudentAccount", back_populates="department")
    faculty = relationship("FacultyAccount", back_populates="department")


class Major(Base):
    __tablename__ = "majors"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    students = relationship("StudentAccount", back_populates="major")
    internships = relationship("InternshipMajor", back_populates="major")


class StudentAccount(Account):
    __tablename__ = "student_accounts"
    id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    major_id = Column(Integer, ForeignKey("majors.id"), nullable=False)

    credit_hours = Column(Integer, nullable=False)
    # 4.0 (2, 1) up to 4.0000 (5, 4) overkill but don't want to worry about it
    gpa = Column(Numeric(5, 4), nullable=False)
    start_semester = Column(
        Enum("Winter", "Summer", "Fall", name="start_semester_enum"), nullable=False
    )
    start_year = Column(Integer, nullable=False)
    transfer = Column(Boolean, nullable=False)
    resume_link = Column(String(255))  # Nullable

    department = relationship("Department", back_populates="students")
    major = relationship("Major", back_populates="students")

    applications = relationship("InternshipApplication", back_populates="student")

    __table_args__ = (
        CheckConstraint("credit_hours >= 0", name="_check_credit_hours_non_negative"),
        CheckConstraint("gpa >= 0", name="_check_gpa_non_negative"),
        CheckConstraint("start_year >= 0", name="_check_start_year_non_negative"),
    )

    __mapper_args__ = {"polymorphic_identity": "Student"}


class FacultyAccount(Account):
    __tablename__ = "faculty_accounts"
    id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True)
    # Should be Unique according to assignment directions
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

    department = relationship("Department", back_populates="faculty")
    # department = relationship("Department", uselist=False)  # 1-to-1 with Department

    __mapper_args__ = {"polymorphic_identity": "Faculty"}


class Internship(Base):
    __tablename__ = "internships"
    id = Column(Integer, primary_key=True)
    company_id = Column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    location_type = Column(
        Enum("Remote", "Company", "Other", name="location_type"), nullable=False
    )
    # Nullable (Remote: NULL, Company: companies.address_id, Other: Unique address.id)
    address_id = Column(Integer, ForeignKey("addresses.id"))
    duration_weeks = Column(Integer, nullable=False)
    weekly_hours = Column(Integer, nullable=False)
    total_work_hours = Column(Integer, nullable=False)  # Calculated!
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
        server_default="Open",
    )

    company = relationship("Company", back_populates="internships")
    address = relationship("Address")
    majors = relationship("InternshipMajor", back_populates="internship")

    required_skills = relationship("InternshipReqSkill", back_populates="internship")
    preferred_skills = relationship("InternshipPrefSkill", back_populates="internship")
    applications = relationship("InternshipApplication", back_populates="internship")

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
    __tablename__ = "internship_majors"
    internship_id = Column(
        Integer,
        ForeignKey("internships.id", ondelete="CASCADE"),
        nullable=False,
    )
    major_id = Column(
        Integer, ForeignKey("majors.id", ondelete="CASCADE"), nullable=False
    )

    internship = relationship("Internship", back_populates="majors")
    major = relationship("Major", back_populates="internships")

    __table_args__ = (
        PrimaryKeyConstraint("internship_id", "major_id", name="_internship_major_pk"),
    )


class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)


class InternshipReqSkill(Base):
    __tablename__ = "internship_required_skills"
    internship_id = Column(
        Integer, ForeignKey("internships.id", ondelete="CASCADE"), nullable=False
    )
    skill_id = Column(
        Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )

    internship = relationship("Internship", back_populates="required_skills")
    skill = relationship("Skill")

    __table_args__ = (
        PrimaryKeyConstraint(
            "internship_id", "skill_id", name="_internship_required_skill_pk"
        ),
    )


class InternshipPrefSkill(Base):
    __tablename__ = "internship_preferred_skills"
    internship_id = Column(
        Integer, ForeignKey("internships.id", ondelete="CASCADE"), nullable=False
    )
    skill_id = Column(
        Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )

    internship = relationship("Internship", back_populates="preferred_skills")
    skill = relationship("Skill")

    __table_args__ = (
        PrimaryKeyConstraint(
            "internship_id", "skill_id", name="_internship_preferred_skill_pk"
        ),
    )


class InternshipApplication(Base):
    __tablename__ = "internship_applications"
    internship_id = Column(
        Integer, ForeignKey("internships.id", ondelete="CASCADE"), nullable=False
    )
    student_id = Column(
        Integer, ForeignKey("student_accounts.id", ondelete="CASCADE"), nullable=False
    )
    coop_credit_eligibility = Column(Boolean, nullable=False)

    internship = relationship("Internship", back_populates="applications")
    student = relationship("StudentAccount", back_populates="applications")
    summary = relationship(
        "InternshipSummary", back_populates="application", uselist=False
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "internship_id", "student_id", name="_internship_student_pk"
        ),
    )


class InternshipSummary(Base):
    __tablename__ = "internship_summaries"
    internship_id = Column(Integer, primary_key=True)
    student_id = Column(Integer, primary_key=True)
    summary = Column(Text, nullable=False)
    employer_approval = Column(Boolean, default=False, server_default="0", nullable=False)
    letter_grade = Column(String(2))  # E.g., A, B, C, etc.  # Nullable

    # 1-to-1 with InternshipApplication
    application = relationship(
        "InternshipApplication", back_populates="summary", uselist=False
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["internship_id", "student_id"],
            [
                "internship_applications.internship_id",
                "internship_applications.student_id",
            ],
            ondelete="CASCADE",
        ),
    )
