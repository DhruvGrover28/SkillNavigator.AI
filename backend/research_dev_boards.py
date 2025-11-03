#!/usr/bin/env python3
"""
Research smaller, developer-focused job boards that are easier to scrape
"""

import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detailed_test(name, url, selectors_list):
    """Test a source with detailed analysis"""
    
    print(f"\n🔍 Testing {name}")
    print(f"   URL: {url}")
    print("-" * 50)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        print(f"   📡 Response: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ Bad response code")
            return False, None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text()
        
        # Check if page has job-related content
        job_keywords = ['developer', 'engineer', 'software', 'remote', 'job', 'position']
        found_keywords = [kw for kw in job_keywords if kw.lower() in page_text.lower()]
        print(f"   🔍 Job keywords found: {found_keywords}")
        
        best_result = None
        
        for job_selector, title_selector, company_selector in selectors_list:
            try:
                containers = soup.select(job_selector)
                print(f"   📦 Selector '{job_selector}': {len(containers)} containers")
                
                if len(containers) > 0:
                    # Test first container
                    first = containers[0]
                    
                    # Try to find title
                    title_elem = first.select_one(title_selector) if title_selector else first.find(['h1', 'h2', 'h3', 'h4', 'a'])
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    # Try to find company
                    company = ""
                    if company_selector:
                        company_elem = first.select_one(company_selector)
                        company = company_elem.get_text(strip=True) if company_elem else ""
                    
                    # Try to find link
                    link_elem = first.find('a', href=True)
                    link = link_elem.get('href') if link_elem else ""
                    
                    print(f"      Sample job:")
                    print(f"        Title: '{title[:60]}...' ({len(title)} chars)")
                    if company:
                        print(f"        Company: '{company}'")
                    if link:
                        print(f"        Link: '{link[:60]}...'")
                    
                    # Score this selector
                    score = 0
                    if title and len(title) > 5:
                        score += 2
                    if company:
                        score += 1
                    if link:
                        score += 1
                    if len(containers) >= 10:
                        score += 2
                    
                    print(f"      Score: {score}/6")
                    
                    if score >= 4:  # Good enough
                        best_result = (job_selector, title_selector, company_selector, len(containers))
                        print(f"      ✅ Good selector found!")
                        break
                        
            except Exception as e:
                print(f"   ⚠️ Selector error: {e}")
                continue
        
        if best_result:
            print(f"   🎉 {name} looks GOOD!")
            return True, best_result
        else:
            print(f"   ❌ {name} not suitable")
            return False, None
            
    except Exception as e:
        print(f"   ❌ Error testing {name}: {e}")
        return False, None

def research_dev_job_boards():
    """Research developer-focused job boards"""
    
    print("🔍 Researching Developer-Focused Job Boards")
    print("=" * 60)
    
    dev_job_boards = [
        {
            'name': 'StackOverflow Jobs',
            'url': 'https://stackoverflow.com/jobs/remote-developer-jobs',
            'selectors': [
                ('[data-jobid]', '.job-link', '.company'),
                ('.listResults .job', 'h2', '.employer'),
                ('.-job', '.-title', '.-company')
            ]
        },
        {
            'name': 'AuthenticJobs',
            'url': 'https://authenticjobs.com/#remote=true&skills=software-development',
            'selectors': [
                ('.job', '.title', '.company'),
                ('article', 'h3', '.company-name'),
                ('.listing', '.job-title', '.employer')
            ]
        },
        {
            'name': 'AngelList API',
            'url': 'https://angel.co/jobs',
            'selectors': [
                ('[data-test="StartupResult"]', '[data-test="JobTitle"]', '[data-test="StartupName"]'),
                ('.startup-link', '.job-title', '.startup-name'),
                ('.job-listing', 'h4', '.company')
            ]
        },
        {
            'name': 'LaunchJobs',
            'url': 'https://launchjobs.com/jobs/remote',
            'selectors': [
                ('.job-item', '.job-title', '.company-name'),
                ('article', 'h3', '.company'),
                ('.listing', 'h2', '.employer')
            ]
        },
        {
            'name': 'RemoteOK Alternative',
            'url': 'https://remoteok.io/remote-jobs',
            'selectors': [
                ('tr.job', 'td.company h2', 'td.company h3'),
                ('.job', '.position', '.company'),
                ('tr[data-url]', '.company-name', '.location')
            ]
        },
        {
            'name': 'Dribbble Jobs',
            'url': 'https://dribbble.com/jobs?location=Anywhere',
            'selectors': [
                ('.job-board-job', '.job-title', '.company-name'),
                ('article', 'h4', '.company'),
                ('.listing', 'h3', '.employer')
            ]
        }
    ]
    
    good_sources = []
    
    for source in dev_job_boards:
        is_good, result = detailed_test(
            source['name'],
            source['url'],
            source['selectors']
        )
        
        if is_good:
            good_sources.append((source['name'], source['url'], result))
    
    print(f"\n" + "="*60)
    print(f"📊 FINAL RESULTS")
    print(f"="*60)
    
    if good_sources:
        print(f"✅ Found {len(good_sources)} workable sources:")
        
        for name, url, (job_sel, title_sel, company_sel, count) in good_sources:
            print(f"\n   🎯 {name}")
            print(f"      URL: {url}")
            print(f"      Jobs found: {count}")
            print(f"      Job selector: {job_sel}")
            print(f"      Title selector: {title_sel}")
            print(f"      Company selector: {company_sel}")
        
        # Pick the best one
        best = max(good_sources, key=lambda x: x[2][3])  # Most jobs
        print(f"\n🏆 RECOMMENDED: {best[0]} ({best[2][3]} jobs)")
        
        return {
            'name': best[0],
            'url': best[1],
            'job_selector': best[2][0],
            'title_selector': best[2][1], 
            'company_selector': best[2][2],
            'job_count': best[2][3]
        }
    else:
        print(f"❌ No suitable sources found")
        return None

if __name__ == "__main__":
    result = research_dev_job_boards()
    
    if result:
        print(f"\n🚀 READY TO IMPLEMENT!")
        print(f"   Source: {result['name']}")
        print(f"   Jobs available: {result['job_count']}")
        print(f"   Should be easy to scrape with static HTML")
    else:
        print(f"\n💡 May need to use RSS feeds or find API endpoints instead")