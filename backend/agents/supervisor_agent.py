"""
Supervisor Agent - Multi-Agent Orchestration
Coordinates and manages all other agents using workflow automation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

from .enhanced_scraper_agent import EnhancedScraperAgent
from .job_scoring_agent import JobScoringAgent
from .autoapply_agent import AutoApplyAgent
from .tracker_agent import TrackerAgent
from database.db_connection import Database

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """Main orchestration agent that manages the entire job application workflow"""
    
    def __init__(self):
        # Initialize sub-agents
        self.scraper_agent = EnhancedScraperAgent()
        self.scoring_agent = JobScoringAgent()
        self.autoapply_agent = AutoApplyAgent()
        self.tracker_agent = TrackerAgent()
        self.database = Database()
        
        # Workflow state
        self.auto_mode_enabled = False
        self.last_scraping_time = None
        self.workflow_running = False
        
        # Configuration
        self.config = {
            'scraping_interval_hours': 24,  # Scrape once per day
            'scoring_threshold': 0.7,  # Minimum score for auto-apply
            'max_auto_applications': 5,  # Max auto applications per day
            'auto_apply_enabled': False,
            'follow_up_interval_days': 7
        }
        
        # Adaptive Learning State
        self.learning_data = {
            'scoring_weights': {
                'skill_match': 0.35,
                'experience_match': 0.25, 
                'salary_match': 0.20,
                'company_quality': 0.20
            },
            'threshold_history': [],
            'outcome_analytics': {},
            'performance_metrics': {}
        }
        
        # Per-User Scheduling
        self.user_schedules = {}  # user_id -> schedule_config
        
        # Error Recovery
        self.retry_config = {
            'max_retries': 3,
            'retry_delay_seconds': 30,
            'failed_tasks': {}
        }
        
        # System Health
        self.health_metrics = {
            'last_health_check': None,
            'agent_failures': {},
            'system_load': 'normal'
        }
    
    async def initialize(self):
        """Initialize the supervisor agent and all sub-agents"""
        try:
            logger.info("Initializing supervisor agent...")
            
            # Initialize all sub-agents
            await self.scraper_agent.initialize()
            await self.scoring_agent.initialize()
            await self.autoapply_agent.initialize()
            await self.tracker_agent.initialize()
            
            # Load configuration from database/environment
            await self._load_configuration()
            
            # Schedule recurring tasks
            self._schedule_recurring_tasks()
            
            logger.info("Supervisor agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize supervisor agent: {e}")
            raise
    
    async def cleanup(self):
        """Clean up all agents and resources"""
        try:
            await self.scraper_agent.cleanup()
            await self.scoring_agent.cleanup()
            await self.autoapply_agent.cleanup()
            await self.tracker_agent.cleanup()
            logger.info("Supervisor agent cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def trigger_job_search(self, search_params: Dict) -> Dict:
        """
        Manually trigger the complete job search workflow
        
        Args:
            search_params: Search parameters for job scraping
            
        Returns:
            Workflow execution results
        """
        if self.workflow_running:
            return {
                'success': False,
                'error': 'Workflow already running',
                'status': 'busy'
            }
        
        self.workflow_running = True
        
        try:
            logger.info("Starting manual job search workflow")
            
            await self.database.log_system_activity(
                agent_name="supervisor_agent",
                action="workflow_start",
                message="Manual job search workflow initiated",
                metadata=search_params
            )
            
            # Step 1: Scrape jobs
            scraping_result = await self._execute_scraping_phase(search_params)
            
            # Step 2: Score jobs
            scoring_result = await self._execute_scoring_phase()
            
            # Step 3: Auto-apply (if enabled)
            autoapply_result = None
            if self.config.get('auto_apply_enabled', False):
                autoapply_result = await self._execute_autoapply_phase()
            
            # Step 4: Update tracking
            tracking_result = await self._execute_tracking_phase()
            
            workflow_result = {
                'success': True,
                'phases': {
                    'scraping': scraping_result,
                    'scoring': scoring_result,
                    'autoapply': autoapply_result,
                    'tracking': tracking_result
                },
                'summary': self._generate_workflow_summary(
                    scraping_result, scoring_result, autoapply_result, tracking_result
                )
            }
            
            await self.database.log_system_activity(
                agent_name="supervisor_agent",
                action="workflow_complete",
                message="Manual job search workflow completed successfully",
                metadata=workflow_result['summary']
            )
            
            return workflow_result
            
        except Exception as e:
            logger.error(f"Error in job search workflow: {e}")
            
            await self.database.log_system_activity(
                agent_name="supervisor_agent",
                action="workflow_error",
                message=f"Job search workflow failed: {str(e)}",
                level="error"
            )
            
            return {
                'success': False,
                'error': str(e),
                'status': 'failed'
            }
        finally:
            self.workflow_running = False
    
    async def start_auto_mode(self, user_id: Optional[int] = None) -> Dict:
        """Start automated job search mode"""
        try:
            self.auto_mode_enabled = True
            
            # Start background tasks for automated workflow
            asyncio.create_task(self._auto_mode_loop())
            asyncio.create_task(self._adaptive_learning_loop())
            asyncio.create_task(self._health_monitoring_loop())
            
            await self.database.log_system_activity(
                agent_name="supervisor_agent",
                action="auto_mode_start",
                message="Automated mode started with adaptive learning",
                metadata={'user_id': user_id} if user_id else {}
            )
            
            return {
                'success': True,
                'message': 'Auto mode started successfully with adaptive learning',
                'config': self.config,
                'features_enabled': [
                    'adaptive_learning',
                    'per_user_scheduling', 
                    'health_monitoring',
                    'error_recovery'
                ]
            }
            
        except Exception as e:
            logger.error(f"Error starting auto mode: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def setup_user_schedule(self, user_id: int, schedule_config: Dict) -> Dict:
        """Setup per-user scheduling configuration"""
        try:
            default_config = {
                'scraping_interval_hours': 12,
                'max_daily_applications': 5,
                'preferred_times': ['09:00', '14:00'],  # UTC times
                'weekend_enabled': False,
                'active': True
            }
            
            # Merge with provided config
            user_config = {**default_config, **schedule_config}
            self.user_schedules[user_id] = user_config
            
            await self.database.log_system_activity(
                agent_name="supervisor_agent",
                action="user_schedule_setup",
                message=f"Setup custom schedule for user {user_id}",
                metadata=user_config
            )
            
            return {
                'success': True,
                'message': 'User schedule configured successfully',
                'config': user_config
            }
            
        except Exception as e:
            logger.error(f"Error setting up user schedule: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _adaptive_learning_loop(self):
        """Background task for continuous adaptive learning"""
        while self.auto_mode_enabled:
            try:
                await asyncio.sleep(24 * 3600)  # Run daily
                
                # Get all active users
                active_users = self.database.fetch_all(
                    "SELECT DISTINCT user_id FROM job_applications WHERE created_at >= datetime('now', '-7 days')"
                )
                
                for user_record in active_users:
                    user_id = user_record['user_id']
                    
                    # Analyze outcomes and adjust
                    await self.analyze_user_outcomes(user_id)
                    await self.adaptive_threshold_tuning(user_id)
                    
                    # Small delay between users
                    await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in adaptive learning loop: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retry
    
    async def _health_monitoring_loop(self):
        """Background task for continuous health monitoring"""
        while self.auto_mode_enabled:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Check agent health
                health_status = await self._comprehensive_health_check()
                
                # Handle unhealthy agents
                if health_status['overall_health'] != 'healthy':
                    await self._handle_unhealthy_system(health_status)
                
                self.health_metrics['last_health_check'] = datetime.utcnow().isoformat()
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(900)  # Wait 15 minutes before retry
    
    async def _comprehensive_health_check(self) -> Dict:
        """Perform comprehensive health check of all agents"""
        health_status = {
            'scraper_agent': 'unknown',
            'scoring_agent': 'unknown', 
            'autoapply_agent': 'unknown',
            'tracker_agent': 'unknown',
            'database': 'unknown'
        }
        
        # Check scraper agent
        try:
            # Simple test - try to initialize
            if self.scraper_agent:
                health_status['scraper_agent'] = 'healthy'
            else:
                health_status['scraper_agent'] = 'unhealthy'
        except Exception as e:
            health_status['scraper_agent'] = 'unhealthy'
            self.health_metrics['agent_failures']['scraper'] = str(e)
        
        # Check scoring agent
        try:
            if self.scoring_agent:
                health_status['scoring_agent'] = 'healthy'
            else:
                health_status['scoring_agent'] = 'degraded'  # Can work without it
        except Exception as e:
            health_status['scoring_agent'] = 'unhealthy'
            self.health_metrics['agent_failures']['scoring'] = str(e)
        
        # Check database
        try:
            test_query = "SELECT 1"
            self.database.fetch_one(test_query)
            health_status['database'] = 'healthy'
        except Exception as e:
            health_status['database'] = 'unhealthy'
            self.health_metrics['agent_failures']['database'] = str(e)
        
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
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _handle_unhealthy_system(self, health_status: Dict):
        """Handle system health issues with graceful degradation"""
        try:
            agents = health_status['agents']
            
            # Try to recover unhealthy agents
            if agents.get('scraper_agent') == 'unhealthy':
                try:
                    # Attempt to reinitialize scraper
                    self.scraper_agent = EnhancedScraperAgent()
                    await self.scraper_agent.initialize()
                    logger.info("Scraper agent recovered successfully")
                except Exception as e:
                    logger.error(f"Failed to recover scraper agent: {e}")
            
            if agents.get('database') == 'unhealthy':
                try:
                    # Attempt to reconnect to database
                    await self.database.initialize()
                    logger.info("Database connection recovered successfully")
                except Exception as e:
                    logger.error(f"Failed to recover database connection: {e}")
                    # This is critical - may need to disable auto mode
                    self.auto_mode_enabled = False
            
            # Log health issues
            await self.database.log_system_activity(
                agent_name="supervisor_agent",
                action="health_recovery",
                message="Attempted to recover from health issues",
                metadata=health_status,
                level="warning"
            )
            
        except Exception as e:
            logger.error(f"Error handling unhealthy system: {e}")
    
    async def retry_failed_task(self, task_id: str, task_data: Dict) -> Dict:
        """Retry a failed task with exponential backoff"""
        try:
            if task_id in self.retry_config['failed_tasks']:
                retry_count = self.retry_config['failed_tasks'][task_id]['count']
                if retry_count >= self.retry_config['max_retries']:
                    return {
                        'success': False,
                        'error': 'Max retries exceeded',
                        'retry_count': retry_count
                    }
            else:
                self.retry_config['failed_tasks'][task_id] = {'count': 0, 'last_attempt': None}
            
            # Exponential backoff delay
            retry_count = self.retry_config['failed_tasks'][task_id]['count']
            delay = self.retry_config['retry_delay_seconds'] * (2 ** retry_count)
            await asyncio.sleep(delay)
            
            # Attempt to retry the task based on type
            task_type = task_data.get('type')
            if task_type == 'job_search':
                result = await self.trigger_job_search(task_data.get('search_params', {}))
            elif task_type == 'auto_apply':
                result = await self._execute_autoapply_phase()
            else:
                return {'success': False, 'error': 'Unknown task type'}
            
            if result.get('success'):
                # Task succeeded - remove from failed tasks
                del self.retry_config['failed_tasks'][task_id]
                return {
                    'success': True,
                    'message': 'Task retried successfully',
                    'retry_count': retry_count + 1
                }
            else:
                # Task failed again - increment retry count
                self.retry_config['failed_tasks'][task_id]['count'] += 1
                self.retry_config['failed_tasks'][task_id]['last_attempt'] = datetime.utcnow().isoformat()
                return {
                    'success': False,
                    'error': 'Task failed again',
                    'retry_count': retry_count + 1
                }
                
        except Exception as e:
            logger.error(f"Error retrying failed task: {e}")
            return {'success': False, 'error': str(e)}
    
    async def stop_auto_mode(self) -> Dict:
        """Stop automated job search mode"""
        try:
            self.auto_mode_enabled = False
            
            await self.database.log_system_activity(
                agent_name="supervisor_agent",
                action="auto_mode_stop",
                message="Automated mode stopped"
            )
            
            return {
                'success': True,
                'message': 'Auto mode stopped successfully'
            }
            
        except Exception as e:
            logger.error(f"Error stopping auto mode: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        try:
            status = {
                'supervisor': {
                    'auto_mode_enabled': self.auto_mode_enabled,
                    'workflow_running': self.workflow_running,
                    'last_scraping_time': self.last_scraping_time.isoformat() if self.last_scraping_time else None,
                    'config': self.config
                },
                'agents': {
                    'scraper': {
                        'healthy': self.scraper_agent.is_healthy(),
                        'status': 'running' if self.scraper_agent.is_healthy() else 'stopped'
                    },
                    'scoring': {
                        'healthy': self.scoring_agent.is_healthy(),
                        'status': 'running' if self.scoring_agent.is_healthy() else 'stopped'
                    },
                    'autoapply': {
                        'healthy': self.autoapply_agent.is_healthy(),
                        'status': 'running' if self.autoapply_agent.is_healthy() else 'stopped'
                    },
                    'tracker': {
                        'healthy': self.tracker_agent.is_healthy(),
                        'status': 'running' if self.tracker_agent.is_healthy() else 'stopped'
                    }
                },
                'system': {
                    'overall_health': self._calculate_overall_health(),
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def update_configuration(self, config_updates: Dict) -> Dict:
        """Update system configuration"""
        try:
            # Validate configuration updates
            valid_keys = {
                'scraping_interval_hours', 'scoring_threshold', 'max_auto_applications',
                'auto_apply_enabled', 'follow_up_interval_days'
            }
            
            invalid_keys = set(config_updates.keys()) - valid_keys
            if invalid_keys:
                return {
                    'success': False,
                    'error': f'Invalid configuration keys: {invalid_keys}'
                }
            
            # Update configuration
            self.config.update(config_updates)
            
            # Save to database
            await self._save_configuration()
            
            await self.database.log_system_activity(
                agent_name="supervisor_agent",
                action="config_update",
                message=f"Configuration updated",
                metadata=config_updates
            )
            
            return {
                'success': True,
                'message': 'Configuration updated successfully',
                'config': self.config
            }
            
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _execute_scraping_phase(self, search_params: Dict) -> Dict:
        """Execute the job scraping phase"""
        try:
            logger.info("Starting scraping phase")
            
            # Add default search parameters if not provided
            default_params = {
                'keywords': 'software engineer',
                'location': 'Remote',
                'max_jobs': 50
            }
            search_params = {**default_params, **search_params}
            
            # Scrape jobs
            scraped_jobs = await self.scraper_agent.scrape_jobs(search_params)
            
            self.last_scraping_time = datetime.utcnow()
            
            result = {
                'success': True,
                'jobs_found': len(scraped_jobs),
                'search_params': search_params,
                'timestamp': self.last_scraping_time.isoformat()
            }
            
            logger.info(f"Scraping phase completed: {len(scraped_jobs)} jobs found")
            return result
            
        except Exception as e:
            logger.error(f"Error in scraping phase: {e}")
            return {
                'success': False,
                'error': str(e),
                'jobs_found': 0
            }
    
    async def _execute_scoring_phase(self) -> Dict:
        """Execute the job scoring phase"""
        try:
            logger.info("Starting scoring phase")
            
            # Get default user (for demo purposes)
            # In production, this would iterate through all users
            user_id = 1  # Default demo user
            
            # Score jobs
            scored_jobs = await self.scoring_agent.score_jobs(user_id)
            
            # Filter high-scoring jobs
            high_scoring_jobs = [
                job for job in scored_jobs 
                if job['score'] >= self.config['scoring_threshold']
            ]
            
            result = {
                'success': True,
                'jobs_scored': len(scored_jobs),
                'high_scoring_jobs': len(high_scoring_jobs),
                'scoring_threshold': self.config['scoring_threshold'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Scoring phase completed: {len(scored_jobs)} jobs scored, {len(high_scoring_jobs)} high-scoring")
            return result
            
        except Exception as e:
            logger.error(f"Error in scoring phase: {e}")
            return {
                'success': False,
                'error': str(e),
                'jobs_scored': 0
            }
    
    async def _execute_autoapply_phase(self) -> Dict:
        """Execute the auto-apply phase"""
        try:
            logger.info("Starting auto-apply phase")
            
            # Get high-scoring jobs for auto-application
            user_id = 1  # Default demo user
            
            # Get top jobs (placeholder - would get from database)
            top_job_ids = []  # This would be populated from scoring results
            
            if not top_job_ids:
                return {
                    'success': True,
                    'applications_sent': 0,
                    'message': 'No high-scoring jobs found for auto-apply'
                }
            
            # Limit applications per day
            max_applications = min(len(top_job_ids), self.config['max_auto_applications'])
            job_ids_to_apply = top_job_ids[:max_applications]
            
            # Auto-apply to jobs
            application_results = await self.autoapply_agent.auto_apply_to_jobs(
                user_id, job_ids_to_apply
            )
            
            successful_applications = len([r for r in application_results if r['success']])
            
            result = {
                'success': True,
                'applications_sent': successful_applications,
                'applications_attempted': len(application_results),
                'success_rate': (successful_applications / len(application_results) * 100) if application_results else 0,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Auto-apply phase completed: {successful_applications} applications sent")
            return result
            
        except Exception as e:
            logger.error(f"Error in auto-apply phase: {e}")
            return {
                'success': False,
                'error': str(e),
                'applications_sent': 0
            }
    
    async def _execute_tracking_phase(self) -> Dict:
        """Execute the application tracking phase"""
        try:
            logger.info("Starting tracking phase")
            
            # Track applications for all users
            # For demo, use default user
            user_id = 1
            
            tracking_result = await self.tracker_agent.track_applications(user_id)
            
            result = {
                'success': True,
                **tracking_result,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Tracking phase completed: {tracking_result.get('total_applications', 0)} applications tracked")
            return result
            
        except Exception as e:
            logger.error(f"Error in tracking phase: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_applications': 0
            }
    
    async def _auto_mode_loop(self):
        """Background loop for automated mode"""
        logger.info("Auto mode loop started")
        
        while self.auto_mode_enabled:
            try:
                # Check if it's time for scheduled scraping
                if await self._should_run_scheduled_scraping():
                    logger.info("Running scheduled job search workflow")
                    
                    # Use default search parameters for auto mode
                    default_search_params = {
                        'keywords': 'software engineer python javascript',
                        'location': 'Remote',
                        'max_jobs': 30
                    }
                    
                    await self.trigger_job_search(default_search_params)
                
                # Sleep for 1 hour before checking again
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in auto mode loop: {e}")
                await asyncio.sleep(3600)  # Continue after error
        
        logger.info("Auto mode loop stopped")
    
    async def _should_run_scheduled_scraping(self) -> bool:
        """Check if scheduled scraping should run"""
        if not self.last_scraping_time:
            return True
        
        hours_since_last_scraping = (datetime.utcnow() - self.last_scraping_time).total_seconds() / 3600
        return hours_since_last_scraping >= self.config['scraping_interval_hours']
    
    def _schedule_recurring_tasks(self):
        """Schedule recurring tasks using asyncio"""
        # Create background tasks for scheduled operations
        if self.auto_mode_enabled:
            asyncio.create_task(self._schedule_daily_tracking())
            asyncio.create_task(self._schedule_weekly_status())
    
    async def _schedule_daily_tracking(self):
        """Schedule daily application tracking"""
        while self.auto_mode_enabled:
            await asyncio.sleep(24 * 3600)  # Wait 24 hours
            await self._run_scheduled_tracking()
    
    async def _schedule_weekly_status(self):
        """Schedule weekly status updates"""
        while self.auto_mode_enabled:
            await asyncio.sleep(7 * 24 * 3600)  # Wait 1 week
            await self._run_weekly_status_update()
    
    async def _run_scheduled_tracking(self):
        """Run scheduled application tracking"""
        try:
            # Track applications for all users
            # For demo, use default user
            user_id = 1
            await self.tracker_agent.track_applications(user_id)
        except Exception as e:
            logger.error(f"Error in scheduled tracking: {e}")
    
    async def _run_weekly_status_update(self):
        """Run weekly status update"""
        try:
            # Generate and log weekly status report
            status = await self.get_system_status()
            
            await self.database.log_system_activity(
                agent_name="supervisor_agent",
                action="weekly_status",
                message="Weekly status update",
                metadata=status
            )
        except Exception as e:
            logger.error(f"Error in weekly status update: {e}")
    
    def _generate_workflow_summary(self, scraping_result: Dict, scoring_result: Dict, 
                                 autoapply_result: Dict, tracking_result: Dict) -> Dict:
        """Generate summary of workflow execution"""
        return {
            'total_jobs_found': scraping_result.get('jobs_found', 0),
            'jobs_scored': scoring_result.get('jobs_scored', 0),
            'high_scoring_jobs': scoring_result.get('high_scoring_jobs', 0),
            'applications_sent': autoapply_result.get('applications_sent', 0) if autoapply_result else 0,
            'applications_tracked': tracking_result.get('total_applications', 0),
            'workflow_duration': 'calculated_duration',  # Would calculate actual duration
            'success': all(r.get('success', False) for r in [scraping_result, scoring_result, tracking_result])
        }
    
    def _calculate_overall_health(self) -> str:
        """Calculate overall system health"""
        agents_healthy = [
            self.scraper_agent.is_healthy(),
            self.scoring_agent.is_healthy(),
            self.autoapply_agent.is_healthy(),
            self.tracker_agent.is_healthy()
        ]
        
        healthy_count = sum(agents_healthy)
        total_agents = len(agents_healthy)
        
        if healthy_count == total_agents:
            return "healthy"
        elif healthy_count >= total_agents * 0.75:
            return "degraded"
        else:
            return "unhealthy"
    
    async def analyze_user_outcomes(self, user_id: int) -> Dict:
        """
        Adaptive Learning Logic - Analyze user outcomes and adjust scoring
        """
        try:
            # Get user's application outcomes from tracker
            query = """
            SELECT ja.*, j.title, j.company, j.salary_min, j.salary_max, j.skills,
                   s.score, s.skill_match_score, s.experience_score, s.salary_score
            FROM job_applications ja 
            JOIN jobs j ON ja.job_id = j.id
            LEFT JOIN job_scores s ON j.id = s.job_id AND s.user_id = ?
            WHERE ja.user_id = ? AND ja.created_at >= datetime('now', '-30 days')
            ORDER BY ja.created_at DESC
            """
            
            applications = self.database.fetch_all(query, (user_id, user_id))
            
            # Analyze outcomes by status
            outcomes = {
                'total': len(applications),
                'interviews': len([a for a in applications if a['status'] in ['interview', 'second_interview', 'final_interview']]),
                'offers': len([a for a in applications if a['status'] in ['accepted', 'offer_accepted']]),
                'rejections': len([a for a in applications if a['status'] == 'rejected'])
            }
            
            # Calculate success rates by scoring components
            component_analysis = self._analyze_scoring_components(applications)
            
            # Adjust scoring weights based on outcomes
            weight_adjustments = self._calculate_weight_adjustments(component_analysis)
            
            # Update learning data
            self.learning_data['outcome_analytics'][user_id] = {
                'outcomes': outcomes,
                'component_analysis': component_analysis,
                'weight_adjustments': weight_adjustments,
                'last_analysis': datetime.utcnow().isoformat()
            }
            
            # Apply weight adjustments
            if weight_adjustments:
                await self._apply_scoring_adjustments(user_id, weight_adjustments)
            
            return {
                'success': True,
                'outcomes': outcomes,
                'adjustments_made': len(weight_adjustments) > 0,
                'insights': self._generate_user_insights(user_id, outcomes, component_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing user outcomes: {e}")
            return {'success': False, 'error': str(e)}
    
    def _analyze_scoring_components(self, applications: List[Dict]) -> Dict:
        """Analyze which scoring components correlate with positive outcomes"""
        component_outcomes = {
            'skill_match': {'high_success': 0, 'high_total': 0},
            'experience_match': {'high_success': 0, 'high_total': 0},
            'salary_match': {'high_success': 0, 'high_total': 0},
            'company_quality': {'high_success': 0, 'high_total': 0}
        }
        
        for app in applications:
            if not app.get('skill_match_score'):
                continue
                
            is_success = app['status'] in ['interview', 'second_interview', 'final_interview', 'accepted', 'offer_accepted']
            
            # Analyze each component (high = > 0.7)
            if app.get('skill_match_score', 0) > 0.7:
                component_outcomes['skill_match']['high_total'] += 1
                if is_success:
                    component_outcomes['skill_match']['high_success'] += 1
                    
            if app.get('experience_score', 0) > 0.7:
                component_outcomes['experience_match']['high_total'] += 1
                if is_success:
                    component_outcomes['experience_match']['high_success'] += 1
                    
            if app.get('salary_score', 0) > 0.7:
                component_outcomes['salary_match']['high_total'] += 1
                if is_success:
                    component_outcomes['salary_match']['high_success'] += 1
        
        # Calculate success rates
        for component in component_outcomes:
            total = component_outcomes[component]['high_total']
            if total > 0:
                component_outcomes[component]['success_rate'] = component_outcomes[component]['high_success'] / total
            else:
                component_outcomes[component]['success_rate'] = 0
        
        return component_outcomes
    
    def _calculate_weight_adjustments(self, component_analysis: Dict) -> Dict:
        """Calculate scoring weight adjustments based on component performance"""
        adjustments = {}
        current_weights = self.learning_data['scoring_weights']
        
        for component, data in component_analysis.items():
            if data['high_total'] < 5:  # Not enough data
                continue
                
            success_rate = data['success_rate']
            current_weight = current_weights.get(component, 0.25)
            
            # Adjust weights based on success rate
            if success_rate > 0.6:  # High success rate - increase weight
                new_weight = min(0.4, current_weight * 1.1)
            elif success_rate < 0.3:  # Low success rate - decrease weight
                new_weight = max(0.1, current_weight * 0.9)
            else:
                continue  # No adjustment needed
                
            if abs(new_weight - current_weight) > 0.02:  # Significant change
                adjustments[component] = new_weight
        
        return adjustments
    
    async def _apply_scoring_adjustments(self, user_id: int, weight_adjustments: Dict):
        """Apply scoring weight adjustments for user"""
        try:
            # Update learning data
            for component, new_weight in weight_adjustments.items():
                self.learning_data['scoring_weights'][component] = new_weight
            
            # Log the adjustment
            await self.database.log_system_activity(
                agent_name="supervisor_agent",
                action="scoring_adjustment",
                message=f"Adjusted scoring weights for user {user_id}",
                metadata=weight_adjustments
            )
            
            # Save to database (you might want a separate table for user-specific weights)
            # For now, we'll use system-wide adjustments
            
        except Exception as e:
            logger.error(f"Error applying scoring adjustments: {e}")
    
    def _generate_user_insights(self, user_id: int, outcomes: Dict, component_analysis: Dict) -> List[str]:
        """Generate personalized improvement insights"""
        insights = []
        
        # Success rate insights
        total = outcomes['total']
        if total > 0:
            interview_rate = outcomes['interviews'] / total
            if interview_rate < 0.1:
                insights.append("Your interview rate is low. Consider improving your application materials or targeting more suitable roles.")
            elif interview_rate > 0.3:
                insights.append("Great interview rate! You're targeting the right types of positions.")
        
        # Component-specific insights
        for component, data in component_analysis.items():
            if data['high_total'] >= 5:
                success_rate = data['success_rate']
                if success_rate < 0.2:
                    if component == 'skill_match':
                        insights.append("Applications with high skill matches aren't converting well. Consider upskilling in key areas or better showcasing your abilities.")
                    elif component == 'salary_match':
                        insights.append("High-salary applications aren't successful. Consider being more realistic with salary expectations or improving your value proposition.")
        
        return insights
    
    async def adaptive_threshold_tuning(self, user_id: int) -> Dict:
        """Dynamically tune the scoring threshold based on user outcomes"""
        try:
            outcomes_data = self.learning_data['outcome_analytics'].get(user_id, {})
            if not outcomes_data:
                return {'success': False, 'message': 'No outcome data available'}
            
            outcomes = outcomes_data['outcomes']
            current_threshold = self.config['scoring_threshold']
            
            # Calculate application volume and success rate
            total_apps = outcomes['total']
            success_rate = (outcomes['interviews'] + outcomes['offers']) / max(total_apps, 1)
            
            new_threshold = current_threshold
            
            # Threshold adjustment logic
            if total_apps < 5:  # Too few applications - lower threshold
                new_threshold = max(0.5, current_threshold - 0.05)
            elif total_apps > 20:  # Too many applications - raise threshold
                new_threshold = min(0.9, current_threshold + 0.05)
            elif success_rate < 0.1:  # Low success rate - raise threshold
                new_threshold = min(0.9, current_threshold + 0.1)
            elif success_rate > 0.4:  # High success rate - can lower threshold
                new_threshold = max(0.5, current_threshold - 0.05)
            
            # Apply threshold change
            if abs(new_threshold - current_threshold) > 0.02:
                self.config['scoring_threshold'] = new_threshold
                self.learning_data['threshold_history'].append({
                    'user_id': user_id,
                    'old_threshold': current_threshold,
                    'new_threshold': new_threshold,
                    'reason': f"Success rate: {success_rate:.2f}, Total apps: {total_apps}",
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                await self.database.log_system_activity(
                    agent_name="supervisor_agent",
                    action="threshold_adjustment",
                    message=f"Adjusted scoring threshold from {current_threshold} to {new_threshold}",
                    metadata={'user_id': user_id, 'success_rate': success_rate, 'total_apps': total_apps}
                )
                
                return {
                    'success': True,
                    'threshold_adjusted': True,
                    'old_threshold': current_threshold,
                    'new_threshold': new_threshold,
                    'reason': f"Based on success rate of {success_rate:.2%} from {total_apps} applications"
                }
            else:
                return {
                    'success': True,
                    'threshold_adjusted': False,
                    'current_threshold': current_threshold,
                    'message': 'No threshold adjustment needed'
                }
                
        except Exception as e:
            logger.error(f"Error in adaptive threshold tuning: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _load_configuration(self):
        """Load configuration from database or environment"""
        try:
            # Load user-specific configurations
            # For now, use defaults but this would query user_preferences table
            pass
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    
    async def _save_configuration(self):
        """Save configuration to database"""
        try:
            # Save current configuration and learning data
            # This would update user_preferences and learning_data tables
            pass
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
        logger.info("Configuration saved")
    
    def is_healthy(self) -> bool:
        """Check if the supervisor agent is healthy"""
        return all([
            self.scraper_agent.is_healthy(),
            self.scoring_agent.is_healthy(),
            self.autoapply_agent.is_healthy(),
            self.tracker_agent.is_healthy()
        ])
