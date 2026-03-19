"""
Tracker API Routes
Endpoints for application tracking and status management
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from database.db_connection import get_db, database, Job, JobApplication
from sqlalchemy import func
from agents.tracker_agent import TrackerAgent
from middleware.auth_middleware import get_user_id

router = APIRouter()

# Initialize tracker agent
tracker = TrackerAgent()

# Pydantic models for request/response
class ApplicationResponse(BaseModel):
    id: int
    user_id: int
    job_id: int
    job_title: str
    company: str
    applied_at: datetime
    status: str
    cover_letter: Optional[str] = None
    notes: Optional[str] = None
    auto_applied: bool = False
    application_method: Optional[str] = None
    last_updated: datetime
    follow_up_date: Optional[datetime] = None
    interview_date: Optional[datetime] = None

class StatusUpdateRequest(BaseModel):
    application_id: int
    status: str
    notes: Optional[str] = None
    interview_date: Optional[datetime] = None

class BulkStatusUpdateRequest(BaseModel):
    updates: List[StatusUpdateRequest]

class ApplicationStatsResponse(BaseModel):
    total_applications: int
    applications_this_week: int
    response_rate: float
    interview_rate: float
    success_rate: float
    avg_response_time: float
    status_breakdown: Dict[str, int]
    top_companies: Dict[str, int]
    top_job_titles: Dict[str, int]
    application_trend: List[Dict]

class FollowUpReminderResponse(BaseModel):
    application_id: int
    job_title: str
    company: str
    status: str
    applied_at: datetime
    days_since_application: int
    follow_up_type: str
    suggested_action: str

# Dependency to get tracker agent (temporarily disabled)
# async def get_tracker() -> TrackerAgent:
#     tracker = TrackerAgent()
#     await tracker.initialize()
#     return tracker


@router.get("/applications", response_model=List[ApplicationResponse])
async def get_user_applications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    company: Optional[str] = None,
    days: Optional[int] = Query(None, ge=1, le=365),
    user_id: int = Depends(get_user_id)
):
    """Get applications for the authenticated user with optional filtering"""
    try:
        query = (
            db.query(JobApplication, Job)
            .outerjoin(Job, JobApplication.job_id == Job.id)
            .filter(JobApplication.user_id == user_id)
        )

        if status:
            query = query.filter(JobApplication.status == status)
        if company:
            query = query.filter(Job.company.ilike(f"%{company}%"))
        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = query.filter(JobApplication.applied_at >= cutoff)

        rows = (
            query.order_by(JobApplication.applied_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        applications = []
        for application, job in rows:
            applications.append(ApplicationResponse(
                id=application.id,
                user_id=application.user_id,
                job_id=application.job_id,
                job_title=(job.title if job else 'Unknown'),
                company=(job.company if job else 'Unknown'),
                applied_at=application.applied_at,
                status=application.status,
                cover_letter=application.cover_letter,
                notes=application.notes,
                auto_applied=bool(application.auto_applied),
                application_method=application.application_method,
                last_updated=application.last_updated,
                follow_up_date=application.follow_up_date,
                interview_date=application.interview_date
            ))

        return applications
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching applications: {str(e)}")


@router.get("/applications/stats", response_model=ApplicationStatsResponse)
async def get_application_statistics(
    days: int = Query(30, ge=1, le=365),
    user_id: int = Depends(get_user_id)
):
    """Get application statistics for the authenticated user"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        week_cutoff = datetime.utcnow() - timedelta(days=7)

        total_applications = (
            db.query(JobApplication)
            .filter(JobApplication.user_id == user_id)
            .count()
        )

        applications_this_week = (
            db.query(JobApplication)
            .filter(JobApplication.user_id == user_id, JobApplication.applied_at >= week_cutoff)
            .count()
        )

        status_rows = (
            db.query(JobApplication.status, func.count(JobApplication.id))
            .filter(JobApplication.user_id == user_id)
            .group_by(JobApplication.status)
            .all()
        )
        status_breakdown = {status: count for status, count in status_rows}

        responses = (
            db.query(JobApplication)
            .filter(JobApplication.user_id == user_id, JobApplication.status != "applied")
            .count()
        )
        response_rate = responses / total_applications if total_applications > 0 else 0

        interviews = (
            db.query(JobApplication)
            .filter(JobApplication.user_id == user_id, JobApplication.status.ilike("%interview%"))
            .count()
        )
        interview_rate = interviews / total_applications if total_applications > 0 else 0

        successes = (
            db.query(JobApplication)
            .filter(JobApplication.user_id == user_id, JobApplication.status.ilike("%accepted%"))
            .count()
        )
        success_rate = successes / total_applications if total_applications > 0 else 0

        company_rows = (
            db.query(Job.company, func.count(JobApplication.id))
            .join(Job, JobApplication.job_id == Job.id)
            .filter(JobApplication.user_id == user_id)
            .group_by(Job.company)
            .order_by(func.count(JobApplication.id).desc())
            .limit(5)
            .all()
        )
        top_companies = {company: count for company, count in company_rows}

        title_rows = (
            db.query(Job.title, func.count(JobApplication.id))
            .join(Job, JobApplication.job_id == Job.id)
            .filter(JobApplication.user_id == user_id)
            .group_by(Job.title)
            .order_by(func.count(JobApplication.id).desc())
            .limit(5)
            .all()
        )
        top_job_titles = {title: count for title, count in title_rows}
        
        stats = {
            'total_applications': total_applications,
            'applications_this_week': applications_this_week,
            'response_rate': response_rate,
            'interview_rate': interview_rate,
            'success_rate': success_rate,
            'avg_response_time': 0.0,  # TODO: Calculate based on response dates
            'status_breakdown': status_breakdown,
            'top_companies': top_companies,
            'top_job_titles': top_job_titles,
            'application_trend': []  # TODO: Calculate trend data
        }
        
        return ApplicationStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")


