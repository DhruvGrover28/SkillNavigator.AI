#!/usr/bin/env python3
"""
Minimal FastAPI server for testing
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
from typing import Optional

app = FastAPI(title="SkillNavigator API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('skill_navigator.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
async def root():
    return {"message": "SkillNavigator API is running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.get("/api/jobs")
async def get_jobs(limit: Optional[int] = 10, offset: Optional[int] = 0):
    """Get jobs with pagination"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total = cursor.fetchone()[0]
        
        # Get jobs with pagination
        cursor.execute("""
            SELECT * FROM jobs 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        jobs = []
        for row in cursor.fetchall():
            job = dict(row)
            # Parse JSON fields if they exist
            for field in ['skills', 'benefits']:
                if job.get(field):
                    try:
                        job[field] = json.loads(job[field])
                    except json.JSONDecodeError:
                        job[field] = []
            jobs.append(job)
        
        conn.close()
        
        return {
            "jobs": jobs,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/resume/parse")
async def parse_resume_demo():
    """Demo resume parser endpoint"""
    # Return demo parsed data for testing
    return {
        "success": True,
        "filename": "demo_resume.txt",
        "parsed_data": {
            "success": True,
            "personal_info": {
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe"
            },
            "contact_info": {
                "email": "john.doe@email.com",
                "phone": "(555) 123-4567",
                "linkedin": "https://linkedin.com/in/johndoe"
            },
            "skills": ["JavaScript", "Python", "React", "Node.js", "SQL", "Git"],
            "experience": [
                {
                    "title": "Software Engineer",
                    "company": "Tech Corp",
                    "duration": "2021 - Present"
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Science Computer Science",
                    "institution": "University of Technology",
                    "year": "2020"
                }
            ]
        }
    }

@app.post("/api/preferences/save")
async def save_preferences(preferences_data: dict):
    """Save user preferences and parsed resume data"""
    try:
        # For demo purposes, just return success
        return {
            "success": True,
            "message": "Preferences saved successfully",
            "data": preferences_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving preferences: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting SkillNavigator Demo API Server...")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🌐 Frontend URL: http://localhost:5176")
    uvicorn.run("demo_server:app", host="0.0.0.0", port=8000, reload=False)