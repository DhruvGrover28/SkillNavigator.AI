#!/usr/bin/env python3
"""
Test the updated supervisor agent with enhanced scraper
"""

import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.simple_supervisor_agent import SimpleSupervisorAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_supervisor_with_enhanced_scraper():
    """Test supervisor agent with enhanced scraper integration"""
    
    print("🔧 Testing supervisor agent with enhanced scraper...")
    
    # Create supervisor agent
    supervisor = SimpleSupervisorAgent()
    
    try:
        # Initialize
        await supervisor.initialize()
        print("✅ Supervisor agent initialized")
        
        # Test job search
        search_params = {
            'keywords': 'python',
            'location': 'remote', 
            'max_results': 10
        }
        
        print(f"\n🔍 Testing job search with params: {search_params}")
        result = await supervisor.trigger_job_search(search_params)
        
        if result['success']:
            print(f"✅ SUCCESS: Found {result['total_found']} jobs")
            print(f"💾 Saved {result['saved_to_db']} jobs to database")
            print(f"⏱️ Search took {result['search_duration_seconds']:.2f} seconds")
            
            # Show some job details
            jobs = result.get('jobs', [])
            for i, job in enumerate(jobs[:3]):  # Show first 3 jobs
                print(f"\n📋 Job {i+1}: {job['title']}")
                print(f"   🏢 Company: {job['company']}")
                print(f"   📍 Location: {job['location']}")
                print(f"   🔗 URL: {job['url']}")
                if job.get('skills'):
                    print(f"   🛠️ Skills: {', '.join(job['skills'][:5])}")
        else:
            print(f"❌ Search failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        try:
            await supervisor.cleanup()
            print("🧹 Cleanup completed")
        except:
            pass
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_supervisor_with_enhanced_scraper())
    if success:
        print("\n🎉 All tests passed! Enhanced scraper is integrated successfully.")
    else:
        print("\n💥 Tests failed!")
        sys.exit(1)