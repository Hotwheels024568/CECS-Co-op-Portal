@echo off
REM Change directory to the repository root
cd /d "%~dp0\.."

REM Change to frontend directory and run Vite dev server
cd frontend
npm run dev