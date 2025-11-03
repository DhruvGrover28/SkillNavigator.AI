#!/usr/bin/env python3
"""
Research more simple job sources - focusing on older, simpler sites
"""

import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_simple_source(name, url, selectors_list):
    """Test a job source with multiple selector combinations"""
    
    print(f"\n🔍 Testing {name}")
    print(f"   URL: {url}")
    print("-" * 40)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        best_result = None
        best_count = 0
        
        # Try different selector combinations
        for job_selector, title_selector, company_selector in selectors_list:
            job_containers = soup.select(job_selector)
            
            if len(job_containers) > best_count:
                print(f"   📊 Trying '{job_selector}': {len(job_containers)} containers")
                
                jobs_parsed = 0
                sample_jobs = []
                
                for i, container in enumerate(job_containers[:5]):
                    try:
                        # Extract title
                        title_elem = container.select_one(title_selector) if title_selector else container.find(['h1', 'h2', 'h3', 'h4'])
                        title = title_elem.get_text(strip=True) if title_elem else ""
                        
                        # Extract company
                        company = ""
                        if company_selector:
                            company_elem = container.select_one(company_selector)
                            company = company_elem.get_text(strip=True) if company_elem else ""
                        
                        # Extract link
                        link_elem = container.find('a', href=True)
                        link = link_elem.get('href') if link_elem else ""
                        
                        if title and len(title) > 5:
                            jobs_parsed += 1
                            sample_jobs.append((title, company, link))
                    
                    except Exception as e:
                        continue
                
                if jobs_parsed > 0:
                    print(f"   ✅ Parsed {jobs_parsed}/5 jobs successfully")
                    for i, (title, company, link) in enumerate(sample_jobs[:3]):
                        print(f"      [{i+1}] '{title[:40]}...'")
                        if company:
                            print(f"          Company: {company}")
                        if link:
                            print(f"          Link: {link[:50]}...")
                    
                    if jobs_parsed >= 3 and len(job_containers) >= 10:
                        best_result = (job_selector, title_selector, company_selector)
                        best_count = len(job_containers)
                        print(f"   🎯 This selector combination works well!")
        
        if best_result:
            print(f"   🎉 {name} is GOOD for scraping!")
            print(f"   📈 Best: {best_count} containers, good parsing")
            return True, best_result, best_count
        else:
            print(f"   ⚠️ {name} needs more work")
            return False, None, 0
        
    except Exception as e:
        print(f"   ❌ Error testing {name}: {e}")
        return False, None, 0

def research_alternative_sources():
    """Research alternative simple job sources"""
    
    print("🔍 Researching Alternative Simple Job Sources")
    print("=" * 55)
    
    sources_to_test = [
        {
            'name': 'SimplyHired Remote Jobs',
            'url': 'https://www.simplyhired.com/search?q=software+developer&l=remote',
            'selectors': [
                ('[data-jk]', '[data-testid="jobTitle"]', '[data-testid="companyName"]'),
                ('.jobposting', '.jobposting-title', '.jobposting-company'),
                ('article', 'h3', 'span')
            ]
        },
        {
            'name': 'Indeed Remote Jobs',
            'url': 'https://www.indeed.com/jobs?q=software+developer&l=remote',
            'selectors': [
                ('[data-jk]', 'h2 a span', 'span[data-testid="company-name"]'),
                ('.jobsearch-SerpJobCard', '.jobTitle', '.companyName'),
                ('.job_seen_beacon', 'h2', '.companyName')
            ]
        },
        {
            'name': 'Monster Remote Jobs',
            'url': 'https://www.monster.com/jobs/search?q=software-developer&where=remote',
            'selectors': [
                ('[data-test-id="svx-job-card"]', 'h2', '[data-test-id="svx-job-card-company"]'),
                ('.mux-job-result', '.job-title', '.company'),
                ('article', 'h3', '.company-name')
            ]
        },
        {
            'name': 'Dice Remote Jobs',
            'url': 'https://www.dice.com/jobs?q=software%20developer&location=Remote&radius=30&radiusUnit=mi',
            'selectors': [
                ('[data-cy="search-result-card"]', '[data-cy="job-title"]', '[data-cy="company-name"]'),
                ('.search-result-card', '.job-title', '.company-name'),
                ('.card', 'h5', '.company')
            ]
        },
        {
            'name': 'Glassdoor Remote Jobs',
            'url': 'https://www.glassdoor.com/Job/remote-software-developer-jobs-SRCH_IL.0,6_IS11047_KO7,25.htm',
            'selectors': [
                ('[data-test="job-card"]', '[data-test="job-title"]', '[data-test="employer-name"]'),
                ('.react-job-listing', '.jobTitle', '.employerName'),
                ('li[data-id]', 'a', '.employerName')
            ]
        }
    ]
    
    good_sources = []
    
    for source in sources_to_test:
        is_good, selectors, job_count = test_simple_source(
            source['name'],
            source['url'],
            source['selectors']
        )
        
        if is_good:
            good_sources.append((source['name'], source['url'], selectors, job_count))
    
    print(f"\n" + "="*55)
    print(f"📊 RESULTS")
    print(f"="*55)
    
    if good_sources:
        print(f"✅ Found {len(good_sources)} good sources:")
        for name, url, selectors, count in good_sources:
            print(f"   🎯 {name}: {count} jobs")
            print(f"      URL: {url}")
            print(f"      Selectors: {selectors}")
        
        # Return the best one
        best_source = max(good_sources, key=lambda x: x[3])  # Most jobs
        print(f"\n🏆 RECOMMENDED: {best_source[0]} with {best_source[3]} jobs")
        return {
            'name': best_source[0],
            'url': best_source[1],
            'job_selector': best_source[2][0],
            'title_selector': best_source[2][1],
            'company_selector': best_source[2][2]
        }
    else:
        print(f"❌ No good sources found in this batch")
        return None

if __name__ == "__main__":
    recommended = research_alternative_sources()
    
    if recommended:
        print(f"\n✅ Ready to implement: {recommended['name']}")
        print(f"   URL: {recommended['url']}")
        print(f"   Job selector: {recommended['job_selector']}")
        print(f"   Title selector: {recommended['title_selector']}")
        print(f"   Company selector: {recommended['company_selector']}")
    else:
        print(f"\n⚠️ Will try more specific job boards next")