"""
Enhanced Scraper Agent - Real Job Data Collection
Uses multiple strategies to get real job data from scraping-friendly sources
"""

import requests
import asyncio
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup
import re
import time
import random
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class JobListing:
    """Data class for job listings"""
    title: str
    company: str
    location: str
    description: str
    url: str
    salary: Optional[str] = None
    date_posted: Optional[str] = None
    job_type: Optional[str] = None
    experience: Optional[str] = None
    skills: Optional[List[str]] = None
    apply_url: Optional[str] = None

class EnhancedScraperAgent:
    """
    Enhanced scraper that actually gets real job data from multiple sources
    Focuses on sites that allow scraping and have good job data
    """
    
    def __init__(self):
        self.session = None
        # Rotate user agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'
        ]
        
        # Focus on scraping-friendly job sites with real data
        self.job_sources = {
            'remoteok_api': {
                'name': 'RemoteOK API', 
                'base_url': 'https://remoteok.io/api',
                'enabled': True,
                'parser': self._parse_remoteok_api
            },
            'arbeitnow_api': {
                'name': 'ArbeitNow API',
                'base_url': 'https://www.arbeitnow.com/api/job-board-api',
                'enabled': True,  # Enable - tested and working with 100 jobs
                'parser': self._parse_arbeitnow_jobs
            },
            'justremote': {
                'name': 'JustRemote Jobs',
                'base_url': 'https://justremote.co/remote-jobs',
                'enabled': True,  # Enable - tested and working
                'parser': self._parse_justremote_jobs
            },
            'himalayas_api': {
                'name': 'Himalayas Jobs API',
                'base_url': 'https://himalayas.app/jobs/api',
                'enabled': False,  # Disable - returns 403
                'parser': self._parse_himalayas_jobs
            },
            'ycombinator': {
                'name': 'Y Combinator Jobs',
                'base_url': 'https://www.ycombinator.com/companies/jobs',
                'enabled': False,  # Often blocked
                'parser': self._parse_ycombinator_jobs
            },
            'stackoverflow_rss': {
                'name': 'Stack Overflow Jobs RSS',
                'base_url': 'https://stackoverflow.com/jobs/feed',
                'enabled': False,  # SO Jobs was discontinued
                'parser': self._parse_stackoverflow_rss
            },
            'freecodecamp': {
                'name': 'FreeCodeCamp Job Board',
                'base_url': 'https://www.freecodecamp.org/news/tag/jobs/',
                'enabled': False,  # Not reliable job source
                'parser': self._parse_freecodecamp_jobs
            }
        }
    
    async def initialize(self):
        """Initialize the enhanced scraper"""
        try:
            self.session = requests.Session()
            self._rotate_user_agent()
            logger.info("Enhanced scraper agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize enhanced scraper: {e}")
            raise
    
    def _rotate_user_agent(self):
        """Rotate user agent to avoid detection"""
        user_agent = random.choice(self.user_agents)
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    async def scrape_jobs(self, search_params: Dict) -> List[JobListing]:
        """Scrape real jobs from multiple sources"""
        if not self.session:
            await self.initialize()
        
        all_jobs = []
        keywords = search_params.get('keywords', 'python developer')
        location = search_params.get('location', 'remote')
        max_results = search_params.get('max_results', 50)
        
        enabled_sources = {name: config for name, config in self.job_sources.items() 
                          if config.get('enabled', True)}
        
        logger.info(f"Scraping from {len(enabled_sources)} sources: {list(enabled_sources.keys())}")
        
        for source_name, source_config in enabled_sources.items():
            try:
                logger.info(f"Scraping jobs from {source_config['name']}")
                jobs = await self._scrape_source(source_name, source_config, keywords, location)
                all_jobs.extend(jobs)
                logger.info(f"Found {len(jobs)} jobs from {source_config['name']}")
                
                # Random delay between sources
                await asyncio.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"Error scraping {source_name}: {e}")
                continue
        
        # Remove duplicates and limit results
        unique_jobs = self._remove_duplicates(all_jobs)
        return unique_jobs[:max_results]
    
    async def _scrape_source(self, source_name: str, config: Dict, keywords: str, location: str) -> List[JobListing]:
        """Scrape jobs from a specific source"""
        try:
            parser = config['parser']
            jobs = await parser(keywords, location)
            return jobs
        except Exception as e:
            logger.error(f"Error parsing {source_name}: {e}")
            return []
    
    async def _parse_remoteok_api(self, keywords: str, location: str) -> List[JobListing]:
        """Parse jobs from RemoteOK API - this actually works!"""
        jobs = []
        try:
            url = "https://remoteok.io/api"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"RemoteOK API response: {len(data)} items")
                
                # Skip the first item which is metadata
                if isinstance(data, list) and len(data) > 1:
                    job_data = data[1:]  # Skip metadata
                    logger.info(f"Processing {len(job_data)} job entries")
                    
                    for job_info in job_data[:50]:  # Limit to 50 jobs for more variety
                        if not isinstance(job_info, dict):
                            continue
                        
                        # Improved keyword matching - more inclusive
                        include_job = True
                        if keywords and keywords.lower() not in ['all', '', 'any']:
                            # Split keywords to check for multiple terms
                            keyword_terms = [term.strip().lower() for term in keywords.lower().split()]
                            
                            title = job_info.get('position', '').lower()
                            tags = [str(tag).lower() for tag in job_info.get('tags', [])]
                            description = job_info.get('description', '').lower()
                            
                            # Check if any keyword term matches title, tags, or description
                            matches = []
                            for term in keyword_terms:
                                title_match = term in title
                                tag_match = any(term in tag for tag in tags)
                                desc_match = term in description
                                
                                if title_match or tag_match or desc_match:
                                    matches.append(term)
                            
                            # Include job if at least one keyword term matches
                            include_job = len(matches) > 0
                        
                        if not include_job:
                            continue
                        
                        # Clean description (remove HTML but keep full content for AI scoring)
                        description = job_info.get('description', 'Remote position opportunity')
                        if description:
                            # Strip HTML tags but preserve full content
                            import re
                            description = re.sub(r'<[^>]+>', ' ', description)
                            description = re.sub(r'\s+', ' ', description).strip()
                        
                        # Extract job details
                        job = JobListing(
                            title=job_info.get('position', 'Remote Position'),
                            company=job_info.get('company', 'Remote Company'),
                            location=job_info.get('location', 'Remote'),
                            description=description,
                            url=job_info.get('url', f"https://remoteok.com/remote-jobs/{job_info.get('slug', job_info.get('id', ''))}"),
                            salary=self._format_salary(job_info.get('salary_min'), job_info.get('salary_max')),
                            date_posted=job_info.get('date'),
                            job_type='Remote',
                            skills=job_info.get('tags', [])[:8],  # Limit skills to 8
                            apply_url=job_info.get('apply_url') or job_info.get('url', f"https://remoteok.com/remote-jobs/{job_info.get('slug', job_info.get('id', ''))}")
                        )
                        jobs.append(job)
                        
            logger.info(f"RemoteOK API returned {len(jobs)} jobs")
            
        except Exception as e:
            logger.error(f"Error parsing RemoteOK API: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
        return jobs
    
    async def _parse_himalayas_jobs(self, keywords: str, location: str) -> List[JobListing]:
        """Parse jobs from Himalayas.app - good remote job source"""
        jobs = []
        try:
            # Himalayas has a simple job listing page we can scrape
            url = "https://himalayas.app/jobs"
            if keywords and keywords.lower() != 'all':
                url += f"?query={quote(keywords)}"
                
            self._rotate_user_agent()
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for job cards or listings
                job_elements = soup.find_all(['div', 'article'], class_=re.compile(r'job|listing|card'))
                
                for job_elem in job_elements[:12]:  # Limit to 12 jobs
                    try:
                        # Extract title
                        title_elem = job_elem.find(['h2', 'h3', 'a'], class_=re.compile(r'title|position'))
                        if not title_elem:
                            title_elem = job_elem.find('a')
                        
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text(strip=True)
                        
                        # Extract company
                        company_elem = job_elem.find(['span', 'div'], class_=re.compile(r'company'))
                        company = company_elem.get_text(strip=True) if company_elem else "Remote Company"
                        
                        # Extract location
                        location_elem = job_elem.find(['span', 'div'], class_=re.compile(r'location'))
                        job_location = location_elem.get_text(strip=True) if location_elem else "Remote"
                        
                        # Extract link
                        link_elem = job_elem.find('a', href=True)
                        job_url = urljoin("https://himalayas.app", link_elem['href']) if link_elem else "https://himalayas.app/jobs"
                        
                        job = JobListing(
                            title=title,
                            company=company,
                            location=job_location,
                            description=f"Remote position at {company}: {title}",
                            url=job_url,
                            job_type="Remote",
                            apply_url=job_url
                        )
                        jobs.append(job)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing Himalayas job: {e}")
                        continue
                        
            logger.info(f"Himalayas returned {len(jobs)} jobs")
            
        except Exception as e:
            logger.error(f"Error scraping Himalayas: {e}")
            
        return jobs
    
    async def _parse_arbeitnow_jobs(self, keywords: str, location: str) -> List[JobListing]:
        """Parse jobs from ArbeitNow API - reliable European job source with 100+ jobs"""
        jobs = []
        try:
            logger.info("Scraping jobs from ArbeitNow API")
            url = "https://www.arbeitnow.com/api/job-board-api"
            
            self._rotate_user_agent()
            response = self.session.get(url, timeout=15, headers={'Accept': 'application/json'})
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"ArbeitNow API response: {len(data.get('data', []))} items")
                
                if 'data' in data and isinstance(data['data'], list):
                    job_list = data['data']
                    
                    for job_info in job_list[:20]:  # Limit to 20 jobs for variety
                        if not isinstance(job_info, dict):
                            continue
                            
                        # Improved keyword matching - more inclusive
                        include_job = True
                        if keywords and keywords.lower() not in ['all', '', 'any']:
                            keyword_terms = [term.strip().lower() for term in keywords.lower().split()]
                            
                            title = job_info.get('title', '').lower()
                            description = job_info.get('description', '').lower()
                            tags = [str(tag).lower() for tag in job_info.get('tags', [])]
                            
                            # Check if any keyword term matches
                            matches = []
                            for term in keyword_terms:
                                if (term in title or term in description or 
                                    any(term in tag for tag in tags)):
                                    matches.append(term)
                            
                            include_job = len(matches) > 0
                        
                        if not include_job:
                            continue
                        
                        # Clean HTML from description
                        description = job_info.get('description', 'Professional opportunity')
                        if description:
                            import re
                            description = re.sub(r'<[^>]+>', ' ', description)
                            description = re.sub(r'\s+', ' ', description).strip()
                            # Keep full description for better AI matching
                        
                        job = JobListing(
                            title=job_info.get('title', 'Professional Position'),
                            company=job_info.get('company_name', 'European Company'),
                            location=job_info.get('location', 'Remote'),
                            description=description,
                            url=job_info.get('url', 'https://www.arbeitnow.com'),
                            salary=None,  # ArbeitNow doesn't typically include salary in API
                            date_posted=job_info.get('created_at'),
                            job_type='Full-time',
                            skills=job_info.get('tags', [])[:6],  # Limit to 6 tags
                            apply_url=job_info.get('url', 'https://www.arbeitnow.com')
                        )
                        jobs.append(job)
                        
            logger.info(f"ArbeitNow API returned {len(jobs)} jobs")
            
        except Exception as e:
            logger.error(f"Error parsing ArbeitNow API: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
        return jobs
    
    async def _parse_justremote_jobs(self, keywords: str, location: str) -> List[JobListing]:
        """Parse jobs from JustRemote - popular remote job board
        Note: JustRemote uses dynamic content loading, so we'll use their API if available
        """
        jobs = []
        try:
            logger.info("Scraping jobs from JustRemote")
            
            # Try API approach first
            api_url = "https://justremote.co/api/jobs"
            params = {
                'limit': 20,
                'q': keywords if keywords else 'developer',
                'location': 'remote'
            }
            
            self._rotate_user_agent()
            
            # Try API first
            try:
                response = self.session.get(api_url, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    api_jobs = data.get('jobs', []) if isinstance(data, dict) else data
                    
                    if isinstance(api_jobs, list) and api_jobs:
                        logger.info(f"JustRemote API found {len(api_jobs)} jobs")
                        
                        for job_data in api_jobs[:15]:  # Limit to 15
                            try:
                                title = job_data.get('title', '').strip()
                                company = job_data.get('company', {}).get('name', 'Remote Company') if isinstance(job_data.get('company'), dict) else str(job_data.get('company', 'Remote Company'))
                                
                                if not title or len(title) < 3:
                                    continue
                                
                                # Build job URL
                                job_id = job_data.get('id') or job_data.get('slug', '')
                                job_url = f"https://justremote.co/remote-jobs/{job_id}" if job_id else "https://justremote.co/remote-jobs"
                                
                                # Extract description (keep full content for AI scoring)
                                description = job_data.get('description', '') or job_data.get('summary', '') or f"Remote {title} position at {company}"
                                # Clean description but preserve full content
                                if isinstance(description, str):
                                    description = re.sub(r'<[^>]+>', ' ', description)
                                    description = re.sub(r'\s+', ' ', description).strip()
                                
                                job = JobListing(
                                    title=title,
                                    company=company,
                                    location=job_data.get('location', 'Remote'),
                                    description=description,
                                    url=job_url,
                                    salary=job_data.get('salary'),
                                    date_posted=job_data.get('created_at') or job_data.get('published_at'),
                                    job_type=job_data.get('type', 'Remote'),
                                    apply_url=job_data.get('apply_url') or job_url
                                )
                                jobs.append(job)
                                
                            except Exception as e:
                                logger.debug(f"Error parsing JustRemote API job: {e}")
                                continue
                        
                        if jobs:
                            logger.info(f"JustRemote API returned {len(jobs)} jobs")
                            return jobs
                    
            except Exception as e:
                logger.debug(f"JustRemote API failed: {e}")
            
            # Fallback to web scraping (limited due to dynamic content)
            logger.info("JustRemote API failed, trying web scraping")
            url = "https://justremote.co/remote-developer-jobs"
            
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Since JustRemote is dynamic, look for any job-related links in the static HTML
                job_links = soup.find_all('a', href=True)
                job_urls = []
                
                for link in job_links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    # Look for actual job links (not category links)
                    if ('/remote-jobs/' in href and 
                        href != '/remote-jobs/new' and 
                        len(text) > 10 and 
                        not any(word in text.lower() for word in ['list your', 'post', 'category', 'filter'])):
                        
                        full_url = href if href.startswith('http') else f"https://justremote.co{href}"
                        job_urls.append((text, full_url))
                
                logger.info(f"JustRemote found {len(job_urls)} job links in static HTML")
                
                # Create jobs from the links we found
                for title, job_url in job_urls[:10]:  # Limit to 10
                    job = JobListing(
                        title=title,
                        company="Remote Company",
                        location="Remote",
                        description=f"Remote position: {title}",
                        url=job_url,
                        job_type="Remote",
                        apply_url=job_url
                    )
                    jobs.append(job)
                        
            logger.info(f"JustRemote returned {len(jobs)} jobs")
            
        except Exception as e:
            logger.error(f"Error parsing JustRemote: {e}")
            
        return jobs
    
    async def _parse_ycombinator_jobs(self, keywords: str, location: str) -> List[JobListing]:
        """Parse jobs from Y Combinator job board"""
        jobs = []
        try:
            url = "https://www.ycombinator.com/companies/jobs"
            self._rotate_user_agent()
            
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for job listings - YC uses specific classes
                job_elements = soup.find_all(['div', 'tr'], class_=re.compile(r'job|position|listing'))
                
                for job_elem in job_elements[:15]:  # Limit to 15 jobs
                    try:
                        # Extract title
                        title_elem = job_elem.find(['a', 'h3', 'span'], string=re.compile(r'engineer|developer|analyst|manager', re.I))
                        if not title_elem:
                            title_elem = job_elem.find(['a', 'h3', 'span'])
                        
                        title = title_elem.get_text(strip=True) if title_elem else "Software Engineer"
                        
                        # Filter by keywords
                        if keywords and keywords.lower() != 'all':
                            if keywords.lower() not in title.lower():
                                continue
                        
                        # Extract company
                        company_elem = job_elem.find(['span', 'div'], class_=re.compile(r'company'))
                        company = company_elem.get_text(strip=True) if company_elem else"YC Company"
                        
                        # Extract link
                        link_elem = job_elem.find('a', href=True)
                        job_url = urljoin("https://www.ycombinator.com", link_elem['href']) if link_elem else "https://www.ycombinator.com/companies/jobs"
                        
                        job = JobListing(
                            title=title,
                            company=company,
                            location="San Francisco, CA",
                            description=f"Position at Y Combinator company {company}: {title}",
                            url=job_url,
                            job_type="Full-time",
                            apply_url=job_url
                        )
                        jobs.append(job)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing YC job: {e}")
                        continue
                        
            logger.info(f"Y Combinator returned {len(jobs)} jobs")
            
        except Exception as e:
            logger.error(f"Error scraping Y Combinator: {e}")
            
        return jobs
    
    async def _parse_stackoverflow_rss(self, keywords: str, location: str) -> List[JobListing]:
        """Parse jobs from Stack Overflow RSS feed"""
        jobs = []
        try:
            # Stack Overflow has job RSS feeds
            url = f"https://stackoverflow.com/jobs/feed?q={quote(keywords)}&l={quote(location)}"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                # Parse RSS/XML
                soup = BeautifulSoup(response.text, 'xml')
                items = soup.find_all('item')
                
                for item in items[:10]:  # Limit to 10 jobs
                    try:
                        title = item.find('title').text if item.find('title') else "Developer Position"
                        description = item.find('description').text if item.find('description') else "Stack Overflow job opportunity"
                        link = item.find('link').text if item.find('link') else "https://stackoverflow.com/jobs"
                        
                        # Extract company from title or description
                        company = "Tech Company"
                        if " at " in title:
                            company = title.split(" at ")[-1]
                        
                        job = JobListing(
                            title=title,
                            company=company,
                            location=location or "Remote",
                            description=description[:300],
                            url=link,
                            job_type="Full-time",
                            apply_url=link
                        )
                        jobs.append(job)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing SO RSS job: {e}")
                        continue
                        
            logger.info(f"Stack Overflow RSS returned {len(jobs)} jobs")
            
        except Exception as e:
            logger.error(f"Error scraping Stack Overflow RSS: {e}")
            
        return jobs
    
    async def _parse_freecodecamp_jobs(self, keywords: str, location: str) -> List[JobListing]:
        """Parse jobs from FreeCodeCamp job posts"""
        jobs = []
        try:
            url = "https://www.freecodecamp.org/news/tag/jobs/"
            self._rotate_user_agent()
            
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for job-related articles
                articles = soup.find_all(['article', 'div'], class_=re.compile(r'post|article'))
                
                for article in articles[:8]:  # Limit to 8 jobs
                    try:
                        title_elem = article.find(['h2', 'h3', 'a'])
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text(strip=True)
                        
                        # Check if it's job-related
                        job_keywords = ['job', 'hiring', 'developer', 'engineer', 'position', 'career']
                        if not any(keyword in title.lower() for keyword in job_keywords):
                            continue
                        
                        link_elem = article.find('a', href=True)
                        job_url = urljoin("https://www.freecodecamp.org", link_elem['href']) if link_elem else "https://www.freecodecamp.org/news/tag/jobs/"
                        
                        job = JobListing(
                            title=title,
                            company="FreeCodeCamp Community",
                            location="Remote",
                            description=f"Job opportunity from FreeCodeCamp community: {title}",
                            url=job_url,
                            job_type="Various",
                            apply_url=job_url
                        )
                        jobs.append(job)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing FCC job: {e}")
                        continue
                        
            logger.info(f"FreeCodeCamp returned {len(jobs)} jobs")
            
        except Exception as e:
            logger.error(f"Error scraping FreeCodeCamp: {e}")
            
        return jobs
    
    def _format_salary(self, min_sal, max_sal):
        """Format salary range"""
        if min_sal and max_sal:
            return f"${min_sal:,} - ${max_sal:,}"
        elif min_sal:
            return f"${min_sal:,}+"
        elif max_sal:
            return f"Up to ${max_sal:,}"
        return None
    
    def _remove_duplicates(self, jobs: List[JobListing]) -> List[JobListing]:
        """Remove duplicate jobs based on multiple criteria"""
        seen_combinations = set()
        seen_urls = set()
        unique_jobs = []
        
        for job in jobs:
            # Create multiple keys for duplicate detection
            title_company_key = (job.title.lower().strip(), job.company.lower().strip())
            url_key = job.url.lower().strip() if job.url else ""
            
            # Skip if we've seen this exact title+company combination
            if title_company_key in seen_combinations:
                logger.debug(f"Skipping duplicate job: {job.title} at {job.company}")
                continue
            
            # Skip if we've seen this exact URL
            if url_key and url_key in seen_urls:
                logger.debug(f"Skipping duplicate URL: {url_key}")
                continue
            
            # Skip jobs with generic/placeholder data
            if (job.title.lower() in ['remote position', 'developer position', 'professional position'] or
                job.company.lower() in ['remote company', 'tech company', 'european company'] or
                len(job.title.strip()) < 3 or len(job.company.strip()) < 2):
                logger.debug(f"Skipping generic job: {job.title} at {job.company}")
                continue
            
            # Add to seen sets and unique jobs
            seen_combinations.add(title_company_key)
            if url_key:
                seen_urls.add(url_key)
            unique_jobs.append(job)
        
        logger.info(f"Deduplicated: {len(jobs)} -> {len(unique_jobs)} unique jobs")
        return unique_jobs
    
    async def _parse_placeholder_jobs(self, keywords: str, location: str) -> List[JobListing]:
        """Placeholder parser for disabled sources"""
        return []
    
    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            self.session.close()
        logger.info("Enhanced scraper agent cleaned up")