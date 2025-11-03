#!/usr/bin/env python3
"""
Research and test additional job sites similar to RemoteOK
Focus on popular sites that are scraping-friendly
"""

import requests
import json
from bs4 import BeautifulSoup
import time

def test_potential_job_sources():
    """Test potential job sources for scraping compatibility"""
    
    print("🔍 Researching Additional Job Sources Similar to RemoteOK...")
    print("=" * 60)
    
    # Potential sources to test (popular and scraping-friendly)
    sources_to_test = [
        {
            'name': 'AngelList (Wellfound) Jobs API',
            'base_url': 'https://angel.co',
            'api_url': 'https://angel.co/job_listings/startup_ids',
            'description': 'Popular startup job platform with API access',
            'scraping_friendly': True
        },
        {
            'name': 'Himalayas Remote Jobs',
            'base_url': 'https://himalayas.app',
            'test_url': 'https://himalayas.app/jobs/remote',
            'description': 'Remote-focused job board, very clean structure',
            'scraping_friendly': True
        },
        {
            'name': 'JustRemote',
            'base_url': 'https://justremote.co',
            'test_url': 'https://justremote.co/remote-jobs',
            'description': 'Clean remote job listings, simple structure',
            'scraping_friendly': True
        },
        {
            'name': 'NoDesk Remote Jobs',
            'base_url': 'https://nodesk.co',
            'test_url': 'https://nodesk.co/remote-jobs/',
            'description': 'Remote work focused job board',
            'scraping_friendly': True
        },
        {
            'name': 'Arbeitnow API',
            'base_url': 'https://www.arbeitnow.com',
            'api_url': 'https://www.arbeitnow.com/api/job-board-api',
            'description': 'European job board with public API',
            'scraping_friendly': True
        }
    ]
    
    results = []
    
    for source in sources_to_test:
        print(f"\n🌐 Testing: {source['name']}")
        print(f"   Base URL: {source['base_url']}")
        
        try:
            # Test basic connectivity
            test_url = source.get('test_url', source.get('api_url', source['base_url']))
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            }
            
            response = requests.get(test_url, headers=headers, timeout=10)
            
            result = {
                'name': source['name'],
                'status_code': response.status_code,
                'accessible': response.status_code == 200,
                'content_length': len(response.text),
                'appears_scrapable': False,
                'has_job_data': False,
                'notes': []
            }
            
            if response.status_code == 200:
                print(f"   ✅ Accessible (Status: {response.status_code})")
                print(f"   📄 Content Length: {len(response.text)} chars")
                
                # Check if it's JSON API
                try:
                    json_data = response.json()
                    result['appears_scrapable'] = True
                    result['has_job_data'] = True
                    result['notes'].append(f"JSON API with {len(json_data)} items")
                    print(f"   🔧 JSON API detected with {len(json_data)} items")
                except:
                    # Check HTML structure for job listings
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for common job listing patterns
                    job_indicators = [
                        soup.find_all(attrs={'class': lambda x: x and 'job' in x.lower()}),
                        soup.find_all(attrs={'class': lambda x: x and 'position' in x.lower()}),
                        soup.find_all(attrs={'class': lambda x: x and 'listing' in x.lower()}),
                        soup.find_all('h1', string=lambda x: x and 'job' in x.lower()),
                        soup.find_all('h2', string=lambda x: x and any(word in x.lower() for word in ['developer', 'engineer', 'manager']))
                    ]
                    
                    total_job_elements = sum(len(indicator) for indicator in job_indicators)
                    
                    if total_job_elements > 0:
                        result['appears_scrapable'] = True
                        result['has_job_data'] = True
                        result['notes'].append(f"HTML with ~{total_job_elements} job-related elements")
                        print(f"   🔧 HTML structure looks scrapable (~{total_job_elements} job elements)")
                    else:
                        result['notes'].append("HTML structure unclear")
                        print(f"   ⚠️ HTML structure unclear for scraping")
                
            else:
                print(f"   ❌ Not accessible (Status: {response.status_code})")
                result['notes'].append(f"HTTP {response.status_code}")
            
            results.append(result)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            result = {
                'name': source['name'],
                'accessible': False,
                'error': str(e),
                'notes': [f"Connection failed: {e}"]
            }
            results.append(result)
        
        # Be respectful - small delay between requests
        time.sleep(2)
    
    # Summary
    print(f"\n📊 SUMMARY OF POTENTIAL JOB SOURCES")
    print("=" * 50)
    
    viable_sources = []
    for result in results:
        status = "✅" if result.get('accessible') and result.get('appears_scrapable') else "❌"
        print(f"{status} {result['name']}")
        
        for note in result.get('notes', []):
            print(f"    📝 {note}")
        
        if result.get('accessible') and result.get('appears_scrapable'):
            viable_sources.append(result['name'])
    
    print(f"\n🎯 RECOMMENDED SOURCES TO IMPLEMENT:")
    for i, source in enumerate(viable_sources[:2], 1):  # Top 2 recommendations
        print(f"   {i}. {source}")
    
    return viable_sources[:2]

if __name__ == "__main__":
    recommended = test_potential_job_sources()
    if recommended:
        print(f"\n✅ Found {len(recommended)} additional viable job sources!")
        print("🚀 Ready to implement these in the enhanced scraper!")
    else:
        print(f"\n⚠️ No additional viable sources found - RemoteOK remains primary source")