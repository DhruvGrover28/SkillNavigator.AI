#!/usr/bin/env python3
"""
Check the correct API endpoints on port 8000
"""

import requests
import json

def test_port_8000_endpoints():
    """Test various endpoints on port 8000"""
    
    print("🔍 Testing Port 8000 API Endpoints")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    endpoints_to_test = [
        "/api/jobs",
        "/jobs",
        "/api/jobs/search",
        "/api/search",
        "/",
        "/health",
        "/status"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            url = f"{base_url}{endpoint}"
            print(f"📡 Testing: {url}")
            
            response = requests.get(url, timeout=5)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    # Try to parse as JSON
                    data = response.json()
                    
                    if isinstance(data, list):
                        print(f"   ✅ JSON Array with {len(data)} items")
                        if data and 'title' in str(data[0]):
                            print(f"   🎯 Looks like jobs data!")
                            # Show sample
                            sample = data[0] if data else {}
                            print(f"      Sample: {sample.get('title', 'No title')} at {sample.get('company', 'No company')}")
                    elif isinstance(data, dict):
                        print(f"   ✅ JSON Object with keys: {list(data.keys())}")
                        if 'jobs' in data:
                            jobs = data['jobs']
                            print(f"   🎯 Found jobs array with {len(jobs)} jobs!")
                        elif 'data' in data:
                            print(f"   🎯 Found data field")
                    else:
                        print(f"   ✅ JSON: {str(data)[:100]}...")
                        
                except json.JSONDecodeError:
                    # Not JSON, check if it's HTML or text
                    content = response.text
                    if '<html' in content.lower():
                        print(f"   ✅ HTML page (length: {len(content)})")
                        if 'job' in content.lower():
                            print(f"      🎯 Contains job-related content")
                    else:
                        print(f"   ✅ Text response: {content[:100]}...")
            
            elif response.status_code == 404:
                print(f"   ❌ Not found")
            elif response.status_code == 405:
                print(f"   ❌ Method not allowed")
            else:
                print(f"   ⚠️ Unexpected status")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection failed")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()

def test_job_search_with_params():
    """Test job search with parameters"""
    
    print("🔍 Testing Job Search with Parameters")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    search_endpoints = [
        "/api/jobs?keywords=developer",
        "/api/jobs?q=software",
        "/jobs?search=python",
        "/api/search?keywords=remote",
        "/search?q=developer"
    ]
    
    for endpoint in search_endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"📡 Testing: {url}")
            
            response = requests.get(url, timeout=5)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   ✅ Found {len(data)} jobs in search results")
                        if data:
                            sample = data[0]
                            print(f"      Sample: {sample.get('title', 'No title')}")
                            print(f"      Source: {sample.get('source', 'No source')}")
                    elif isinstance(data, dict) and 'jobs' in data:
                        jobs = data['jobs']
                        print(f"   ✅ Found {len(jobs)} jobs in search results")
                except:
                    print(f"   ⚠️ Non-JSON response")
            else:
                print(f"   ❌ Status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    test_port_8000_endpoints()
    test_job_search_with_params()