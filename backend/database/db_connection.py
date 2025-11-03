"""
Database Connection and Models
SQLite database setup with SQLAlchemy ORM
"""

import os
import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.pool import StaticPool
import json

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./skillnavigator.db")

# SQLAlchemy setup
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    poolclass=StaticPool if "sqlite" in DATABASE_URL else None,
    echo=os.getenv("DEBUG", "false").lower() == "true"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models
class User(Base):
    """User profile model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Profile data
    resume_path = Column(String, nullable=True)
    skills = Column(Text, nullable=True)  # JSON string
    preferences = Column(Text, nullable=True)  # JSON string
    location = Column(String, nullable=True)
    experience_years = Column(Integer, default=0)
    
    # Relationships
    job_applications = relationship("JobApplication", back_populates="user")
    
    def get_skills(self) -> List[str]:
        """Get skills as list"""
        if self.skills:
            return json.loads(self.skills)
        return []
    
    def set_skills(self, skills: List[str]):
        """Set skills from list"""
        self.skills = json.dumps(skills)
    
    def get_preferences(self) -> dict:
        """Get preferences as dict"""
        if self.preferences:
            return json.loads(self.preferences)
        return {}
    
    def set_preferences(self, preferences: dict):
        """Set preferences from dict"""
        self.preferences = json.dumps(preferences)
    
    @property
    def first_name(self):
        """Backward compatibility property for first_name access"""
        # If someone tries to access first_name, return the first part of name
        if self.name:
            return self.name.split()[0]
        return ""
    
    @property  
    def last_name(self):
        """Backward compatibility property for last_name access"""
        # If someone tries to access last_name, return the last part of name
        if self.name and len(self.name.split()) > 1:
            return " ".join(self.name.split()[1:])
        return ""


class Job(Base):
    """Job listing model"""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)  # ID from job portal
    title = Column(String, nullable=False, index=True)
    company = Column(String, nullable=False, index=True)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    job_type = Column(String, nullable=True)  # full-time, part-time, contract
    experience_level = Column(String, nullable=True)  # entry, mid, senior
    remote_allowed = Column(Boolean, default=False)
    apply_url = Column(String, nullable=True)
    posted_date = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String, nullable=False)  # linkedin, indeed, etc.
    
    # AI scoring
    relevance_score = Column(Float, nullable=True)
    skills_match = Column(Text, nullable=True)  # JSON string of matched skills
    
    # Enhanced AI scoring from JobScoringAgent
    match_score = Column(Float, nullable=True)  # 0-100 scale
    classification = Column(String, nullable=True)  # Excellent/Good/Fair/Poor Fit
    score_breakdown = Column(Text, nullable=True)  # JSON: skills, experience, education scores
    score_explanation = Column(Text, nullable=True)  # Human-readable explanation
    
    # Relationships
    applications = relationship("JobApplication", back_populates="job")
    
    def get_skills_match(self) -> dict:
        """Get skills match as dict"""
        if self.skills_match:
            return json.loads(self.skills_match)
        return {}
    
    def set_skills_match(self, skills_match: dict):
        """Set skills match from dict"""
        self.skills_match = json.dumps(skills_match)


class JobApplication(Base):
    """Job application tracking model"""
    __tablename__ = "job_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    
    # Application details
    applied_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="applied")  # applied, interview, rejected, accepted
    cover_letter = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Auto-application details
    auto_applied = Column(Boolean, default=False)
    application_method = Column(String, nullable=True)  # email, form, api
    
    # Follow-up tracking
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    follow_up_date = Column(DateTime, nullable=True)
    interview_date = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="job_applications")
    job = relationship("Job", back_populates="applications")


class ScrapingLog(Base):
    """Scraping activity log"""
    __tablename__ = "scraping_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)  # linkedin, indeed, etc.
    search_query = Column(String, nullable=False)
    jobs_found = Column(Integer, default=0)
    jobs_saved = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, default="running")  # running, completed, failed
    error_message = Column(Text, nullable=True)


class SystemLog(Base):
    """System activity and agent logs"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, nullable=False)
    action = Column(String, nullable=False)
    message = Column(Text, nullable=True)
    level = Column(String, default="info")  # debug, info, warning, error
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(Text, nullable=True)  # JSON string for additional data
    
    def get_metadata(self) -> dict:
        """Get metadata as dict"""
        if self.metadata_json:
            return json.loads(self.metadata_json)
        return {}
    
    def set_metadata(self, metadata: dict):
        """Set metadata from dict"""
        self.metadata_json = json.dumps(metadata)


