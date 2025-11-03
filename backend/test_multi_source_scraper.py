#!/usr/bin/env python3
"""
Test the enhanced scraper with multiple job sources
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

async def test_multi_source_scraper():
    """Test enhanced scraper with multiple job sources"""
    
    print("🚀 Testing Enhanced Scraper with Multiple Job Sources")
    print("=" * 60)
    
    # Create enhanced scraper
    scraper = EnhancedScraperAgent()
    
    try:
        # Initialize scraper
        await scraper.initialize()
        print("✅ Enhanced scraper initialized with multiple sources")
        
        # Check which sources are enabled
        enabled_sources = {name: config for name, config in scraper.job_sources.items() 
                          if config.get('enabled', True)}
        
        print(f"\n📊 Enabled Job Sources: {len(enabled_sources)}")
        for name, config in enabled_sources.items():
            print(f"   • {config['name']} ({name})")
        
        # Test with different search terms
        search_queries = [
            {'keywords': 'software engineer', 'max_results': 15},
            {'keywords': 'python developer', 'max_results': 10},
        ]
        
        all_jobs = []
        
        for i, query in enumerate(search_queries, 1):
            print(f"\n🔍 Search {i}: '{query['keywords']}' (max: {query['max_results']})")
            print("-" * 50)
            
            jobs = await scraper.scrape_jobs(query)
            search_jobs = len(jobs)
            all_jobs.extend(jobs)
            
            print(f"📈 Total jobs found: {search_jobs}")
            
            # Group jobs by source to see distribution
            source_counts = {}
            for job in jobs:
                # Try to determine source from URL
                if 'remoteok.com' in job.url:
                    source = 'RemoteOK'
                elif 'arbeitnow.com' in job.url:
                    source = 'ArbeitNow'
                elif 'justremote.co' in job.url:
                    source = 'JustRemote'
                else:
                    source = 'Unknown'
                
                source_counts[source] = source_counts.get(source, 0) + 1
            
            print("📊 Jobs by source:")
            for source, count in source_counts.items():
                print(f"   • {source}: {count} jobs")
            
            # Show sample jobs
            print(f"\n📋 Sample jobs from search '{query['keywords']}':")
            for j, job in enumerate(jobs[:3], 1):
                print(f"  {j}. 🏢 {job.title}")
                print(f"     Company: {job.company}")
                print(f"     Location: {job.location}")
                print(f"     URL: {job.url}")
                if job.skills:
                    print(f"     Skills: {', '.join(job.skills[:3])}")
            
            # Small delay between searches
            await asyncio.sleep(2)
        
        # Remove duplicates
        seen_urls = set()
        unique_jobs = []
        for job in all_jobs:
            if job.url not in seen_urls:
                seen_urls.add(job.url)
                unique_jobs.append(job)
        
        print(f"\n📊 FINAL RESULTS")
        print("=" * 40)
        print(f"📈 Total jobs collected: {len(all_jobs)}")
        print(f"🔗 Unique jobs (deduplicated): {len(unique_jobs)}")
        
        # Final source breakdown
        final_source_counts = {}
        for job in unique_jobs:
            if 'remoteok.com' in job.url:
                source = 'RemoteOK'
            elif 'arbeitnow.com' in job.url:
                source = 'ArbeitNow'  
            elif 'justremote.co' in job.url:
                source = 'JustRemote'
            else:
                source = 'Unknown'
            
            final_source_counts[source] = final_source_counts.get(source, 0) + 1
        
        print(f"\n🌐 Final distribution across all sources:")
        for source, count in final_source_counts.items():
            percentage = (count / len(unique_jobs)) * 100 if unique_jobs else 0
            print(f"   • {source}: {count} jobs ({percentage:.1f}%)")
        
        # Check URL quality
        working_urls = 0
        for job in unique_jobs:
            url = job.url
            if (('remoteok.com/remote-jobs' in url) or 
                ('arbeitnow.com/jobs' in url) or 
                ('justremote.co' in url)) and len(url) > 30:
                working_urls += 1
        
        print(f"\n🔗 URL Quality:")
        print(f"   Working job URLs: {working_urls}/{len(unique_jobs)} ({(working_urls/len(unique_jobs)*100):.1f}%)")
        
        success_criteria = [
            (len(unique_jobs) >= 15, f"Got {len(unique_jobs)} unique jobs (target: ≥15)"),
            (len(final_source_counts) >= 2, f"Using {len(final_source_counts)} sources (target: ≥2)"),
            (working_urls >= 10, f"Got {working_urls} working URLs (target: ≥10)")
        ]
        
        print(f"\n✅ Success Criteria:")
        passed = 0
        for is_passing, description in success_criteria:
            status = "✅" if is_passing else "❌"
            print(f"{status} {description}")
            if is_passing:
                passed += 1
        
        if passed == len(success_criteria):
            print(f"\n🎉 SUCCESS: Multi-source scraper working perfectly!")
            print(f"🚀 Your platform now scrapes from {len(final_source_counts)} different job sources!")
            return True
        else:
            print(f"\n⚠️ Partial success: {passed}/{len(success_criteria)} criteria met")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        try:
            await scraper.cleanup()
            print("\n🧹 Cleanup completed")
        except:
            pass

if __name__ == "__main__":
    success = asyncio.run(test_multi_source_scraper())
    if success:
        print(f"\n🎉 Multi-source scraper integration complete!")
    else:
        print(f"\n⚠️ Some issues with multi-source integration")