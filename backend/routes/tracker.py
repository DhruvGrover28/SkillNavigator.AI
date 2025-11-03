"""
Tracker API Routes
Endpoints for application tracking and status management
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime

from database.db_connection import get_db, database
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
        import sqlite3
        
        conn = sqlite3.connect('skillnavigator.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query
        query = '''
            SELECT ja.*, j.title as job_title, j.company 
            FROM job_applications ja
            LEFT JOIN jobs j ON ja.job_id = j.id
            WHERE ja.user_id = ?
        '''
        params = [user_id]
        
        # Add filters
        if status:
            query += ' AND ja.status = ?'
            params.append(status)
        if company:
            query += ' AND j.company LIKE ?'
            params.append(f'%{company}%')
        if days:
            query += ' AND ja.applied_at >= datetime("now", "-{} days")'.format(days)
        
        query += ' ORDER BY ja.applied_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        applications = []
        for row in rows:
            applications.append(ApplicationResponse(
                id=row['id'],
                user_id=row['user_id'],
                job_id=row['job_id'],
                job_title=row['job_title'] or 'Unknown',
                company=row['company'] or 'Unknown',
                applied_at=datetime.fromisoformat(row['applied_at']),
                status=row['status'],
                cover_letter=row['cover_letter'],
                notes=row['notes'],
                auto_applied=bool(row['auto_applied']),
                application_method=row['application_method'],
                last_updated=datetime.fromisoformat(row['last_updated']),
                follow_up_date=datetime.fromisoformat(row['follow_up_date']) if row['follow_up_date'] else None,
                interview_date=datetime.fromisoformat(row['interview_date']) if row['interview_date'] else None
            ))
        
        conn.close()
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
        import sqlite3
        from datetime import datetime, timedelta
        
        conn = sqlite3.connect('skillnavigator.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        week_cutoff = datetime.utcnow() - timedelta(days=7)
        
        # Total applications
        cursor.execute('SELECT COUNT(*) FROM job_applications WHERE user_id = ?', (user_id,))
        total_applications = cursor.fetchone()[0]
        
        # Applications this week
        cursor.execute('SELECT COUNT(*) FROM job_applications WHERE user_id = ? AND applied_at >= ?', 
                      (user_id, week_cutoff.isoformat()))
        applications_this_week = cursor.fetchone()[0]
        
        # Status breakdown
        cursor.execute('SELECT status, COUNT(*) FROM job_applications WHERE user_id = ? GROUP BY status', 
                      (user_id,))
        status_breakdown = dict(cursor.fetchall())
        
        # Response rate (applications with status != 'applied')
        cursor.execute('SELECT COUNT(*) FROM job_applications WHERE user_id = ? AND status != "applied"', 
                      (user_id,))
        responses = cursor.fetchone()[0]
        response_rate = responses / total_applications if total_applications > 0 else 0
        
        # Interview rate
        cursor.execute('SELECT COUNT(*) FROM job_applications WHERE user_id = ? AND status LIKE "%interview%"', 
                      (user_id,))
        interviews = cursor.fetchone()[0]
        interview_rate = interviews / total_applications if total_applications > 0 else 0
        
        # Success rate (accepted offers)
        cursor.execute('SELECT COUNT(*) FROM job_applications WHERE user_id = ? AND status LIKE "%accepted%"', 
                      (user_id,))
        successes = cursor.fetchone()[0]
        success_rate = successes / total_applications if total_applications > 0 else 0
        
        # Top companies
        cursor.execute('''
            SELECT j.company, COUNT(*) as count 
            FROM job_applications ja 
            JOIN jobs j ON ja.job_id = j.id 
            WHERE ja.user_id = ? 
            GROUP BY j.company 
            ORDER BY count DESC 
            LIMIT 5
        ''', (user_id,))
        top_companies = dict(cursor.fetchall())
        
        # Top job titles
        cursor.execute('''
            SELECT j.title, COUNT(*) as count 
            FROM job_applications ja 
            JOIN jobs j ON ja.job_id = j.id 
            WHERE ja.user_id = ? 
            GROUP BY j.title 
            ORDER BY count DESC 
            LIMIT 5
        ''', (user_id,))
        top_job_titles = dict(cursor.fetchall())
        
        conn.close()
        
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
        import sqlite3
        
        conn = sqlite3.connect('skillnavigator.db')
        cursor = conn.cursor()
        
        # First check if the application exists and belongs to the user
        cursor.execute('SELECT id, status FROM job_applications WHERE id = ? AND user_id = ?', 
                      (status_update.application_id, user_id))
        
        current_app = cursor.fetchone()
        if not current_app:
            conn.close()
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Update the application
        now = datetime.utcnow()
        update_query = '''
            UPDATE job_applications 
            SET status = ?, notes = ?, last_updated = ?
        '''
        params = [status_update.status, status_update.notes, now]
        
        if status_update.interview_date:
            update_query += ', interview_date = ?'
            params.append(status_update.interview_date)
        
        update_query += ' WHERE id = ? AND user_id = ?'
        params.extend([status_update.application_id, user_id])
        
        cursor.execute(update_query, params)
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=400, detail="Failed to update application status")
        
        conn.commit()
        conn.close()
        
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
        import sqlite3
        
        conn = sqlite3.connect('skillnavigator.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ja.*, j.title as job_title, j.company 
            FROM job_applications ja
            LEFT JOIN jobs j ON ja.job_id = j.id
            WHERE ja.id = ? AND ja.user_id = ?
        ''', (application_id, user_id))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Application not found")
        
        application = ApplicationResponse(
            id=row['id'],
            user_id=row['user_id'],
            job_id=row['job_id'],
            job_title=row['job_title'] or 'Unknown',
            company=row['company'] or 'Unknown',
            applied_at=datetime.fromisoformat(row['applied_at']),
            status=row['status'],
            cover_letter=row['cover_letter'],
            notes=row['notes'],
            auto_applied=bool(row['auto_applied']),
            application_method=row['application_method'],
            last_updated=datetime.fromisoformat(row['last_updated']),
            follow_up_date=datetime.fromisoformat(row['follow_up_date']) if row['follow_up_date'] else None,
            interview_date=datetime.fromisoformat(row['interview_date']) if row['interview_date'] else None
        )
        
        return application
        
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
        import sqlite3
        
        conn = sqlite3.connect('skillnavigator.db')
        cursor = conn.cursor()
        
        now = datetime.utcnow()
        
        cursor.execute('''
            INSERT INTO job_applications (
                user_id, job_id, applied_at, status, cover_letter, 
                notes, auto_applied, application_method, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, application_data.job_id, now, application_data.status,
            application_data.cover_letter, application_data.notes, False,
            application_data.application_method, now
        ))
        
        application_id = cursor.lastrowid
        conn.commit()
        
        # Get the job details
        cursor.execute('SELECT title, company FROM jobs WHERE id = ?', (application_data.job_id,))
        job_row = cursor.fetchone()
        
        conn.close()
        
        return ApplicationResponse(
            id=application_id,
            user_id=user_id,
            job_id=application_data.job_id,
            job_title=job_row[0] if job_row else 'Unknown',
            company=job_row[1] if job_row else 'Unknown',
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
        import sqlite3
        
        conn = sqlite3.connect('skillnavigator.db')
        cursor = conn.cursor()
        
        # First check if the application exists and belongs to the user
        cursor.execute('SELECT id FROM job_applications WHERE id = ? AND user_id = ?', 
                      (application_id, user_id))
        
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Delete the application
        cursor.execute('DELETE FROM job_applications WHERE id = ? AND user_id = ?', 
                      (application_id, user_id))
        
        conn.commit()
        conn.close()
        
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
        # This would get timeline data from database
        # For now, return sample timeline
        timeline = []
        
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
        # This would analyze application data and provide insights
        # For now, return sample insights
        insights = {
            "success_patterns": {
                "best_application_days": ["Tuesday", "Wednesday"],
                "best_application_times": ["9:00 AM", "2:00 PM"],
                "most_successful_companies": [],
                "most_successful_job_types": []
            },
            "improvement_suggestions": [
                "Follow up on applications after 1 week",
                "Customize cover letters for each company",
                "Apply to more entry-level positions"
            ],
            "response_rate_trend": [],
            "interview_conversion_trend": [],
            "recommendations": {
                "target_companies": [],
                "skill_gaps": [],
                "application_frequency": "3-5 applications per week"
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
    format: str = Query("csv", regex="^(csv|json|excel)$"),
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
