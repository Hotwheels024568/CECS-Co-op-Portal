#!/bin/bash
# Activate Python venv in the repository root

# Change directory to the repository root
cd "$(dirname "$0")"/.. || exit 1

# Activate venv in the repository root
if [ -d "venv" ]; then
  source venv/bin/activate
else
  echo "ERROR: venv folder not found! Create with python -m venv venv"
  exit 1
fi

# Open an interactive shell with the venv activated
bash --rcfile <(echo "PS1='(venv) \w\$ '")