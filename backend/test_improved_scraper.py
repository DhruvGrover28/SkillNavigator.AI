#!/usr/bin/env python3
"""
Test the improved scraper to fetch 20-30 real job postings
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

async def test_improved_scraper():
    """Test improved scraper with better keyword matching"""
    
    print("🚀 Testing Improved Scraper for 20-30 Real Jobs...")
    
    # Create enhanced scraper
    scraper = EnhancedScraperAgent()
    
    try:
        # Initialize scraper
        await scraper.initialize()
        print("✅ Enhanced scraper initialized")
        
        all_jobs = []
        
        # Test with broader search terms for variety
        search_queries = [
            {'keywords': 'software', 'max_results': 12},    # Should match many jobs
            {'keywords': 'developer', 'max_results': 10},   # Should match many jobs
            {'keywords': 'engineer', 'max_results': 8},     # Should match many jobs
            {'keywords': 'technical', 'max_results': 5},    # Should match some jobs
        ]
        
        for i, query in enumerate(search_queries, 1):
            print(f"\n🔍 Search {i}: '{query['keywords']}' (targeting {query['max_results']} jobs)")
            
            jobs = await scraper.scrape_jobs(query)
            print(f"📊 Found {len(jobs)} jobs for '{query['keywords']}'")
            
            # Show first 3 jobs from this search
            for j, job in enumerate(jobs[:3]):
                print(f"  {j+1}. 🏢 {job.title} at {job.company}")
                print(f"     📍 {job.location}")
                print(f"     🔗 {job.url}")
            
            all_jobs.extend(jobs)
            
            # Small delay between searches
            await asyncio.sleep(1)
        
        # Remove any duplicates by URL
        seen_urls = set()
        unique_jobs = []
        for job in all_jobs:
            if job.url not in seen_urls:
                seen_urls.add(job.url)
                unique_jobs.append(job)
        
        print(f"\n📈 TOTAL UNIQUE JOBS COLLECTED: {len(unique_jobs)}")
        print("=" * 70)
        
        # Show all unique jobs with full details
        print("📋 Complete Unique Job Listings:")
        for i, job in enumerate(unique_jobs, 1):
            print(f"\n{i:2d}. 🏢 {job.title}")
            print(f"     Company: {job.company}")
            print(f"     Location: {job.location}")
            print(f"     Full URL: {job.url}")
            if job.salary:
                print(f"     Salary: {job.salary}")
            if job.skills and len(job.skills) > 0:
                print(f"     Skills: {', '.join(job.skills[:4])}")
            
        # Verify URLs are full RemoteOK URLs
        real_urls = []
        for job in unique_jobs:
            url = job.url
            if 'remoteok.com/remote-jobs/remote-' in url and len(url) > 60:
                real_urls.append(url)
        
        print(f"\n🔗 URL Analysis:")
        print(f"✅ Full RemoteOK URLs: {len(real_urls)}")
        print(f"📊 Total unique jobs: {len(unique_jobs)}")
        
        if len(real_urls) >= 20:
            print(f"🎉 SUCCESS: Got {len(real_urls)} real job URLs (target: 20-30)")
        else:
            print(f"⚠️ Need more jobs. Got {len(real_urls)} real URLs (target: 20-30)")
        
        return unique_jobs
        
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
    jobs = asyncio.run(test_improved_scraper())
    if len(jobs) >= 20:
        print(f"\n🎉 Successfully fetched {len(jobs)} real job postings!")
    else:
        print(f"\n⚠️ Only got {len(jobs)} jobs - may need more improvements")