@echo off
REM Start PostgreSQL (Docker), activate Python venv, start FastAPI/Uvicorn

REM Helper to show usage
:show_help
echo.
echo Usage: %~nx0 [--help ^| -h]
echo.
echo Starts PostgreSQL ^(db in docker-compose^), activates Python venv, and launches FastAPI backend (with UVicorn).
echo.
goto:eof

REM Change to repository root
cd /d "%~dp0\.."

REM Parse command-line arguments
:parse_args
if "%~1"=="" goto after_args
if /I "%~1"=="-h" (
    call :show_help
    exit /b 0
) else if /I "%~1"=="--help" (
    call :show_help
    exit /b 0
) else (
    echo Unknown argument: %~1
    call :show_help
    exit /b 1
)
shift
goto parse_args
:after_args

REM Track if we started the db
set "DB_STARTED=0"

REM Handler for script exit (cleanup)
:cleanup
if "%DB_STARTED%"=="1" (
    echo Stopping PostgreSQL container...
    docker compose down
)
exit /b %1

REM Start PostgreSQL service (db)
docker compose up -d db
if errorlevel 1 exit /b
set "DB_STARTED=1"

REM Wait for PostgreSQL to be ready
echo Waiting for PostgreSQL to initialize...
REM Set to your username and database name to be the same as in your docker-compose.yml
set "POSTGRES_USER=CIS_425_Project"
set "POSTGRES_DB=db"

for /l %%i in (1, 1, 15) do (
    docker compose exec -T db pg_isready -U %POSTGRES_USER% -d %POSTGRES_DB% >nul 2>&1 && goto db_ready
    timeout /t 1 >nul
)

echo WARNING: PostgreSQL may not be ready yet. Continuing anyway...
goto after_db_wait
:db_ready
echo PostgreSQL is ready.
:after_db_wait

REM Activate Python virtual environment
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
) else (
    echo ERROR: venv folder not found! Create with python -m venv venv
    call :cleanup 1
    exit /b 1
)

REM Start FastAPI/Uvicorn
uvicorn src.rcp.backend.main:app --reload --port 8000 --no-use-colors

REM After server exits, cleanup
call :cleanup 0
pause