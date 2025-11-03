"""
Jobs API Routes  
Endpoints for job search, scoring, and management
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime
import json

from database.db_connection import get_db, database, Job, JobApplication, User
from agents.simple_supervisor_agent import SimpleSupervisorAgent

router = APIRouter()

# Pydantic models for request/response
class JobSearchRequest(BaseModel):
    keywords: str
    location: Optional[str] = "Remote"
    experience_level: Optional[str] = "entry"
    job_type: Optional[str] = "full-time"
    remote_ok: Optional[bool] = True
    max_jobs: Optional[int] = 50
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None

class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    location: str
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    remote_allowed: bool = False
    apply_url: Optional[str] = None
    posted_date: Optional[datetime] = None
    scraped_at: Optional[datetime] = None
    source: str
    relevance_score: Optional[float] = None
    
    # AI Scoring Fields
    match_score: Optional[float] = None
    classification: Optional[str] = None
    score_breakdown: Optional[Dict] = None
    score_explanation: Optional[str] = None

class ScoredJobResponse(JobResponse):
    relevance_score: float
    skills_match: Dict
    component_scores: Optional[Dict] = None

class BulkApplyRequest(BaseModel):
    job_ids: List[int]
    user_id: int = 1  # Default user for demo

# Dependency to get supervisor agent
async def get_supervisor() -> SimpleSupervisorAgent:
    # This would be injected from the main app
    # For now, create a new instance (not ideal for production)
    supervisor = SimpleSupervisorAgent()
    await supervisor.initialize()
    return supervisor


@router.get("/", response_model=List[JobResponse])
async def get_jobs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    source: Optional[str] = None,
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0),
    job_type: Optional[str] = None,
    experience_level: Optional[str] = None,
    db = Depends(get_db)
):
    """Get jobs with optional filtering"""
    try:
        # Build query filters
        filters = {}
        if source:
            filters['source'] = source
        if job_type:
            filters['job_type'] = job_type
        if experience_level:
            filters['experience_level'] = experience_level
        if min_score is not None:
            filters['min_score'] = min_score
        
        # Query the database with filters
        query = db.query(Job)
        
        # Apply filters
        if source:
            query = query.filter(Job.source == source)
        if job_type:
            query = query.filter(Job.job_type == job_type)
        if experience_level:
            query = query.filter(Job.experience_level == experience_level)
        if min_score is not None:
            query = query.filter(Job.match_score >= min_score)
        
        # Adaptive filtering based on user preferences
        threshold = _get_adaptive_threshold(db)
        query = query.filter(Job.match_score >= threshold)
        
        # Sort by match score in descending order (highest scores first)
        query = query.order_by(Job.match_score.desc())
        
        # Apply pagination
        jobs = query.offset(offset).limit(limit).all()
        
        # Convert to response format with proper score fields
        job_responses = []
        for job in jobs:
            job_data = {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "description": job.description,
                "requirements": job.requirements,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "job_type": job.job_type,
                "experience_level": job.experience_level,
                "remote_allowed": job.remote_allowed if job.remote_allowed is not None else False,
                "apply_url": job.apply_url,
                "posted_date": job.posted_date,
                "scraped_at": job.scraped_at,
                "source": job.source,
                "relevance_score": job.relevance_score,
                "match_score": job.match_score,
                "classification": job.classification,
                "score_breakdown": json.loads(job.score_breakdown) if job.score_breakdown else None,
                "score_explanation": job.score_explanation
            }
            job_responses.append(job_data)
        
        return job_responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")


@router.post("/search")
async def search_jobs(
    search_request: JobSearchRequest,
    supervisor: SimpleSupervisorAgent = Depends(get_supervisor)
):
    """Trigger job search and scraping"""
    try:
        # Convert request to search parameters
        search_params = search_request.dict(exclude_none=True)
        
        # Trigger job search workflow
        result = await supervisor.trigger_job_search(search_params)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Job search failed'))
        
        return {
            "message": "Job search completed successfully",
            "result": result,
            "jobs_found": result.get('total_found', 0),
            "jobs": result.get('jobs', []),
            "search_duration": result.get('search_duration_seconds', 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in job search: {str(e)}")


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db = Depends(get_db)):
    """Get specific job by ID"""
    try:
        # This would query the database for the specific job
        # For now, return sample job
        job = None
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job: {str(e)}")


@router.get("/scored/{user_id}", response_model=List[ScoredJobResponse])
async def get_scored_jobs(
    user_id: int,
    limit: int = Query(20, ge=1, le=100),
    min_score: float = Query(0.5, ge=0.0, le=1.0),
    db = Depends(get_db)
):
    """Get scored jobs for a specific user"""
    try:
        # This would query scored jobs for the user
        # For now, return empty list
        scored_jobs = []
        
        return scored_jobs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching scored jobs: {str(e)}")


@router.post("/score/{user_id}")
async def score_jobs_for_user(
    user_id: int,
    max_jobs: int = Query(100, ge=1, le=500),
    supervisor: SimpleSupervisorAgent = Depends(get_supervisor)
):
    """Trigger job scoring for a specific user"""
    try:
        # Get scoring agent from supervisor
        scoring_agent = supervisor.scoring_agent
        
        # Score jobs for user
        scored_jobs = await scoring_agent.score_jobs(user_id, max_jobs)
        
        return {
            "message": "Job scoring completed successfully",
            "user_id": user_id,
            "jobs_scored": len(scored_jobs),
            "high_scoring_jobs": len([job for job in scored_jobs if job['score'] >= 0.7]),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scoring jobs: {str(e)}")


@router.post("/apply")
async def apply_to_jobs(
    apply_request: BulkApplyRequest,
    supervisor: SimpleSupervisorAgent = Depends(get_supervisor)
):
    """Apply to multiple jobs automatically"""
    try:
        # Get auto-apply agent from supervisor
        autoapply_agent = supervisor.autoapply_agent
        
        # Apply to jobs
        application_results = await autoapply_agent.auto_apply_to_jobs(
            apply_request.user_id, apply_request.job_ids
        )
        
        successful_applications = len([r for r in application_results if r['success']])
        failed_applications = len([r for r in application_results if not r['success']])
        
        return {
            "message": "Bulk application completed",
            "user_id": apply_request.user_id,
            "total_jobs": len(apply_request.job_ids),
            "successful_applications": successful_applications,
            "failed_applications": failed_applications,
            "success_rate": (successful_applications / len(apply_request.job_ids) * 100) if apply_request.job_ids else 0,
            "application_results": application_results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying to jobs: {str(e)}")


@router.get("/recommendations/{user_id}")
async def get_job_recommendations(
    user_id: int,
    limit: int = Query(10, ge=1, le=50),
    db = Depends(get_db)
):
    """Get personalized job recommendations for a user"""
    try:
        # This would get top scored jobs for the user
        # For now, return empty list
        recommendations = []
        
        return {
            "user_id": user_id,
            "recommendations": recommendations,
            "total_count": len(recommendations),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")


@router.get("/stats/summary")
async def get_jobs_summary(db = Depends(get_db)):
    """Get summary statistics about jobs in the system"""
    try:
        # Query database for actual statistics
        total_jobs = db.query(Job).count()
        
        # Jobs added today
        from datetime import date
        today = date.today()
        jobs_today = db.query(Job).filter(
            Job.scraped_at >= today
        ).count()
        
        # Top companies (limit to 5)
        company_counts = db.query(Job.company).distinct().limit(5).all()
        top_companies = [comp[0] for comp in company_counts]
        
        # Top job titles (limit to 5)
        title_counts = db.query(Job.title).distinct().limit(5).all()
        top_job_titles = [title[0] for title in title_counts]
        
        # Source breakdown
        sources = {}
        for source in ['linkedin', 'indeed', 'glassdoor']:
            count = db.query(Job).filter(Job.source == source).count()
            sources[source] = count
        
        # Job type breakdown
        job_types = {}
        for job_type in ['full-time', 'part-time', 'contract', 'internship']:
            count = db.query(Job).filter(Job.job_type == job_type).count()
            job_types[job_type] = count
        
        # Experience level breakdown
        experience_levels = {}
        for level in ['entry', 'mid', 'senior']:
            count = db.query(Job).filter(Job.experience_level == level).count()
            experience_levels[level] = count
        
        # Remote jobs count
        remote_jobs = db.query(Job).filter(Job.remote_allowed == True).count()
        
        # Calculate average match score
        avg_match_score = 0.0
        if total_jobs > 0:
            # Get all match scores that are not null
            match_scores = db.query(Job.match_score).filter(Job.match_score.isnot(None)).all()
            if match_scores:
                scores = [score[0] for score in match_scores if score[0] is not None]
                if scores:
                    avg_match_score = sum(scores) / len(scores)
        
        stats = {
            "total_jobs": total_jobs,
            "jobs_today": jobs_today,
            "avg_match_score": round(avg_match_score, 1),
            "top_companies": top_companies,
            "top_job_titles": top_job_titles,
            "sources": sources,
            "job_types": job_types,
            "experience_levels": experience_levels,
            "remote_jobs": remote_jobs,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting job statistics: {str(e)}")


@router.get("/stats/dashboard")
async def get_dashboard_stats(user_id: int = 1, db = Depends(get_db)):
    """Get dashboard statistics including applications"""
    try:
        # Application statistics
        total_applications = db.query(JobApplication).filter(JobApplication.user_id == user_id).count()
        
        # Status breakdown
        status_counts = {}
        for status in ['applied', 'pending', 'interview', 'rejected', 'accepted']:
            count = db.query(JobApplication).filter(
                JobApplication.user_id == user_id,
                JobApplication.status == status
            ).count()
            status_counts[status] = count
        
        # Calculate rates
        interviews = status_counts.get('interview', 0)
        accepted = status_counts.get('accepted', 0)
        
        interview_rate = (interviews / total_applications * 100) if total_applications > 0 else 0
        success_rate = (accepted / total_applications * 100) if total_applications > 0 else 0
        
        # Recent applications (last 7 days)
        from datetime import date, timedelta
        week_ago = date.today() - timedelta(days=7)
        recent_applications = db.query(JobApplication).filter(
            JobApplication.user_id == user_id,
            JobApplication.applied_at >= week_ago.isoformat()
        ).count()
        
        dashboard_stats = {
            "total_applications": total_applications,
            "pending_reviews": status_counts.get('pending', 0),
            "interviews_scheduled": status_counts.get('interview', 0),
            "success_rate": round(success_rate, 1),
            "applications_this_week": recent_applications,
            "status_breakdown": status_counts,
            "response_rate": round((total_applications - status_counts.get('applied', 0)) / total_applications * 100, 1) if total_applications > 0 else 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return dashboard_stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard statistics: {str(e)}")


@router.delete("/{job_id}")
async def delete_job(job_id: int, db = Depends(get_db)):
    """Delete a specific job"""
    try:
        # This would delete the job from database
        # For now, just return success
        
        return {
            "message": f"Job {job_id} deleted successfully",
            "job_id": job_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting job: {str(e)}")


@router.post("/bulk-delete")
async def bulk_delete_jobs(job_ids: List[int], db = Depends(get_db)):
    """Delete multiple jobs"""
    try:
        # This would delete multiple jobs from database
        # For now, just return success
        
        return {
            "message": f"Deleted {len(job_ids)} jobs successfully",
            "deleted_job_ids": job_ids,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error bulk deleting jobs: {str(e)}")


@router.post("/refresh-scores/{user_id}")
async def refresh_job_scores(
    user_id: int,
    supervisor: SimpleSupervisorAgent = Depends(get_supervisor)
):
    """Refresh job scores for a user (when their profile changes)"""
    try:
        # Get scoring agent from supervisor
        scoring_agent = supervisor.scoring_agent
        
        # Rescore jobs for user
        scored_jobs = await scoring_agent.rescore_jobs_for_user(user_id)
        
        return {
            "message": "Job scores refreshed successfully",
            "user_id": user_id,
            "jobs_rescored": len(scored_jobs),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing job scores: {str(e)}")


@router.get("/similar/{job_id}")
async def get_similar_jobs(
    job_id: int,
    limit: int = Query(5, ge=1, le=20),
    db = Depends(get_db)
):
    """Get jobs similar to a specific job"""
    try:
        # This would find similar jobs using ML/similarity algorithms
        # For now, return empty list
        similar_jobs = []
        
        return {
            "job_id": job_id,
            "similar_jobs": similar_jobs,
            "total_count": len(similar_jobs),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding similar jobs: {str(e)}")


@router.get("/apply-info/{job_id}")
async def get_job_apply_info(job_id: int, db = Depends(get_db)):
    """Get job application information for auto-apply agent"""
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "job_id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "apply_url": job.apply_url,
            "description": job.description,
            "requirements": job.requirements,
            "source": job.source,
            "is_applicable": bool(job.apply_url),  # Whether auto-apply is possible
            "auto_apply_ready": job.apply_url is not None and "remoteok" in (job.source or ""),
            "instructions": {
                "message": "Use the apply_url to visit the original job posting",
                "notes": "Auto-apply agent should navigate to apply_url and follow application process",
                "source_info": f"Job sourced from {job.source}"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting apply info: {str(e)}")


# Auto-apply settings endpoints (must come before parameterized routes)
@router.post("/auto-apply/enable")
async def enable_auto_apply(threshold: float = 80.0, max_per_day: int = 10):
    """Enable automatic job applications for high-scoring jobs"""
    try:
        # Use default user_id for now - this would come from authentication
        user_id = 1
        
        supervisor = await get_supervisor()
        result = await supervisor.configure_auto_apply({
            'enabled': True,
            'threshold': threshold,
            'max_per_day': max_per_day
        })
        
        if result.get('success'):
            return {
                "message": "Auto-apply enabled successfully",
                "threshold": threshold,
                "max_per_day": max_per_day,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('message', 'Failed to enable auto-apply'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enabling auto-apply: {str(e)}")


@router.post("/auto-apply/disable")
async def disable_auto_apply():
    """Disable automatic job applications"""
    try:
        supervisor = await get_supervisor()
        result = await supervisor.configure_auto_apply({'enabled': False})
        
        if result.get('success'):
            return {
                "message": "Auto-apply disabled successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('message', 'Failed to disable auto-apply'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error disabling auto-apply: {str(e)}")


@router.get("/auto-apply/status")
async def get_auto_apply_status():
    """Get current auto-apply settings and status"""
    try:
        supervisor = await get_supervisor()
        return supervisor.get_auto_apply_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting auto-apply status: {str(e)}")


@router.post("/auto-apply/{job_id}")
async def trigger_auto_apply(
    job_id: int, 
    db = Depends(get_db),
    supervisor: SimpleSupervisorAgent = Depends(get_supervisor)
):
    """Endpoint to trigger auto-apply for a specific job"""
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if not job.apply_url:
            raise HTTPException(status_code=400, detail="Job does not have an application URL")
        
        # Use default user_id for now - this would come from authentication
        user_id = 1
        
        # Trigger auto-apply using supervisor
        result = await supervisor.apply_to_job(user_id, job_id)
        
        if result['success']:
            return {
                "message": "Auto-apply completed successfully!",
                "job_id": job.id,
                "job_title": job.title,
                "company": job.company,
                "apply_url": job.apply_url,
                "status": "completed",
                "method": result.get('method', 'auto'),
                "timestamp": result.get('timestamp'),
                "success": True
            }
        else:
            return {
                "message": "Auto-apply failed",
                "job_id": job.id,
                "job_title": job.title,
                "company": job.company,
                "apply_url": job.apply_url,
                "status": "failed",
                "error": result.get('error'),
                "timestamp": result.get('timestamp'),
                "success": False
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering auto-apply: {str(e)}")


@router.post("/auto-apply/check")
async def trigger_auto_apply_check():
    """Manually trigger auto-apply check for high-scoring jobs"""
    try:
        # Use default user_id for now - this would come from authentication
        user_id = 1
        
        supervisor = await get_supervisor()
        result = await supervisor.check_and_auto_apply(user_id)
        
        return {
            "message": "Auto-apply check completed",
            **result
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running auto-apply check: {str(e)}")


@router.get("/auto-apply/analytics")
async def get_auto_apply_analytics(
    days: int = Query(30, ge=1, le=365),
    user_id: int = Query(None, ge=1)
):
    """Get auto-apply analytics and performance metrics"""
    try:
        supervisor = await get_supervisor()
        analytics = await supervisor.autoapply_agent.get_auto_apply_analytics(user_id, days)
        
        return {
            "message": "Auto-apply analytics retrieved successfully",
            "analytics": analytics,
            "timestamp": datetime.utcnow().isoformat()
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting auto-apply analytics: {str(e)}")


# Auto-apply settings endpoints
@router.get("/auto-apply/settings/{user_id}")
async def get_auto_apply_settings(user_id: int, db = Depends(get_db)):
    """Get auto-apply settings for a user"""
    try:
        from database.db_connection import AutoApplySettings
        
        settings = db.query(AutoApplySettings).filter(AutoApplySettings.user_id == user_id).first()
        
        if not settings:
            # Return default settings
            return {
                "user_id": user_id,
                "enabled": False,
                "min_match_score": 80.0,
                "max_applications_per_day": 10,
                "preferred_methods": ['email', 'http_form'],
                "excluded_methods": [],
                "delay_between_applications": 60,
                "excluded_companies": [],
                "message": "Default settings (not saved yet)"
            }
        
        return {
            "user_id": user_id,
            "enabled": settings.enabled,
            "min_match_score": settings.min_match_score,
            "max_applications_per_day": settings.max_applications_per_day,
            "preferred_methods": settings.get_preferred_methods(),
            "excluded_methods": json.loads(settings.excluded_methods) if settings.excluded_methods else [],
            "delay_between_applications": settings.delay_between_applications,
            "excluded_companies": settings.get_excluded_companies(),
            "last_run": settings.last_run.isoformat() if settings.last_run else None,
            "created_at": settings.created_at.isoformat(),
            "updated_at": settings.updated_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting auto-apply settings: {str(e)}")


@router.put("/auto-apply/settings/{user_id}")
async def update_auto_apply_settings(
    user_id: int, 
    settings_data: Dict,
    db = Depends(get_db)
):
    """Update auto-apply settings for a user"""
    try:
        from database.db_connection import AutoApplySettings
        
        settings = db.query(AutoApplySettings).filter(AutoApplySettings.user_id == user_id).first()
        
        if not settings:
            # Create new settings
            settings = AutoApplySettings(user_id=user_id)
            db.add(settings)
        
        # Update settings
        if 'enabled' in settings_data:
            settings.enabled = settings_data['enabled']
        if 'min_match_score' in settings_data:
            settings.min_match_score = float(settings_data['min_match_score'])
        if 'max_applications_per_day' in settings_data:
            settings.max_applications_per_day = int(settings_data['max_applications_per_day'])
        if 'preferred_methods' in settings_data:
            settings.set_preferred_methods(settings_data['preferred_methods'])
        if 'excluded_methods' in settings_data:
            settings.excluded_methods = json.dumps(settings_data['excluded_methods'])
        if 'delay_between_applications' in settings_data:
            settings.delay_between_applications = int(settings_data['delay_between_applications'])
        if 'excluded_companies' in settings_data:
            settings.set_excluded_companies(settings_data['excluded_companies'])
        
        settings.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(settings)
        
        return {
            "message": "Auto-apply settings updated successfully",
            "user_id": user_id,
            "settings": {
                "enabled": settings.enabled,
                "min_match_score": settings.min_match_score,
                "max_applications_per_day": settings.max_applications_per_day,
                "preferred_methods": settings.get_preferred_methods(),
                "excluded_companies": settings.get_excluded_companies()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating auto-apply settings: {str(e)}")


def _get_adaptive_threshold(db) -> float:
    """Get adaptive filtering threshold based on user preferences"""
    try:
        # Check if user has preferences (from resume or manual entry)
        user = db.query(User).filter(
            (User.skills.isnot(None)) | 
            (User.preferences.isnot(None))
        ).first()
        
        if user and (user.skills or user.preferences):
            # User has preferences - temporarily lowered to show some results for demo
            return 20.0
        else:
            # No user preferences - use lower threshold to show more jobs
            return 15.0
            
    except Exception:
        # Default to lower threshold if error
        return 15.0


# WebSocket endpoint for real-time job updates (would be implemented separately)
# @router.websocket("/ws/{user_id}")
# async def websocket_job_updates(websocket: WebSocket, user_id: int):
#     """WebSocket for real-time job updates"""
#     pass
