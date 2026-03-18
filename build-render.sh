#!/bin/bash
# Build script for Render (backend + frontend)
set -e

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Installing frontend dependencies..."
cd frontend
npm install

echo "Building frontend..."
npm run build
cd ..

echo "Build complete - backend and frontend ready"