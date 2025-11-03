#!/usr/bin/env python3
"""
Debug keyword filtering to understand why we're getting so few results
"""

import asyncio
import requests
import json

async def debug_keyword_filtering():
    """Debug the RemoteOK API response and keyword filtering"""
    
    print("🔍 Debugging RemoteOK API and Keyword Filtering...")
    
    # Get raw API response
    try:
        response = requests.get('https://remoteok.io/api', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"📊 API returned {len(data)} total items")
            
            # Skip the first item (it's metadata)
            jobs_data = data[1:] if len(data) > 1 else []
            print(f"📋 Processing {len(jobs_data)} job entries")
            
            # Test different keywords
            keywords_to_test = ['python', 'javascript', 'software', 'developer', 'engineer']
            
            for keyword in keywords_to_test:
                matches = 0
                examples = []
                
                for i, job_data in enumerate(jobs_data[:20]):  # Check first 20 jobs
                    if not isinstance(job_data, dict):
                        continue
                    
                    title = job_data.get('position', '').lower()
                    description = job_data.get('description', '').lower()
                    tags = job_data.get('tags', [])
                    
                    # Current filtering logic
                    title_match = keyword.lower() in title
                    desc_match = keyword.lower() in description
                    tag_match = any(keyword.lower() in str(tag).lower() for tag in tags)
                    
                    if title_match or desc_match or tag_match:
                        matches += 1
                        if len(examples) < 3:
                            examples.append({
                                'title': job_data.get('position', 'N/A'),
                                'company': job_data.get('company', 'N/A'),
                                'tags': tags[:5],
                                'match_reason': 'title' if title_match else ('desc' if desc_match else 'tags')
                            })
                
                print(f"\n🔍 Keyword '{keyword}':")
                print(f"   Matches: {matches}/20 jobs")
                for ex in examples:
                    print(f"   ✅ {ex['title']} at {ex['company']} (matched in {ex['match_reason']})")
                    print(f"      Tags: {ex['tags']}")
            
            # Show all available job titles for debugging
            print(f"\n📝 Sample job titles from API:")
            for i, job_data in enumerate(jobs_data[:15]):
                if isinstance(job_data, dict):
                    title = job_data.get('position', 'N/A')
                    company = job_data.get('company', 'N/A') 
                    tags = job_data.get('tags', [])[:3]
                    print(f"   {i+1:2d}. {title} at {company} | Tags: {tags}")
                    
        else:
            print(f"❌ API request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_keyword_filtering())