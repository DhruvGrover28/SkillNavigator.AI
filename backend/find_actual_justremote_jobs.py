#!/usr/bin/env python3
"""
Find the actual job listings on JustRemote, not the navigation elements
"""

import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_actual_jobs():
    """Find actual job listings on JustRemote"""
    
    print("🔍 Finding Actual Job Listings on JustRemote")
    print("=" * 45)
    
    try:
        url = "https://justremote.co/remote-developer-jobs"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for actual job listing patterns
        job_selectors = [
            'div[class*="job-list"]',
            'div[class*="job-item"]', 
            'div[class*="job-card"]',
            'div[class*="listing-item"]',
            'li[class*="job"]',
            'article',
            '[data-cy*="job"]',
            '[data-testid*="job"]',
            '.job',
            'div[class*="position"]',
            'div[class*="opportunity"]'
        ]
        
        print("🎯 Testing job listing selectors:")
        for selector in job_selectors:
            containers = soup.select(selector)
            if containers:
                print(f"  ✅ '{selector}': {len(containers)} containers")
                # Check first container for job-like content
                first = containers[0]
                text = first.get_text(strip=True)
                if any(word in text.lower() for word in ['apply', 'salary', 'experience', 'remote', 'developer']):
                    print(f"     🎯 Contains job keywords!")
                    # Show some content
                    print(f"     Content preview: '{text[:100]}...'")
            else:
                print(f"  ❌ '{selector}': 0 containers")
        
        # Let's also check for links that might lead to job details
        print(f"\n🔗 Looking for job detail links:")
        job_links = soup.find_all('a', href=True)
        job_detail_links = []
        
        for link in job_links:
            href = link.get('href')
            text = link.get_text(strip=True)
            
            # Look for links that might be job details
            if href and any(pattern in href for pattern in ['/jobs/', '/job/', '/position/', '/remote-jobs/']):
                if text and len(text) > 10:  # Reasonable job title length
                    job_detail_links.append((text, href))
        
        print(f"Found {len(job_detail_links)} potential job detail links:")
        for i, (text, href) in enumerate(job_detail_links[:10]):  # Show first 10
            print(f"  [{i+1}] '{text}' -> {href}")
        
        # Check if jobs are loaded dynamically
        print(f"\n📄 Checking page content:")
        
        # Look for common job-related text patterns
        page_text = soup.get_text().lower()
        job_indicators = ['software developer', 'engineer', 'programmer', 'full stack', 'backend', 'frontend']
        
        found_indicators = [indicator for indicator in job_indicators if indicator in page_text]
        print(f"Job-related keywords found: {found_indicators}")
        
        # Check for JavaScript/dynamic content indicators
        scripts = soup.find_all('script')
        has_react = any('react' in script.get_text().lower() for script in scripts if script.string)
        has_vue = any('vue' in script.get_text().lower() for script in scripts if script.string)
        has_angular = any('angular' in script.get_text().lower() for script in scripts if script.string)
        
        print(f"Dynamic content frameworks detected:")
        print(f"  React: {has_react}")
        print(f"  Vue: {has_vue}")  
        print(f"  Angular: {has_angular}")
        
        # If we found job detail links, that's promising
        if job_detail_links:
            print(f"\n✅ Found {len(job_detail_links)} job links - site likely working")
            return job_detail_links
        else:
            print(f"\n❌ No job links found - may need different approach")
            return []
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    jobs = find_actual_jobs()
    print(f"\n📊 Total job links found: {len(jobs)}")