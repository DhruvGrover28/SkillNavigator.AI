#!/usr/bin/env python3
"""
Fetch 20-30 real job postings with full working URLs
"""

import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.enhanced_scraper_agent import EnhancedScraperAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def fetch_more_real_jobs():
    """Fetch 20-30 real job postings with various keywords"""
    
    print("🚀 Fetching 20-30 Real Job Postings with Full URLs...")
    
    # Create enhanced scraper
    scraper = EnhancedScraperAgent()
    
    try:
        # Initialize scraper
        await scraper.initialize()
        print("✅ Enhanced scraper initialized")
        
        all_jobs = []
        
        # Use different search terms to get variety
        search_queries = [
            {'keywords': 'python developer', 'max_results': 8},
            {'keywords': 'javascript react', 'max_results': 6}, 
            {'keywords': 'software engineer', 'max_results': 6},
            {'keywords': 'full stack developer', 'max_results': 5},
            {'keywords': 'backend developer', 'max_results': 5},
            {'keywords': 'frontend developer', 'max_results': 5}
        ]
        
        for i, query in enumerate(search_queries, 1):
            print(f"\n🔍 Search {i}: {query['keywords']} (targeting {query['max_results']} jobs)")
            
            jobs = await scraper.scrape_jobs(query)
            print(f"📊 Found {len(jobs)} jobs for '{query['keywords']}'")
            
            # Show first 2 jobs from this search
            for j, job in enumerate(jobs[:2]):
                print(f"  {j+1}. 🏢 {job.title} at {job.company}")
                print(f"     📍 {job.location}")
                print(f"     🔗 {job.url}")
                print()
            
            all_jobs.extend(jobs)
            
            # Avoid overwhelming the API
            await asyncio.sleep(2)
        
        print(f"\n📈 TOTAL JOBS COLLECTED: {len(all_jobs)}")
        print("=" * 60)
        
        # Show all jobs with full details
        print("📋 Complete Job Listings with Full URLs:")
        for i, job in enumerate(all_jobs, 1):
            print(f"\n{i:2d}. 🏢 {job.title}")
            print(f"     Company: {job.company}")
            print(f"     Location: {job.location}")
            print(f"     Full URL: {job.url}")
            print(f"     Apply URL: {job.apply_url or job.url}")
            if job.salary:
                print(f"     Salary: {job.salary}")
            if job.skills and len(job.skills) > 0:
                print(f"     Skills: {', '.join(job.skills[:5])}")
            
        # Verify URLs are real (not generic)
        real_urls = []
        generic_urls = []
        
        for job in all_jobs:
            url = job.url
            if 'remoteok.com/remote-jobs/remote-' in url and len(url) > 50:
                real_urls.append(url)
            else:
                generic_urls.append(url)
        
        print(f"\n🔗 URL Analysis:")
        print(f"✅ Real specific URLs: {len(real_urls)}")
        print(f"⚠️ Generic URLs: {len(generic_urls)}")
        
        if len(real_urls) > 0:
            print(f"\n📝 Sample real URLs:")
            for url in real_urls[:3]:
                print(f"  - {url}")
        
        return all_jobs
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []
    finally:
        try:
            await scraper.cleanup()
            print("\n🧹 Cleanup completed")
        except:
            pass

if __name__ == "__main__":
    jobs = asyncio.run(fetch_more_real_jobs())
    if jobs:
        print(f"\n🎉 Successfully fetched {len(jobs)} real job postings!")
    else:
        print("\n💥 Failed to fetch jobs!")
        sys.exit(1)