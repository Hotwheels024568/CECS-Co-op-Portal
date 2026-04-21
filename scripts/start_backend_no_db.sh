#!/bin/bash
# Activate Python venv and runs FastAPI app with uvicorn

# Change directory to the repository root
cd "$(dirname "$0")"/.. || exit 1

# Activate venv in the repository root
if [ -d "venv" ]; then
  source venv/bin/activate
else
  echo "ERROR: venv folder not found! Create with python -m venv venv"
  exit 1
fi

# Start FastAPI/Uvicorn server
uvicorn backend.main:app --reload --port 8000
