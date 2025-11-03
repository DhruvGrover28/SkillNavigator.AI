#!/usr/bin/env python3
"""
Test the updated JustRemote parser
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

async def test_justremote_parser():
    """Test the updated JustRemote parser"""
    
    print("🔄 Testing Updated JustRemote Parser")
    print("=" * 40)
    
    scraper = EnhancedScraperAgent()
    
    try:
        await scraper.initialize()
        print("✅ Scraper initialized")
        
        # Test JustRemote parser directly
        print("\n📡 Testing JustRemote parser...")
        jobs = await scraper._parse_justremote_jobs("software developer", "remote")
        
        print(f"📊 JustRemote Results:")
        print(f"   Jobs found: {len(jobs)}")
        
        if jobs:
            print(f"\n📋 Sample jobs:")
            for i, job in enumerate(jobs[:5]):  # Show first 5
                print(f"   [{i+1}] {job.title}")
                print(f"       Company: {job.company}")
                print(f"       Location: {job.location}")
                print(f"       URL: {job.url}")
                print()
        else:
            print("   ❌ No jobs found")
        
        return len(jobs)
        
    except Exception as e:
        print(f"❌ Error testing JustRemote: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        try:
            await scraper.cleanup()
        except:
            pass

async def test_all_sources():
    """Test all sources to make sure they're still working"""
    
    print("\n" + "="*50)
    print("🔄 Testing All Job Sources")
    print("="*50)
    
    scraper = EnhancedScraperAgent()
    
    try:
        await scraper.initialize()
        
        # Test all sources
        search_params = {
            'keywords': 'software developer',
            'location': 'remote',
            'max_jobs': 10
        }
        
        all_jobs = await scraper.scrape_jobs(search_params)
        
        # Group by source
        by_source = {}
        for job in all_jobs:
            source = job.url.split('//')[1].split('/')[0] if job.url else 'unknown'
            if 'remoteok' in source:
                source = 'RemoteOK'
            elif 'arbeitnow' in source:
                source = 'ArbeitNow'
            elif 'justremote' in source:
                source = 'JustRemote'
            else:
                source = 'Other'
            
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(job)
        
        print(f"\n📊 Multi-Source Results:")
        print(f"   Total jobs: {len(all_jobs)}")
        
        for source, jobs in by_source.items():
            print(f"   {source}: {len(jobs)} jobs")
            
        # Check if JustRemote is working now
        justremote_jobs = by_source.get('JustRemote', [])
        if justremote_jobs:
            print(f"\n🎉 JustRemote is now working! Found {len(justremote_jobs)} jobs")
            print(f"   Sample: {justremote_jobs[0].title} at {justremote_jobs[0].company}")
        else:
            print(f"\n⚠️ JustRemote still not returning jobs")
        
        return len(all_jobs), len(justremote_jobs)
        
    except Exception as e:
        print(f"❌ Error testing all sources: {e}")
        return 0, 0
    finally:
        try:
            await scraper.cleanup()
        except:
            pass

if __name__ == "__main__":
    # Test JustRemote specifically
    justremote_count = asyncio.run(test_justremote_parser())
    
    # Test all sources
    total_jobs, justremote_jobs = asyncio.run(test_all_sources())
    
    print(f"\n📊 Final Results:")
    print(f"   JustRemote direct test: {justremote_count} jobs")
    print(f"   JustRemote in full test: {justremote_jobs} jobs") 
    print(f"   Total jobs from all sources: {total_jobs}")
    
    if justremote_count > 0 or justremote_jobs > 0:
        print(f"\n✅ SUCCESS: JustRemote parser is now working!")
    else:
        print(f"\n⚠️ JustRemote still needs work, but other sources working")