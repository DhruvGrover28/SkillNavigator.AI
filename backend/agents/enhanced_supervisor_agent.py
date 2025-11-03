#!/usr/bin/env python3
"""
Enhanced Supervisor Agent - Orchestrates job scraping, scoring, and filtering
Handles the complete workflow: Schedule → Scrape → Score → Filter → Store

Features:
- Automated scheduling (every 12 hours)
- Job scraping coordination
- AI-powered job scoring
- Score-based filtering
- Database management
- User preference integration
"""

import os
import sqlite3
import schedule
import time
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import json

# Import our agents
try:
    from agents.enhanced_scraper_agent import EnhancedScraperAgent
    HAS_SCRAPER = True
except ImportError:
    HAS_SCRAPER = False
    print("⚠️  Enhanced scraper agent not available")

try:
    from agents.job_scoring_agent import JobScoringAgent
    HAS_SCORING = True
except ImportError:
    HAS_SCORING = False
    print("⚠️  Job scoring agent not available")

try:
    from agents.resume_parser_agent import ResumeParserAgent
    HAS_PARSER = True
except ImportError:
    HAS_PARSER = False
    print("⚠️  Resume parser agent not available")

class EnhancedSupervisorAgent:
    """
    Enhanced supervisor agent that orchestrates the complete job matching workflow
    
    Workflow:
    1. Schedule: Runs every 12 hours (configurable)
    2. Scrape: Multi-source job scraping
    3. Score: AI-powered candidate-job matching
    4. Filter: Remove poor matches (< threshold)
    5. Store: Save scored jobs to database
    6. Notify: Update frontend with new matches
    """
    
    def __init__(self, db_path: str = "skillnavigator.db"):
        """Initialize supervisor with database connection and agents"""
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        
        # Initialize agents
        self.scraper = EnhancedScraperAgent() if HAS_SCRAPER else None
        self.scoring_agent = JobScoringAgent() if HAS_SCORING else None
        self.resume_parser = ResumeParserAgent() if HAS_PARSER else None
        
        # Configuration
        self.config = {
            'scraping_interval_hours': 12,
            'scoring_threshold': 40.0,  # Filter out jobs with score < 40 (Poor Fit)
            'max_jobs_per_run': 100,
            'auto_scoring_enabled': True,
            'sources': ['remoteok', 'weworkremotely'],  # Default sources
        }
        
        # State tracking
        self.last_run_time = None
        self.is_running = False
        self.scheduler_thread = None
        self.stats = {
            'total_runs': 0,
            'jobs_scraped': 0,
            'jobs_scored': 0,
            'jobs_filtered': 0,
            'jobs_stored': 0
        }
        
        self.logger.info("Enhanced Supervisor Agent initialized")
    
    def start_scheduler(self):
        """Start the automated scheduling system"""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.logger.warning("Scheduler already running")
            return
        
        # Schedule the workflow
        schedule.every(self.config['scraping_interval_hours']).hours.do(self._run_workflow)
        
        # Also schedule a manual run in 30 seconds for testing
        schedule.every(30).seconds.do(self._run_workflow).tag('initial')
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info(f"Scheduler started - will run every {self.config['scraping_interval_hours']} hours")
    
    def stop_scheduler(self):
        """Stop the automated scheduling system"""
        schedule.clear()
        if self.scheduler_thread:
            self.scheduler_thread = None
        self.logger.info("Scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop (runs in separate thread)"""
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def _run_workflow(self):
        """Run the complete job matching workflow"""
        if self.is_running:
            self.logger.warning("Workflow already running, skipping this cycle")
            return
        
        # Run the async workflow
        asyncio.run(self._run_async_workflow())
    
    async def _run_async_workflow(self):
        """Async version of the workflow"""
        self.is_running = True
        start_time = datetime.now()
        
        try:
            self.logger.info("🚀 Starting automated job matching workflow")
            
            # Step 1: Get user preferences for scoring
            user_preferences = self._get_user_preferences()
            has_user_preferences = user_preferences is not None
            
            if not has_user_preferences:
                self.logger.info("📋 No user preferences - using broad search & relaxed filtering")
                user_preferences = self._get_demo_preferences()
                # Lower threshold for users without preferences (show more jobs)
                self.config['scoring_threshold'] = 15.0
            else:
                self.logger.info("👤 User preferences found - using personalized search & scoring")
                # Higher threshold for users with preferences (quality matches)
                self.config['scoring_threshold'] = 40.0
            
            # Step 2: Scrape jobs (personalized if preferences available)
            scraped_jobs = await self._scrape_jobs(user_preferences, has_user_preferences)
            if not scraped_jobs:
                self.logger.warning("No jobs scraped, ending workflow")
                return
            
            # Step 3: Score jobs
            scored_jobs = self._score_jobs(scraped_jobs, user_preferences)
            if not scored_jobs:
                self.logger.warning("No jobs scored, ending workflow")
                return
            
            # Step 4: Filter jobs by score
            filtered_jobs = self._filter_jobs(scored_jobs)
            
            # Step 5: Store results
            stored_count = self._store_jobs(filtered_jobs)
            
            # Step 6: Update statistics
            self._update_stats(len(scraped_jobs), len(scored_jobs), len(filtered_jobs), stored_count)
            
            # Clear initial run tag after first execution
            schedule.clear('initial')
            
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"✅ Workflow completed in {duration:.1f}s - {stored_count} jobs stored")
            
        except Exception as e:
            self.logger.error(f"❌ Workflow failed: {str(e)}")
        finally:
            self.is_running = False
            self.last_run_time = datetime.now()
    
    async def _scrape_jobs(self, user_preferences: Dict[str, Any], has_preferences: bool) -> List[Dict[str, Any]]:
        """Scrape jobs from configured sources with personalized keywords"""
        if not self.scraper:
            self.logger.warning("Scraper not available, using mock data")
            return self._get_mock_jobs()
        
        try:
            # Configure scraper with search parameters
            max_jobs = self.config.get('max_jobs_per_run', 100)
            
            # Use personalized keywords if available
            if has_preferences and user_preferences.get('skills'):
                # Extract top skills for targeted scraping
                keywords = user_preferences['skills'][:5]  # Use top 5 skills
                keyword_string = ' '.join(keywords)
                self.logger.info(f"🎯 Personalized search using skills: {keywords}")
            else:
                # Broad search for users without preferences
                keyword_string = 'developer software engineer programmer'
                self.logger.info("🌐 Broad search for all users")
            
            search_params = {
                'keywords': keyword_string,
                'location': 'remote',
                'max_results': max_jobs
            }
            
            # Scrape jobs using the enhanced scraper
            job_listings = await self.scraper.scrape_jobs(search_params)
            
            # Convert JobListing objects to dictionaries
            jobs = []
            for job_listing in job_listings:
                job_dict = {
                    'title': job_listing.title,
                    'company': job_listing.company,
                    'location': job_listing.location,
                    'description': job_listing.description,
                    'url': job_listing.url,
                    'salary': job_listing.salary,
                    'date_posted': job_listing.date_posted,
                    'job_type': job_listing.job_type,
                    'source': 'enhanced_scraper'
                }
                jobs.append(job_dict)
            
            self.logger.info(f"Total jobs scraped: {len(jobs)}")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            return []
    
    def _score_jobs(self, jobs: List[Dict[str, Any]], user_preferences: Dict[str, Any]) -> List[Tuple[Dict[str, Any], Any]]:
        """Score jobs against user preferences"""
        if not self.scoring_agent:
            self.logger.warning("Scoring agent not available, using mock scores")
            return [(job, self._mock_scoring_result(75.0)) for job in jobs]
        
        try:
            # Use batch scoring for efficiency
            scored_jobs = self.scoring_agent.batch_score_jobs(
                resume_data=user_preferences,
                jobs=jobs,
                filter_threshold=self.config['scoring_threshold']
            )
            
            self.logger.info(f"Scored {len(scored_jobs)} jobs (filtered {len(jobs) - len(scored_jobs)} poor matches)")
            return scored_jobs
            
        except Exception as e:
            self.logger.error(f"Scoring failed: {e}")
            return []
    
    def _filter_jobs(self, scored_jobs: List[Tuple[Dict[str, Any], Any]]) -> List[Tuple[Dict[str, Any], Any]]:
        """Apply additional filtering logic"""
        threshold = self.config['scoring_threshold']
        filtered = [(job, score) for job, score in scored_jobs if score.total_score >= threshold]
        
        self.logger.info(f"Filtered jobs: {len(filtered)} kept, {len(scored_jobs) - len(filtered)} removed (< {threshold})")
        return filtered
    
    def _store_jobs(self, filtered_jobs: List[Tuple[Dict[str, Any], Any]]) -> int:
        """Store scored and filtered jobs in database"""
        if not filtered_jobs:
            return 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ensure jobs table exists with scoring columns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    description TEXT,
                    url TEXT UNIQUE,
                    source TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    score REAL,
                    classification TEXT,
                    score_breakdown TEXT,
                    score_explanation TEXT,
                    is_filtered BOOLEAN DEFAULT 0
                )
            ''')
            
            stored_count = 0
            for job, scoring_result in filtered_jobs:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO jobs 
                        (title, company, location, description, apply_url, source, match_score, 
                         classification, score_breakdown, score_explanation)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        job.get('title', ''),
                        job.get('company', ''),
                        job.get('location', ''),
                        job.get('description', ''),
                        job.get('url', ''),
                        job.get('source', ''),
                        float(scoring_result.total_score),
                        scoring_result.classification,
                        json.dumps({k: float(v) for k, v in scoring_result.section_scores.items()}),
                        scoring_result.explanation
                    ))
                    stored_count += 1
                except sqlite3.IntegrityError:
                    # Job already exists (duplicate URL)
                    continue
                except Exception as e:
                    self.logger.error(f"Error storing job: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Stored {stored_count} jobs in database")
            return stored_count
            
        except Exception as e:
            self.logger.error(f"Database storage failed: {e}")
            return 0
    
    def _get_user_preferences(self) -> Optional[Dict[str, Any]]:
        """Get saved user preferences from database (from resume parsing or manual entry)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check users table for parsed resume data first
            cursor.execute('''
                SELECT skills, preferences FROM users 
                WHERE (skills IS NOT NULL AND skills != '') OR (preferences IS NOT NULL AND preferences != '')
                ORDER BY updated_at DESC LIMIT 1
            ''')
            
            user_result = cursor.fetchone()
            
            if user_result and (user_result[0] or user_result[1]):
                # User has saved preferences from resume or manual entry
                skills_json, preferences_json = user_result
                
                skills = []
                experience = []
                education = []
                
                if skills_json:
                    skills = json.loads(skills_json) if skills_json != '' else []
                
                if preferences_json:
                    prefs = json.loads(preferences_json) if preferences_json != '' else {}
                    experience = prefs.get('experience', [])
                    education = prefs.get('education', [])
                
                conn.close()
                self.logger.info(f"Using saved user preferences: {len(skills)} skills found")
                
                return {
                    'skills': skills,
                    'experience': experience,
                    'education': education
                }
            
            # Fallback: check user_preferences table
            cursor.execute('''
                SELECT skills, experience, education FROM user_preferences 
                ORDER BY created_at DESC LIMIT 1
            ''')
            
            pref_result = cursor.fetchone()
            conn.close()
            
            if pref_result and any(pref_result):
                self.logger.info("Using manual preferences from user_preferences table")
                return {
                    'skills': pref_result[0].split(',') if pref_result[0] else [],
                    'experience': [{'description': pref_result[1] or ''}],
                    'education': [{'degree': pref_result[2] or ''}]
                }
            
            # No preferences found
            self.logger.info("No user preferences found - will show all jobs")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting user preferences: {e}")
            return None
    
    def _get_demo_preferences(self) -> Dict[str, Any]:
        """Get demo user preferences for testing"""
        return {
            'skills': ['Python', 'JavaScript', 'React', 'Node.js', 'SQL', 'Machine Learning'],
            'experience': [
                {
                    'title': 'Software Developer',
                    'company': 'Tech Corp',
                    'description': 'Developed web applications using modern technologies'
                }
            ],
            'education': [
                {
                    'degree': 'Bachelor of Technology',
                    'field': 'Computer Science',
                    'institution': 'Tech University'
                }
            ]
        }
    
    def _get_mock_jobs(self) -> List[Dict[str, Any]]:
        """Get mock jobs for testing when scraper is unavailable"""
        return [
            {
                'title': 'Python Developer',
                'company': 'Tech Startup',
                'location': 'Remote',
                'description': 'Python developer with React experience needed for web development',
                'url': 'https://example.com/job1',
                'source': 'mock'
            },
            {
                'title': 'Full Stack Engineer',
                'company': 'Innovation Corp',
                'location': 'Remote',
                'description': 'Full stack engineer with JavaScript, Node.js, and SQL experience',
                'url': 'https://example.com/job2',
                'source': 'mock'
            }
        ]
    
    def _mock_scoring_result(self, score: float):
        """Create mock scoring result for testing"""
        class MockResult:
            def __init__(self, score):
                self.total_score = score
                self.classification = "Good Fit" if score >= 60 else "Fair Fit"
                self.section_scores = {'skills': score, 'experience': score, 'education': score}
                self.explanation = f"Mock scoring result with {score}% match"
        
        return MockResult(score)
    
    def _update_stats(self, scraped: int, scored: int, filtered: int, stored: int):
        """Update workflow statistics"""
        self.stats['total_runs'] += 1
        self.stats['jobs_scraped'] += scraped
        self.stats['jobs_scored'] += scored
        self.stats['jobs_filtered'] += filtered
        self.stats['jobs_stored'] += stored
    
    def get_status(self) -> Dict[str, Any]:
        """Get current supervisor status"""
        return {
            'is_running': self.is_running,
            'last_run_time': self.last_run_time.isoformat() if self.last_run_time else None,
            'config': self.config,
            'stats': self.stats,
            'agents_available': {
                'scraper': HAS_SCRAPER,
                'scoring': HAS_SCORING,
                'parser': HAS_PARSER
            }
        }
    
    def manual_run(self) -> Dict[str, Any]:
        """Manually trigger the workflow (for testing/debugging)"""
        if self.is_running:
            return {'success': False, 'error': 'Workflow already running'}
        
        try:
            # Run workflow in a separate thread to avoid blocking
            threading.Thread(target=self._run_workflow, daemon=True).start()
            return {'success': True, 'message': 'Workflow started'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Demo function
def demo_supervisor():
    """Demo the supervisor agent functionality"""
    print("=== Enhanced Supervisor Agent Demo ===")
    
    supervisor = EnhancedSupervisorAgent()
    
    # Show initial status
    status = supervisor.get_status()
    print(f"Agents available: {status['agents_available']}")
    
    # Manual run
    print("Starting manual workflow run...")
    result = supervisor.manual_run()
    print(f"Manual run result: {result}")
    
    # Wait a bit and check status
    import time
    time.sleep(2)
    status = supervisor.get_status()
    print(f"Current status: {status}")

if __name__ == "__main__":
    demo_supervisor()