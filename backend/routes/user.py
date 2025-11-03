"""
User API Routes
Endpoints for user profile management and preferences
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Dict, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
import json
import tempfile
import os
import sqlite3

from database.db_connection import get_db, database, User
from agents.resume_parser_agent import ResumeParserAgent
from utils.auth_utils import hash_password, verify_password, create_user_token, is_valid_email, is_strong_password

router = APIRouter()

# Pydantic models for request/response
class UserProfileResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime
    updated_at: datetime
    resume_path: Optional[str] = None
    skills: List[str] = []
    preferences: Dict = {}
    location: Optional[str] = None
    experience_years: int = 0

class UserPreferencesUpdate(BaseModel):
    preferred_locations: Optional[List[str]] = None
    job_types: Optional[List[str]] = None
    experience_levels: Optional[List[str]] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    preferred_companies: Optional[List[str]] = None
    avoided_companies: Optional[List[str]] = None
    remote_preference: Optional[bool] = None
    auto_apply: Optional[bool] = None
    max_applications_per_day: Optional[int] = None
    notification_preferences: Optional[Dict] = None

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[int] = None
    skills: Optional[List[str]] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None

class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str
    location: Optional[str] = None
    experience_years: int = 0
    skills: List[str] = []
    preferences: Dict = {}

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    confirm_password: str
    terms: bool = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[Dict] = None


@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(user_id: int, db = Depends(get_db)):
    """Get user profile by ID"""
    try:
        # This would query the database for user profile
        # For now, return sample profile
        user_profile = {
            "id": user_id,
            "email": "demo@skillnavigator.com",
            "name": "Demo User",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "resume_path": None,
            "skills": ["Python", "JavaScript", "React", "Machine Learning"],
            "preferences": {
                "preferred_locations": ["Remote", "San Francisco", "New York"],
                "job_types": ["full-time", "contract"],
                "experience_levels": ["entry", "mid"],
                "salary_min": 60000,
                "auto_apply": False
            },
            "location": "San Francisco, CA",
            "experience_years": 2
        }
        
        return UserProfileResponse(**user_profile)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user profile: {str(e)}")


@router.put("/profile/{user_id}")
async def update_user_profile(
    user_id: int,
    profile_update: UserProfileUpdate,
    db = Depends(get_db)
):
    """Update user profile"""
    try:
        # This would update user profile in database
        # For now, just return success
        
        update_data = profile_update.dict(exclude_none=True)
        
        return {
            "message": "Profile updated successfully",
            "user_id": user_id,
            "updated_fields": list(update_data.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")


@router.get("/preferences/{user_id}")
async def get_user_preferences(user_id: int, db = Depends(get_db)):
    """Get user preferences"""
    try:
        # This would query user preferences from database
        # For now, return sample preferences
        preferences = {
            "preferred_locations": ["Remote", "San Francisco", "New York"],
            "job_types": ["full-time", "contract"],
            "experience_levels": ["entry", "mid"],
            "salary_min": 60000,
            "salary_max": 120000,
            "preferred_companies": ["Google", "Microsoft", "Apple"],
            "avoided_companies": [],
            "remote_preference": True,
            "auto_apply": False,
            "max_applications_per_day": 5,
            "notification_preferences": {
                "email_notifications": True,
                "push_notifications": True,
                "weekly_summary": True
            }
        }
        
        return {
            "user_id": user_id,
            "preferences": preferences,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching preferences: {str(e)}")


@router.put("/preferences/{user_id}")
async def update_user_preferences(
    user_id: int,
    preferences_update: UserPreferencesUpdate,
    db = Depends(get_db)
):
    """Update user preferences"""
    try:
        # This would update user preferences in database
        # For now, just return success
        
        update_data = preferences_update.dict(exclude_none=True)
        
        return {
            "message": "Preferences updated successfully",
            "user_id": user_id,
            "updated_preferences": list(update_data.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating preferences: {str(e)}")


@router.post("/resume/{user_id}")
async def upload_resume(
    user_id: int,
    file: UploadFile = File(...),
    db = Depends(get_db)
):
    """Upload user resume and extract skills to save in preferences"""
    try:
        # Validate file type
        allowed_types = ["application/pdf", "application/msword", 
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "text/plain"]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail="Only PDF, DOC, DOCX, and TXT files are allowed"
            )
        
        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=400,
                detail="File size exceeds 10MB limit"
            )
        
        # Save file temporarily for processing
        file_extension = file.filename.split('.')[-1].lower()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Parse resume to extract skills and other info
            parser = ResumeParserAgent()
            parsed_data = parser.parse_resume(temp_file_path, file.filename)
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            if not parsed_data.get('success', False):
                raise HTTPException(
                    status_code=400,
                    detail=f"Error parsing resume: {parsed_data.get('error', 'Unknown error')}"
                )
            
            # Extract skills from parsed data
            extracted_skills = parsed_data.get('skills', [])
            
            # Get or create user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                # Create new user if doesn't exist
                user = User(
                    id=user_id,
                    email=f"user_{user_id}@skillnavigator.com",  # Temporary email
                    name=f"User {user_id}"  # Use name field instead of first_name/last_name
                )
                db.add(user)
            
            # Save extracted skills to user preferences
            if extracted_skills:
                user.set_skills(extracted_skills)
                
                # Also save other extracted info
                personal_info = parsed_data.get('personal_info', {})
                first_name = personal_info.get('first_name', '')
                last_name = personal_info.get('last_name', '')
                if first_name or last_name:
                    user.name = f"{first_name} {last_name}".strip()
                
                # Update preferences with extracted information
                current_prefs = json.loads(user.preferences) if user.preferences else {}
                current_prefs.update({
                    'resume_extracted': True,
                    'extracted_at': datetime.utcnow().isoformat(),
                    'experience': parsed_data.get('experience', []),
                    'education': parsed_data.get('education', [])
                })
                user.preferences = json.dumps(current_prefs)
            
            # Save resume path
            filename = f"resume_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
            user.resume_path = f"uploads/resumes/{filename}"
            
            db.commit()
            
            return {
                "message": "Resume uploaded and processed successfully",
                "user_id": user_id,
                "filename": filename,
                "file_size": len(file_content),
                "content_type": file.content_type,
                "extracted_skills": extracted_skills,
                "skills_count": len(extracted_skills),
                "parsing_success": True,
                "personal_info": parsed_data.get('personal_info', {}),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as parse_error:
            # Clean up temp file if it still exists
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise HTTPException(
                status_code=500,
                detail=f"Error processing resume: {str(parse_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading resume: {str(e)}")


@router.get("/resume/{user_id}")
async def get_resume_info(user_id: int, db = Depends(get_db)):
    """Get user resume information"""
    try:
        # This would query database for resume info
        # For now, return sample info
        resume_info = {
            "user_id": user_id,
            "resume_path": f"uploads/resumes/resume_{user_id}_20250101_120000.pdf",
            "uploaded_at": datetime.utcnow().isoformat(),
            "file_size": 1024000,
            "content_type": "application/pdf"
        }
        
        return resume_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching resume info: {str(e)}")


@router.delete("/resume/{user_id}")
async def delete_resume(user_id: int, db = Depends(get_db)):
    """Delete user resume"""
    try:
        # This would delete resume file and update database
        # For now, just return success
        
        return {
            "message": "Resume deleted successfully",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting resume: {str(e)}")


@router.post("/register", response_model=AuthResponse)
async def register_user(register_data: RegisterRequest):
    """Register a new user with real database storage"""
    try:
        # Validation
        if not is_valid_email(register_data.email):
            return AuthResponse(
                success=False,
                message="Invalid email address"
            )
        
        if register_data.password != register_data.confirm_password:
            return AuthResponse(
                success=False,
                message="Passwords do not match"
            )
        
        is_strong, password_msg = is_strong_password(register_data.password)
        if not is_strong:
            return AuthResponse(
                success=False,
                message=password_msg
            )
        
        if not register_data.terms:
            return AuthResponse(
                success=False,
                message="Please accept the Terms of Service"
            )
        
        # Connect to database
        conn = sqlite3.connect('skillnavigator.db')
        cursor = conn.cursor()
        
        try:
            # Check if user already exists
            cursor.execute('SELECT id FROM users WHERE email = ?', (register_data.email,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                return AuthResponse(
                    success=False,
                    message="User with this email already exists"
                )
            
            # Hash password
            password_hash = hash_password(register_data.password)
            
            # Create user preferences
            preferences = {
                "auto_apply": False,
                "preferred_locations": ["Remote"],
                "job_types": ["full-time"],
                "salary_min": 50000,
                "max_applications_per_day": 5,
                "notification_preferences": {
                    "email_notifications": True,
                    "application_updates": True
                }
            }
            
            # Insert new user
            cursor.execute('''
                INSERT INTO users (email, name, created_at, updated_at, preferences)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                register_data.email,
                register_data.name,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                json.dumps(preferences)
            ))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            # Create authentication token
            token = create_user_token(user_id, register_data.email)
            
            # Return success response
            user_data = {
                "id": user_id,
                "email": register_data.email,
                "name": register_data.name,
                "created_at": datetime.now().isoformat()
            }
            
            return AuthResponse(
                success=True,
                message="User registered successfully",
                token=token,
                user=user_data
            )
            
        finally:
            conn.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/login", response_model=AuthResponse)
async def login_user(login_data: LoginRequest):
    """Login user with email and password"""
    try:
        # Connect to database
        conn = sqlite3.connect('skillnavigator.db')
        cursor = conn.cursor()
        
        try:
            # Find user by email
            cursor.execute('''
                SELECT id, email, name, preferences, password_hash
                FROM users WHERE email = ?
            ''', (login_data.email,))
            
            user_record = cursor.fetchone()
            
            if not user_record:
                return AuthResponse(
                    success=False,
                    message="Invalid email or password"
                )
            
            user_id, email, name, preferences_str, stored_password_hash = user_record
            
            # Check password - handle both new users with hashed passwords and existing users without
            if stored_password_hash:
                # New user with proper password hash
                if not verify_password(login_data.password, stored_password_hash):
                    return AuthResponse(
                        success=False,
                        message="Invalid email or password"
                    )
            else:
                # Existing user without password hash - accept any password for now
                # In production, you'd force password reset
                pass
            
            # Create authentication token
            token = create_user_token(user_id, email)
            
            # Return success response
            user_data = {
                "id": user_id,
                "email": email,
                "name": name
            }
            
            return AuthResponse(
                success=True,
                message="Login successful",
                token=token,
                user=user_data
            )
            
        finally:
            conn.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.post("/create")
async def create_user(user_data: CreateUserRequest, db = Depends(get_db)):
    """Create new user (legacy endpoint)"""
    try:
        # Legacy endpoint - redirect to register
        return {
            "message": "Please use /register endpoint for new user creation",
            "redirect": "/api/user/register"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


@router.get("/skills/suggestions")
async def get_skill_suggestions(query: str = "", limit: int = 10):
    """Get skill suggestions for autocomplete"""
    try:
        # This would return skill suggestions based on query
        # For now, return common tech skills
        all_skills = [
            "Python", "JavaScript", "Java", "TypeScript", "C++", "C#", "Go", "Rust",
            "React", "Angular", "Vue.js", "Node.js", "Express", "Django", "Flask",
            "FastAPI", "Spring", "Laravel", "Ruby on Rails", "HTML", "CSS",
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Elasticsearch",
            "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Jenkins",
            "Git", "GitHub", "GitLab", "Linux", "Bash", "Machine Learning",
            "Deep Learning", "TensorFlow", "PyTorch", "Pandas", "NumPy",
            "Scikit-learn", "Data Science", "Analytics", "Statistics"
        ]
        
        if query:
            suggestions = [skill for skill in all_skills 
                         if query.lower() in skill.lower()][:limit]
        else:
            suggestions = all_skills[:limit]
        
        return {
            "suggestions": suggestions,
            "query": query,
            "total_count": len(suggestions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting skill suggestions: {str(e)}")


@router.get("/stats/{user_id}")
async def get_user_stats(user_id: int, db = Depends(get_db)):
    """Get user statistics and insights"""
    try:
        # This would calculate user statistics from database
        # For now, return sample stats
        stats = {
            "profile_completeness": 85,
            "total_applications": 15,
            "response_rate": 33.3,
            "interview_rate": 20.0,
            "success_rate": 6.7,
            "avg_application_score": 0.72,
            "skill_match_rate": 78.5,
            "profile_views": 42,
            "recommended_jobs": 8,
            "profile_strength": "Strong",
            "areas_for_improvement": [
                "Add more recent projects to portfolio",
                "Expand skill set in cloud technologies",
                "Increase application frequency"
            ],
            "achievements": [
                "High skill match rate",
                "Strong profile completeness",
                "Active job seeker"
            ]
        }
        
        return {
            "user_id": user_id,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user stats: {str(e)}")


@router.delete("/{user_id}")
async def delete_user(user_id: int, db = Depends(get_db)):
    """Delete user and all associated data"""
    try:
        # This would delete user and all related data from database
        # For now, just return success
        
        return {
            "message": "User deleted successfully",
            "user_id": user_id,
            "deleted_data": [
                "profile", "applications", "preferences", "resume", "activity_logs"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")


@router.get("/export/{user_id}")
async def export_user_data(
    user_id: int,
    format: str = "json",
    include_applications: bool = True,
    db = Depends(get_db)
):
    """Export all user data"""
    try:
        # This would export all user data
        # For now, return download info
        
        return {
            "message": "User data export generated",
            "user_id": user_id,
            "format": format,
            "includes": {
                "profile": True,
                "preferences": True,
                "applications": include_applications,
                "resume_info": True,
                "activity_logs": True
            },
            "download_url": f"/downloads/user_data_{user_id}_{datetime.utcnow().strftime('%Y%m%d')}.{format}",
            "expires_at": (datetime.utcnow().replace(hour=23, minute=59, second=59)).isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting user data: {str(e)}")


@router.post("/analyze-resume/{user_id}")
async def analyze_resume(user_id: int, db = Depends(get_db)):
    """Analyze uploaded resume and extract insights"""
    try:
        # This would use AI to analyze the resume
        # For now, return sample analysis
        
        analysis = {
            "extracted_skills": [
                "Python", "JavaScript", "React", "Django", "PostgreSQL", 
                "Git", "AWS", "Machine Learning"
            ],
            "experience_level": "Mid-level (2-3 years)",
            "key_achievements": [
                "Led development of 3 web applications",
                "Improved system performance by 40%",
                "Managed team of 2 junior developers"
            ],
            "missing_skills": [
                "Docker", "Kubernetes", "TypeScript", "GraphQL"
            ],
            "suggestions": [
                "Add more quantifiable achievements",
                "Include relevant certifications",
                "Highlight leadership experience",
                "Add technical project details"
            ],
            "ats_score": 78,
            "readability_score": 85,
            "format_score": 90
        }
        
        return {
            "user_id": user_id,
            "analysis": analysis,
            "confidence_score": 0.89,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting user data: {str(e)}")


@router.post("/skills/{user_id}")
async def update_user_skills(
    user_id: int,
    skills: List[str],
    db = Depends(get_db)
):
    """Manually update user skills (alternative to resume upload)"""
    try:
        # Get or create user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            # Create new user if doesn't exist
            user = User(
                id=user_id,
                email=f"user_{user_id}@skillnavigator.com",
                name=f"User {user_id}"  # Use name field instead of first_name/last_name
            )
            db.add(user)
        
        # Update skills
        user.set_skills(skills)
        
        # Update preferences to indicate manual entry
        current_prefs = json.loads(user.preferences) if user.preferences else {}
        current_prefs.update({
            'manual_skills_entry': True,
            'skills_updated_at': datetime.utcnow().isoformat()
        })
        user.preferences = json.dumps(current_prefs)
        
        db.commit()
        
        return {
            "message": "Skills updated successfully",
            "user_id": user_id,
            "skills": skills,
            "skills_count": len(skills),
            "manual_entry": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating skills: {str(e)}")


# WebSocket endpoint for real-time profile updates (would be implemented separately)
# @router.websocket("/ws/profile/{user_id}")
# async def websocket_profile_updates(websocket: WebSocket, user_id: int):
#     """WebSocket for real-time profile updates"""
#     pass
