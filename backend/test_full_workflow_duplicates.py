#!/usr/bin/env python3
"""
Test the full workflow: scrape jobs -> deduplicate -> save to database -> verify no duplicates
"""

import asyncio
import logging
import sys
import os
import sqlite3

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.simple_supervisor_agent import SimpleSupervisorAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_full_workflow_no_duplicates():
    """Test the full workflow including database duplicate prevention"""
    
    print("🔄 Testing Full Workflow: Scrape -> Deduplicate -> Database")
    print("=" * 60)
    
    # Check database before
    db_path = os.path.join(os.path.dirname(__file__), 'skillnavigator.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Count jobs before
    cursor.execute("SELECT COUNT(*) FROM jobs")
    jobs_before = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE source IN ('remoteok', 'arbeitnow', 'justremote')")
    scraped_before = cursor.fetchone()[0]
    
    print(f"📊 Database before test:")
    print(f"   Total jobs: {jobs_before}")
    print(f"   Scraped jobs: {scraped_before}")
    
    conn.close()
    
    # Test supervisor agent (which handles scraping + database saving)
    supervisor = SimpleSupervisorAgent()
    
    try:
        await supervisor.initialize()
        print(f"\n✅ Supervisor agent initialized")
        
        # Trigger job search (this will scrape and save to database)
        search_params = {
            'keywords': 'software developer',
            'location': 'remote',
            'max_jobs': 15
        }
        
        print(f"\n🔍 Running job search: {search_params}")
        result = await supervisor.trigger_job_search(search_params)
        
        if result['success']:
            jobs_found = result['total_found']
            saved_to_db = result['saved_to_db']
            
            print(f"✅ Job search completed:")
            print(f"   Jobs found: {jobs_found}")
            print(f"   Saved to database: {saved_to_db}")
            
            # Check database after
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM jobs")
            jobs_after = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM jobs WHERE source IN ('remoteok', 'arbeitnow', 'justremote')")
            scraped_after = cursor.fetchone()[0]
            
            print(f"\n📊 Database after test:")
            print(f"   Total jobs: {jobs_after}")
            print(f"   Scraped jobs: {scraped_after}")
            print(f"   New jobs added: {jobs_after - jobs_before}")
            
            # Check for duplicate external_ids
            cursor.execute("""
                SELECT external_id, COUNT(*) as count 
                FROM jobs 
                WHERE source IN ('remoteok', 'arbeitnow', 'justremote')
                GROUP BY external_id 
                HAVING COUNT(*) > 1
            """)
            
            duplicates = cursor.fetchall()
            
            print(f"\n🔍 Duplicate Check:")
            print(f"   Duplicate external_ids found: {len(duplicates)}")
            
            if len(duplicates) > 0:
                print(f"   ⚠️ Duplicates detected:")
                for ext_id, count in duplicates:
                    print(f"      {ext_id}: {count} entries")
            else:
                print(f"   ✅ No duplicates found!")
            
            # Show sample of recent jobs
            cursor.execute("""
                SELECT title, company, source, external_id, scraped_at
                FROM jobs 
                WHERE source IN ('remoteok', 'arbeitnow', 'justremote')
                ORDER BY scraped_at DESC 
                LIMIT 5
            """)
            
            recent_jobs = cursor.fetchall()
            print(f"\n📋 Recent scraped jobs:")
            for title, company, source, ext_id, scraped_at in recent_jobs:
                print(f"   🏢 {title} at {company} ({source})")
                print(f"      ID: {ext_id[:20]}... | {scraped_at}")
            
            conn.close()
            
            # Success criteria
            success = (
                jobs_found > 0 and
                saved_to_db >= 0 and  # May be 0 if all were duplicates
                len(duplicates) == 0 and
                jobs_after >= jobs_before
            )
            
            if success:
                print(f"\n🎉 SUCCESS: Full workflow with duplicate prevention working!")
                print(f"📊 Summary:")
                print(f"   • Found {jobs_found} jobs from multiple sources")
                print(f"   • Added {saved_to_db} new jobs to database")
                print(f"   • Zero duplicates in database")
                print(f"   • Database integrity maintained")
                return True
            else:
                print(f"\n⚠️ Issues detected in workflow")
                return False
                
        else:
            print(f"❌ Job search failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        try:
            await supervisor.cleanup()
        except:
            pass

if __name__ == "__main__":
    success = asyncio.run(test_full_workflow_no_duplicates())
    if success:
        print(f"\n✅ Full duplicate prevention system working perfectly!")
    else:
        print(f"\n❌ Issues with duplicate prevention system")