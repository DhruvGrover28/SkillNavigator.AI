#!/usr/bin/env python3
"""
Test the SimpleScraperAgent to see if it can scrape real jobs
"""
import sys
import os
import asyncio
sys.path.append('backend')

from backend.agents.simple_scraper_agent import SimpleScraperAgent

async def test_scraper():
    print("Testing SimpleScraperAgent...")
    
    scraper = SimpleScraperAgent()
    await scraper.initialize()
    
    # Test search parameters
    search_params = {
        'keywords': 'python developer',
        'location': 'remote',
        'max_results': 10
    }
    
    print(f"Search params: {search_params}")
    print("Enabled sites:", [name for name, config in scraper.job_sites.items() if config.get('enabled', True)])
    
    # Try to scrape jobs
    try:
        jobs = await scraper.scrape_jobs(search_params)
        print(f"\nFound {len(jobs)} jobs total")
        
        if jobs:
            print("\nSample jobs:")
            for i, job in enumerate(jobs[:3]):
                print(f"\n{i+1}. {job.title}")
                print(f"   Company: {job.company}")
                print(f"   Location: {job.location}")
                print(f"   URL: {job.url}")
                print(f"   Description: {job.description[:100]}...")
        else:
            print("No jobs found - scraper may not be working properly")
            
    except Exception as e:
        print(f"Error during scraping: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await scraper.cleanup()
        print("Test completed")

if __name__ == "__main__":
    asyncio.run(test_scraper())