class AutoApplySettings(Base):
    """Auto-apply preferences and settings per user"""
    __tablename__ = "auto_apply_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Auto-apply configuration
    enabled = Column(Boolean, default=False)
    min_match_score = Column(Float, default=80.0)  # Minimum match score threshold
    max_applications_per_day = Column(Integer, default=10)
    
    # Method preferences (JSON string with method priorities)
    preferred_methods = Column(Text, nullable=True)  # JSON: ['email', 'http_form', 'form']
    excluded_methods = Column(Text, nullable=True)   # JSON: ['linkedin'] if user doesn't want LinkedIn
    
    # Timing settings
    auto_apply_times = Column(Text, nullable=True)   # JSON: ['09:00', '14:00'] for preferred times
    delay_between_applications = Column(Integer, default=60)  # seconds
    
    # Content customization
    cover_letter_template = Column(Text, nullable=True)
    custom_signature = Column(Text, nullable=True)
    
    # Company and job filtering
    excluded_companies = Column(Text, nullable=True)  # JSON: ['company1', 'company2']
    required_keywords = Column(Text, nullable=True)   # JSON: ['remote', 'python']
    excluded_keywords = Column(Text, nullable=True)   # JSON: ['senior', 'lead']
    
    # Status tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_run = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", backref="auto_apply_settings")
    
    def get_preferred_methods(self) -> List[str]:
        """Get preferred methods as list"""
        if self.preferred_methods:
            return json.loads(self.preferred_methods)
        return ['email', 'http_form', 'form']
    
    def set_preferred_methods(self, methods: List[str]):
        """Set preferred methods from list"""
        self.preferred_methods = json.dumps(methods)
    
    def get_excluded_companies(self) -> List[str]:
        """Get excluded companies as list"""
        if self.excluded_companies:
            return json.loads(self.excluded_companies)
        return []
    
    def set_excluded_companies(self, companies: List[str]):
        """Set excluded companies from list"""
        self.excluded_companies = json.dumps(companies)


class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    async def initialize(self):
        """Initialize database and create tables"""
        try:
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            
            # Create default user if not exists
            await self._create_default_data()
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _create_default_data(self):
        """Create default data for testing"""
        db = self.get_session()
        try:
            # Check if any users exist
            user_count = db.query(User).count()
            if user_count == 0:
                # Create default user
                default_user = User(
                    email="demo@skillnavigator.com",
                    name="Demo User",
                    skills=json.dumps(["Python", "JavaScript", "React", "Machine Learning"]),
                    preferences=json.dumps({
                        "preferred_locations": ["Remote", "San Francisco", "New York"],
                        "job_types": ["full-time", "contract"],
                        "experience_levels": ["entry", "mid"],
                        "salary_min": 60000,
                        "auto_apply": False
                    }),
                    location="San Francisco, CA",
                    experience_years=2
                )
                db.add(default_user)
                db.commit()
                logger.info("Default user created")
        except Exception as e:
            logger.error(f"Failed to create default data: {e}")
            db.rollback()
        finally:
            db.close()
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            db = self.get_session()
            # Simple query to test connection
            db.execute("SELECT 1")
            db.close()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        db = self.get_session()
        try:
            return db.query(User).filter(User.email == email).first()
        finally:
            db.close()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        db = self.get_session()
        try:
            return db.query(User).filter(User.id == user_id).first()
        finally:
            db.close()
    
    async def create_user(self, user_data: dict) -> User:
        """Create new user"""
        db = self.get_session()
        try:
            user = User(**user_data)
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    async def save_jobs(self, jobs: List[dict]) -> List[Job]:
        """Save scraped jobs to database"""
        db = self.get_session()
        saved_jobs = []
        
        try:
            for job_data in jobs:
                # Check if job already exists
                existing_job = db.query(Job).filter(
                    Job.external_id == job_data.get("external_id")
                ).first()
                
                if not existing_job:
                    job = Job(**job_data)
                    db.add(job)
                    saved_jobs.append(job)
            
            db.commit()
            
            # Refresh all saved jobs
            for job in saved_jobs:
                db.refresh(job)
            
            return saved_jobs
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save jobs: {e}")
            raise e
        finally:
            db.close()
    
    async def get_jobs_for_scoring(self, limit: int = 100) -> List[Job]:
        """Get jobs that need scoring"""
        db = self.get_session()
        try:
            return db.query(Job).filter(
                Job.relevance_score.is_(None)
            ).limit(limit).all()
        finally:
            db.close()

    async def get_job_by_id(self, job_id: int) -> Optional[Job]:
        """Get job by ID"""
        db = self.get_session()
        try:
            return db.query(Job).filter(Job.id == job_id).first()
        finally:
            db.close()
    
    async def update_job_scores(self, job_scores: List[dict]):
        """Update job relevance scores"""
        db = self.get_session()
        try:
            for score_data in job_scores:
                job = db.query(Job).filter(Job.id == score_data["job_id"]).first()
                if job:
                    job.relevance_score = score_data["score"]
                    if "skills_match" in score_data:
                        job.set_skills_match(score_data["skills_match"])
            
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update job scores: {e}")
            raise e
        finally:
            db.close()
    
    async def log_system_activity(self, agent_name: str, action: str, message: str, 
                                 level: str = "info", metadata: dict = None):
        """Log system activity"""
        db = self.get_session()
        try:
            log_entry = SystemLog(
                agent_name=agent_name,
                action=action,
                message=message,
                level=level
            )
            if metadata:
                log_entry.set_metadata(metadata)
            
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log system activity: {e}")
        finally:
            db.close()


# Dependency to get database session
def get_db():
    """FastAPI dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database instance
database = Database()


if __name__ == "__main__":
    # Initialize database when run directly
    import asyncio
    
    async def main():
        await database.initialize()
        print("Database initialized successfully!")
    
    asyncio.run(main())
