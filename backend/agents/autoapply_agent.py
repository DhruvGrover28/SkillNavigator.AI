"""
Auto-Apply Agent - Automated Job Application
Automatically fills out job applications and generates personalized cover letters
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json
import requests
import time

# Optional Playwright imports for future use
try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = Browser = None

from database.db_connection import database
from utils.prompt_templates import CoverLetterGenerator
from utils.scraper_helpers import wait_random_delay

logger = logging.getLogger(__name__)


class AutoApplyAgent:
    """Autonomous agent for automatically applying to jobs"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.cover_letter_generator = CoverLetterGenerator()
        self.applications_today = 0
        self.max_applications_per_day = int(os.getenv("MAX_APPLICATIONS_PER_DAY", 10))
        
        # Enhanced error handling and retry settings
        self.max_retries = 3
        self.retry_delay_base = 5  # seconds
        self.fallback_strategies = ['http_form', 'email', 'manual']
        self.success_rate_threshold = 0.3  # Switch methods if success rate < 30%
        
        # Track method performance for optimization
        self.method_stats = {
            'linkedin': {'attempts': 0, 'successes': 0},
            'indeed': {'attempts': 0, 'successes': 0},
            'internshala': {'attempts': 0, 'successes': 0},
            'email': {'attempts': 0, 'successes': 0},
            'form': {'attempts': 0, 'successes': 0},
            'http_form': {'attempts': 0, 'successes': 0}
        }
        
        # Application methods
        self.application_handlers = {
            'linkedin': self._apply_linkedin,
            'indeed': self._apply_indeed,
            'internshala': self._apply_internshala,
            'email': self._apply_via_email,
            'form': self._apply_via_form,
            'http_form': self._apply_http_form
        }
    
    async def initialize(self):
        """Initialize the auto-apply agent"""
        try:
            # For Windows compatibility, use a simple HTTP-based approach
            import platform
            
            # Create an HTTP session for making requests
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            self.browser = "http_session"  # Mark as using HTTP session
            
            await self.cover_letter_generator.initialize()
            
            # Get today's application count
            self.applications_today = await self._get_applications_today()
            
            logger.info("Auto-apply agent initialized successfully with HTTP session")
            
        except Exception as e:
            logger.error(f"Failed to initialize auto-apply agent: {e}")
            # Don't raise the exception, allow graceful degradation
            self.browser = None
    
    async def _init_playwright(self):
        """Initialize Playwright browser"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--disable-web-security']
            )
        except NotImplementedError as e:
            logger.error(f"Playwright subprocess creation failed (likely Windows compatibility issue): {e}")
            logger.warning("Auto-apply functionality will be disabled")
            self.browser = None
        except Exception as e:
            logger.error(f"Playwright initialization failed: {e}")
            self.browser = None
    
    async def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'session') and self.session:
            # For requests.Session, just close it (non-async)
            self.session.close()
        if self.page and PLAYWRIGHT_AVAILABLE:
            await self.page.close()
        if self.browser and self.browser != "http_session" and PLAYWRIGHT_AVAILABLE:
            await self.browser.close()
    
    async def auto_apply_to_jobs(self, user_id: int, job_ids: List[int]) -> List[Dict]:
        """
        Automatically apply to a list of jobs for a user
        
        Args:
            user_id: User ID
            job_ids: List of job IDs to apply to
            
        Returns:
            List of application results
        """
        results = []
        
        # Check if auto-apply is available (browser or HTTP session initialized)
        if not self.browser:
            logger.error("Auto-apply functionality not available - neither browser nor HTTP session initialized")
            return [{"job_id": job_id, "success": False, "status": "failed", "reason": "Auto-apply not available"} for job_id in job_ids]
        
        # Check daily limit
        if self.applications_today >= self.max_applications_per_day:
            logger.warning(f"Daily application limit reached ({self.max_applications_per_day})")
            return results
        
        # Get user profile
        user_profile = await self._get_user_profile(user_id)
        if not user_profile:
            raise ValueError(f"User profile not found for user_id: {user_id}")
        
        logger.info(f"Starting auto-apply for {len(job_ids)} jobs for user {user_id}")
        
        await database.log_system_activity(
            agent_name="autoapply_agent",
            action="auto_apply_start",
            message=f"Starting auto-apply for {len(job_ids)} jobs",
            metadata={"user_id": user_id, "job_count": len(job_ids)}
        )
        
        for job_id in job_ids:
            try:
                # Check daily limit
                if self.applications_today >= self.max_applications_per_day:
                    logger.info("Daily application limit reached, stopping")
                    break
                
                # Get job details
                job = await self._get_job_details(job_id)
                if not job:
                    logger.warning(f"Job {job_id} not found")
                    continue
                
                # Check if already applied
                existing_application = await self._check_existing_application(user_id, job_id)
                if existing_application:
                    logger.info(f"Already applied to job {job_id}")
                    continue
                
                # Apply to the job
                application_result = await self._apply_to_job(user_profile, job)
                results.append(application_result)
                
                # Record application in database
                if application_result['success']:
                    await self._record_application(user_id, job_id, application_result)
                    self.applications_today += 1
                
                # Delay between applications
                await wait_random_delay(30, 60)  # 30-60 seconds
                
            except Exception as e:
                logger.error(f"Error applying to job {job_id}: {e}")
                results.append({
                    'job_id': job_id,
                    'success': False,
                    'error': str(e),
                    'method': 'unknown'
                })
        
        await database.log_system_activity(
            agent_name="autoapply_agent",
            action="auto_apply_complete",
            message=f"Completed auto-apply: {len([r for r in results if r['success']])} successful applications",
            metadata={
                "user_id": user_id,
                "total_jobs": len(job_ids),
                "successful_applications": len([r for r in results if r['success']]),
                "failed_applications": len([r for r in results if not r['success']])
            }
        )
        
        return results
    
    async def _apply_to_job(self, user_profile: Dict, job) -> Dict:
        """Apply to a single job using the appropriate method with retry logic"""
        
        # Generate cover letter once
        cover_letter = await self.cover_letter_generator.generate_cover_letter(
            user_profile, job
        )
        
        # Determine primary application method and fallbacks
        primary_method = self._determine_application_method(job)
        methods_to_try = [primary_method]
        
        # Add fallback methods if primary fails
        for fallback in self.fallback_strategies:
            if fallback != primary_method and fallback not in methods_to_try:
                # Check if this fallback is applicable for this job
                if self._is_method_applicable(job, fallback):
                    methods_to_try.append(fallback)
        
        last_error = None
        
        # Try each method with retries
        for method in methods_to_try:
            if method not in self.application_handlers:
                continue
                
            # Track method attempt
            self.method_stats[method]['attempts'] += 1
            
            # Try this method with retries
            for attempt in range(self.max_retries):
                try:
                    logger.info(f"Attempting {method} application for job {job.id} (attempt {attempt + 1})")
                    
                    result = await self.application_handlers[method](
                        user_profile, job, cover_letter
                    )
                    
                    if result['success']:
                        # Track success
                        self.method_stats[method]['successes'] += 1
                        result['cover_letter'] = cover_letter
                        result['attempts_made'] = attempt + 1
                        result['method_tried'] = method
                        logger.info(f"Successfully applied using {method} for job {job.id}")
                        return result
                    else:
                        last_error = result.get('error', 'Unknown error')
                        logger.warning(f"{method} attempt {attempt + 1} failed: {last_error}")
                        
                        # Wait before retry (exponential backoff)
                        if attempt < self.max_retries - 1:
                            delay = self.retry_delay_base * (2 ** attempt)
                            await wait_random_delay(delay, delay + 2)
                        
                except Exception as e:
                    last_error = str(e)
                    logger.error(f"{method} attempt {attempt + 1} threw exception: {e}")
                    
                    # Wait before retry
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay_base * (2 ** attempt)
                        await wait_random_delay(delay, delay + 2)
            
            # If we get here, all retries for this method failed
            logger.warning(f"All {self.max_retries} attempts failed for method {method}")
        
        # All methods failed
        return {
            'job_id': job.id,
            'success': False,
            'error': f'All application methods failed. Last error: {last_error}',
            'methods_tried': methods_to_try,
            'cover_letter': cover_letter,
            'total_attempts': sum(self.max_retries for _ in methods_to_try)
        }
    
    def _determine_application_method(self, job) -> str:
        """Determine the best application method for a job based on success rates and availability"""
        source = getattr(job, 'source', 'unknown')
        apply_url = getattr(job, 'apply_url', '')
        
        # Check success rates and prefer better performing methods
        available_methods = []
        
        # If using HTTP session (not browser), prioritize HTTP-based methods
        if self.browser == "http_session":
            if 'mailto:' in apply_url:
                available_methods.append(('email', self._get_method_success_rate('email')))
            
            # Check for specific platform optimizations
            if any(platform in apply_url.lower() for platform in ['remoteok', 'arbeitnow', 'himalayas']):
                available_methods.append(('http_form', self._get_method_success_rate('http_form')))
            
            if not available_methods:
                available_methods.append(('http_form', self._get_method_success_rate('http_form')))
        else:
            # Browser-based methods with success rate priority
            if source in ['linkedin', 'indeed', 'internshala']:
                rate = self._get_method_success_rate(source)
                if rate > self.success_rate_threshold:
                    available_methods.append((source, rate))
            
            if 'mailto:' in apply_url:
                available_methods.append(('email', self._get_method_success_rate('email')))
            elif apply_url:
                available_methods.append(('form', self._get_method_success_rate('form')))
        
        # Sort by success rate and return the best method
        if available_methods:
            available_methods.sort(key=lambda x: x[1], reverse=True)
            return available_methods[0][0]
        
        return 'manual'
    
    def _get_method_success_rate(self, method: str) -> float:
        """Calculate success rate for a given method"""
        stats = self.method_stats.get(method, {'attempts': 0, 'successes': 0})
        if stats['attempts'] == 0:
            return 1.0  # Assume perfect rate for untested methods
        return stats['successes'] / stats['attempts']
    
    def _is_method_applicable(self, job, method: str) -> bool:
        """Check if a method is applicable for this job"""
        apply_url = getattr(job, 'apply_url', '')
        source = getattr(job, 'source', 'unknown')
        
        if method == 'email':
            return 'mailto:' in apply_url
        elif method == 'http_form':
            return bool(apply_url) and 'mailto:' not in apply_url
        elif method in ['linkedin', 'indeed', 'internshala']:
            return source == method or method in apply_url.lower()
        elif method == 'form':
            return bool(apply_url) and self.browser != "http_session"
        elif method == 'manual':
            return True
        
        return False
    
    async def _apply_http_form(self, user_profile: Dict, job, cover_letter: str) -> Dict:
        """Apply to job using HTTP requests instead of browser automation"""
        try:
            apply_url = getattr(job, 'apply_url', '')
            if not apply_url or 'mailto:' in apply_url:
                return {
                    'job_id': job.id,
                    'success': False,
                    'error': 'No valid application URL found',
                    'method': 'http_form'
                }
            
            # Get the application page to analyze the form
            response = self.session.get(apply_url)
            if response.status_code != 200:
                return {
                    'job_id': job.id,
                    'success': False,
                    'error': f'Failed to access application page: {response.status_code}',
                    'method': 'http_form'
                }
            
            page_content = response.text
            
            # For now, we'll analyze if it's a known job portal and provide specific handling
            if 'linkedin.com' in apply_url:
                return await self._apply_http_linkedin(user_profile, job, cover_letter)
            elif 'indeed.com' in apply_url:
                return await self._apply_http_indeed(user_profile, job, cover_letter)
            else:
                # Generic HTTP form handling
                return await self._apply_http_generic(user_profile, job, cover_letter, page_content)
                    
        except Exception as e:
            logger.error(f"HTTP form application failed for job {job.id}: {e}")
            return {
                'job_id': job.id,
                'success': False,
                'error': f'HTTP request failed: {str(e)}',
                'method': 'http_form'
            }
    
    async def _apply_http_linkedin(self, user_profile: Dict, job, cover_letter: str) -> Dict:
        """Apply to LinkedIn job via HTTP (requires LinkedIn session)"""
        return {
            'job_id': job.id,
            'success': False,
            'error': 'LinkedIn applications require manual login - please apply manually',
            'method': 'http_linkedin',
            'manual_application_required': True
        }
    
    async def _apply_http_indeed(self, user_profile: Dict, job, cover_letter: str) -> Dict:
        """Apply to Indeed job via HTTP"""
        return {
            'job_id': job.id,
            'success': False,
            'error': 'Indeed applications require browser automation - please apply manually',
            'method': 'http_indeed',
            'manual_application_required': True
        }
    
    async def _apply_http_generic(self, user_profile: Dict, job, cover_letter: str, page_content: str) -> Dict:
        """Apply to generic job form via HTTP - ACTUAL WORKING FORM SUBMISSION"""
        try:
            from bs4 import BeautifulSoup
            import re
            from urllib.parse import urljoin, urlparse
            
            apply_url = getattr(job, 'apply_url', '')
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # Find the first form on the page
            form = soup.find('form')
            if not form:
                return {
                    'job_id': job.id,
                    'success': False,
                    'error': 'No form found on application page',
                    'method': 'http_form'
                }
            
            # Get form action URL
            form_action = form.get('action', '')
            if form_action:
                if form_action.startswith('/'):
                    # Relative URL
                    parsed_url = urlparse(apply_url)
                    form_action = f"{parsed_url.scheme}://{parsed_url.netloc}{form_action}"
                elif not form_action.startswith('http'):
                    # Relative to current page
                    form_action = urljoin(apply_url, form_action)
            else:
                form_action = apply_url
            
            # Build form data by analyzing input fields
            form_data = {}
            
            # Find all input fields, textareas, and selects
            form_fields = form.find_all(['input', 'textarea', 'select'])
            
            for field in form_fields:
                field_name = field.get('name', '')
                field_type = field.get('type', 'text')
                
                # Skip buttons, hidden fields, and files for now
                if field_type in ['submit', 'button', 'file', 'hidden']:
                    continue
                
                if not field_name:
                    continue
                
                # Smart field mapping based on common patterns
                field_value = self._get_field_value(field_name, field, user_profile, job, cover_letter)
                
                if field_value:
                    form_data[field_name] = field_value
                    logger.info(f"Mapped field '{field_name}' = '{field_value[:50]}...'")
            
            # Add any hidden fields that might be required
            hidden_fields = form.find_all('input', {'type': 'hidden'})
            for hidden in hidden_fields:
                name = hidden.get('name', '')
                value = hidden.get('value', '')
                if name and value:
                    form_data[name] = value
            
            logger.info(f"Submitting form to: {form_action}")
            logger.info(f"Form data fields: {list(form_data.keys())}")
            
            # Submit the form
            method = form.get('method', 'post').lower()
            if method == 'post':
                response = self.session.post(form_action, data=form_data)
            else:
                response = self.session.get(form_action, params=form_data)
            
            # Check if submission was successful
            success_indicators = [
                'thank you', 'application received', 'successfully submitted',
                'application complete', 'thank you for applying', 
                'your application', 'we have received', 'submission successful'
            ]
            
            response_text = response.text.lower()
            is_success = any(indicator in response_text for indicator in success_indicators)
            
            # Also check for redirect to thank you page
            if response.status_code in [200, 302] and (
                '/thank' in response.url.lower() or 
                '/success' in response.url.lower() or
                '/complete' in response.url.lower()
            ):
                is_success = True
            
            if is_success:
                logger.info(f"✅ FORM SUCCESSFULLY SUBMITTED for job {job.id}")
                return {
                    'job_id': job.id,
                    'success': True,
                    'method': 'http_form',
                    'message': f'✅ Application successfully submitted via form to {job.company}',
                    'form_url': form_action,
                    'response_url': response.url,
                    'fields_submitted': list(form_data.keys())
                }
            else:
                # Form submitted but no clear success indication
                return {
                    'job_id': job.id,
                    'success': False,
                    'error': 'Form submitted but success not confirmed - may have been successful',
                    'method': 'http_form',
                    'form_url': form_action,
                    'response_status': response.status_code,
                    'manual_verification_needed': True
                }
                
        except Exception as e:
            logger.error(f"HTTP form submission failed for job {job.id}: {e}")
            return {
                'job_id': job.id,
                'success': False,
                'error': f'Form submission failed: {str(e)}',
                'method': 'http_form'
            }
    
    def _get_field_value(self, field_name: str, field_element, user_profile: Dict, job, cover_letter: str) -> str:
        """Smart field value mapping based on field name patterns"""
        field_name_lower = field_name.lower()
        
        # Name fields
        if any(pattern in field_name_lower for pattern in ['name', 'fullname', 'full_name', 'applicant_name']):
            return user_profile.get('name', '')
        
        # First name
        if any(pattern in field_name_lower for pattern in ['firstname', 'first_name', 'fname']):
            name = user_profile.get('name', '')
            return name.split()[0] if name else ''
        
        # Last name  
        if any(pattern in field_name_lower for pattern in ['lastname', 'last_name', 'lname', 'surname']):
            name = user_profile.get('name', '')
            return ' '.join(name.split()[1:]) if name and len(name.split()) > 1 else ''
        
        # Email fields
        if any(pattern in field_name_lower for pattern in ['email', 'e_mail', 'mail']):
            return user_profile.get('email', '')
        
        # Phone fields
        if any(pattern in field_name_lower for pattern in ['phone', 'telephone', 'mobile', 'contact']):
            return user_profile.get('phone', '')
        
        # Cover letter / message fields
        if any(pattern in field_name_lower for pattern in [
            'cover', 'letter', 'message', 'motivation', 'why', 'interest', 
            'additional', 'comments', 'notes', 'description'
        ]):
            return cover_letter
        
        # Position/job title fields
        if any(pattern in field_name_lower for pattern in ['position', 'job', 'role', 'title']):
            return getattr(job, 'title', '')
        
        # Resume/CV fields (text, not file upload)
        if any(pattern in field_name_lower for pattern in ['resume', 'cv']) and field_element.name != 'input':
            return f"Please find my resume attached. {cover_letter}"
        
        # LinkedIn fields
        if 'linkedin' in field_name_lower:
            return user_profile.get('linkedin_url', '')
        
        # Portfolio/website fields
        if any(pattern in field_name_lower for pattern in ['portfolio', 'website', 'url', 'link']):
            return user_profile.get('portfolio_url', '')
        
        # Salary expectation fields
        if any(pattern in field_name_lower for pattern in ['salary', 'expected', 'compensation']):
            return user_profile.get('expected_salary', 'Negotiable')
        
        # Available start date
        if any(pattern in field_name_lower for pattern in ['start', 'available', 'date']):
            return user_profile.get('start_date', 'Immediately')
        
        # Generic text fields - use cover letter
        if field_element.name == 'textarea':
            return cover_letter
        
        return ''
    
    async def _apply_linkedin(self, user_profile: Dict, job, cover_letter: str) -> Dict:
        """Apply to LinkedIn job"""
        try:
            if not self.page:
                self.page = await self.browser.new_page()
            
            # Navigate to job application page
            apply_url = job.apply_url
            if not apply_url:
                return {
                    'job_id': job.id,
                    'success': False,
                    'error': 'No application URL found',
                    'method': 'linkedin'
                }
            
            await self.page.goto(apply_url)
            await wait_random_delay(3, 5)
            
            # Check if login is required
            if '/login' in self.page.url or await self.page.query_selector('input[name="session_key"]'):
                return {
                    'job_id': job.id,
                    'success': False,
                    'error': 'LinkedIn login required',
                    'method': 'linkedin'
                }
            
            # Look for Easy Apply button
            easy_apply_button = await self.page.query_selector('.jobs-apply-button')
            if not easy_apply_button:
                return {
                    'job_id': job.id,
                    'success': False,
                    'error': 'Easy Apply button not found',
                    'method': 'linkedin'
                }
            
            # Click Easy Apply
            await easy_apply_button.click()
            await wait_random_delay(2, 3)
            
            # Fill out application form
            await self._fill_linkedin_application_form(user_profile, cover_letter)
            
            return {
                'job_id': job.id,
                'success': True,
                'method': 'linkedin',
                'message': 'Applied via LinkedIn Easy Apply'
            }
            
        except Exception as e:
            return {
                'job_id': job.id,
                'success': False,
                'error': str(e),
                'method': 'linkedin'
            }
    
    async def _fill_linkedin_application_form(self, user_profile: Dict, cover_letter: str):
        """Fill out LinkedIn application form"""
        try:
            # Fill basic information
            name_field = await self.page.query_selector('input[name="name"]')
            if name_field:
                await name_field.fill(user_profile.get('name', ''))
            
            email_field = await self.page.query_selector('input[name="email"]')
            if email_field:
                await email_field.fill(user_profile.get('email', ''))
            
            phone_field = await self.page.query_selector('input[name="phone"]')
            if phone_field:
                await phone_field.fill(user_profile.get('phone', ''))
            
            # Fill cover letter if there's a text area
            cover_letter_field = await self.page.query_selector('textarea')
            if cover_letter_field:
                await cover_letter_field.fill(cover_letter)
            
            # Upload resume if file input exists
            resume_upload = await self.page.query_selector('input[type="file"]')
            if resume_upload and user_profile.get('resume_path'):
                await resume_upload.set_input_files(user_profile['resume_path'])
            
            # Submit application
            submit_button = await self.page.query_selector('button[type="submit"]')
            if submit_button:
                await submit_button.click()
                await wait_random_delay(2, 3)
            
        except Exception as e:
            logger.warning(f"Error filling LinkedIn form: {e}")
    
    async def _apply_indeed(self, user_profile: Dict, job, cover_letter: str) -> Dict:
        """Apply to Indeed job"""
        try:
            if not self.page:
                self.page = await self.browser.new_page()
            
            apply_url = job.apply_url
            if not apply_url:
                return {
                    'job_id': job.id,
                    'success': False,
                    'error': 'No application URL found',
                    'method': 'indeed'
                }
            
            await self.page.goto(apply_url)
            await wait_random_delay(3, 5)
            
            # Look for apply button
            apply_button = await self.page.query_selector('.np-button, .indeed-apply-button')
            if not apply_button:
                return {
                    'job_id': job.id,
                    'success': False,
                    'error': 'Apply button not found',
                    'method': 'indeed'
                }
            
            await apply_button.click()
            await wait_random_delay(2, 3)
            
            # Fill application form
            await self._fill_indeed_application_form(user_profile, cover_letter)
            
            return {
                'job_id': job.id,
                'success': True,
                'method': 'indeed',
                'message': 'Applied via Indeed'
            }
            
        except Exception as e:
            return {
                'job_id': job.id,
                'success': False,
                'error': str(e),
                'method': 'indeed'
            }
    
    async def _fill_indeed_application_form(self, user_profile: Dict, cover_letter: str):
        """Fill out Indeed application form"""
        try:
            # Fill contact information
            fields_mapping = {
                'input[name*="name"]': user_profile.get('name', ''),
                'input[name*="email"]': user_profile.get('email', ''),
                'input[name*="phone"]': user_profile.get('phone', ''),
                'textarea[name*="cover"]': cover_letter,
                'textarea[name*="message"]': cover_letter
            }
            
            for selector, value in fields_mapping.items():
                field = await self.page.query_selector(selector)
                if field and value:
                    await field.fill(value)
            
            # Upload resume
            resume_upload = await self.page.query_selector('input[type="file"]')
            if resume_upload and user_profile.get('resume_path'):
                await resume_upload.set_input_files(user_profile['resume_path'])
            
            # Submit
            submit_button = await self.page.query_selector('button[type="submit"], input[type="submit"]')
            if submit_button:
                await submit_button.click()
                await wait_random_delay(2, 3)
            
        except Exception as e:
            logger.warning(f"Error filling Indeed form: {e}")
    
    async def _apply_internshala(self, user_profile: Dict, job, cover_letter: str) -> Dict:
        """Apply to Internshala job"""
        # Similar implementation to LinkedIn/Indeed
        return {
            'job_id': job.id,
            'success': False,
            'error': 'Internshala application not implemented',
            'method': 'internshala'
        }
    
    async def _apply_via_email(self, user_profile: Dict, job, cover_letter: str) -> Dict:
        """Apply via email - ACTUAL WORKING EMAIL SENDER"""
        try:
            # Extract email from apply_url (mailto: links)
            apply_url = job.apply_url
            if not apply_url.startswith('mailto:'):
                return {
                    'job_id': job.id,
                    'success': False,
                    'error': 'Not a valid email application URL',
                    'method': 'email'
                }
            
            recipient_email = apply_url.replace('mailto:', '').split('?')[0]
            
            # Create email
            subject = f"Application for {job.title} at {job.company}"
            
            # Send email using SMTP
            email_result = await self._send_application_email(
                recipient_email,
                subject,
                cover_letter,
                user_profile
            )
            
            if email_result['success']:
                logger.info(f"✅ REAL EMAIL SENT to {recipient_email} for job {job.id}")
                return {
                    'job_id': job.id,
                    'success': True,
                    'method': 'email',
                    'message': f'✅ Application successfully sent via email to {recipient_email}',
                    'recipient': recipient_email,
                    'timestamp': email_result.get('timestamp'),
                    'email_id': email_result.get('email_id')
                }
            else:
                return {
                    'job_id': job.id,
                    'success': False,
                    'error': f'Email sending failed: {email_result["error"]}',
                    'method': 'email'
                }
            
        except Exception as e:
            logger.error(f"Email application failed for job {job.id}: {str(e)}")
            return {
                'job_id': job.id,
                'success': False,
                'error': f'Email application exception: {str(e)}',
                'method': 'email'
            }
    
    async def _send_application_email(self, recipient: str, subject: str, 
                                    cover_letter: str, user_profile: Dict) -> Dict:
        """ACTUAL WORKING SMTP EMAIL SENDER"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            import os
            from datetime import datetime
            
            # Get SMTP settings from user profile or environment
            smtp_host = user_profile.get('smtp_host', os.getenv('SMTP_HOST', 'smtp.gmail.com'))
            smtp_port = int(user_profile.get('smtp_port', os.getenv('SMTP_PORT', '587')))
            sender_email = user_profile.get('email', os.getenv('SENDER_EMAIL'))
            sender_password = user_profile.get('email_password', os.getenv('SENDER_PASSWORD'))
            
            if not sender_email or not sender_password:
                return {
                    'success': False,
                    'error': 'Missing email credentials. Please configure SMTP settings in your profile.'
                }
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = f"{user_profile.get('name', 'Job Applicant')} <{sender_email}>"
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # Create professional email body
            email_body = f"""Dear Hiring Manager,

I hope this email finds you well. I am writing to express my strong interest in the {user_profile.get('target_position', 'position')} role at your organization.

{cover_letter}

I have attached my resume for your review and would welcome the opportunity to discuss how my background and skills align with your team's needs.

Thank you for your time and consideration. I look forward to hearing from you.

Best regards,
{user_profile.get('name', 'N/A')}
{user_profile.get('phone', '')}
{sender_email}

---
This application was sent via SkillNavigator Auto-Apply System
"""
            
            # Attach email body
            msg.attach(MIMEText(email_body, 'plain'))
            
            # Attach resume if available
            resume_path = user_profile.get('resume_path')
            if resume_path and os.path.exists(resume_path):
                try:
                    with open(resume_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(resume_path)}',
                    )
                    msg.attach(part)
                    logger.info(f"Resume attached: {resume_path}")
                except Exception as e:
                    logger.warning(f"Could not attach resume: {e}")
            
            # Send email via SMTP
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()  # Enable TLS encryption
                server.login(sender_email, sender_password)
                
                text = msg.as_string()
                server.sendmail(sender_email, recipient, text)
                
                logger.info(f"✅ EMAIL SUCCESSFULLY SENT to {recipient}")
                
                return {
                    'success': True,
                    'timestamp': datetime.now().isoformat(),
                    'recipient': recipient,
                    'sender': sender_email,
                    'email_id': f"job_app_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'message': f'Email sent successfully to {recipient}'
                }
                
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed: {e}")
            return {
                'success': False,
                'error': 'Email authentication failed. Check your email credentials.'
            }
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"Recipient email refused: {e}")
            return {
                'success': False,
                'error': f'Recipient email {recipient} was refused by the server.'
            }
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error occurred: {e}")
            return {
                'success': False,
                'error': f'Email sending failed: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return {
                'success': False,
                'error': f'Unexpected email error: {str(e)}'
            }
        """Send application email"""
        
        # Email configuration
        smtp_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("EMAIL_PORT", 587))
        email_user = os.getenv("EMAIL_USERNAME")
        email_password = os.getenv("EMAIL_PASSWORD")
        
        if not email_user or not email_password:
            raise ValueError("Email credentials not configured")
        
        # Create message
        message = MIMEMultipart()
        message["From"] = email_user
        message["To"] = recipient
        message["Subject"] = subject
        
        # Add cover letter as body
        message.attach(MIMEText(cover_letter, "plain"))
        
        # Attach resume if available
        if user_profile.get('resume_path'):
            try:
                with open(user_profile['resume_path'], 'rb') as f:
                    resume_attachment = MIMEText(f.read(), 'base64', 'utf-8')
                    resume_attachment.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{user_profile.get("name", "resume")}_resume.pdf"'
                    )
                    message.attach(resume_attachment)
            except Exception as e:
                logger.warning(f"Could not attach resume: {e}")
        
        # Send email
        try:
            await aiosmtplib.send(
                message,
                hostname=smtp_host,
                port=smtp_port,
                start_tls=True,
                username=email_user,
                password=email_password
            )
            logger.info(f"Application email sent to {recipient}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise
    
    async def _apply_via_form(self, user_profile: Dict, job, cover_letter: str) -> Dict:
        """Apply via web form"""
        try:
            if not self.page:
                self.page = await self.browser.new_page()
            
            apply_url = job.apply_url
            await self.page.goto(apply_url)
            await wait_random_delay(3, 5)
            
            # Generic form filling
            await self._fill_generic_application_form(user_profile, cover_letter)
            
            return {
                'job_id': job.id,
                'success': True,
                'method': 'form',
                'message': 'Applied via web form'
            }
            
        except Exception as e:
            return {
                'job_id': job.id,
                'success': False,
                'error': str(e),
                'method': 'form'
            }
    
    async def _fill_generic_application_form(self, user_profile: Dict, cover_letter: str):
        """Fill generic application form"""
        try:
            # Common field patterns
            field_patterns = {
                'name': ['input[name*="name"]', 'input[id*="name"]'],
                'email': ['input[name*="email"]', 'input[id*="email"]'],
                'phone': ['input[name*="phone"]', 'input[id*="phone"]'],
                'cover_letter': ['textarea[name*="cover"]', 'textarea[name*="message"]', 'textarea']
            }
            
            # Fill fields
            for field_type, selectors in field_patterns.items():
                for selector in selectors:
                    field = await self.page.query_selector(selector)
                    if field:
                        value = user_profile.get(field_type, '')
                        if field_type == 'cover_letter':
                            value = cover_letter
                        if value:
                            await field.fill(value)
                        break
            
            # Upload resume
            file_input = await self.page.query_selector('input[type="file"]')
            if file_input and user_profile.get('resume_path'):
                await file_input.set_input_files(user_profile['resume_path'])
            
            # Submit form
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Submit")',
                'button:has-text("Apply")'
            ]
            
            for selector in submit_selectors:
                submit_button = await self.page.query_selector(selector)
                if submit_button:
                    await submit_button.click()
                    await wait_random_delay(2, 3)
                    break
            
        except Exception as e:
            logger.warning(f"Error filling generic form: {e}")
    
    async def _apply_generic(self, user_profile: Dict, job, cover_letter: str) -> Dict:
        """Generic application method"""
        return {
            'job_id': job.id,
            'success': False,
            'error': 'Manual application required',
            'method': 'manual',
            'message': 'This job requires manual application'
        }
    
    async def _get_user_profile(self, user_id: int) -> Optional[Dict]:
        """Get user profile for applications"""
        user = await database.get_user_by_id(user_id)
        if not user:
            return None
        
        return {
            'user_id': user_id,
            'name': user.name,
            'email': user.email,
            'phone': user.get_preferences().get('phone', ''),
            'resume_path': user.resume_path,
            'skills': user.get_skills(),
            'experience_years': user.experience_years,
            'location': user.location,
            **user.get_preferences()
        }
    
    async def _get_job_details(self, job_id: int):
        """Get job details from database"""
        try:
            from database.db_connection import database
            job = await database.get_job_by_id(job_id)
            return job
        except Exception as e:
            logger.error(f"Error fetching job {job_id}: {e}")
            return None
    
    async def _check_existing_application(self, user_id: int, job_id: int) -> bool:
        """Check if user has already applied to this job"""
        try:
            from database.db_connection import get_db
            from sqlalchemy.orm import Session
            from database.db_connection import JobApplication
            
            # Create a database session
            db_gen = get_db()
            db: Session = next(db_gen)
            
            try:
                # Query for existing application
                existing_app = db.query(JobApplication).filter(
                    JobApplication.user_id == user_id,
                    JobApplication.job_id == job_id
                ).first()
                
                return existing_app is not None
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error checking existing application: {e}")
            # Return False to allow application attempt (fail-safe)
            return False
    
    async def _record_application(self, user_id: int, job_id: int, application_result: Dict):
        """Record application in database"""
        try:
            from database.db_connection import get_db
            from sqlalchemy.orm import Session
            from database.db_connection import JobApplication
            from datetime import datetime
            
            # Create a database session
            db_gen = get_db()
            db: Session = next(db_gen)
            
            try:
                # Create new job application record
                new_application = JobApplication(
                    user_id=user_id,
                    job_id=job_id,
                    applied_at=datetime.utcnow(),
                    status="applied" if application_result['success'] else "failed",
                    cover_letter=application_result.get('cover_letter', ''),
                    auto_applied=True,
                    application_method=application_result.get('method', 'auto'),
                    notes=f"Auto-applied using {application_result.get('method', 'unknown')} method. "
                          f"Attempts: {application_result.get('attempts_made', 1)}. "
                          f"Cover letter generated automatically."
                )
                
                # Add error details if failed
                if not application_result['success']:
                    new_application.status = "failed"
                    new_application.notes += f" Error: {application_result.get('error', 'Unknown error')}"
                
                db.add(new_application)
                db.commit()
                
                logger.info(f"Successfully recorded application: User {user_id} -> Job {job_id}")
                
            except Exception as db_error:
                db.rollback()
                logger.error(f"Database error recording application: {db_error}")
                raise
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error recording application: {e}")
            # Don't raise exception here to avoid breaking the application flow
    
    async def _get_applications_today(self) -> int:
        """Get number of applications made today"""
        try:
            from database.db_connection import get_db
            from sqlalchemy.orm import Session
            from database.db_connection import JobApplication
            from datetime import datetime, date
            
            # Create a database session
            db_gen = get_db()
            db: Session = next(db_gen)
            
            try:
                # Get today's date
                today_start = datetime.combine(date.today(), datetime.min.time())
                
                # Query for applications made today by auto-apply
                count = db.query(JobApplication).filter(
                    JobApplication.auto_applied == True,
                    JobApplication.applied_at >= today_start
                ).count()
                
                return count
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting today's applications count: {e}")
            return 0
    
    async def get_auto_apply_analytics(self, user_id: int = None, days: int = 30) -> Dict:
        """Get comprehensive analytics for auto-apply performance"""
        try:
            from database.db_connection import get_db
            from sqlalchemy.orm import Session
            from database.db_connection import JobApplication, Job
            from datetime import datetime, timedelta
            from sqlalchemy import func, and_
            
            db_gen = get_db()
            db: Session = next(db_gen)
            
            try:
                # Date filter
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # Base query for auto-applied jobs
                base_query = db.query(JobApplication).filter(
                    JobApplication.auto_applied == True,
                    JobApplication.applied_at >= cutoff_date
                )
                
                if user_id:
                    base_query = base_query.filter(JobApplication.user_id == user_id)
                
                # Total statistics
                total_auto_applications = base_query.count()
                successful_applications = base_query.filter(JobApplication.status == 'applied').count()
                
                # Method performance analysis
                method_stats = {}
                methods = db.query(JobApplication.application_method, 
                                 func.count(JobApplication.id).label('count'),
                                 func.sum(func.case([(JobApplication.status == 'applied', 1)], else_=0)).label('successes')
                                ).filter(
                    JobApplication.auto_applied == True,
                    JobApplication.applied_at >= cutoff_date
                ).group_by(JobApplication.application_method).all()
                
                for method, count, successes in methods:
                    method_stats[method] = {
                        'total_attempts': count,
                        'successes': successes or 0,
                        'success_rate': (successes or 0) / count if count > 0 else 0
                    }
                
                # Daily application trend
                daily_stats = db.query(
                    func.date(JobApplication.applied_at).label('date'),
                    func.count(JobApplication.id).label('applications')
                ).filter(
                    JobApplication.auto_applied == True,
                    JobApplication.applied_at >= cutoff_date
                ).group_by(func.date(JobApplication.applied_at)).order_by('date').all()
                
                # Top performing job sources
                source_stats = db.query(
                    Job.source,
                    func.count(JobApplication.id).label('applications'),
                    func.sum(func.case([(JobApplication.status == 'applied', 1)], else_=0)).label('successes')
                ).join(Job, JobApplication.job_id == Job.id).filter(
                    JobApplication.auto_applied == True,
                    JobApplication.applied_at >= cutoff_date
                ).group_by(Job.source).all()
                
                # Calculate overall metrics
                overall_success_rate = (successful_applications / total_auto_applications) if total_auto_applications > 0 else 0
                
                # Generate recommendations
                recommendations = self._generate_auto_apply_recommendations(method_stats, overall_success_rate)
                
                return {
                    'period_days': days,
                    'total_auto_applications': total_auto_applications,
                    'successful_applications': successful_applications,
                    'overall_success_rate': round(overall_success_rate * 100, 2),
                    'method_performance': method_stats,
                    'daily_trend': [{'date': str(date), 'applications': apps} for date, apps in daily_stats],
                    'source_performance': [
                        {
                            'source': source, 
                            'applications': apps, 
                            'successes': succ or 0,
                            'success_rate': round((succ or 0) / apps * 100, 2) if apps > 0 else 0
                        } 
                        for source, apps, succ in source_stats
                    ],
                    'recommendations': recommendations,
                    'in_memory_stats': self.method_stats,
                    'current_session_applications': self.applications_today
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error generating auto-apply analytics: {e}")
            return {
                'error': str(e),
                'in_memory_stats': self.method_stats,
                'current_session_applications': self.applications_today
            }
    
    def _generate_auto_apply_recommendations(self, method_stats: Dict, overall_success_rate: float) -> List[str]:
        """Generate recommendations based on performance data"""
        recommendations = []
        
        if overall_success_rate < 0.2:
            recommendations.append("⚠️ Low overall success rate (<20%). Consider reviewing job matching criteria.")
        
        # Find best performing method
        best_method = None
        best_rate = 0
        for method, stats in method_stats.items():
            if stats['total_attempts'] >= 3 and stats['success_rate'] > best_rate:
                best_method = method
                best_rate = stats['success_rate']
        
        if best_method and best_rate > 0.5:
            recommendations.append(f"✅ {best_method} method performing well ({best_rate*100:.1f}% success). Prioritize this method.")
        
        # Find underperforming methods
        for method, stats in method_stats.items():
            if stats['total_attempts'] >= 5 and stats['success_rate'] < 0.1:
                recommendations.append(f"⚠️ {method} method has low success rate ({stats['success_rate']*100:.1f}%). Consider improvements.")
        
        if not recommendations:
            recommendations.append("📊 Auto-apply performance looks good. Continue monitoring.")
        
        recommendations.append("💡 Tip: Higher match scores typically lead to better application success rates.")
        
        return recommendations
    
    def is_healthy(self) -> bool:
        """Check if the auto-apply agent is healthy"""
        return self.browser is not None and self.cover_letter_generator is not None
