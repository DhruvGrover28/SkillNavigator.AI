#!/usr/bin/env python3
"""
Replace template jobs with real scraped jobs in the database
"""

import asyncio
import sqlite3
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.enhanced_scraper_agent import EnhancedScraperAgent
from database.db_connection import Database

async def replace_template_jobs_with_real():
    """Replace template jobs with real scraped jobs"""
    
    print("🔄 Replacing Template Jobs with Real Scraped Jobs...")
    
    # Database path
    db_path = os.path.join(os.path.dirname(__file__), 'skillnavigator.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    print(f"📊 Working with database: {db_path}")
    
    # Step 1: Check current state
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Count current jobs
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_jobs_before = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE description LIKE 'We are seeking a talented%'")
        template_jobs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE source = 'remoteok'")
        existing_real_jobs = cursor.fetchone()[0]
        
        print(f"📈 Current database state:")
        print(f"   Total jobs: {total_jobs_before}")
        print(f"   Template jobs: {template_jobs}")
        print(f"   Real RemoteOK jobs: {existing_real_jobs}")
        
        # Step 2: Delete template jobs
        print(f"\n🗑️ Deleting {template_jobs} template jobs...")
        cursor.execute("DELETE FROM jobs WHERE description LIKE 'We are seeking a talented%'")
        deleted_count = cursor.rowcount
        conn.commit()
        print(f"✅ Deleted {deleted_count} template jobs")
        
        # Step 3: Fetch fresh real jobs
        print(f"\n🚀 Fetching 25-30 fresh real jobs...")
        scraper = EnhancedScraperAgent()
        await scraper.initialize()
        
        # Get jobs with different search terms for variety
        all_jobs = []
        search_queries = [
            {'keywords': 'software engineer', 'max_results': 8},
            {'keywords': 'developer', 'max_results': 8}, 
            {'keywords': 'technical', 'max_results': 6},
            {'keywords': 'manager', 'max_results': 4},
            {'keywords': 'analyst', 'max_results': 4}
        ]
        
        for query in search_queries:
            jobs = await scraper.scrape_jobs(query)
            all_jobs.extend(jobs)
            await asyncio.sleep(1)  # Be nice to the API
        
        # Remove duplicates by URL
        seen_urls = set()
        unique_jobs = []
        for job in all_jobs:
            if job.url not in seen_urls:
                seen_urls.add(job.url)
                unique_jobs.append(job)
        
        await scraper.cleanup()
        print(f"📊 Fetched {len(unique_jobs)} unique real jobs")
        
        # Step 4: Insert real jobs into database
        print(f"\n📥 Inserting real jobs into database...")
        
        insert_count = 0
        for job in unique_jobs:
            try:
                # Convert date string to datetime object if needed
                posted_date = job.date_posted
                if isinstance(posted_date, str) and posted_date:
                    try:
                        from datetime import datetime
                        posted_date = datetime.fromisoformat(posted_date.replace('Z', '+00:00'))
                    except:
                        posted_date = datetime.now()
                elif not posted_date:
                    from datetime import datetime
                    posted_date = datetime.now()
                
                cursor.execute("""
                    INSERT INTO jobs (
                        external_id, title, company, location, description,
                        salary_min, salary_max, job_type, experience_level,
                        remote_allowed, apply_url, posted_date, scraped_at,
                        source, skills_match
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?)
                """, (
                    f"remoteok_{hash(job.title + job.company)}",  # external_id
                    job.title,
                    job.company, 
                    job.location,
                    job.description,
                    None,  # salary_min (parse from job.salary if needed)
                    None,  # salary_max
                    job.job_type or 'Remote',
                    job.experience,
                    True,  # remote_allowed
                    job.apply_url or job.url,
                    posted_date,
                    'remoteok',  # source
                    str(job.skills) if job.skills else None  # skills_match
                ))
                insert_count += 1
                
            except Exception as e:
                print(f"⚠️ Failed to insert job '{job.title}': {e}")
                continue
        
        conn.commit()
        print(f"✅ Inserted {insert_count} real jobs")
        
        # Step 5: Verify final state
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_jobs_after = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE source = 'remoteok'")
        real_jobs_after = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE description LIKE 'We are seeking a talented%'")
        remaining_template = cursor.fetchone()[0]
        
        print(f"\n📊 Final database state:")
        print(f"   Total jobs: {total_jobs_after}")
        print(f"   Real RemoteOK jobs: {real_jobs_after}")
        print(f"   Remaining template jobs: {remaining_template}")
        
        # Show some sample real jobs
        cursor.execute("""
            SELECT title, company, location, apply_url 
            FROM jobs 
            WHERE source = 'remoteok' 
            ORDER BY scraped_at DESC 
            LIMIT 5
        """)
        
        sample_jobs = cursor.fetchall()
        print(f"\n📋 Sample real jobs in database:")
        for i, (title, company, location, url) in enumerate(sample_jobs, 1):
            print(f"  {i}. 🏢 {title} at {company}")
            print(f"     📍 {location}")
            print(f"     🔗 {url}")
        
        if real_jobs_after >= 20 and remaining_template == 0:
            print(f"\n🎉 SUCCESS: Replaced template jobs with {real_jobs_after} real jobs!")
            return True
        else:
            print(f"\n⚠️ Partial success: {real_jobs_after} real jobs, {remaining_template} templates remain")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = asyncio.run(replace_template_jobs_with_real())
    if success:
        print("\n✅ Database successfully updated with real job data!")
    else:
        print("\n❌ Database update failed or incomplete!")
        sys.exit(1)