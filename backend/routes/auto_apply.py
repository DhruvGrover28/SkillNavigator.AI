"""
Auto Apply Routes - Real Email Application System
Handles automated job applications with real SMTP email sending
"""

import logging
from typing import List, Dict
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import json
import base64

from agents.autoapply_agent import AutoApplyAgent
from middleware.auth_middleware import get_current_user, get_user_id
from database.db_connection import get_db, User, Job, JobApplication

logger = logging.getLogger(__name__)

router = APIRouter()


class AutoApplyRequest(BaseModel):
    job_ids: List[int]


class AutoApplyResponse(BaseModel):
    success: bool
    applications_sent: int
    total_jobs: int
    results: List[Dict]
    message: str


class EmailTestRequest(BaseModel):
    recipient_email: str


def get_user_profile(db, user_id: int = 1) -> Dict:
    """Get user profile with decoded email credentials"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")

    preferences = user.get_preferences()

    # Decode password
    encoded_password = preferences.get('email_password')
    if not encoded_password:
        raise HTTPException(
            status_code=400,
            detail="Email credentials not configured. Please set up SMTP settings."
        )

    decoded_password = base64.b64decode(encoded_password.encode()).decode()

    return {
        'name': user.name,
        'email': user.email,
        'resume_path': user.resume_path,
        'target_position': 'Software Developer',
        'phone': '+1-555-0123',
        'smtp_host': 'smtp.gmail.com',
        'smtp_port': '587',
        'email_password': decoded_password
    }


@router.post("/apply", response_model=AutoApplyResponse)
async def auto_apply_to_jobs(
    request: AutoApplyRequest,
    user_id: int = Depends(get_user_id),
    db = Depends(get_db)
):
    """
    Apply to multiple jobs automatically using real email sending
    Requires authentication - user_id extracted from JWT token
    """
    try:
        logger.info(f"Starting auto-apply for user {user_id} to {len(request.job_ids)} jobs")
        
        # Get user profile
        user_profile = get_user_profile(db, user_id)
        
        # Initialize agent
        agent = AutoApplyAgent()
        
        # Apply to jobs
        results = await agent.auto_apply_to_jobs(user_id, request.job_ids)
        
        # Count successes
        successful_applications = sum(1 for result in results if result.get('success', False))
        
        logger.info(f"Auto-apply completed: {successful_applications}/{len(results)} successful")
        
        return AutoApplyResponse(
            success=True,
            applications_sent=successful_applications,
            total_jobs=len(request.job_ids),
            results=results,
            message=f"Applied to {successful_applications} out of {len(request.job_ids)} jobs successfully"
        )
        
    except Exception as e:
        logger.error(f"Auto-apply failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Auto-apply failed: {str(e)}")


@router.get("/email-jobs")
async def get_email_jobs(db = Depends(get_db)):
    """
    Get all jobs that can be applied to via email
    """
    try:
        jobs = []
        results = (
            db.query(Job)
            .filter(Job.apply_url.like("mailto:%"))
            .order_by(Job.id.desc())
            .limit(20)
            .all()
        )

        for job in results:
            description = job.description
            if description and len(description) > 200:
                description = description[:200] + "..."
            jobs.append({
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'apply_url': job.apply_url,
                'description': description,
                'salary_min': job.salary_min,
                'salary_max': job.salary_max
            })
        
        return {
            'success': True,
            'jobs': jobs,
            'count': len(jobs)
        }
        
    except Exception as e:
        logger.error(f"Failed to get email jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get email jobs: {str(e)}")


@router.post("/test-email")
async def test_email_connection(
    request: EmailTestRequest,
    user_id: int = Depends(get_user_id),
    db = Depends(get_db)
):
    """
    Test email configuration by sending a test email
    Requires authentication - user_id extracted from JWT token
    """
    try:
        # Get user profile
        user_profile = get_user_profile(db, user_id)
        
        # Initialize agent
        agent = AutoApplyAgent()
        
        # Create a mock job for testing
        class MockJob:
            def __init__(self):
                self.id = 999
                self.title = "Email Configuration Test"
                self.company = "SkillNavigator"
                self.apply_url = f"mailto:{request.recipient_email}"
        
        mock_job = MockJob()
        test_message = """This is a test email from your SkillNavigator auto-apply system.

If you received this email, your SMTP configuration is working correctly!

Best regards,
SkillNavigator Auto-Apply System"""
        
        # Send test email
        result = await agent._apply_via_email(user_profile, mock_job, test_message)
        
        if result.get('success'):
            return {
                'success': True,
                'message': f"Test email sent successfully to {request.recipient_email}",
                'details': result
            }
        else:
            return {
                'success': False,
                'message': f"Test email failed: {result.get('error', 'Unknown error')}",
                'details': result
            }
        
    except Exception as e:
        logger.error(f"Email test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email test failed: {str(e)}")


@router.get("/stats")
async def get_auto_apply_stats(db = Depends(get_db)):
    """
    Get auto-apply statistics
    """
    try:
        total_email_jobs = db.query(Job).filter(Job.apply_url.like("mailto:%")).count()

        total_email_applications = (
            db.query(JobApplication)
            .filter(JobApplication.application_method == "email")
            .count()
        )

        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        recent_applications = (
            db.query(JobApplication)
            .filter(
                JobApplication.application_method == "email",
                JobApplication.status == "sent",
                JobApplication.applied_at >= recent_cutoff
            )
            .count()
        )
        
        return {
            'success': True,
            'stats': {
                'total_email_jobs': total_email_jobs,
                'total_email_applications': total_email_applications,
                'recent_applications_7_days': recent_applications,
                'email_enabled': True
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/health")
async def health_check(user_id: int = Depends(get_user_id), db = Depends(get_db)):
    """
    Health check for auto-apply system
    Requires authentication - user_id extracted from JWT token
    """
    try:
        # Check if user profile and email are configured
        user_profile = get_user_profile(db, user_id)
        
        return {
            'success': True,
            'status': 'healthy',
            'email_configured': bool(user_profile.get('email_password')),
            'user_email': user_profile.get('email'),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }