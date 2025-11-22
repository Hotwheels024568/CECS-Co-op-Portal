from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.database.manage import AsyncDBManager
from src.backend.globals import DB_MANAGER

from src.backend.routers.auth import router as auth_router
from src.backend.routers.accounts import router as accounts_router
from src.backend.routers.notifications import router as notifications_router

from src.backend.routers.profiles.students import router as students_router
from src.backend.routers.profiles.employers import router as employers_router
from src.backend.routers.profiles.faculty import router as faculty_router
from src.backend.routers.profiles.companies import router as companies_router

from src.backend.routers.internships.internships import router as internships_router
from src.backend.routers.internships.applications import router as applications_router
from src.backend.routers.internships.summaries import router as summaries_router

from src.backend.routers.references.addresses import router as addresses_router
from src.backend.routers.references.departments import router as departments_router
from src.backend.routers.references.majors import router as majors_router
from src.backend.routers.references.skills import router as skills_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    global DB_MANAGER
    DB_MANAGER = await AsyncDBManager.create(rebuild=True, seed=True)

    yield  # <-- App runs while you wait here

    # Shutdown code (if needed)
    # Perform cleanup if applicable, e.g. await DB_MANAGER.close() if you define such a method


app = FastAPI(lifespan=lifespan)

# Allow React dev client to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev only!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# DO NOT DELETE
@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}


app.include_router(auth_router, prefix="/auth")
app.include_router(accounts_router, prefix="/accounts")
app.include_router(notifications_router, prefix="/notifications")

app.include_router(companies_router, prefix="/companies")
app.include_router(employers_router, prefix="/employers")
app.include_router(faculty_router, prefix="/faculty")
app.include_router(students_router, prefix="/students")

app.include_router(internships_router, prefix="/internships")
app.include_router(applications_router, prefix="/applications")
app.include_router(summaries_router, prefix="/summaries")

app.include_router(addresses_router, prefix="/addresses")
app.include_router(departments_router, prefix="/departments")
app.include_router(majors_router, prefix="/majors")
app.include_router(skills_router, prefix="/skills")

"""
Core Routers to Implement
1. Authentication & Account
    /auth/ (login, logout, registration, token)
    /accounts/ (generic for all account types: Employer, Student, Faculty)
    Subroutes: /students/, /employers/, /faculty/
2. Profile Management
    /companies/ (create/view/update company profiles)
    /students/ (manage student profiles, by student or faculty)
    /faculty/ (manage faculty/coordinator profiles)
    /contacts/ (contact info for accounts)
3. Address Management
    /addresses/ (used by companies and possibly other entities)
4. Department & Major Management
    /departments/
    /majors/
5. Internship Opportunity
    /internships/
    CRUD for internship postings (employers, possibly faculty)
    GET/search for opportunities (students, faculty)
    Internships can have majors, skills, status (enums), hours, etc.
6. Internship Application
    /applications/
    Students apply to opportunities
    Employers/faculty view/manage applications
    Contains co-op eligibility info
7. Internship Summary (and Grades)
    /summaries/
    Students submit, employers approve, faculty review/assign grades
8. Skills
    /skills/
    /internships/{id}/required-skills/ and /internships/{id}/preferred-skills/ (junction tables)
9. Notifications (Bonus/Optional)
    /notifications/
    For system to send emails or portal notifications

Suggested Router Module List
Here's a concise summary for implementation and file/folder structure guidance:
    auth_router.py (login/register endpoints)
    accounts_router.py (account generic routes)
    students_router.py (profile, applications, summaries)
    employers_router.py (profile, company, opportunities, applications)
    faculty_router.py (profile, manage students/summaries in dept)
    companies_router.py
    addresses_router.py
    departments_router.py
    majors_router.py
    internships_router.py (posting, searching, updating status)
    applications_router.py
    summaries_router.py
    skills_router.py
    notifications_router.py (optional/bonus)

Quick Use-Case Mapping
    ...
    Skill Tagging: /skills/, with internship linkage
    Notification/Communication: /notifications/ (if implementing email/alerts)
"""
