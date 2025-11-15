from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.database.manage import AsyncDBManager
from src.backend.globals import DB_MANAGER
from src.backend.routers.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    global DB_MANAGER
    DB_MANAGER = await AsyncDBManager.create()

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
    Authentication: /auth/
    Accounts/Profiles: /accounts/, /students/, /employers/, /faculty/
    Company and Address: /companies/, /addresses/
    Department/Major: /departments/, /majors/
    Internship Posting/Searching: /internships/
    Application Submission/Management: /applications/
    Summary Submission/Approval/Grading: /summaries/
    Skill Tagging: /skills/, with internship linkage
    Notification/Communication: /notifications/ (if implementing email/alerts)
"""
