#!/usr/bin/env python3
"""
Simple FastAPI server for testing the frontend without complex agent dependencies
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
from typing import Optional
import tempfile
import os
from fastapi import UploadFile, File
# Resume parser import (with error handling)
try:
    from agents.resume_parser_agent import ResumeParserAgent
    HAS_RESUME_PARSER = True
except ImportError as e:
    print(f"Resume parser not available: {e}")
    HAS_RESUME_PARSER = False

app = FastAPI(title="SkillNavigator API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5175", "http://localhost:3000"],
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

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: int):
    """Get a specific job by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = dict(row)
        # Parse JSON fields if they exist
        for field in ['skills', 'benefits']:
            if job.get(field):
                try:
                    job[field] = json.loads(job[field])
                except json.JSONDecodeError:
                    job[field] = []
        
        conn.close()
        return job
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/resume/parse")
async def parse_resume(file: UploadFile = File(...)):
    """Parse uploaded resume file and extract structured information"""
    try:
        # Validate file type
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']
        file_ext = os.path.splitext(file.filename.lower())[1]
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Parse resume
            if not HAS_RESUME_PARSER:
                return {
                    "success": False,
                    "error": "Resume parser not available. Please check server configuration."
                }
            
            parser = ResumeParserAgent()
            parsed_data = parser.parse_resume(temp_file_path, file.filename)
            
            return {
                "success": True,
                "filename": file.filename,
                "parsed_data": parsed_data
            }
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume parsing error: {str(e)}")

@app.post("/api/preferences/save")
async def save_preferences(preferences_data: dict):
    """Save user preferences and parsed resume data"""
    try:
        # For demo purposes, just return success
        # In production, this would save to database
        return {
            "success": True,
            "message": "Preferences saved successfully",
            "data": preferences_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving preferences: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting SkillNavigator Simple API Server...")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🌐 Frontend URL: http://localhost:5175")
    uvicorn.run("simple_main:app", host="0.0.0.0", port=8000, reload=False)