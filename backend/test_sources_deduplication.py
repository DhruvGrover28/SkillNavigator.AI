#!/usr/bin/env python3
"""
Quick test to verify sources are working and fix URL detection
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

async def test_sources_and_deduplication():
    """Quick test of multi-source functionality with duplicate prevention"""
    
    print("🔍 Quick Multi-Source Test with Duplicate Prevention")
    print("=" * 55)
    
    scraper = EnhancedScraperAgent()
    
    try:
        await scraper.initialize()
        
        # Test with a simple search
        search_params = {'keywords': 'software', 'max_results': 20}
        print(f"🔍 Testing search: {search_params}")
        
        jobs = await scraper.scrape_jobs(search_params)
        print(f"📊 Total unique jobs after deduplication: {len(jobs)}")
        
        # Check source distribution
        source_counts = {}
        url_analysis = {'remoteok': 0, 'arbeitnow': 0, 'justremote': 0, 'other': 0}
        
        print(f"\n📋 Sample jobs with source detection:")
        for i, job in enumerate(jobs[:8], 1):
            # Detect source from URL
            if 'remoteok.com' in job.url or 'remoteOK.com' in job.url:
                source = 'RemoteOK'
                url_analysis['remoteok'] += 1
            elif 'arbeitnow.com' in job.url:
                source = 'ArbeitNow'
                url_analysis['arbeitnow'] += 1
            elif 'justremote.co' in job.url:
                source = 'JustRemote'
                url_analysis['justremote'] += 1
            else:
                source = 'Other'
                url_analysis['other'] += 1
            
            source_counts[source] = source_counts.get(source, 0) + 1
            
            print(f"  {i}. 🏢 {job.title}")
            print(f"     Company: {job.company}")
            print(f"     Source: {source}")
            print(f"     URL: {job.url}")
        
        print(f"\n📊 Source Distribution:")
        for source, count in source_counts.items():
            percentage = (count / len(jobs)) * 100 if jobs else 0
            print(f"   • {source}: {count} jobs ({percentage:.1f}%)")
        
        print(f"\n🔗 URL Analysis:")
        print(f"   • RemoteOK URLs: {url_analysis['remoteok']}")
        print(f"   • ArbeitNow URLs: {url_analysis['arbeitnow']}")
        print(f"   • JustRemote URLs: {url_analysis['justremote']}")
        print(f"   • Other URLs: {url_analysis['other']}")
        
        # Check for duplicates by manually comparing
        titles_companies = set()
        urls = set()
        duplicates_found = 0
        
        for job in jobs:
            title_company = (job.title.lower(), job.company.lower())
            url = job.url.lower() if job.url else ""
            
            if title_company in titles_companies or (url and url in urls):
                duplicates_found += 1
            else:
                titles_companies.add(title_company)
                if url:
                    urls.add(url)
        
        print(f"\n✅ Deduplication Check:")
        print(f"   • Duplicates found: {duplicates_found}")
        print(f"   • Unique jobs: {len(jobs)}")
        
        success = (len(jobs) >= 15 and 
                  len(source_counts) >= 2 and 
                  duplicates_found == 0)
        
        if success:
            print(f"\n🎉 SUCCESS: Multi-source scraper with deduplication working!")
        else:
            print(f"\n⚠️ Issues detected - need investigation")
        
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    success = asyncio.run(test_sources_and_deduplication())
    if success:
        print(f"\n✅ Multi-source scraper ready for production!")
    else:
        print(f"\n🔧 Needs adjustments before production use")