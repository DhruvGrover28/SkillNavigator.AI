"""
Simple Supervisor Agent - Windows Compatible Version
Uses the enhanced scraper with real job data sources
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

from .enhanced_scraper_agent import EnhancedScraperAgent, JobListing
from database.db_connection import Database
from .autoapply_agent import AutoApplyAgent
# from .scoring_agent import ScoringAgent  # Temporarily disabled due to PyTorch memory issues

logger = logging.getLogger(__name__)

class SimpleSupervisorAgent:
    """
    A simplified supervisor agent that coordinates job search activities
    without requiring browser automation or complex subprocess management.
    """
    
    def __init__(self):
        self.scraper_agent = EnhancedScraperAgent()
        self.database = Database()
        self.autoapply_agent = AutoApplyAgent()
        # self.scoring_agent = ScoringAgent()  # Temporarily disabled due to PyTorch memory issues
        self.scoring_agent = None  # Disabled - using built-in simple scoring instead
        self.is_auto_mode = False
        self.auto_task = None
        self.last_search_time = None
        self.search_results_cache = {}
        self.max_cache_age = timedelta(hours=1)  # Cache results for 1 hour
        
        # Auto-apply settings
        self.auto_apply_enabled = True  # Enable auto-apply by default
        self.auto_apply_threshold = 70.0  # Lower threshold for more applications
        self.max_auto_applies_per_day = 5  # Conservative limit
        
        # Learning and health monitoring
        self.learning_data = {
            'scoring_weights': {'skill_match': 0.4, 'experience_match': 0.3, 'salary_match': 0.3},
            'user_insights': {},
            'threshold_history': []
        }
        self.health_metrics = {
            'last_health_check': None,
            'agent_failures': {},
            'system_load': 'normal'
        }
        self.retry_config = {
            'max_retries': 3,
            'failed_tasks': {}
        }
    
    async def initialize(self):
        """Initialize the supervisor agent"""
        try:
            await self.scraper_agent.initialize()
            
            # Try to initialize auto-apply agent with graceful failure handling
            try:
                await self.autoapply_agent.initialize()
                logger.info("Auto-apply agent initialized successfully")
            except Exception as e:
                logger.warning(f"Auto-apply agent initialization failed: {e}")
                logger.info("Continuing without auto-apply functionality")
            
            # Temporarily disable scoring agent due to PyTorch memory issues
            try:
                if self.scoring_agent:
                    await self.scoring_agent.initialize()
                    logger.info("Scoring agent initialized successfully")
                else:
                    logger.info("Scoring agent disabled - using simplified scoring")
            except Exception as e:
                logger.warning(f"Scoring agent initialization failed: {e}")
                logger.info("Continuing without ML scoring functionality")
            
            logger.info("Simple supervisor agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize simple supervisor agent: {e}")
            raise
    
    async def cleanup(self):
        """Clean up resources"""
        if self.auto_task:
            self.auto_task.cancel()
        
        if self.scraper_agent:
            await self.scraper_agent.cleanup()
        
        if self.autoapply_agent:
            await self.autoapply_agent.cleanup()
        
        logger.info("Simple supervisor agent cleaned up")
    
    def simple_score_job(self, job_dict: Dict, user_profile: Dict = None) -> float:
        """
        Simple scoring algorithm without ML dependencies
        
        Args:
            job_dict: Job information dictionary
            user_profile: User profile for matching (optional)
            
        Returns:
            Score between 0-100
        """
        score = 0.0
        
        # Base score for having essential fields
        if job_dict.get('title'): score += 20
        if job_dict.get('company'): score += 15
        if job_dict.get('description'): score += 10
        
        # Title-based scoring (simple keyword matching)
        title = job_dict.get('title', '').lower()
        description = job_dict.get('description', '').lower()
        
        # Python/Software keywords
        python_keywords = ['python', 'django', 'flask', 'fastapi', 'pandas', 'numpy', 'ml', 'machine learning']
        for keyword in python_keywords:
            if keyword in title: score += 8
            elif keyword in description: score += 3
            
        # Experience level matching
        experience = job_dict.get('experience_level', '').lower()
        if 'junior' in experience or 'entry' in experience: score += 5
        if 'mid' in experience or 'intermediate' in experience: score += 8
        if 'senior' in experience: score += 6
        
        # Remote work bonus
        location = job_dict.get('location', '').lower()
        if 'remote' in location: score += 10
        
        # Job type preference (full-time preferred)
        job_type = job_dict.get('job_type', '').lower()
        if 'full-time' in job_type or 'full time' in job_type: score += 5
        
        # Ensure score is within bounds
        return min(100.0, max(0.0, score))

    async def trigger_job_search(self, search_params: Dict) -> Dict:
        """
        Trigger a manual job search
        
        Args:
            search_params: Dict with search criteria
        
        Returns:
            Dict with search results and metadata
        """
        try:
            logger.info(f"Starting job search with params: {search_params}")
            
            # Create cache key
            cache_key = self._create_cache_key(search_params)
            
            # Check cache first
            if self._is_cache_valid(cache_key):
                logger.info("Returning cached results")
                return self.search_results_cache[cache_key]
            
            # Perform search
            start_time = datetime.now()
            jobs = await self.scraper_agent.scrape_jobs(search_params)
            search_duration = (datetime.now() - start_time).total_seconds()
            
            # Convert JobListing objects to dicts and save to database
            job_dicts = []
            for job in jobs:
                # Convert ISO string date to datetime object if needed
                posted_date = job.date_posted
                if isinstance(posted_date, str):
                    try:
                        # Parse ISO format like "2025-10-30T11:00:02+00:00"
                        posted_date = datetime.fromisoformat(posted_date.replace('Z', '+00:00'))
                    except:
                        posted_date = datetime.now()
                
                # Detect source from URL
                source = 'unknown'
                if job.url:
                    if 'remoteok.com' in job.url or 'remoteOK.com' in job.url:
                        source = 'remoteok'
                    elif 'arbeitnow.com' in job.url:
                        source = 'arbeitnow'
                    elif 'justremote.co' in job.url:
                        source = 'justremote'
                
                # Generate unique external_id for duplicate prevention
                # Use URL if available, otherwise title+company+source
                if job.url and len(job.url) > 10:
                    external_id = f"{source}_{hash(job.url)}"
                else:
                    external_id = f"{source}_{hash(job.title + job.company + source)}"
                
                job_dict = {
                    'title': job.title,
                    'company': job.company,
                    'location': job.location,
                    'description': job.description,
                    'apply_url': job.url,  # Map url to apply_url
                    'job_type': job.job_type,
                    'experience_level': job.experience,
                    'source': source,
                    'posted_date': posted_date,
                    'external_id': external_id
                }
                job_dicts.append(job_dict)
            
            # Save jobs to database if any were found
            saved_jobs = []
            scored_jobs = []
            auto_applied_jobs = []
            
            if job_dicts:
                try:
                    saved_jobs = await self.database.save_jobs(job_dicts)
                    logger.info(f"Saved {len(saved_jobs)} jobs to database")
                    
                    # Score the jobs using simple scoring
                    for job_dict in job_dicts:
                        score = self.simple_score_job(job_dict)
                        job_dict['match_score'] = score
                        scored_jobs.append(job_dict)
                        
                        # Auto-apply if score meets threshold and auto-apply is enabled
                        if (self.auto_apply_enabled and 
                            score >= self.auto_apply_threshold and 
                            len(auto_applied_jobs) < self.max_auto_applies_per_day):
                            try:
                                if self.autoapply_agent:
                                    apply_result = await self.autoapply_agent.apply_to_job(job_dict)
                                    if apply_result.get('success'):
                                        auto_applied_jobs.append(job_dict)
                                        logger.info(f"Auto-applied to {job_dict['title']} at {job_dict['company']} (score: {score})")
                            except Exception as e:
                                logger.error(f"Auto-apply failed for {job_dict['title']}: {e}")
                    
                    logger.info(f"Scored {len(scored_jobs)} jobs, auto-applied to {len(auto_applied_jobs)} jobs")
                    
                except Exception as e:
                    logger.error(f"Failed to save jobs to database: {e}")
            
            # Prepare response with original job format for frontend including scores
            response_jobs = []
            for i, job in enumerate(jobs):
                job_dict = {
                    'title': job.title,
                    'company': job.company,
                    'location': job.location,
                    'description': job.description,
                    'url': job.url,
                    'salary': job.salary,
                    'date_posted': job.date_posted,
                    'job_type': job.job_type,
                    'experience': job.experience,
                    'skills': job.skills or [],
                    'match_score': scored_jobs[i]['match_score'] if i < len(scored_jobs) else 0
                }
                response_jobs.append(job_dict)
            
            # Prepare response
            result = {
                'success': True,
                'search_params': search_params,
                'jobs': response_jobs,
                'total_found': len(response_jobs),
                'saved_to_db': len(saved_jobs),
                'scored_jobs': len(scored_jobs),
                'auto_applied': len(auto_applied_jobs),
                'search_duration_seconds': search_duration,
                'timestamp': datetime.now().isoformat(),
                'cache_key': cache_key
            }
            
            # Cache the results
            self.search_results_cache[cache_key] = result
            self.last_search_time = datetime.now()
            
            logger.info(f"Job search completed: found {len(job_dicts)} jobs in {search_duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Job search failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'search_params': search_params,
                'timestamp': datetime.now().isoformat()
            }
    
    async def start_auto_mode(self, search_params: Optional[Dict] = None) -> Dict:
        """
        Start automated job search mode
        
        Args:
            search_params: Optional search parameters, uses defaults if not provided
        
        Returns:
            Dict with operation status
        """
        try:
            if self.is_auto_mode:
                return {
                    'success': False,
                    'message': 'Auto mode is already running',
                    'status': 'already_running'
                }
            
            # Use default search params if not provided
            if not search_params:
                search_params = {
                    'keywords': 'software developer',
                    'location': 'India',
                    'max_results': 50
                }
            
            self.is_auto_mode = True
            self.auto_task = asyncio.create_task(
                self._auto_search_loop(search_params)
            )
            
            logger.info("Auto mode started")
            return {
                'success': True,
                'message': 'Auto mode started successfully',
                'search_params': search_params,
                'status': 'started'
            }
            
        except Exception as e:
            logger.error(f"Failed to start auto mode: {e}")
            return {
                'success': False,
                'error': str(e),
                'status': 'failed'
            }
    
    async def stop_auto_mode(self) -> Dict:
        """
        Stop automated job search mode
        
        Returns:
            Dict with operation status
        """
        try:
            if not self.is_auto_mode:
                return {
                    'success': False,
                    'message': 'Auto mode is not running',
                    'status': 'not_running'
                }
            
            self.is_auto_mode = False
            
            if self.auto_task:
                self.auto_task.cancel()
                try:
                    await self.auto_task
                except asyncio.CancelledError:
                    pass
                self.auto_task = None
            
            logger.info("Auto mode stopped")
            return {
                'success': True,
                'message': 'Auto mode stopped successfully',
                'status': 'stopped'
            }
            
        except Exception as e:
            logger.error(f"Failed to stop auto mode: {e}")
            return {
                'success': False,
                'error': str(e),
                'status': 'failed'
            }
    
    async def get_system_status(self) -> Dict:
        """
        Get current system status
        
        Returns:
            Dict with system status information
        """
        try:
            # Test scraper connection
            scraper_healthy = False
            if self.scraper_agent:
                scraper_healthy = await self.scraper_agent.test_connection()
            
            status = {
                'supervisor_agent': {
                    'status': 'running',
                    'auto_mode_active': self.is_auto_mode,
                    'last_search_time': self.last_search_time.isoformat() if self.last_search_time else None,
                    'cached_searches': len(self.search_results_cache)
                },
                'scraper_agent': {
                    'status': 'running' if scraper_healthy else 'error',
                    'healthy': scraper_healthy,
                    'type': 'simple_http_scraper'
                },
                'system': {
                    'timestamp': datetime.now().isoformat(),
                    'uptime_info': 'Available',
                    'version': '1.0.0-simple'
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _auto_search_loop(self, search_params: Dict):
        """
        Auto search loop that runs periodically
        """
        search_interval = 3600  # 1 hour in seconds
        
        try:
            while self.is_auto_mode:
                logger.info("Running automated job search")
                
                # Perform search
                result = await self.trigger_job_search(search_params)
                
                if result.get('success'):
                    logger.info(f"Auto search found {result.get('total_found', 0)} jobs")
                else:
                    logger.error(f"Auto search failed: {result.get('error', 'Unknown error')}")
                
                # Wait for next search
                await asyncio.sleep(search_interval)
                
        except asyncio.CancelledError:
            logger.info("Auto search loop cancelled")
        except Exception as e:
            logger.error(f"Auto search loop error: {e}")
            self.is_auto_mode = False
    
    def _create_cache_key(self, search_params: Dict) -> str:
        """Create a cache key from search parameters"""
        # Create a normalized key from search params
        key_parts = [
            search_params.get('keywords', '').lower().strip(),
            search_params.get('location', '').lower().strip(),
            str(search_params.get('max_results', 50))
        ]
        return '|'.join(key_parts)
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached results are still valid"""
        if cache_key not in self.search_results_cache:
            return False
        
        cached_result = self.search_results_cache[cache_key]
        cached_time = datetime.fromisoformat(cached_result['timestamp'])
        
        return datetime.now() - cached_time < self.max_cache_age
    
    def is_healthy(self) -> bool:
        """Check if the supervisor agent is healthy"""
        return (
            self.scraper_agent is not None and 
            self.scraper_agent.is_healthy()
        )
    
    async def apply_to_job(self, user_id: int, job_id: int) -> Dict:
        """Apply to a specific job manually"""
        try:
            logger.info(f"Manual apply triggered for user {user_id}, job {job_id}")
            
            # Apply using auto-apply agent
            results = await self.autoapply_agent.auto_apply_to_jobs(user_id, [job_id])
            
            if results:
                result = results[0]
                return {
                    'success': result.get('success', False),
                    'job_id': job_id,
                    'user_id': user_id,
                    'method': result.get('method', 'unknown'),
                    'message': 'Application submitted successfully' if result.get('success') else 'Application failed',
                    'error': result.get('error'),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'job_id': job_id,
                    'user_id': user_id,
                    'message': 'No application results returned',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in manual apply for job {job_id}: {e}")
            return {
                'success': False,
                'job_id': job_id,
                'user_id': user_id,
                'error': str(e),
                'message': 'Application failed due to error',
                'timestamp': datetime.now().isoformat()
            }
    
    async def enable_auto_apply(self, user_id: int, threshold: float = 80.0, max_per_day: int = 10) -> Dict:
        """Enable automatic job applications for high-scoring jobs"""
        try:
            self.auto_apply_enabled = True
            self.auto_apply_threshold = threshold
            self.max_auto_applies_per_day = max_per_day
            
            logger.info(f"Auto-apply enabled for user {user_id} with threshold {threshold}")
            
            return {
                'success': True,
                'message': f'Auto-apply enabled with {threshold}% threshold',
                'user_id': user_id,
                'threshold': threshold,
                'max_per_day': max_per_day,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error enabling auto-apply: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to enable auto-apply',
                'timestamp': datetime.now().isoformat()
            }
    
    async def configure_auto_apply(self, config: Dict) -> Dict:
        """Configure auto-apply settings"""
        try:
            if 'enabled' in config:
                self.auto_apply_enabled = config['enabled']
            if 'threshold' in config:
                self.auto_apply_threshold = config['threshold']
            if 'max_per_day' in config:
                self.max_auto_applies_per_day = config['max_per_day']
            
            logger.info(f"Auto-apply configured: enabled={self.auto_apply_enabled}, threshold={self.auto_apply_threshold}")
            return {
                'success': True,
                'message': 'Auto-apply configuration updated',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error configuring auto-apply: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to configure auto-apply',
                'timestamp': datetime.now().isoformat()
            }
    
    async def disable_auto_apply(self) -> Dict:
        """Disable automatic job applications"""
        try:
            self.auto_apply_enabled = False
            logger.info("Auto-apply disabled")
            
            return {
                'success': True,
                'message': 'Auto-apply disabled',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error disabling auto-apply: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to disable auto-apply',
                'timestamp': datetime.now().isoformat()
            }
    
    async def check_and_auto_apply(self, user_id: int) -> Dict:
        """Check for high-scoring jobs and auto-apply if enabled"""
        if not self.auto_apply_enabled:
            return {
                'success': False,
                'message': 'Auto-apply is not enabled',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # Get user profile for scoring
            # This would typically get scored jobs above threshold
            # For now, we'll implement a basic version
            
            logger.info(f"Checking for auto-apply opportunities for user {user_id}")
            
            # Get recent jobs that haven't been applied to
            # Score them and apply to high-scoring ones
            # This is a simplified implementation
            
            return {
                'success': True,
                'message': 'Auto-apply check completed',
                'user_id': user_id,
                'threshold': self.auto_apply_threshold,
                'checked_jobs': 0,
                'applied_jobs': 0,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in auto-apply check: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Auto-apply check failed',
                'timestamp': datetime.now().isoformat()
            }
    
    async def _comprehensive_health_check(self) -> Dict:
        """Perform comprehensive health check of all agents"""
        from datetime import datetime
        
        health_status = {
            'scraper_agent': 'healthy' if self.scraper_agent else 'unhealthy',
            'scoring_agent': 'degraded' if self.scoring_agent is None else 'healthy',
            'autoapply_agent': 'healthy' if self.autoapply_agent else 'unhealthy',
            'database': 'healthy'
        }
        
        # Test database connection
        try:
            self.database.fetch_one("SELECT 1")
            health_status['database'] = 'healthy'
        except Exception:
            health_status['database'] = 'unhealthy'
        
        # Calculate overall health
        unhealthy_count = sum(1 for status in health_status.values() if status == 'unhealthy')
        degraded_count = sum(1 for status in health_status.values() if status == 'degraded')
        
        if unhealthy_count == 0 and degraded_count == 0:
            overall_health = 'healthy'
        elif unhealthy_count <= 1:
            overall_health = 'degraded'
        else:
            overall_health = 'unhealthy'
        
        return {
            'agents': health_status,
            'overall_health': overall_health,
            'timestamp': datetime.now().isoformat()
        }
    
    async def analyze_user_outcomes(self, user_id: int) -> Dict:
        """Simplified user outcome analysis"""
        try:
            # Get user's recent applications using SQLAlchemy
            from datetime import datetime, timedelta
            from database.db_connection import JobApplication, Job
            
            db = self.database.get_session()
            try:
                thirty_days_ago = datetime.now() - timedelta(days=30)
                
                # Query applications with job details
                applications_query = db.query(JobApplication, Job).join(Job).filter(
                    JobApplication.user_id == user_id,
                    JobApplication.applied_at >= thirty_days_ago
                ).all()
                
                # Convert to list of dicts for easier processing
                applications = []
                for app, job in applications_query:
                    applications.append({
                        'status': app.status,
                        'applied_at': app.applied_at,
                        'title': job.title,
                        'company': job.company
                    })
                    
            finally:
                db.close()
            
            # Calculate basic outcomes
            outcomes = {
                'total': len(applications),
                'interviews': len([a for a in applications if 'interview' in a.get('status', '').lower()]),
                'offers': len([a for a in applications if a.get('status') in ['accepted', 'offer_accepted']]),
                'rejections': len([a for a in applications if a.get('status') == 'rejected'])
            }
            
            # Generate simple insights
            insights = []
            if outcomes['total'] > 0:
                success_rate = (outcomes['interviews'] + outcomes['offers']) / outcomes['total']
                if success_rate < 0.1:
                    insights.append("Your response rate is low. Consider improving your application materials.")
                elif success_rate > 0.3:
                    insights.append("Great job! You have a strong response rate from employers.")
            
            if outcomes['total'] < 5:
                insights.append("Apply to more positions to improve your job search success.")
            
            # Store insights
            self.learning_data['user_insights'][user_id] = {
                'outcomes': outcomes,
                'insights': insights,
                'last_analysis': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'outcomes': outcomes,
                'insights': insights,
                'adjustments_made': False,
                'message': 'Analysis completed successfully'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing user outcomes: {e}")
            return {'success': False, 'error': str(e)}
    
    async def adaptive_threshold_tuning(self, user_id: int) -> Dict:
        """Simplified adaptive threshold tuning"""
        try:
            user_data = self.learning_data['user_insights'].get(user_id)
            if not user_data:
                return {'success': False, 'message': 'No user data available. Run analysis first.'}
            
            outcomes = user_data['outcomes']
            current_threshold = self.auto_apply_threshold
            
            # Simple threshold adjustment logic
            total_apps = outcomes['total']
            if total_apps > 0:
                success_rate = (outcomes['interviews'] + outcomes['offers']) / total_apps
                
                new_threshold = current_threshold
                if success_rate < 0.1 and total_apps > 10:  # Low success, many apps
                    new_threshold = min(95.0, current_threshold + 5.0)
                elif success_rate > 0.3:  # High success
                    new_threshold = max(70.0, current_threshold - 2.0)
                
                if abs(new_threshold - current_threshold) >= 2.0:
                    self.auto_apply_threshold = new_threshold
                    self.learning_data['threshold_history'].append({
                        'user_id': user_id,
                        'old_threshold': current_threshold,
                        'new_threshold': new_threshold,
                        'success_rate': success_rate,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    return {
                        'success': True,
                        'threshold_adjusted': True,
                        'old_threshold': current_threshold,
                        'new_threshold': new_threshold,
                        'reason': f"Based on {success_rate:.1%} success rate from {total_apps} applications"
                    }
            
            return {
                'success': True,
                'threshold_adjusted': False,
                'current_threshold': current_threshold,
                'message': 'No threshold adjustment needed'
            }
            
        except Exception as e:
            logger.error(f"Error in threshold tuning: {e}")
            return {'success': False, 'error': str(e)}
    
    async def setup_user_schedule(self, user_id: int, schedule_config: Dict) -> Dict:
        """Setup user-specific scheduling (simplified)"""
        try:
            # For now, just acknowledge the request
            # In a full implementation, this would store per-user schedules
            return {
                'success': True,
                'message': 'User schedule configuration acknowledged',
                'user_id': user_id,
                'config': schedule_config
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def retry_failed_task(self, task_id: str, task_data: Dict) -> Dict:
        """Simplified task retry mechanism"""
        try:
            # Basic retry logic - just re-run the task
            task_type = task_data.get('type', 'unknown')
            
            if task_type == 'job_search':
                result = await self.trigger_job_search(task_data.get('search_params', {}))
                return {
                    'success': result.get('success', False),
                    'message': 'Task retry completed',
                    'task_type': task_type,
                    'retry_count': 1
                }
            
            return {
                'success': False,
                'message': f'Unknown task type: {task_type}',
                'task_type': task_type
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_auto_apply_status(self) -> Dict:
        """Get current auto-apply settings and status"""
        return {
            'enabled': self.auto_apply_enabled,
            'threshold': self.auto_apply_threshold,
            'max_per_day': self.max_auto_applies_per_day,
            'applications_today': getattr(self.autoapply_agent, 'applications_today', 0),
            'timestamp': datetime.now().isoformat()
        }
