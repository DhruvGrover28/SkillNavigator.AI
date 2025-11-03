#!/usr/bin/env python3
"""
Debug JustRemote HTML parsing to understand why we find containers but extract 0 jobs
"""

import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_justremote_parsing():
    """Debug JustRemote HTML structure"""
    
    print("🔍 Debugging JustRemote HTML Structure")
    print("=" * 50)
    
    try:
        # Test URL - same as in the scraper
        url = "https://justremote.co/remote-developer-jobs"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"📡 Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check the current selector used in the scraper
        current_selector = 'div[data-testid="job-list-item"]'
        job_containers = soup.select(current_selector)
        
        print(f"📊 Current selector '{current_selector}' found: {len(job_containers)} containers")
        
        if len(job_containers) > 0:
            print(f"\n🔬 Analyzing first job container structure:")
            first_container = job_containers[0]
            print(f"Container HTML (first 500 chars):")
            print(first_container.prettify()[:500])
            print("...")
            
            # Look for job title patterns
            title_selectors = [
                'h3', 'h2', 'h4', 
                '[data-testid*="title"]', 
                '.job-title', 
                'a[href*="/remote-jobs/"]',
                'a[href*="/jobs/"]'
            ]
            
            print(f"\n🎯 Testing title selectors:")
            for selector in title_selectors:
                elements = first_container.select(selector)
                if elements:
                    print(f"  ✅ '{selector}': {len(elements)} elements")
                    for i, elem in enumerate(elements[:2]):
                        text = elem.get_text(strip=True)
                        href = elem.get('href', 'No href')
                        print(f"     [{i}] Text: '{text[:50]}...' | Href: {href}")
                else:
                    print(f"  ❌ '{selector}': 0 elements")
            
            # Look for company patterns
            company_selectors = [
                '[data-testid*="company"]',
                '.company', '.company-name',
                'span:contains("at")',
                'div:contains("Company")'
            ]
            
            print(f"\n🏢 Testing company selectors:")
            for selector in company_selectors:
                elements = first_container.select(selector)
                if elements:
                    print(f"  ✅ '{selector}': {len(elements)} elements")
                    for i, elem in enumerate(elements[:2]):
                        text = elem.get_text(strip=True)
                        print(f"     [{i}] Text: '{text[:50]}...'")
                else:
                    print(f"  ❌ '{selector}': 0 elements")
            
            # Look for all links in the container
            all_links = first_container.find_all('a', href=True)
            print(f"\n🔗 All links in container: {len(all_links)}")
            for i, link in enumerate(all_links[:3]):
                href = link.get('href')
                text = link.get_text(strip=True)
                print(f"  [{i}] '{text[:40]}...' -> {href}")
        
        # Also check alternative selectors
        alternative_selectors = [
            'div[class*="job"]',
            'article',
            '[data-testid*="job"]',
            '.job-card',
            '.job-item'
        ]
        
        print(f"\n🔄 Testing alternative container selectors:")
        for selector in alternative_selectors:
            containers = soup.select(selector)
            print(f"  '{selector}': {len(containers)} containers")
            
        # Check the page structure
        print(f"\n📋 Page structure analysis:")
        main_content = soup.find('main') or soup.find('div', {'id': 'main'}) or soup.find('body')
        if main_content:
            print(f"  Main content found: {main_content.name}")
            # Look for job-related classes
            job_related = main_content.find_all(attrs={'class': lambda x: x and 'job' in ' '.join(x).lower()})[:5]
            print(f"  Elements with 'job' in class: {len(job_related)}")
            for elem in job_related:
                classes = ' '.join(elem.get('class', []))
                print(f"    {elem.name}.{classes}")
        
        return len(job_containers)
        
    except Exception as e:
        print(f"❌ Error debugging JustRemote: {e}")
        return 0

if __name__ == "__main__":
    count = debug_justremote_parsing()
    print(f"\n📊 Summary: Found {count} job containers")