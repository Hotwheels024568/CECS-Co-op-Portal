#!/bin/bash
# Change directory to the repository root
cd "$(dirname "$0")"/..

# Change to frontend directory and run Vite dev server
cd src/rcp/frontend
npm run dev