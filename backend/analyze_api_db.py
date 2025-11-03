#!/usr/bin/env python3
"""
Check the full API response and database vs API comparison
"""

import requests
import sqlite3
import json
import os

def detailed_api_check():
    """Get detailed API response and analyze"""
    
    print("🔍 Detailed API Analysis")
    print("=" * 30)
    
    try:
        response = requests.get("http://localhost:8000/api/jobs", timeout=10)
        
        if response.status_code == 200:
            jobs = response.json()
            print(f"📊 API returned {len(jobs)} jobs")
            
            # Analyze sources
            sources = {}
            for job in jobs:
                source = job.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            
            print(f"📋 Jobs by source in API:")
            for source, count in sources.items():
                print(f"   {source}: {count} jobs")
            
            # Show sample jobs from each source
            print(f"\n📋 Sample jobs by source:")
            seen_sources = set()
            for job in jobs:
                source = job.get('source', 'unknown')
                if source not in seen_sources:
                    print(f"   {source}:")
                    print(f"      Title: {job.get('title', 'No title')}")
                    print(f"      Company: {job.get('company', 'No company')}")
                    print(f"      URL: {job.get('url', 'No URL')}")
                    seen_sources.add(source)
                    
                if len(seen_sources) >= 3:  # Show max 3 sources
                    break
            
            return jobs
        else:
            print(f"❌ API error: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ API request failed: {e}")
        return []

def compare_db_vs_api():
    """Compare database content with API response"""
    
    print("\n🔍 Database vs API Comparison")
    print("=" * 35)
    
    # Get database stats
    db_path = os.path.join(os.path.dirname(__file__), 'skillnavigator.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get database job counts by source
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM jobs 
            GROUP BY source
            ORDER BY count DESC
        """)
        db_sources = dict(cursor.fetchall())
        
        # Get total in database
        cursor.execute("SELECT COUNT(*) FROM jobs")
        db_total = cursor.fetchone()[0]
        
        print(f"📊 Database: {db_total} total jobs")
        for source, count in db_sources.items():
            print(f"   {source}: {count} jobs")
        
        conn.close()
        
        # Get API stats
        api_jobs = detailed_api_check()
        
        if api_jobs:
            api_sources = {}
            for job in api_jobs:
                source = job.get('source', 'unknown')
                api_sources[source] = api_sources.get(source, 0) + 1
            
            print(f"\n📊 API: {len(api_jobs)} total jobs")
            for source, count in api_sources.items():
                print(f"   {source}: {count} jobs")
            
            # Compare
            print(f"\n🔍 Comparison:")
            print(f"   Database total: {db_total}")
            print(f"   API total: {len(api_jobs)}")
            
            if db_total != len(api_jobs):
                print(f"   ⚠️ Mismatch! API showing {len(api_jobs)} out of {db_total} database jobs")
                
                # Check if API is filtering
                if len(api_jobs) < db_total:
                    print(f"   💡 API might be filtering jobs (pagination, limits, etc.)")
            else:
                print(f"   ✅ Counts match!")
            
            # Check sources
            db_sources_set = set(db_sources.keys())
            api_sources_set = set(api_sources.keys())
            
            missing_in_api = db_sources_set - api_sources_set
            if missing_in_api:
                print(f"   ⚠️ Sources in DB but not in API: {missing_in_api}")
            
            extra_in_api = api_sources_set - db_sources_set
            if extra_in_api:
                print(f"   ⚠️ Sources in API but not in DB: {extra_in_api}")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

def test_fresh_scrape():
    """Check if we can trigger a fresh scrape"""
    
    print("\n🔍 Testing Fresh Job Scrape")
    print("=" * 32)
    
    try:
        # Look for scrape endpoint
        scrape_endpoints = [
            "/api/jobs/scrape",
            "/api/scrape",
            "/scrape",
            "/api/jobs/refresh",
            "/api/refresh"
        ]
        
        for endpoint in scrape_endpoints:
            try:
                url = f"http://localhost:8000{endpoint}"
                print(f"📡 Testing: {url}")
                
                # Try POST first
                response = requests.post(url, timeout=10)
                if response.status_code == 200:
                    print(f"   ✅ POST worked: {response.status_code}")
                    try:
                        data = response.json()
                        print(f"   📊 Response: {data}")
                    except:
                        print(f"   📄 Response: {response.text[:200]}...")
                    continue
                    
                # Try GET
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"   ✅ GET worked: {response.status_code}")
                    try:
                        data = response.json()
                        print(f"   📊 Response: {data}")
                    except:
                        print(f"   📄 Response: {response.text[:200]}...")
                else:
                    print(f"   ❌ {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    except Exception as e:
        print(f"❌ Scrape test failed: {e}")

if __name__ == "__main__":
    compare_db_vs_api()
    test_fresh_scrape()