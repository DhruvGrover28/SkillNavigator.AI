#!/usr/bin/env python3
"""
Research simple, easy-to-scrape job sources similar to RemoteOK
Focus on sites with static HTML and simple structure
"""

import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_job_source(name, url, job_selector, title_selector, company_selector=None):
    """Test a job source to see if it's easy to scrape"""
    
    print(f"\n🔍 Testing {name}")
    print(f"   URL: {url}")
    print("-" * 40)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find job containers
        job_containers = soup.select(job_selector)
        print(f"   📊 Found {len(job_containers)} job containers")
        
        if len(job_containers) == 0:
            print(f"   ❌ No containers found")
            return False, 0
        
        # Test parsing first few jobs
        jobs_parsed = 0
        for i, container in enumerate(job_containers[:5]):
            try:
                # Extract title
                title_elem = container.select_one(title_selector)
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                # Extract company if selector provided
                company = ""
                if company_selector:
                    company_elem = container.select_one(company_selector)
                    company = company_elem.get_text(strip=True) if company_elem else ""
                
                # Extract link
                link_elem = container.find('a', href=True)
                link = link_elem.get('href') if link_elem else ""
                
                if title and len(title) > 5:  # Reasonable title
                    print(f"   ✅ Job {i+1}: '{title[:50]}...'")
                    if company:
                        print(f"      Company: {company}")
                    if link:
                        print(f"      Link: {link[:60]}...")
                    jobs_parsed += 1
                else:
                    print(f"   ⚠️ Job {i+1}: No title or too short")
                
            except Exception as e:
                print(f"   ❌ Job {i+1}: Error parsing - {e}")
        
        success_rate = jobs_parsed / min(len(job_containers), 5)
        print(f"   📈 Success rate: {jobs_parsed}/5 = {success_rate:.1%}")
        
        # Determine if this source is good
        is_good = jobs_parsed >= 3 and len(job_containers) >= 10
        if is_good:
            print(f"   🎉 {name} looks GOOD for scraping!")
        else:
            print(f"   ⚠️ {name} may need work")
        
        return is_good, len(job_containers)
        
    except Exception as e:
        print(f"   ❌ Error testing {name}: {e}")
        return False, 0

def research_simple_job_sources():
    """Research simple job sources similar to RemoteOK"""
    
    print("🔍 Researching Simple Job Sources")
    print("=" * 50)
    
    # Test various job sources that are likely to be simple
    sources_to_test = [
        {
            'name': 'We Work Remotely',
            'url': 'https://weworkremotely.com/remote-jobs/search?utf8=%E2%9C%93&term=developer',
            'job_selector': 'li[class*="feature"]',
            'title_selector': 'span[class*="title"]',
            'company_selector': 'span[class*="company"]'
        },
        {
            'name': 'Remote.co',
            'url': 'https://remote.co/remote-jobs/developer/',
            'job_selector': 'div[class*="job_listing"]',
            'title_selector': 'h3, .position',
            'company_selector': '.company'
        },
        {
            'name': 'FlexJobs (free listings)',
            'url': 'https://www.flexjobs.com/remote-jobs/developer',
            'job_selector': 'article',
            'title_selector': 'h5, .job-title',
            'company_selector': '.company-name'
        },
        {
            'name': 'AngelList/Wellfound',
            'url': 'https://wellfound.com/jobs?remote=true&role=developer',
            'job_selector': '[data-test="StartupResult"]',
            'title_selector': '[data-test="JobTitle"]',
            'company_selector': '[data-test="StartupName"]'
        },
        {
            'name': 'Remote OK (different endpoint)',
            'url': 'https://remoteok.io/remote-dev-jobs',
            'job_selector': 'tr[class*="job"]',
            'title_selector': '.company h2',
            'company_selector': '.company h3'
        },
        {
            'name': 'NoDesk',
            'url': 'https://nodesk.co/remote-work/remote-jobs/',
            'job_selector': '.job-listing',
            'title_selector': '.job-title',
            'company_selector': '.company-name'
        },
        {
            'name': 'RemoteBase',
            'url': 'https://remotebase.com/remote-jobs',
            'job_selector': '.job-card',
            'title_selector': '.job-title',
            'company_selector': '.company-name'
        },
        {
            'name': 'Working Nomads',
            'url': 'https://www.workingnomads.co/remote-development-jobs',
            'job_selector': '.job',
            'title_selector': '.job-title',
            'company_selector': '.company'
        }
    ]
    
    good_sources = []
    
    for source in sources_to_test:
        is_good, job_count = test_job_source(
            source['name'],
            source['url'], 
            source['job_selector'],
            source['title_selector'],
            source.get('company_selector')
        )
        
        if is_good:
            good_sources.append((source['name'], source, job_count))
    
    print(f"\n" + "="*50)
    print(f"📊 RESULTS")
    print(f"="*50)
    
    if good_sources:
        print(f"✅ Found {len(good_sources)} good sources:")
        for name, source, count in good_sources:
            print(f"   🎯 {name}: {count} jobs, easy to scrape")
            print(f"      URL: {source['url']}")
            print(f"      Selectors: {source['job_selector']} -> {source['title_selector']}")
        
        # Return the best one
        best_source = max(good_sources, key=lambda x: x[2])  # Most jobs
        print(f"\n🏆 RECOMMENDED: {best_source[0]} with {best_source[2]} jobs")
        return best_source[1]
    else:
        print(f"❌ No good sources found")
        return None

if __name__ == "__main__":
    recommended_source = research_simple_job_sources()
    
    if recommended_source:
        print(f"\n✅ Ready to implement: {recommended_source['name']}")
    else:
        print(f"\n⚠️ Need to research more sources or adjust criteria")