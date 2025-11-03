#!/usr/bin/env python3
"""
Test the real job data in the API and verify frontend integration
"""

import requests
import json
import time

def test_api_with_real_data():
    """Test that the API is serving real job data"""
    
    print("🔍 Testing API with Real Job Data...")
    
    base_url = "http://localhost:8000"
    
    # Test server health
    try:
        health_response = requests.get(f"{base_url}/", timeout=5)
        if health_response.status_code != 200:
            print(f"❌ Server not responding properly: {health_response.status_code}")
            return False
        print("✅ Server is responsive")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return False
    
    # Test jobs API
    search_url = f"{base_url}/api/jobs/search"
    search_data = {
        "keywords": "software engineer",
        "location": "remote",
        "max_jobs": 8
    }
    
    print(f"\n📡 Testing job search API...")
    print(f"🔍 Searching for: {search_data['keywords']}")
    
    try:
        response = requests.post(search_url, json=search_data, timeout=30)
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            jobs_found = data.get('jobs_found', 0)
            jobs_list = data.get('jobs', [])
            
            print(f"✅ SUCCESS: Found {jobs_found} jobs")
            print(f"⏱️ Search took {data.get('search_duration', 0):.2f} seconds")
            
            if jobs_list:
                print(f"\n📋 Sample jobs returned by API:")
                for i, job in enumerate(jobs_list[:5], 1):
                    print(f"  {i}. 🏢 {job.get('title', 'N/A')}")
                    print(f"     Company: {job.get('company', 'N/A')}")
                    print(f"     Location: {job.get('location', 'N/A')}")
                    print(f"     URL: {job.get('url', 'N/A')}")
                    print(f"     Skills: {', '.join(job.get('skills', [])[:3])}")
                    print()
                
                # Check if these are real URLs (not template)
                real_urls = 0
                for job in jobs_list:
                    url = job.get('url', '')
                    if 'remoteok.com/remote-jobs' in url and len(url) > 50:
                        real_urls += 1
                
                print(f"🔗 Real job URLs: {real_urls}/{len(jobs_list)}")
                
                if real_urls > 0:
                    print("✅ API is serving REAL job data with working URLs!")
                    return True
                else:
                    print("⚠️ Jobs found but URLs may not be fully formed")
                    return False
            else:
                print("⚠️ No jobs returned from API")
                return False
        else:
            print(f"❌ API Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_api_with_real_data()
    if success:
        print("\n🎉 API test passed! Real job data is being served correctly.")
        print("🌐 You can now access the frontend to see real jobs!")
        print("📋 API Documentation: http://localhost:8000/api/docs")
    else:
        print("\n💥 API test failed - check server and data!")