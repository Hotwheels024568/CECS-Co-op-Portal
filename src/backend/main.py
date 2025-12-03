from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.database.manage import AsyncDBManager
from src.backend.globals import DB_MANAGER

from src.backend.routers.auth import router as auth_router
from src.backend.routers.accounts import router as accounts_router
from src.backend.routers.notifications import router as notifications_router

from src.backend.routers.profiles.companies import router as companies_router
from src.backend.routers.profiles.employers import router as employers_router
from src.backend.routers.profiles.faculty import router as faculty_router
from src.backend.routers.profiles.students import router as students_router
from src.backend.routers.profiles.relationships import router as relationships_router

from src.backend.routers.internships.internships import router as internships_router
from src.backend.routers.internships.applications import router as applications_router
from src.backend.routers.internships.summaries import router as summaries_router

from src.backend.routers.catalog import router as catalog_router


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
app.include_router(relationships_router)

app.include_router(internships_router, prefix="/internships")
app.include_router(applications_router, prefix="/applications")
app.include_router(summaries_router, prefix="/summaries")

app.include_router(catalog_router, prefix="/catalog")

"""
Core Routers to Implement
1. Authentication & Account
    /auth/ (login, logout, registration, token)
    /accounts/ (generic for all account types: Employer, Student, Faculty)
    Subroutes: /students/, /employers/, /faculty/

5. Internship Opportunity
    /internships/
    CRUD for internship postings (employers, possibly faculty)
    GET/search for opportunities (students, faculty)
    Internships can have majors, skills, status (enums), hours, etc.

9. Notifications (Bonus/Optional)
    /notifications/
    For system to send emails or portal notifications

"""
