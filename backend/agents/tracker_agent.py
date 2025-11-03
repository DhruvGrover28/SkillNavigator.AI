"""
Tracker Agent - Application Status Tracking
Tracks job application status and manages application lifecycle
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json

from database.db_connection import database

logger = logging.getLogger(__name__)


class TrackerAgent:
    """Autonomous agent for tracking job application status and progress"""
    
    def __init__(self):
        self.status_transitions = {
            'applied': ['interview', 'rejected', 'withdrawn'],
            'interview': ['accepted', 'rejected', 'second_interview'],
            'second_interview': ['accepted', 'rejected', 'final_interview'],
            'final_interview': ['accepted', 'rejected'],
            'accepted': ['offer_accepted', 'offer_declined'],
            'rejected': [],  # Terminal state
            'withdrawn': [],  # Terminal state
            'offer_accepted': [],  # Terminal state
            'offer_declined': []  # Terminal state
        }
        
        # Follow-up schedules (days after application)
        self.follow_up_schedule = {
            'first_follow_up': 7,
            'second_follow_up': 14,
            'final_follow_up': 21
        }
    
    async def initialize(self):
        """Initialize the tracker agent"""
        try:
            logger.info("Tracker agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize tracker agent: {e}")
            raise
    
    async def track_applications(self, user_id: int) -> Dict:
        """
        Track and update application statuses for a user
        
        Returns:
            Summary of tracking results
        """
        try:
            # Get all applications for user
            applications = await self._get_user_applications(user_id)
            
            if not applications:
                return {
                    'total_applications': 0,
                    'updates_made': 0,
                    'follow_ups_needed': 0,
                    'status_summary': {}
                }
            
            logger.info(f"Tracking {len(applications)} applications for user {user_id}")
            
            updates_made = 0
            follow_ups_needed = 0
            
            for application in applications:
                # Check if follow-up is needed
                if await self._needs_follow_up(application):
                    await self._schedule_follow_up(application)
                    follow_ups_needed += 1
                
                # Check for automatic status updates
                if await self._update_application_status(application):
                    updates_made += 1
            
            # Generate status summary
            status_summary = await self._generate_status_summary(user_id)
            
            await database.log_system_activity(
                agent_name="tracker_agent",
                action="track_applications",
                message=f"Tracked {len(applications)} applications, {updates_made} updates made",
                metadata={
                    "user_id": user_id,
                    "total_applications": len(applications),
                    "updates_made": updates_made,
                    "follow_ups_needed": follow_ups_needed
                }
            )
            
            return {
                'total_applications': len(applications),
                'updates_made': updates_made,
                'follow_ups_needed': follow_ups_needed,
                'status_summary': status_summary
            }
            
        except Exception as e:
            logger.error(f"Error tracking applications: {e}")
            await database.log_system_activity(
                agent_name="tracker_agent",
                action="track_applications_error",
                message=f"Error tracking applications: {str(e)}",
                level="error"
            )
            raise
    
    async def update_application_status(self, application_id: int, new_status: str, 
                                      notes: str = None, interview_date: datetime = None) -> bool:
        """
        Manually update application status
        
        Args:
            application_id: Application ID
            new_status: New status value
            notes: Optional notes
            interview_date: Optional interview date
            
        Returns:
            True if update successful
        """
        try:
            # Validate status transition
            application = await self._get_application_by_id(application_id)
            if not application:
                raise ValueError(f"Application {application_id} not found")
            
            current_status = application.get('status', 'applied')
            
            if not self._is_valid_status_transition(current_status, new_status):
                logger.warning(f"Invalid status transition: {current_status} -> {new_status}")
                # Allow it anyway for manual updates
            
            # Update application
            update_data = {
                'status': new_status,
                'last_updated': datetime.utcnow(),
                'notes': notes or application.get('notes', '')
            }
            
            if interview_date:
                update_data['interview_date'] = interview_date
            
            # Set follow-up date based on new status
            if new_status == 'applied':
                update_data['follow_up_date'] = datetime.utcnow() + timedelta(
                    days=self.follow_up_schedule['first_follow_up']
                )
            elif new_status == 'interview':
                update_data['follow_up_date'] = interview_date + timedelta(days=2) if interview_date else None
            
            await self._update_application_in_db(application_id, update_data)
            
            await database.log_system_activity(
                agent_name="tracker_agent",
                action="status_update",
                message=f"Updated application {application_id} status to {new_status}",
                metadata={
                    "application_id": application_id,
                    "old_status": current_status,
                    "new_status": new_status
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating application status: {e}")
            return False
    
    async def get_application_statistics(self, user_id: int, days: int = 30) -> Dict:
        """
        Get application statistics for a user
        
        Args:
            user_id: User ID
            days: Number of days to look back
            
        Returns:
            Dictionary with application statistics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            applications = await self._get_user_applications_since(user_id, cutoff_date)
            
            # Calculate statistics
            stats = {
                'total_applications': len(applications),
                'applications_this_week': 0,
                'response_rate': 0.0,
                'interview_rate': 0.0,
                'success_rate': 0.0,
                'avg_response_time': 0,
                'status_breakdown': {},
                'top_companies': {},
                'top_job_titles': {},
                'application_trend': []
            }
            
            if not applications:
                return stats
            
            # Count by status
            status_counts = {}
            company_counts = {}
            title_counts = {}
            response_times = []
            
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            for app in applications:
                # Status breakdown
                status = app.get('status', 'applied')
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Applications this week
                if app.get('applied_at', datetime.utcnow()) > week_ago:
                    stats['applications_this_week'] += 1
                
                # Company and title counts
                company = app.get('job', {}).get('company', 'Unknown')
                title = app.get('job', {}).get('title', 'Unknown')
                company_counts[company] = company_counts.get(company, 0) + 1
                title_counts[title] = title_counts.get(title, 0) + 1
                
                # Response time calculation
                if status != 'applied' and app.get('last_updated'):
                    applied_at = app.get('applied_at', datetime.utcnow())
                    updated_at = app.get('last_updated', datetime.utcnow())
                    response_time = (updated_at - applied_at).days
                    response_times.append(response_time)
            
            # Calculate rates
            total = len(applications)
            responses = sum(1 for app in applications if app.get('status') not in ['applied'])
            interviews = sum(1 for app in applications if 'interview' in app.get('status', ''))
            successes = sum(1 for app in applications if app.get('status') in ['accepted', 'offer_accepted'])
            
            stats['response_rate'] = (responses / total * 100) if total > 0 else 0
            stats['interview_rate'] = (interviews / total * 100) if total > 0 else 0
            stats['success_rate'] = (successes / total * 100) if total > 0 else 0
            stats['avg_response_time'] = sum(response_times) / len(response_times) if response_times else 0
            
            # Top companies and titles
            stats['status_breakdown'] = status_counts
            stats['top_companies'] = dict(sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:5])
            stats['top_job_titles'] = dict(sorted(title_counts.items(), key=lambda x: x[1], reverse=True)[:5])
            
            # Application trend (last 7 days)
            stats['application_trend'] = await self._get_application_trend(user_id, 7)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting application statistics: {e}")
            return {}
    
    async def get_follow_up_reminders(self, user_id: int) -> List[Dict]:
        """Get applications that need follow-up"""
        try:
            applications = await self._get_applications_needing_followup(user_id)
            
            reminders = []
            for app in applications:
                follow_up_date = app.get('follow_up_date')
                if follow_up_date and follow_up_date <= datetime.utcnow():
                    days_since_application = (datetime.utcnow() - app.get('applied_at', datetime.utcnow())).days
                    
                    reminders.append({
                        'application_id': app.get('id'),
                        'job_title': app.get('job', {}).get('title', 'Unknown'),
                        'company': app.get('job', {}).get('company', 'Unknown'),
                        'status': app.get('status', 'applied'),
                        'applied_at': app.get('applied_at'),
                        'days_since_application': days_since_application,
                        'follow_up_type': self._determine_follow_up_type(days_since_application),
                        'suggested_action': self._get_suggested_follow_up_action(app)
                    })
            
            return sorted(reminders, key=lambda x: x['days_since_application'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting follow-up reminders: {e}")
            return []
    
    async def bulk_update_statuses(self, updates: List[Dict]) -> Dict:
        """
        Bulk update application statuses
        
        Args:
            updates: List of update dictionaries with application_id, status, notes
            
        Returns:
            Summary of bulk update results
        """
        successful_updates = 0
        failed_updates = 0
        errors = []
        
        for update in updates:
            try:
                application_id = update.get('application_id')
                status = update.get('status')
                notes = update.get('notes', '')
                
                success = await self.update_application_status(application_id, status, notes)
                if success:
                    successful_updates += 1
                else:
                    failed_updates += 1
                    errors.append(f"Failed to update application {application_id}")
                    
            except Exception as e:
                failed_updates += 1
                errors.append(f"Error updating application {update.get('application_id', 'unknown')}: {str(e)}")
        
        return {
            'successful_updates': successful_updates,
            'failed_updates': failed_updates,
            'errors': errors
        }
    
    async def _get_user_applications(self, user_id: int) -> List[Dict]:
        """Get all applications for a user"""
        # This would query the database for user applications
        # For now, return empty list
        return []
    
    async def _get_user_applications_since(self, user_id: int, since_date: datetime) -> List[Dict]:
        """Get user applications since a specific date"""
        # This would query the database with date filter
        return []
    
    async def _get_application_by_id(self, application_id: int) -> Optional[Dict]:
        """Get application by ID"""
        # This would query the database for specific application
        return None
    
    async def _get_applications_needing_followup(self, user_id: int) -> List[Dict]:
        """Get applications that need follow-up"""
        # This would query the database for applications with follow_up_date <= now
        return []
    
    async def _needs_follow_up(self, application: Dict) -> bool:
        """Check if application needs follow-up"""
        follow_up_date = application.get('follow_up_date')
        status = application.get('status', 'applied')
        
        # Don't follow up on terminal statuses
        if status in ['rejected', 'withdrawn', 'offer_accepted', 'offer_declined']:
            return False
        
        # Check if follow-up date has passed
        if follow_up_date and follow_up_date <= datetime.utcnow():
            return True
        
        return False
    
    async def _schedule_follow_up(self, application: Dict):
        """Schedule follow-up for an application"""
        days_since_application = (datetime.utcnow() - application.get('applied_at', datetime.utcnow())).days
        
        # Determine next follow-up date
        if days_since_application <= 7:
            next_follow_up = datetime.utcnow() + timedelta(days=self.follow_up_schedule['second_follow_up'] - days_since_application)
        elif days_since_application <= 14:
            next_follow_up = datetime.utcnow() + timedelta(days=self.follow_up_schedule['final_follow_up'] - days_since_application)
        else:
            # Stop following up after 3 weeks
            next_follow_up = None
        
        if next_follow_up:
            await self._update_application_in_db(application.get('id'), {
                'follow_up_date': next_follow_up
            })
    
    async def _update_application_status(self, application: Dict) -> bool:
        """Automatically update application status if needed"""
        # This could include logic to:
        # - Check email for responses
        # - Scrape job portals for status updates
        # - Apply business rules for status changes
        
        # For now, return False (no updates made)
        return False
    
    async def _update_application_in_db(self, application_id: int, update_data: Dict):
        """Update application in database"""
        # This would update the database record
        logger.info(f"Updating application {application_id} with data: {update_data}")
    
    async def _generate_status_summary(self, user_id: int) -> Dict:
        """Generate summary of application statuses"""
        applications = await self._get_user_applications(user_id)
        
        summary = {}
        for app in applications:
            status = app.get('status', 'applied')
            summary[status] = summary.get(status, 0) + 1
        
        return summary
    
    async def _get_application_trend(self, user_id: int, days: int) -> List[Dict]:
        """Get application trend over the last N days"""
        trend = []
        
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=i)
            # This would count applications for each day
            count = 0  # Placeholder
            
            trend.append({
                'date': date.strftime('%Y-%m-%d'),
                'applications': count
            })
        
        return list(reversed(trend))
    
    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """Check if status transition is valid"""
        if current_status not in self.status_transitions:
            return True  # Allow any transition from unknown status
        
        return new_status in self.status_transitions[current_status]
    
    def _determine_follow_up_type(self, days_since_application: int) -> str:
        """Determine the type of follow-up needed"""
        if days_since_application <= 7:
            return "first_follow_up"
        elif days_since_application <= 14:
            return "second_follow_up"
        else:
            return "final_follow_up"
    
    def _get_suggested_follow_up_action(self, application: Dict) -> str:
        """Get suggested follow-up action"""
        status = application.get('status', 'applied')
        days_since = (datetime.utcnow() - application.get('applied_at', datetime.utcnow())).days
        
        if status == 'applied':
            if days_since <= 7:
                return "Send a polite follow-up email expressing continued interest"
            elif days_since <= 14:
                return "Send a second follow-up with additional value (portfolio, references)"
            else:
                return "Send final follow-up or consider the application closed"
        elif status == 'interview':
            return "Send thank-you note and check on decision timeline"
        else:
            return "Monitor for updates"
    
    def is_healthy(self) -> bool:
        """Check if the tracker agent is healthy"""
        return True
