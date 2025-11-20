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
    source venv/bin/activate  # (Linux/macOS) OR venv\Scripts\activate.bat (Windows)
    pip install -r min_requirements.txt

# 3. Set up Node.js frontend dependencies
    cd src/rcp/frontend
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
    - In `venv\Scripts\activate.bat` (**before** `:END`), add:
      ~~~bat
      rem Enforces Python to see the src folder and run code as a module
      set PYTHONPATH=%VIRTUAL_ENV%\..\src;%PYTHONPATH%
      ~~~
    - In `venv\Scripts\Activate.ps1` **before** the signature block:
      ~~~powershell
      # Enforces Python to see the src folder and run code as a module
      $env:PYTHONPATH = "$env:VIRTUAL_ENV\..\src;$env:PYTHONPATH"
      ~~~
    - Once finished editing, exit your text editor and return to the terminal.
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
    uvicorn src.rcp.backend.main:app --reload --port 8000   # --no-use-colors (Windows)
    ~~~

### 3. Frontend

- On first run, verify `npm install` was performed in [Node.js & Frontend Setup](#4-nodejs--frontend-setup).
- **Windows:**
  - Double-click or run `start_frontend.bat` in `./scripts`
- **Linux/macOS:** 
  - Run `./scripts/start_frontend.sh`
- The script executes the following:
    ~~~sh
    cd src/rcp/frontend
    npm run dev
    ~~~

    > The Frontend dev server runs at [http://localhost:5173](http://localhost:5173) by default.

---

## Project Layout (for reference):

~~~sh
repository-root/
├── scripts/                      # Helper Scripts
|   ├── start_backend_no_db.bat       # Batch script to start the backend when the DB is already running
|   ├── start_backend_no_db.sh        # Shell script to start the backend when the DB is already running
|   ├── start_backend.bat             # Batch script to start the backend and DB
|   ├── start_backend.sh              # Shell script to start the backend and DB
|   ├── start_db_and_venv.bat
|   ├── start_db_and_venv.sh
|   ├── start_frontend.bat            # Batch script to start the frontend
|   ├── start_frontend.sh             # Shell script to start the frontend
|   ├── start_venv.bat
|   └── start_venv.sh
|
├── src/                          # Project files
|   ├── backend/                      # FastAPI backend
|   |   ├── routers/
|   |   |   ├── internships/
|   |   |   |   ├── __init__.py
|   |   |   |   ├── applications.py
|   |   |   |   ├── internships.py
|   |   |   |   └── summaries.py
|   |   |   ├── profiles/
|   |   |   |   ├── __init__.py
|   |   |   |   ├── companies.py
|   |   |   |   ├── employers.py
|   |   |   |   ├── faculty.py
|   |   |   |   └── students.py
|   |   |   ├── references/             # Maybe condensed into one file (db query to json)
|   |   |   |   ├── __init__.py
|   |   |   |   ├── addresses.py
|   |   |   |   ├── departments.py
|   |   |   |   ├── majors.py
|   |   |   |   └── skills.py
|   |   |   ├── __init__.py
|   |   |   ├── accounts.py
|   |   |   ├── auth.py
|   |   |   ├── notifications.py
|   |   |   └── utils.py
|   |   ├── __init__.py
|   |   ├── globals.py
|   |   └── main.py
|   |
|   ├── database/                     # Database management
|   |   ├── __init__.py
|   |   ├── functions.py                  # Core utility functions for executing and retrieving results
|   |   ├── internship_insertion.py
|   |   ├── internship_retrieval.py
|   |   ├── manage.py                     # Asynchronous singleton manager for database engine, sessions, and schema control.
|   |   ├── profile_insertion.py
|   |   ├── profile_updating.py
|   |   ├── record_deletion.py
|   |   ├── record_get_or_create.py
|   |   ├── record_insertion.py
|   |   ├── record_retrieval.py
|   |   ├── record_updating.py
|   |   └── schema.py                     # Database schema
|   |
|   ├── frontend/                     # React frontend
|   |   ├── .react_router/...
|   |   ├── app/                          # React App (main) files
|   |   |   ├── routes/...
|   |   |   ├── components/...                # currently welcome/
|   |   |   ├── app.css
|   |   |   ├── root.tsx
|   |   |   └── routes.ts
|   |   ├── node_modules/...              # Library (module) files
|   |   ├── public/...                    # App assets
|   |   ├── .dockerignore
|   |   ├── .gitignore                        # React specific ignored files for git
|   |   ├── Dockerfile
|   |   ├── package-lock.json
|   |   ├── package.json
|   |   ├── react-router.config.ts
|   |   ├── README.md
|   |   ├── tsconfig.json
|   |   └── vite.config.ts
|   |
|   ├── utils/                        # General utils
|   |   ├── __init__.py
|   |   └── academics.py
|   └── __init__.py                     # Python package recognition & directory documentation
|
├── venv/                         # Python venv (created)
├── .gitattributes
├── .gitignore
├── config.ini                    # Config file (created)
├── docker-compose.yml            # Docker config for PostgreSQL
├── README.md                     # This file
└── requirements.txt              # Python venv required libraries
~~~

---

## Other Notes

- Only re-run `pip install -r requirements.txt` if `requirements.txt` changes.
- Only re-run `npm install` if `package.json` or `package-lock.json` in `src/rcp/frontend` changes.
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