#!/bin/bash
# Build script for deployment

echo "🏗️ Building SkillNavigator for production..."

# Install frontend dependencies and build
echo "📦 Installing frontend dependencies..."
cd frontend
npm install

echo "🔨 Building frontend..."
npm run build

# Go back to root
cd ..

echo "✅ Build complete! Frontend built to frontend/dist/"
echo "🚀 Backend will serve the built React app from FastAPI"