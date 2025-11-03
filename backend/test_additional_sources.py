#!/usr/bin/env python3
"""
Deep test of JustRemote and Arbeitnow API for implementation
"""

import requests
import json
from bs4 import BeautifulSoup
import re

def test_justremote_detailed():
    """Test JustRemote structure in detail"""
    
    print("🔍 DETAILED TEST: JustRemote")
    print("=" * 40)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        
        response = requests.get('https://justremote.co/remote-jobs', headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for job cards/listings
            job_cards = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'job|card|listing'))
            
            print(f"✅ Found {len(job_cards)} potential job containers")
            
            # Try to extract job details from first few jobs
            jobs_found = []
            for i, card in enumerate(job_cards[:5]):
                try:
                    # Look for title
                    title_elem = card.find(['h1', 'h2', 'h3', 'a'], class_=re.compile(r'title|job|position'))
                    if not title_elem:
                        title_elem = card.find(['h1', 'h2', 'h3'])
                    
                    # Look for company
                    company_elem = card.find(['span', 'div', 'p'], class_=re.compile(r'company|employer'))
                    
                    # Look for link
                    link_elem = card.find('a', href=True)
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                        link = link_elem['href'] if link_elem else None
                        
                        jobs_found.append({
                            'title': title,
                            'company': company,
                            'link': link
                        })
                        
                        print(f"   {i+1}. {title} at {company}")
                        if link:
                            print(f"      🔗 {link}")
                            
                except Exception as e:
                    continue
            
            return len(jobs_found) > 0, jobs_found
            
        else:
            print(f"❌ Failed to access JustRemote: {response.status_code}")
            return False, []
            
    except Exception as e:
        print(f"❌ JustRemote test failed: {e}")
        return False, []

def test_arbeitnow_api_detailed():
    """Test Arbeitnow API structure in detail"""
    
    print("\n🔍 DETAILED TEST: Arbeitnow API")
    print("=" * 40)
    
    try:
        # Test their API endpoint
        api_url = "https://www.arbeitnow.com/api/job-board-api"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(api_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ JSON API accessible")
                print(f"📊 Data type: {type(data)}")
                
                if isinstance(data, dict):
                    print(f"📋 Keys: {list(data.keys())}")
                    
                    # Look for jobs in the data
                    jobs_key = None
                    for key in data.keys():
                        if 'job' in key.lower() or 'data' in key.lower():
                            jobs_key = key
                            break
                    
                    if jobs_key and isinstance(data[jobs_key], list):
                        jobs = data[jobs_key]
                        print(f"📈 Found {len(jobs)} jobs in '{jobs_key}' field")
                        
                        # Show sample job structure
                        if jobs:
                            sample_job = jobs[0]
                            print(f"\n📋 Sample job structure:")
                            for key, value in sample_job.items():
                                print(f"   {key}: {str(value)[:100]}...")
                            
                            # Extract some sample jobs
                            extracted_jobs = []
                            for job in jobs[:3]:
                                title = job.get('title', job.get('position', 'Unknown'))
                                company = job.get('company', job.get('company_name', 'Unknown'))
                                location = job.get('location', 'Remote')
                                url = job.get('url', job.get('link', ''))
                                
                                extracted_jobs.append({
                                    'title': title,
                                    'company': company,
                                    'location': location,
                                    'url': url
                                })
                                
                                print(f"\n   Job {len(extracted_jobs)}: {title}")
                                print(f"   Company: {company}")
                                print(f"   Location: {location}")
                                print(f"   URL: {url}")
                        
                        return True, jobs
                    
                elif isinstance(data, list):
                    print(f"📈 Direct list with {len(data)} items")
                    if data:
                        sample = data[0]
                        print(f"📋 Sample item keys: {list(sample.keys()) if isinstance(sample, dict) else 'Not a dict'}")
                    return True, data
                    
            except json.JSONDecodeError:
                print(f"❌ Response is not valid JSON")
                return False, []
            
        else:
            print(f"❌ API not accessible: {response.status_code}")
            
            # Try alternative endpoint
            alt_url = "https://www.arbeitnow.com/api/job-board-api"
            print(f"🔄 Trying alternative endpoint...")
            
            response = requests.get(alt_url, headers=headers, timeout=15)
            if response.status_code == 200:
                print(f"✅ Alternative endpoint works")
                return True, []
            else:
                return False, []
            
    except Exception as e:
        print(f"❌ Arbeitnow API test failed: {e}")
        return False, []

def main():
    """Test both sources and provide implementation recommendations"""
    
    print("🚀 TESTING ADDITIONAL JOB SOURCES FOR IMPLEMENTATION")
    print("=" * 60)
    
    # Test JustRemote
    justremote_works, justremote_jobs = test_justremote_detailed()
    
    # Test Arbeitnow
    arbeitnow_works, arbeitnow_jobs = test_arbeitnow_api_detailed()
    
    print(f"\n📊 IMPLEMENTATION RECOMMENDATIONS")
    print("=" * 40)
    
    recommendations = []
    
    if justremote_works:
        print(f"✅ JustRemote - RECOMMENDED")
        print(f"   • HTML scraping required")
        print(f"   • Found {len(justremote_jobs)} sample jobs")
        print(f"   • Clean structure for parsing")
        recommendations.append("JustRemote")
    else:
        print(f"❌ JustRemote - NOT RECOMMENDED")
        print(f"   • Scraping issues detected")
    
    if arbeitnow_works:
        print(f"✅ Arbeitnow API - RECOMMENDED") 
        print(f"   • JSON API available")
        print(f"   • Found {len(arbeitnow_jobs)} sample jobs")
        print(f"   • Easy to implement")
        recommendations.append("Arbeitnow API")
    else:
        print(f"❌ Arbeitnow API - NOT RECOMMENDED")
        print(f"   • API access issues")
    
    print(f"\n🎯 FINAL RECOMMENDATION: Implement {len(recommendations)} additional sources")
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
    
    return recommendations

if __name__ == "__main__":
    recommendations = main()
    if recommendations:
        print(f"\n🚀 Ready to implement {len(recommendations)} new job sources!")
    else:
        print(f"\n⚠️ No additional sources viable - stick with RemoteOK for now")