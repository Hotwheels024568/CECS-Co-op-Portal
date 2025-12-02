# CECS Co-op Portal

CIS 425 Project - Information Systems (Fall 2025)

A collaborative project for the CIS 425 course designed to streamline the connection between students, employers, and faculty for credit-bearing internships (co-ops). This portal supports creation and management of profiles, internship postings, applications, and department-based approvals.

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/nodejs-18.x-brightgreen.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-15+-blue.svg)](https://www.postgresql.org/)

---

## Table of Contents

- [Quick Start](#quick-start)
- [Setup](#setup)
  - [Clone the Repository](#1-clone-the-repository)
  - [Python Virtual Environment & Dependencies](#2-python-virtual-environment--dependencies)
  - [Docker Setup for the PostgreSQL Database](#3-docker-setup-for-the-postgresql-database)
  - [Node.js & Frontend Setup](#4-nodejs--frontend-setup)
  - [Config File Setup](#5-config-file-setup)
- [Running the Web App](#running-the-web-app)
- [Project Layout](#project-layout-for-reference)
- [Other Notes](#other-notes)
- [Troubleshooting](#troubleshooting)
- [Tech Stack](#tech-stack)
- [About](#about)

---

## Quick Start

**Get the portal up-and-running quickly:**
~~~sh
# 1. Clone the repository
    git clone https://github.com/Hotwheels024568/CECS-Co-op-Portal
    cd CECS-Co-op-Portal

# 2. Set up Python virtual environment (recommended 3.12)
    python -m venv venv
    
    # Linux/macOS:
    source venv/bin/activate
    # Windows:
    venv\Scripts\activate.bat 

    pip install -r min_requirements.txt

# 3. Set up Node.js frontend dependencies
    cd src/frontend
    npm install

# 4. Make shell scripts executable (Linux/macOS only)
    chmod +x ../../scripts/*.sh

# 5. Run backend and frontend in separate terminals
    # Backend
        # Linux/macOS:
        ./scripts/start_backend.sh
        # Windows:
        .\scripts\start_backend.bat

    # Frontend
        # Linux/macOS:
        ./scripts/start_frontend.sh
        # Windows:
        .\scripts\start_frontend.bat
~~~
> The frontend runs at http://localhost:5173 by default.

---

## Setup

### 1. Clone the Repository

Download and navigate to the repository:
~~~sh
git clone https://github.com/Hotwheels024568/CECS-Co-op-Portal
cd CECS-Co-op-Portal
~~~
### 2. Python Virtual Environment & Dependencies

Recommended: Use Python 3.12 for best compatibility.

- **Windows:**
  - Open **Command Prompt** in your repository root folder (**the folder containing `src/` and `README.md`**).
  - Create the virtual environment:
    ~~~bat
    python -m venv venv
    ~~~
  - Edit the activation scripts to set `PYTHONPATH`:
    - Use a program such as Notepad++, VS Code, or Sublime Text (**Notepad may corrupt line endings**).
    - In `venv\Scripts\activate.bat`, add the following at the end of the file (**before** `:END`):
      ~~~bat
      rem Enforces Python to see the src folder and run code as a module
      set PYTHONPATH=%VIRTUAL_ENV%\..\src;%PYTHONPATH%
      ~~~
    - In `venv\Scripts\Activate.ps1`, add the following at the end of the file (**before** the signature block, if any):
      ~~~powershell
      # Enforces Python to see the src folder and run code as a module
      $env:PYTHONPATH = "$env:VIRTUAL_ENV\..\src;$env:PYTHONPATH"
      ~~~
    - Save both files and return to the project root.
  - Activate the virtual environment and install project dependencies:
    ~~~bat
    venv\Scripts\activate.bat
    pip install -r requirements.txt
    ~~~

- **Linux/macOS:**
  - Open a **Terminal** in your repository root folder (**the folder containing `src/` and `README.md`**).
  - Create the virtual environment:
    ~~~sh
    python3 -m venv venv
    ~~~
  - Edit the activation script to set `PYTHONPATH`:
    - Use a program such as Vim, Kate, VS Code, or any other text editor.
    - Here's an example using Vim
      ~~~sh
      vim venv/bin/activate
      ~~~
    - Edit `venv/bin/activate` at the end of the file:
      ~~~sh
      # type i to enter insert mode
      export PYTHONPATH="$VIRTUAL_ENV/../src:$PYTHONPATH"
      # press Esc to exit insert mode
      # type :wq to save text edits
      ~~~
  - Activate the virtual environment and install project dependencies:
    ~~~sh
    source venv/bin/activate
    pip install -r requirements.txt
    ~~~
  - **Recommended**
    - Make helper scripts executable if you want to use them:
      ~~~sh
      chmod +x scripts/*.sh
      ~~~

### 3. Docker Setup for the PostgreSQL Database

- **Docker** must be installed and running on your machine:  
  - [Docker Desktop for Windows/macOS](https://docs.docker.com/get-docker/)  
  - [Docker Engine for Linux](https://docs.docker.com/engine/install/)

> Ensure Docker Desktop/Engine is running before starting backend.

### 4. Node.js & Frontend Setup

- **Windows:**
  - Download and install Node.js LTS from [nodejs.org](https://nodejs.org/en/download)
    > Use the standalone installer, not Docker or Visual Studio. Select all default components, and optionally enable "Tools for Native Modules."
  - Run the following in **Command Prompt** from your repository root:
    ~~~bat
    cd src\frontend
    npm install
    ~~~
- **Linux/macOS:**
  - Make sure Node.js is installed (via your package manager or [nodejs.org](https://nodejs.org/en/download)).
  - Run the following in a **Terminal** from your repository root:
    ~~~sh
    cd src/frontend
    npm install
    ~~~

### 5. Config File Setup

Create a file named `config.ini` in your repository root and insert the following:
~~~ini
[db]
Username = CIS_425_Project
Password = CECS_Co-op_Portal
Database = db
~~~

---

## Running the Web App

### 1. Create two separate terminals (both in your repository root folder)

- The backend (FastAPI) and frontend (React) run separately
  - **Backend** launches the database and API server.
  - **Frontend** launches the development UI server.

### 2. Backend

- **Windows:**
  - Double-click or run `start_backend.bat` in `./scripts`
- **Linux/macOS:** 
  - Run `./scripts/start_backend.sh`

- The scripts execute the following:
    ~~~sh
    # Creates and mounts a PostgreSQL Database Container for the Volume (created on the first run)
    docker compose up -d db
    # Start the Python venv
    source venv/bin/activate    # (Linux/macOS) OR venv\Scripts\activate.bat (Windows)
    # Start the FastAPI Backend using uvicorn
    uvicorn src.backend.main:app --reload --port 8000   # --no-use-colors (Windows)
    ~~~

### 3. Frontend

- On first run, verify `npm install` was performed in [Node.js & Frontend Setup](#4-nodejs--frontend-setup).
- **Windows:**
  - Double-click or run `start_frontend.bat` in `./scripts`
- **Linux/macOS:** 
  - Run `./scripts/start_frontend.sh`
- The script executes the following:
    ~~~sh
    cd src/frontend
    npm run dev
    ~~~

    > The Frontend dev server runs at [http://localhost:5173](http://localhost:5173) by default.

---

## Project Layout (for reference):

~~~sh
repository-root/
├── scripts/                      # Scripts to automate backend, DB, and frontend startup tasks
|   ├── start_backend_no_db.bat       # Starts the backend when the DB is already running (Windows)
|   ├── start_backend_no_db.sh        # Starts the backend when the DB is already running (Linux/Mac)
|   ├── start_backend.bat             # Starts the backend and DB (Windows)
|   ├── start_backend.sh              # Starts the backend and DB (Linux/Mac)
|   ├── start_db_and_venv.bat           # Starts the DB and activates the Python virtual environment (Windows)
|   ├── start_db_and_venv.sh            # Starts the DB and activates the Python virtual environment (Linux/Mac)
|   ├── start_frontend.bat            # Starts the frontend app (Windows)
|   ├── start_frontend.sh             # Starts the frontend app (Linux/Mac)
|   ├── start_venv.bat                  # Activates the Python virtual environment (Windows)
|   └── start_venv.sh                   # Activates the Python virtual environment (Linux/Mac)
|
├── src/                          # Source code and main project files
|   ├── backend/                      # FastAPI backend application
|   |   ├── routers/                      # API endpoint definitions
|   |   |   ├── internships/                  # Endpoints for Internship management
|   |   |   |   ├── __init__.py                   # Package marker
|   |   |   |   ├── applications.py               # Endpoints for internship applications
|   |   |   |   ├── internships.py                # Endpoints for internship management
|   |   |   |   └── summaries.py                  # Endpoints for internship summaries/statistics
|   |   |   ├── profiles/                     # Endpoints for profile management
|   |   |   |   ├── __init__.py                   # Package marker
|   |   |   |   ├── companies.py                  # Endpoints for company profiles
|   |   |   |   ├── employers.py                  # Endpoints for employer profiles
|   |   |   |   ├── faculty.py                    # Endpoints for faculty profiles
|   |   |   |   ├── relationships.py              # Endpoints for browsing profiles
|   |   |   |   └── students.py                   # Endpoints for student profiles
|   |   |   ├── __init__.py                   # Package marker
|   |   |   ├── accounts.py                   # Endpoints for user account actions (change username, password, or user type)
|   |   |   ├── auth.py                       # Endpoints for user authentication (login, registration, etc.)
|   |   |   ├── catalog.py                    # Endpoints for course/major/department catalogs
|   |   |   ├── models.py                     # API-level data models (Pydantic schemas for request/response validation)
|   |   |   ├── notifications.py              # Endpoints for system/user notifications
|   |   |   └── utils.py                      # Utility functions for routers
|   |   ├── __init__.py                   # Package marker
|   |   ├── globals.py                    # Global backend definitions/constants
|   |   └── main.py                       # FastAPI app entrypoint
|   |
|   ├── database/                     # Database management and logic
|   |   ├── __init__.py                   # Package marker
|   |   ├── internship_insertion.py       # Functions for inserting internship-related records
|   |   ├── internship_retrieval.py       # Functions for retrieving internship-related records
|   |   ├── manage.py                     # Asynchronous singleton DB engine/session manager & schema control
|   |   ├── profile_insertion.py          # Functions for inserting profile records
|   |   ├── profile_updating.py           # Functions to update profile records
|   |   ├── record_deletion.py            # Generic deletion logic for DB records
|   |   ├── record_get_or_create.py       # Get-or-create logic for DB records
|   |   ├── record_insertion.py           # Generic insertion logic for DB records
|   |   ├── record_retrieval.py           # Generic retrieval logic for DB records
|   |   ├── record_updating.py            # Generic updating logic for DB records
|   |   ├── schema.py                     # Database table and ORM schema definitions
|   |   └── utils.py                      # Core DB utility functions
|   |
|   ├── frontend/                     # React frontend
|   |   ├── .react_router/...             # React router configuration files
|   |   ├── app/                          # Main React App files/components
|   |   |   ├── routes/...                    # Route-specific React components
|   |   |   ├── components/...                # Shared React components (ex: welcome/)
|   |   |   ├── app.css                       # App-specific styles
|   |   |   ├── root.tsx                      # Main React root app component
|   |   |   └── routes.ts                     # Route configuration
|   |   ├── node_modules/...              # Installed JavaScript dependencies
|   |   ├── public/...                    # Static assets/public files for the React app
|   |   ├── .dockerignore                 # Docker ignore rules for frontend
|   |   ├── .gitignore                    # Git ignore rules for frontend code
|   |   ├── Dockerfile                    # Docker build instructions for frontend
|   |   ├── package-lock.json             # NPM lock file for JS dependencies
|   |   ├── package.json                  # NPM config for frontend
|   |   ├── react-router.config.ts        # React Router configuration
|   |   ├── README.md                     # Frontend README/documentation
|   |   ├── tsconfig.json                 # TypeScript config
|   |   └── vite.config.ts                # Vite build tool config
|   |
|   ├── __init__.py               # Package marker
|   ├── seed_data.json            # DB seed data
|   └── utils_semesters.json      # Semester util functions
|
├── venv/...                  # Python virtual environment
├── .gitattributes            # Git attributes configuration
├── .gitignore                # Top-level git ignore configuration
├── config.ini                # Project-wide configuration file
├── docker-compose.yml        # Docker compose file for PostgreSQL and backend
├── README.md                 # Top-level project documentation
└── requirements.txt          # Python dependencies for backend
~~~

---

## Other Notes

- Only re-run `pip install -r requirements.txt` if `requirements.txt` changes.
- Only re-run `npm install` if `package.json` or `package-lock.json` in `src/frontend` changes.
- Backend and frontend both support live-reload during development.
- For development, passwords are visible in config.ini/docker-compose.yml for simplicity; for production, these should use Docker secrets/env vars.

---

## Troubleshooting

- **Permission errors for `.sh` scripts:**
  - Run `chmod +x start_backend.sh start_frontend.sh` in the repository root.
- **Frontend/backend won't start:**
  - Confirm directory activations (repository root or `src/frontend`)
  - Ensure the Python virtual environment is activated (Not necessary to run the frontend)
  - Node.js and npm are installed and in your PATH (`node -v`, `npm -v`)
- **Unable to get (docker) image 'postgres:15'**
  - Make sure that **Docker Desktop** is running if you see the following error:
    ~~~plaintext
    unable to get image 'postgres:15':
      error during connect: Get "http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/v1.51/images/postgres:15/json":
      open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
    ~~~
- **Install/update errors:**
  - Frontend: Delete `node_modules` and run `npm install`
  - Backend: Run `find . -name '*.pyc' -delete` (Linux)
  - Re-run `pip install -r requirements.txt` or `npm install` if you see module errors.
- **Still stuck?** [Open a GitHub issue](https://github.com/Hotwheels024568/CECS-Co-op-Portal/issues) or see script comments.

---

## Tech Stack

- **Backend:** Python (FastAPI), SQLAlchemy & asyncpg
- **Database:** PostgreSQL (containerized with Docker)
- **Frontend:** React, Node.js & Vite
- **DevOps:** Docker & docker-compose

---

## About

This portal models real internship workflow for students (credit, eligibility), employers (posting/hiring), and faculty (validation, grading). If you have questions or feedback, please [open a GitHub issue](https://github.com/Hotwheels024568/CECS-Co-op-Portal/issues).

Team: *Jacob Sampt & Michael Asman* | *CIS 425, Fall 2025*