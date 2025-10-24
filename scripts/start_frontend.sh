#!/bin/bash
# Change directory to the repository root
cd "$(dirname "$0")"/.. || exit 1

# Change to frontend directory and run Vite dev server
cd src/frontend
npm run dev