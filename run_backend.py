#!/usr/bin/env python3
"""
Backend Runner Script
Runs the SkillNavigator backend from the correct directory with proper path setup
"""

import os
import sys
import subprocess

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

# Change to backend directory
os.chdir(backend_dir)

# Run the FastAPI app using uvicorn
if __name__ == "__main__":
    try:
        # Import and run
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
    except ImportError:
        print("uvicorn not found, trying to run main.py directly...")
        exec(open('main.py').read())
