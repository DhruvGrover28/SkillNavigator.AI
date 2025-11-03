#!/usr/bin/env python3
"""
Test the job search API endpoint with the enhanced scraper
"""

import requests
import json

def test_job_search_api():
    """Test the job search API endpoint"""
    
    base_url = "http://localhost:8000"
    
    print("🔍 Testing Job Search API with Enhanced Scraper")
    print(f"🌐 Base URL: {base_url}")
    
    # Test API health first
    try:
        health_response = requests.get(f"{base_url}/")
        print(f"✅ Server is responsive: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return False
    
    # Test job search endpoint
    search_url = f"{base_url}/api/jobs/search"
    search_data = {
        "keywords": "python developer",
        "location": "remote",
        "max_jobs": 8
    }
    
    print(f"\n📡 POST {search_url}")
    print(f"📦 Request data: {json.dumps(search_data, indent=2)}")
    
    try:
        response = requests.post(search_url, json=search_data, timeout=30)
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS: Job search completed")
            print(f"📈 Jobs found: {data.get('jobs_found', 0)}")
            print(f"⏱️ Search duration: {data.get('search_duration', 0):.2f}s")
            
            # Show job details
            jobs = data.get('jobs', [])
            if jobs:
                print(f"\n📋 Job listings:")
                for i, job in enumerate(jobs[:3]):  # Show first 3 jobs
                    print(f"  {i+1}. 🏢 {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
                    print(f"     📍 {job.get('location', 'N/A')}")
                    print(f"     🔗 {job.get('url', 'N/A')}")
                    print(f"     🛠️ Skills: {', '.join(job.get('skills', [])[:3])}")
                    print()
            else:
                print("⚠️ No jobs returned")
            
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📄 Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📄 Error text: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (>30s)")
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    success = test_job_search_api()
    if success:
        print("🎉 API test passed! Enhanced scraper is working via API.")
    else:
        print("💥 API test failed!")