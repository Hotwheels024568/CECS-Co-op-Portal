#!/bin/bash
# Start PostgreSQL DB (Docker), activate Python venv, and allow running Python scripts
# Usage: %~nx0 [--help | -h]

set -e

# Save original directory to restore when done
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

# Helper: Show usage
show_help() {
    echo
    echo "Usage: ${0##*/} [--help | -h]"
    echo
    echo "Starts PostgreSQL DB (Docker) and activates Python venv."
    echo
}

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
            show_help
            exit 1
            ;;
    esac
    shift
done

# Track if DB was started
DB_STARTED=0

# Cleanup on exit
cleanup() {
    if [[ "$DB_STARTED" == "1" ]]; then
        echo
        echo "Stopping PostgreSQL container..."
        docker compose down
        echo
    fi
    # Deactivate venv if active
    if [[ -n "$VIRTUAL_ENV" ]]; then
        deactivate
    fi
    cd "$SCRIPT_DIR"
}
trap cleanup EXIT

# Start the database
echo
echo "Starting PostgreSQL Docker container..."
docker compose up -d db
DB_STARTED=1

# Wait for database to be ready
echo
echo "Waiting for PostgreSQL to initialize..."
POSTGRES_USER="CIS_425_Project"
POSTGRES_DB="db"
for i in {1..15}; do
    if docker compose exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
        echo "PostgreSQL is ready."
        break
    fi
    sleep 1
done

if (( i == 15 )); then
    echo "WARNING: PostgreSQL may not be ready yet. Continuing anyway..."
fi

# Activate Python venv
if [[ -f "venv/bin/activate" ]]; then
    source "venv/bin/activate"
else
    echo "ERROR: venv folder not found! Create one with:"
    echo "    python3 -m venv venv"
    exit 1
fi

echo
echo "Environment is ready."
echo "Run your Python scripts as needed."
echo "When finished, type 'deactivate' then 'exit'."
echo

# Enter an interactive shell with the venv activated
bash --rcfile <(echo "PS1='(venv) \w$ '")