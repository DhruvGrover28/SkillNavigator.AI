#!/bin/bash
# Simple Python-only build script for Render

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Build complete - Python dependencies installed"
echo "🚀 Ready to start FastAPI server"