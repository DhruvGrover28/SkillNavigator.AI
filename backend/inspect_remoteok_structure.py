#!/usr/bin/env python3
"""
Inspect RemoteOK API response to fix URL construction
"""

import requests
import json

def inspect_remoteok_api():
    """Inspect actual RemoteOK API response structure"""
    
    print("🔍 Inspecting RemoteOK API Response Structure...")
    
    try:
        response = requests.get('https://remoteok.io/api', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"📊 API returned {len(data)} total items")
            
            # Skip metadata and look at first few real jobs
            jobs_data = data[1:] if len(data) > 1 else []
            
            print(f"\n📋 First 5 Job Data Structures:")
            for i, job_data in enumerate(jobs_data[:5]):
                if isinstance(job_data, dict):
                    print(f"\n--- Job {i+1} ---")
                    print(f"Title: {job_data.get('position', 'N/A')}")
                    print(f"Company: {job_data.get('company', 'N/A')}")
                    print(f"ID: {job_data.get('id', 'N/A')}")
                    print(f"Slug: {job_data.get('slug', 'N/A')}")
                    print(f"URL: {job_data.get('url', 'N/A')}")
                    print(f"Apply URL: {job_data.get('apply_url', 'N/A')}")
                    
                    # Show all available keys
                    print(f"Available keys: {list(job_data.keys())[:10]}...")  # First 10 keys
                    
                    # Construct what the URL should be
                    job_id = job_data.get('id', '')
                    slug = job_data.get('slug', '')
                    if slug:
                        constructed_url = f"https://remoteok.com/remote-jobs/{slug}"
                        print(f"Constructed URL: {constructed_url}")
                        
        else:
            print(f"❌ API request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect_remoteok_api()