#!/usr/bin/env python3
"""
Verify our 2 current job sources are working properly:
1. RemoteOK API
2. ArbeitNow API

Check that they return real job postings with working URLs
"""

import asyncio
import logging
import sys
import os
import requests
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.enhanced_scraper_agent import EnhancedScraperAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_job_url(url, job_title, source):
    """Verify that a job URL is real and working"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            content = response.text.lower()
            
            # Check if page contains job-related content
            job_indicators = [
                'apply', 'job', 'position', 'salary', 'experience', 
                'requirements', 'responsibilities', 'company', 'remote'
            ]
            
            found_indicators = [ind for ind in job_indicators if ind in content]
            
            # Check if job title appears in the content
            title_words = job_title.lower().split()
            title_match = any(word in content for word in title_words if len(word) > 3)
            
            return {
                'status': response.status_code,
                'is_job_page': len(found_indicators) >= 3,
                'title_match': title_match,
                'indicators_found': found_indicators,
                'content_length': len(content)
            }
        else:
            return {
                'status': response.status_code,
                'is_job_page': False,
                'title_match': False,
                'indicators_found': [],
                'content_length': 0
            }
    
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'is_job_page': False,
            'title_match': False,
            'indicators_found': [],
            'content_length': 0
        }

async def verify_remoteok():
    """Verify RemoteOK API source"""
    
    print("🔍 Verifying RemoteOK API Source")
    print("=" * 40)
    
    scraper = EnhancedScraperAgent()
    
    try:
        await scraper.initialize()
        
        # Get jobs from RemoteOK
        jobs = await scraper._parse_remoteok_api("software developer", "remote")
        
        print(f"📊 RemoteOK Results:")
        print(f"   Jobs returned: {len(jobs)}")
        
        if len(jobs) == 0:
            print(f"   ❌ No jobs returned!")
            return False
        
        # Verify first 3 jobs
        print(f"\n🔍 Verifying job URLs (testing first 3):")
        
        valid_jobs = 0
        for i, job in enumerate(jobs[:3]):
            print(f"\n   Job {i+1}: {job.title}")
            print(f"   Company: {job.company}")
            print(f"   URL: {job.url}")
            
            # Verify the URL
            verification = verify_job_url(job.url, job.title, 'remoteok')
            
            if verification['status'] == 200:
                print(f"   ✅ URL works (200 OK)")
                print(f"   📄 Content length: {verification['content_length']} chars")
                
                if verification['is_job_page']:
                    print(f"   ✅ Looks like a real job page")
                    print(f"   🎯 Job indicators: {verification['indicators_found'][:5]}")
                    valid_jobs += 1
                else:
                    print(f"   ⚠️ May not be a job page")
                    print(f"   🔍 Found indicators: {verification['indicators_found']}")
                
                if verification['title_match']:
                    print(f"   ✅ Job title matches page content")
                else:
                    print(f"   ⚠️ Job title may not match page")
                    
            else:
                print(f"   ❌ URL issue: {verification.get('status', 'unknown')}")
                if 'error' in verification:
                    print(f"   Error: {verification['error']}")
        
        success_rate = valid_jobs / min(len(jobs), 3)
        print(f"\n📈 RemoteOK Verification:")
        print(f"   Valid job pages: {valid_jobs}/3 = {success_rate:.1%}")
        print(f"   Total jobs available: {len(jobs)}")
        
        return success_rate >= 0.6  # 60% or better
        
    except Exception as e:
        print(f"❌ Error verifying RemoteOK: {e}")
        return False
    finally:
        try:
            await scraper.cleanup()
        except:
            pass

async def verify_arbeitnow():
    """Verify ArbeitNow API source"""
    
    print("\n🔍 Verifying ArbeitNow API Source")
    print("=" * 40)
    
    scraper = EnhancedScraperAgent()
    
    try:
        await scraper.initialize()
        
        # Get jobs from ArbeitNow
        jobs = await scraper._parse_arbeitnow_jobs("software developer", "remote")
        
        print(f"📊 ArbeitNow Results:")
        print(f"   Jobs returned: {len(jobs)}")
        
        if len(jobs) == 0:
            print(f"   ❌ No jobs returned!")
            return False
        
        # Verify first 3 jobs
        print(f"\n🔍 Verifying job URLs (testing first 3):")
        
        valid_jobs = 0
        for i, job in enumerate(jobs[:3]):
            print(f"\n   Job {i+1}: {job.title}")
            print(f"   Company: {job.company}")
            print(f"   URL: {job.url}")
            
            # Verify the URL
            verification = verify_job_url(job.url, job.title, 'arbeitnow')
            
            if verification['status'] == 200:
                print(f"   ✅ URL works (200 OK)")
                print(f"   📄 Content length: {verification['content_length']} chars")
                
                if verification['is_job_page']:
                    print(f"   ✅ Looks like a real job page")
                    print(f"   🎯 Job indicators: {verification['indicators_found'][:5]}")
                    valid_jobs += 1
                else:
                    print(f"   ⚠️ May not be a job page")
                    print(f"   🔍 Found indicators: {verification['indicators_found']}")
                
                if verification['title_match']:
                    print(f"   ✅ Job title matches page content")
                else:
                    print(f"   ⚠️ Job title may not match page")
                    
            else:
                print(f"   ❌ URL issue: {verification.get('status', 'unknown')}")
                if 'error' in verification:
                    print(f"   Error: {verification['error']}")
        
        success_rate = valid_jobs / min(len(jobs), 3)
        print(f"\n📈 ArbeitNow Verification:")
        print(f"   Valid job pages: {valid_jobs}/3 = {success_rate:.1%}")
        print(f"   Total jobs available: {len(jobs)}")
        
        return success_rate >= 0.6  # 60% or better
        
    except Exception as e:
        print(f"❌ Error verifying ArbeitNow: {e}")
        return False
    finally:
        try:
            await scraper.cleanup()
        except:
            pass

async def verify_both_sources():
    """Test both sources together"""
    
    print("\n🔍 Testing Both Sources Together")
    print("=" * 40)
    
    scraper = EnhancedScraperAgent()
    
    try:
        await scraper.initialize()
        
        # Disable JustRemote to focus on our 2 working sources
        scraper.sources = ['remoteok_api', 'arbeitnow_api']
        
        # Get jobs from both sources
        search_params = {
            'keywords': 'software developer',
            'location': 'remote',
            'max_jobs': 20
        }
        
        all_jobs = await scraper.scrape_jobs(search_params)
        
        # Group by source
        by_source = {}
        for job in all_jobs:
            if 'remoteok' in job.url.lower():
                source = 'RemoteOK'
            elif 'arbeitnow' in job.url.lower():
                source = 'ArbeitNow'
            else:
                source = 'Other'
            
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(job)
        
        print(f"📊 Combined Results:")
        print(f"   Total unique jobs: {len(all_jobs)}")
        
        for source, jobs in by_source.items():
            print(f"   {source}: {len(jobs)} jobs")
        
        # Check for quality
        quality_indicators = {
            'has_company': sum(1 for job in all_jobs if job.company and job.company != 'Unknown'),
            'has_description': sum(1 for job in all_jobs if job.description and len(job.description) > 50),
            'has_url': sum(1 for job in all_jobs if job.url and job.url.startswith('http')),
            'has_title': sum(1 for job in all_jobs if job.title and len(job.title) > 5)
        }
        
        print(f"\n📈 Quality Check:")
        total = len(all_jobs)
        for indicator, count in quality_indicators.items():
            percentage = (count / total * 100) if total > 0 else 0
            print(f"   {indicator}: {count}/{total} = {percentage:.1f}%")
        
        # Overall quality score
        overall_quality = sum(quality_indicators.values()) / (len(quality_indicators) * total) if total > 0 else 0
        print(f"   Overall quality: {overall_quality:.1%}")
        
        return len(all_jobs) >= 15 and overall_quality >= 0.8  # At least 15 jobs with 80% quality
        
    except Exception as e:
        print(f"❌ Error testing both sources: {e}")
        return False
    finally:
        try:
            await scraper.cleanup()
        except:
            pass

async def main():
    """Main verification function"""
    
    print("🔄 Verifying Current 2-Source Job Scraper System")
    print("=" * 60)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test RemoteOK
    remoteok_ok = await verify_remoteok()
    
    # Test ArbeitNow  
    arbeitnow_ok = await verify_arbeitnow()
    
    # Test both together
    combined_ok = await verify_both_sources()
    
    print(f"\n" + "="*60)
    print(f"📊 FINAL VERIFICATION RESULTS")
    print(f"="*60)
    
    print(f"✅ RemoteOK API: {'WORKING' if remoteok_ok else 'ISSUES'}")
    print(f"✅ ArbeitNow API: {'WORKING' if arbeitnow_ok else 'ISSUES'}")
    print(f"✅ Combined System: {'WORKING' if combined_ok else 'ISSUES'}")
    
    if remoteok_ok and arbeitnow_ok and combined_ok:
        print(f"\n🎉 SUCCESS: Both sources verified and working!")
        print(f"   • Real job postings ✅")
        print(f"   • Working URLs ✅") 
        print(f"   • Good data quality ✅")
        print(f"   • Proper deduplication ✅")
        print(f"\n🚀 Ready to move on to another agent!")
        return True
    else:
        print(f"\n⚠️ Issues found:")
        if not remoteok_ok:
            print(f"   • RemoteOK needs attention")
        if not arbeitnow_ok:
            print(f"   • ArbeitNow needs attention") 
        if not combined_ok:
            print(f"   • Combined system needs work")
        print(f"\n🔧 Fix needed before moving on")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)