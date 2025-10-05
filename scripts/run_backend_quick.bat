@echo off
REM Activate Python venv and run the backend using Uvicorn

REM Change directory to the repository root
cd /d "%~dp0\.."

REM Activate venv in the repository root
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
) else (
    echo ERROR: venv folder not found! Create with python -m venv venv
    exit /b 1
)

REM Start FastAPI/Uvicorn server
uvicorn src.backend.main:app --reload --port 8000 --no-use-colors

pause