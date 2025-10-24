@echo off
REM Start PostgreSQL DB (Docker), activate Python venv, and allow Python "scripts" to be run in repo root.
REM Usage: %~nx0 [--help | -h]

REM Save original directory to restore when done
set "SCRIPTS_DIR=%CD%"

REM Change to repository root (parent of script directory)
cd /d "%~dp0\.."

REM Parse command line arguments
:parse_args
if "%~1"=="" goto after_args
if /I "%~1"=="-h" (
    call :show_help
    goto :exit
) else if /I "%~1"=="--help" (
    call :show_help
    goto :exit
) else (
    echo Unknown argument: %~1
    call :show_help
    goto :exit
)
shift
goto parse_args
:after_args

REM Track if we started the DB
set "DB_STARTED=0"

REM Start PostgreSQL database container
echo.
echo Starting PostgreSQL Docker container...
docker compose up -d db
if errorlevel 1 (
    echo Error: Docker Compose failed to start the db service.
    pause
    goto :cleanup
)
set "DB_STARTED=1"

REM Wait for database to be ready (max 15 seconds)
echo.
echo Waiting for PostgreSQL to initialize...
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

REM Activate Python venv
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
) else (
    echo ERROR: venv folder not found! Create one with:
    echo    python -m venv venv
    goto :cleanup
)

echo.
echo The environment is ready.
echo Run Python scripts as needed. When finished, type exit to clean up.
echo.

REM Launch interactive shell with the venv activated
cmd /k

REM Cleanup DB and venv on exit
:cleanup
IF "%DB_STARTED%"=="1" (
    echo.
    echo Stopping PostgreSQL container...
    docker compose down
    echo.
)

REM Deactivate venv if active
REM (This is a no-op if venv isn't currently activated)
IF DEFINED VIRTUAL_ENV (
    deactivate
)

:exit
cd /d "%SCRIPT_DIR%"
exit /b


REM Helper to show usage
:show_help
echo.
echo Usage: %~nx0 [--help ^| -h]
echo.
echo Starts PostgreSQL DB (Docker) and activates Python venv for project use.
echo.
goto :eof