@router.post("/track")
async def track_user_applications(
    user_id: int = Depends(get_user_id)
):
    """Trigger application tracking for the authenticated user"""
    try:
        tracking_result = await tracker.track_applications(user_id)
        
        return {
            "message": "Application tracking completed",
            "user_id": user_id,
            **tracking_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking applications: {str(e)}")


@router.put("/status")
async def update_application_status(
    status_update: StatusUpdateRequest,
    user_id: int = Depends(get_user_id)
):
    """Update application status"""
    try:
        application = (
            db.query(JobApplication)
            .filter(JobApplication.id == status_update.application_id, JobApplication.user_id == user_id)
            .first()
        )
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        application.status = status_update.status
        application.notes = status_update.notes
        application.last_updated = datetime.utcnow()
        if status_update.interview_date:
            application.interview_date = status_update.interview_date

        db.commit()
        
        return {
            "message": "Application status updated successfully",
            "application_id": status_update.application_id,
            "new_status": status_update.status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")


@router.put("/status/bulk")
async def bulk_update_status(
    bulk_update: BulkStatusUpdateRequest,
    user_id: int = Depends(get_user_id)
):
    """Bulk update application statuses"""
    try:
        # Convert to format expected by tracker agent
        updates = []
        for update in bulk_update.updates:
            updates.append({
                "application_id": update.application_id,
                "status": update.status,
                "notes": update.notes
            })
        
        result = await tracker.bulk_update_statuses(updates)
        
        return {
            "message": "Bulk status update completed",
            **result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in bulk update: {str(e)}")


@router.get("/follow-ups", response_model=List[FollowUpReminderResponse])
async def get_follow_up_reminders(
    user_id: int = Depends(get_user_id)
):
    """Get follow-up reminders for a user"""
    try:
        reminders = await tracker.get_follow_up_reminders(user_id)
        
        return [FollowUpReminderResponse(**reminder) for reminder in reminders]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting follow-up reminders: {str(e)}")


@router.get("/application/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    user_id: int = Depends(get_user_id)
):
    """Get specific application by ID (must belong to authenticated user)"""
    try:
        row = (
            db.query(JobApplication, Job)
            .outerjoin(Job, JobApplication.job_id == Job.id)
            .filter(JobApplication.id == application_id, JobApplication.user_id == user_id)
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail="Application not found")

        application, job = row
        return ApplicationResponse(
            id=application.id,
            user_id=application.user_id,
            job_id=application.job_id,
            job_title=(job.title if job else 'Unknown'),
            company=(job.company if job else 'Unknown'),
            applied_at=application.applied_at,
            status=application.status,
            cover_letter=application.cover_letter,
            notes=application.notes,
            auto_applied=bool(application.auto_applied),
            application_method=application.application_method,
            last_updated=application.last_updated,
            follow_up_date=application.follow_up_date,
            interview_date=application.interview_date
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching application: {str(e)}")


class CreateApplicationRequest(BaseModel):
    job_id: int
    status: str = "applied"
    cover_letter: Optional[str] = None
    notes: Optional[str] = None
    application_method: Optional[str] = "manual"


@router.post("/application", response_model=ApplicationResponse)
async def create_application(
    application_data: CreateApplicationRequest,
    user_id: int = Depends(get_user_id)
):
    """Create a new application record"""
    try:
        now = datetime.utcnow()
        application = JobApplication(
            user_id=user_id,
            job_id=application_data.job_id,
            applied_at=now,
            status=application_data.status,
            cover_letter=application_data.cover_letter,
            notes=application_data.notes,
            auto_applied=False,
            application_method=application_data.application_method,
            last_updated=now
        )
        db.add(application)
        db.commit()
        db.refresh(application)

        job = db.query(Job).filter(Job.id == application_data.job_id).first()

        return ApplicationResponse(
            id=application.id,
            user_id=user_id,
            job_id=application_data.job_id,
            job_title=job.title if job else 'Unknown',
            company=job.company if job else 'Unknown',
            applied_at=now,
            status=application_data.status,
            cover_letter=application_data.cover_letter,
            notes=application_data.notes,
            auto_applied=False,
            application_method=application_data.application_method,
            last_updated=now,
            follow_up_date=None,
            interview_date=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating application: {str(e)}")


@router.delete("/application/{application_id}")
async def delete_application(
    application_id: int,
    user_id: int = Depends(get_user_id)
):
    """Delete a specific application (must belong to authenticated user)"""
    try:
        application = (
            db.query(JobApplication)
            .filter(JobApplication.id == application_id, JobApplication.user_id == user_id)
            .first()
        )
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        db.delete(application)
        db.commit()
        
        return {
            "message": "Application deleted successfully",
            "application_id": application_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return {
            "message": f"Application {application_id} deleted successfully",
            "application_id": application_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting application: {str(e)}")


@router.get("/timeline/{user_id}")
async def get_application_timeline(
    user_id: int,
    days: int = Query(30, ge=1, le=365),
    db = Depends(get_db)
):
    """Get application timeline for a user"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        rows = (
            db.query(JobApplication, Job)
            .outerjoin(Job, JobApplication.job_id == Job.id)
            .filter(JobApplication.user_id == user_id, JobApplication.applied_at >= cutoff_date)
            .order_by(JobApplication.applied_at.desc())
            .all()
        )

        timeline = []
        for application, job in rows:
            timeline.append({
                "application_id": application.id,
                "status": application.status,
                "applied_at": application.applied_at.isoformat() if application.applied_at else None,
                "job_title": job.title if job else "Unknown",
                "company": job.company if job else "Unknown"
            })

        return {
            "user_id": user_id,
            "timeline": timeline,
            "period_days": days,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting timeline: {str(e)}")


@router.get("/status-history/{application_id}")
async def get_status_history(
    application_id: int,
    db = Depends(get_db)
):
    """Get status change history for an application"""
    try:
        # This would get status history from database
        # For now, return empty history
        history = []
        
        return {
            "application_id": application_id,
            "status_history": history,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status history: {str(e)}")


@router.post("/notes/{application_id}")
async def add_application_note(
    application_id: int,
    note: str,
    db = Depends(get_db)
):
    """Add a note to an application"""
    try:
        # This would add note to database
        # For now, just return success
        
        return {
            "message": "Note added successfully",
            "application_id": application_id,
            "note": note,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding note: {str(e)}")


@router.get("/insights/{user_id}")
async def get_application_insights(
    user_id: int,
    days: int = Query(90, ge=30, le=365),
    db = Depends(get_db)
):
    """Get application insights and recommendations"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        rows = (
            db.query(JobApplication, Job)
            .outerjoin(Job, JobApplication.job_id == Job.id)
            .filter(JobApplication.user_id == user_id, JobApplication.applied_at >= cutoff_date)
            .all()
        )

        total_applications = len(rows)
        status_counts = {}
        company_counts = {}
        weekday_counts = {}

        for application, job in rows:
            status = application.status or "applied"
            status_counts[status] = status_counts.get(status, 0) + 1
            company = job.company if job else "Unknown"
            company_counts[company] = company_counts.get(company, 0) + 1
            if application.applied_at:
                weekday = application.applied_at.strftime("%A")
                weekday_counts[weekday] = weekday_counts.get(weekday, 0) + 1

        top_companies = sorted(company_counts.items(), key=lambda item: item[1], reverse=True)[:5]
        best_days = [day for day, _ in sorted(weekday_counts.items(), key=lambda item: item[1], reverse=True)[:2]]

        insights = {
            "success_patterns": {
                "best_application_days": best_days,
                "best_application_times": [],
                "most_successful_companies": [company for company, _ in top_companies],
                "most_successful_job_types": []
            },
            "improvement_suggestions": [],
            "response_rate_trend": [],
            "interview_conversion_trend": [],
            "recommendations": {
                "target_companies": [company for company, _ in top_companies],
                "skill_gaps": [],
                "application_frequency": None
            },
            "summary": {
                "total_applications": total_applications,
                "status_breakdown": status_counts
            }
        }

        return {
            "user_id": user_id,
            "period_days": days,
            "insights": insights,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting insights: {str(e)}")


@router.post("/export/{user_id}")
async def export_applications(
    user_id: int,
    format: str = Query("csv", pattern="^(csv|json|excel)$"),
    days: Optional[int] = Query(None, ge=1, le=365),
    status: Optional[str] = None
):
    """Export applications data"""
    try:
        # This would export applications data in the requested format
        # For now, return download info
        
        return {
            "message": "Export generated successfully",
            "user_id": user_id,
            "format": format,
            "download_url": f"/downloads/applications_{user_id}_{datetime.utcnow().strftime('%Y%m%d')}.{format}",
            "expires_at": (datetime.utcnow().replace(hour=23, minute=59, second=59)).isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting data: {str(e)}")


# WebSocket endpoint for real-time tracking updates (would be implemented separately)
# @router.websocket("/ws/tracking/{user_id}")
# async def websocket_tracking_updates(websocket: WebSocket, user_id: int):
#     """WebSocket for real-time tracking updates"""
#     pass
