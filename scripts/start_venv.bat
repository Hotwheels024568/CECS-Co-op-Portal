@echo off
REM Activate Python venv in the repository root

REM Change directory to the repository root
cd /d "%~dp0\.."

REM Activate venv in the repository root
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
) else (
    echo ERROR: venv folder not found! Create with python -m venv venv
    exit /b 1
)

REM Launch interactive shell with the venv activated
cmd /k