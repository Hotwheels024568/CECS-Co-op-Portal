#!/bin/bash
# Activate Python venv and run the backend using Uvicorn

# Change directory to the repository root
cd "$(dirname "$0")"/..

# Activate venv in the repository root
if [ -d "venv" ]; then
  source venv/bin/activate
else
  echo "ERROR: venv folder not found! Create with python -m venv venv"
  exit 1
fi

# Start FastAPI/Uvicorn server
uvicorn src.backend.main:app --reload --port 8000
