#!/usr/bin/env python3
"""
Final verification: Complete end-to-end test of real job data flow
"""

import requests
import json
import sqlite3
import os

def verify_complete_integration():
    """Verify the complete integration of real job data"""
    
    print("🎯 FINAL VERIFICATION: Complete Real Job Data Integration")
    print("=" * 70)
    
    results = {
        'database_real_jobs': 0,
        'api_working': False,
        'api_jobs_returned': 0,
        'real_urls_count': 0,
        'frontend_accessible': False
    }
    
    # 1. Check Database
    print("1️⃣ Checking Database for Real Jobs...")
    db_path = os.path.join(os.path.dirname(__file__), 'skillnavigator.db')
    
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Count real RemoteOK jobs
            cursor.execute("SELECT COUNT(*) FROM jobs WHERE source = 'remoteok'")
            real_jobs = cursor.fetchone()[0]
            results['database_real_jobs'] = real_jobs
            
            # Count template jobs (should be 0)
            cursor.execute("SELECT COUNT(*) FROM jobs WHERE description LIKE 'We are seeking a talented%'")
            template_jobs = cursor.fetchone()[0]
            
            print(f"   ✅ Real RemoteOK jobs in database: {real_jobs}")
            print(f"   ✅ Template jobs remaining: {template_jobs}")
            
            # Show sample real jobs
            cursor.execute("""
                SELECT title, company, location, apply_url 
                FROM jobs 
                WHERE source = 'remoteok' 
                ORDER BY scraped_at DESC 
                LIMIT 3
            """)
            
            sample_jobs = cursor.fetchall()
            print(f"   📋 Sample real jobs:")
            for i, (title, company, location, url) in enumerate(sample_jobs, 1):
                print(f"      {i}. {title} at {company} ({location})")
                print(f"         🔗 {url}")
            
        except Exception as e:
            print(f"   ❌ Database error: {e}")
        finally:
            conn.close()
    else:
        print(f"   ❌ Database not found at: {db_path}")
    
    # 2. Test API
    print(f"\n2️⃣ Testing API Integration...")
    try:
        # Test health
        health_response = requests.get("http://localhost:8000/", timeout=5)
        if health_response.status_code == 200:
            print(f"   ✅ API server responsive")
            
            # Test job search
            search_response = requests.post(
                "http://localhost:8000/api/jobs/search",
                json={"keywords": "software", "max_jobs": 5},
                timeout=15
            )
            
            if search_response.status_code == 200:
                results['api_working'] = True
                data = search_response.json()
                jobs_count = data.get('jobs_found', 0)
                jobs_list = data.get('jobs', [])
                results['api_jobs_returned'] = jobs_count
                
                print(f"   ✅ API job search working: {jobs_count} jobs found")
                
                # Check URL quality
                real_urls = 0
                for job in jobs_list:
                    url = job.get('url', '')
                    if 'remoteok.com/remote-jobs' in url and len(url) > 40:
                        real_urls += 1
                
                results['real_urls_count'] = real_urls
                print(f"   ✅ Real job URLs returned: {real_urls}/{len(jobs_list)}")
                
                # Show sample API response
                if jobs_list:
                    print(f"   📋 Sample API job response:")
                    job = jobs_list[0]
                    print(f"      Title: {job.get('title', 'N/A')}")
                    print(f"      Company: {job.get('company', 'N/A')}")
                    print(f"      URL: {job.get('url', 'N/A')}")
            else:
                print(f"   ❌ API search failed: {search_response.status_code}")
        else:
            print(f"   ❌ API server not responding: {health_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ API test failed: {e}")
    
    # 3. Test Frontend
    print(f"\n3️⃣ Testing Frontend Accessibility...")
    try:
        frontend_response = requests.get("http://localhost:5174/", timeout=5)
        if frontend_response.status_code == 200:
            results['frontend_accessible'] = True
            print(f"   ✅ Frontend accessible at http://localhost:5174")
            print(f"   📱 Users can now search for real jobs in the UI!")
        else:
            print(f"   ❌ Frontend not responding: {frontend_response.status_code}")
    except Exception as e:
        print(f"   ❌ Frontend test failed: {e}")
    
    # 4. Final Assessment
    print(f"\n🎯 FINAL ASSESSMENT")
    print("=" * 50)
    
    success_criteria = [
        (results['database_real_jobs'] >= 20, f"Database has {results['database_real_jobs']} real jobs (target: ≥20)"),
        (results['api_working'], f"API is working and serving jobs"),
        (results['api_jobs_returned'] >= 5, f"API returns {results['api_jobs_returned']} jobs (target: ≥5)"),
        (results['real_urls_count'] >= 3, f"API returns {results['real_urls_count']} real job URLs (target: ≥3)"),
        (results['frontend_accessible'], f"Frontend is accessible for users")
    ]
    
    passed = 0
    total = len(success_criteria)
    
    for is_passing, description in success_criteria:
        status = "✅" if is_passing else "❌"
        print(f"{status} {description}")
        if is_passing:
            passed += 1
    
    print(f"\n📊 SCORE: {passed}/{total} criteria passed")
    
    if passed == total:
        print(f"\n🎉 SUCCESS: Complete real job data integration working!")
        print(f"🚀 Your SkillNavigator platform now serves REAL job data:")
        print(f"   • {results['database_real_jobs']} real jobs in database")
        print(f"   • API serving {results['api_jobs_returned']} jobs per search")
        print(f"   • Frontend accessible at http://localhost:5174")
        print(f"   • Backend API docs at http://localhost:8000/api/docs")
        print(f"\n🎯 DEPLOYMENT READY: Everything is working with real data!")
        return True
    else:
        print(f"\n⚠️ Some issues found - {total-passed} criteria failed")
        return False

if __name__ == "__main__":
    success = verify_complete_integration()
    if success:
        print(f"\n✅ Verification complete - ready for deployment!")
    else:
        print(f"\n❌ Verification failed - check issues above")