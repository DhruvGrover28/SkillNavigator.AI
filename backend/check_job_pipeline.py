#!/usr/bin/env python3
"""
Check if new job postings are being saved to database and accessible via frontend API
"""

import sqlite3
import requests
import json
from datetime import datetime, timedelta
import os

def check_database_jobs():
    """Check jobs in the database"""
    
    print("🔍 Checking Database for New Job Postings")
    print("=" * 50)
    
    db_path = os.path.join(os.path.dirname(__file__), 'skillnavigator.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check total jobs
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = cursor.fetchone()[0]
        print(f"📊 Total jobs in database: {total_jobs}")
        
        # Check jobs from our verified sources
        cursor.execute("""
            SELECT COUNT(*) FROM jobs 
            WHERE source IN ('remoteok', 'arbeitnow')
        """)
        scraped_jobs = cursor.fetchone()[0]
        print(f"📊 Jobs from verified sources: {scraped_jobs}")
        
        # Check recent jobs (last 24 hours)
        cursor.execute("""
            SELECT COUNT(*) FROM jobs 
            WHERE scraped_at > datetime('now', '-1 day')
        """)
        recent_jobs = cursor.fetchone()[0]
        print(f"📊 Jobs added in last 24 hours: {recent_jobs}")
        
        # Check jobs by source
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM jobs 
            GROUP BY source
            ORDER BY count DESC
        """)
        source_counts = cursor.fetchall()
        
        print(f"\n📋 Jobs by source:")
        for source, count in source_counts:
            print(f"   {source}: {count} jobs")
        
        # Show sample of recent jobs from verified sources
        cursor.execute("""
            SELECT title, company, source, apply_url, scraped_at
            FROM jobs 
            WHERE source IN ('remoteok', 'arbeitnow')
            ORDER BY scraped_at DESC
            LIMIT 5
        """)
        
        recent_verified_jobs = cursor.fetchall()
        
        if recent_verified_jobs:
            print(f"\n📋 Recent jobs from verified sources:")
            for title, company, source, url, scraped_at in recent_verified_jobs:
                print(f"   🏢 {title} at {company}")
                print(f"      Source: {source} | Added: {scraped_at}")
                print(f"      URL: {url[:60]}...")
                print()
        else:
            print(f"\n⚠️ No jobs found from verified sources (remoteok, arbeitnow)")
        
        conn.close()
        return scraped_jobs > 0
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_frontend_api():
    """Check if jobs are accessible via frontend API"""
    
    print("🔍 Checking Frontend API")
    print("=" * 30)
    
    # Try different possible API endpoints
    api_endpoints = [
        'http://localhost:5000/api/jobs',
        'http://localhost:3000/api/jobs', 
        'http://127.0.0.1:5000/api/jobs',
        'http://127.0.0.1:3000/api/jobs'
    ]
    
    for endpoint in api_endpoints:
        try:
            print(f"📡 Testing: {endpoint}")
            response = requests.get(endpoint, timeout=5)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if isinstance(data, list):
                        jobs_count = len(data)
                    elif isinstance(data, dict) and 'jobs' in data:
                        jobs_count = len(data['jobs'])
                    elif isinstance(data, dict) and 'data' in data:
                        jobs_count = len(data['data'])
                    else:
                        jobs_count = 1 if data else 0
                    
                    print(f"   ✅ API working! Found {jobs_count} jobs")
                    
                    # Check if we have jobs from verified sources
                    if isinstance(data, list) and data:
                        sample_job = data[0]
                        print(f"   📋 Sample job: {sample_job.get('title', 'No title')}")
                        print(f"      Company: {sample_job.get('company', 'No company')}")
                        print(f"      Source: {sample_job.get('source', 'No source')}")
                        
                        # Count jobs by source
                        sources = {}
                        for job in data:
                            source = job.get('source', 'unknown')
                            sources[source] = sources.get(source, 0) + 1
                        
                        print(f"   📊 Jobs by source in API:")
                        for source, count in sources.items():
                            print(f"      {source}: {count} jobs")
                        
                        # Check for our verified sources
                        verified_sources = ['remoteok', 'arbeitnow']
                        found_verified = any(source in sources for source in verified_sources)
                        
                        if found_verified:
                            print(f"   ✅ Verified sources found in API!")
                            return True, jobs_count
                        else:
                            print(f"   ⚠️ No verified sources in API")
                            return True, jobs_count
                    
                    return True, jobs_count
                    
                except json.JSONDecodeError:
                    print(f"   ⚠️ API returned non-JSON response")
                    print(f"   Response: {response.text[:200]}...")
                    return False, 0
                    
            else:
                print(f"   ❌ API returned {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection failed (server not running?)")
        except requests.exceptions.Timeout:
            print(f"   ❌ Request timeout")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"❌ No working API endpoints found")
    return False, 0

def check_if_backend_running():
    """Check if the backend server is running"""
    
    print("🔍 Checking if Backend Server is Running")
    print("=" * 42)
    
    ports_to_check = [5000, 3000, 8000, 8080]
    
    for port in ports_to_check:
        try:
            url = f"http://localhost:{port}"
            response = requests.get(url, timeout=3)
            print(f"   ✅ Server running on port {port}")
            print(f"      Status: {response.status_code}")
            return True, port
            
        except requests.exceptions.ConnectionError:
            print(f"   ❌ No server on port {port}")
        except Exception as e:
            print(f"   ❌ Port {port} error: {e}")
    
    print(f"⚠️ No backend server detected")
    return False, None

def main():
    """Main check function"""
    
    print("🔄 Checking Job Postings Flow: Scraper → Database → Frontend")
    print("=" * 65)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)
    
    # Check database
    db_has_jobs = check_database_jobs()
    
    print()
    
    # Check if backend is running
    backend_running, port = check_if_backend_running()
    
    print()
    
    # Check frontend API
    api_working, api_job_count = check_frontend_api()
    
    print()
    print("=" * 65)
    print("📊 SUMMARY")
    print("=" * 65)
    
    print(f"✅ Database has jobs: {'YES' if db_has_jobs else 'NO'}")
    print(f"✅ Backend server running: {'YES' if backend_running else 'NO'}")
    if backend_running:
        print(f"   Running on port: {port}")
    print(f"✅ Frontend API working: {'YES' if api_working else 'NO'}")
    if api_working:
        print(f"   Jobs in API: {api_job_count}")
    
    if db_has_jobs and backend_running and api_working:
        print(f"\n🎉 SUCCESS: Full pipeline working!")
        print(f"   Scraper → Database → API → Frontend ✅")
    else:
        print(f"\n⚠️ Issues in the pipeline:")
        if not db_has_jobs:
            print(f"   • Database missing verified source jobs")
        if not backend_running:
            print(f"   • Backend server not running")
        if not api_working:
            print(f"   • Frontend API not accessible")
        
        print(f"\n💡 Next steps:")
        if not backend_running:
            print(f"   1. Start the backend server: python main.py")
        if not db_has_jobs:
            print(f"   2. Run job scraper to populate database")
        if not api_working and backend_running:
            print(f"   3. Check API endpoints and routes")

if __name__ == "__main__":
    main()