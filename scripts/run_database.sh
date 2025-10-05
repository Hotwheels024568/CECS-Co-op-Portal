#!/usr/bin/env bash
# Start PostgreSQL (Docker), activate Python venv, start FastAPI/Uvicorn

set -e

show_help() {
  echo
  echo "Usage: $(basename "$0") [--help|-h]"
  echo
  echo "Starts PostgreSQL (db in docker-compose) and activates Python venv"
  echo
  exit 0
}

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      show_help
      ;;
    *)
      echo "Unknown argument: $1"
      show_help
      ;;
  esac
done

# Change to repo root (folder above this script)
cd "$(dirname "$0")/.."

# POSTGRES_USER should match docker-compose.yml
POSTGRES_USER="CIS_425_Project"   # <-- Set to the value you use in docker-compose.yml
POSTGRES_DB="db"           # <-- Optional: set to your db name

# Clean up on exit
cleanup() {
  echo "Stopping Docker Compose containers..."
  docker compose down
}
trap cleanup EXIT

# Start PostgreSQL container
docker compose up -d db

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to initialize..."
for i in {1..15}; do
  if docker compose exec -T db pg_isready -U "$POSTGRES_USER" >/dev/null 2>&1; then
    echo "PostgreSQL is ready!"
    break
  fi
  sleep 1
done

# Activate Python virtual environment
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
else
  echo "ERROR: venv folder not found! Create with: python -m venv venv"
  exit 1
fi

# When server exits, cleanup runs automatically by trap above.