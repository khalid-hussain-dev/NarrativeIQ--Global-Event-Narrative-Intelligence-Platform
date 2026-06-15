#!/usr/bin/env bash
# Exit on error
set -o errexit

echo ">>> Building NarrativeIQ Frontend and Backend for Render <<<"

echo "1. Installing backend dependencies..."
cd backend
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn uvicorn
cd ..

echo "2. Building frontend static export..."
cd frontend
npm install
npm run build
cd ..

echo ">>> Build completed successfully! <<<"
