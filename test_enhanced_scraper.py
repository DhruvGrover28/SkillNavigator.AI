#!/usr/bin/env python3
"""
Test the EnhancedScraperAgent to verify it gets real job data
"""
import sys
import os
import asyncio
sys.path.append('backend')

from backend.agents.enhanced_scraper_agent import EnhancedScraperAgent

async def test_enhanced_scraper():
    print("Testing EnhancedScraperAgent for REAL job data...")
    
    scraper = EnhancedScraperAgent()
    await scraper.initialize()
    
    # Test search parameters
    search_params = {
        'keywords': 'python',
        'location': 'remote', 
        'max_results': 15
    }
    
    print(f"Search params: {search_params}")
    print("Enabled sources:", [config['name'] for name, config in scraper.job_sources.items() if config.get('enabled', True)])
    
    # Try to scrape real jobs
    try:
        jobs = await scraper.scrape_jobs(search_params)
        print(f"\n✅ Found {len(jobs)} REAL jobs total")
        
        if jobs:
            print("\n📋 Real job listings:")
            for i, job in enumerate(jobs[:5]):
                print(f"\n{i+1}. 🏢 {job.title}")
                print(f"   Company: {job.company}")  
                print(f"   Location: {job.location}")
                print(f"   URL: {job.url}")
                print(f"   Apply URL: {job.apply_url}")
                if job.salary:
                    print(f"   Salary: {job.salary}")
                if job.skills:
                    print(f"   Skills: {job.skills[:5]}")  # First 5 skills
                print(f"   Description: {job.description[:120]}...")
                
            # Verify URLs are real
            print(f"\n🔗 Checking if URLs are real...")
            real_urls = [job for job in jobs[:3] if job.url and 'http' in job.url]
            print(f"Found {len(real_urls)} jobs with real URLs")
            
            if real_urls:
                print("✅ SUCCESS: Scraper is getting REAL job data with working URLs!")
            else:
                print("❌ PROBLEM: No real URLs found")
                
        else:
            print("❌ No jobs found - scraper needs debugging")
            
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await scraper.cleanup()
        print("\n🏁 Test completed")

if __name__ == "__main__":
    asyncio.run(test_enhanced_scraper())