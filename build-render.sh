#!/bin/bash
# Build script for Render (backend + frontend)
set -e

echo "Installing Python dependencies..."
pip install -r requirements.txt

if command -v npm >/dev/null 2>&1; then
	echo "Installing frontend dependencies..."
	cd frontend
	npm install

	echo "Building frontend..."
	npm run build
	cd ..
else
	echo "npm not found; skipping frontend build (using committed dist assets)"
fi

echo "Build complete - backend and frontend ready"