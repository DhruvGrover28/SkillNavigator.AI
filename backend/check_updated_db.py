#!/usr/bin/env python3
"""
Check if real scraped job data has been saved to the database
"""

import asyncio
import sqlite3
import os
from datetime import datetime

async def check_database_jobs():
    """Check the jobs in the database"""
    
    # Database path
    db_path = os.path.join(os.path.dirname(__file__), 'skillnavigator.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return
    
    print(f"📊 Checking database at: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get total job count
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = cursor.fetchone()[0]
        print(f"📈 Total jobs in database: {total_jobs}")
        
        # Check for remoteok jobs (real scraped data)
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE source = 'remoteok'")
        remoteok_jobs = cursor.fetchone()[0]
        print(f"🚀 RemoteOK jobs (real scraped): {remoteok_jobs}")
        
        # Check for template jobs 
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE description LIKE 'We are seeking a talented%'")
        template_jobs = cursor.fetchone()[0]
        print(f"📝 Template jobs (generated): {template_jobs}")
        
        # Show recent remoteok jobs
        if remoteok_jobs > 0:
            print(f"\n📋 Recent RemoteOK jobs:")
            cursor.execute("""
                SELECT title, company, location, apply_url, scraped_at 
                FROM jobs 
                WHERE source = 'remoteok' 
                ORDER BY scraped_at DESC 
                LIMIT 5
            """)
            
            jobs = cursor.fetchall()
            for i, (title, company, location, url, scraped_at) in enumerate(jobs, 1):
                print(f"  {i}. 🏢 {title} at {company}")
                print(f"     📍 {location}")
                print(f"     🔗 {url}")
                print(f"     ⏰ Scraped: {scraped_at}")
                print()
        
        # Show database schema to understand structure
        print("🗂️ Database structure:")
        cursor.execute("PRAGMA table_info(jobs)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(check_database_jobs())