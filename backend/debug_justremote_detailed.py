#!/usr/bin/env python3
"""
More detailed JustRemote HTML analysis focusing on the job containers found
"""

import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detailed_justremote_analysis():
    """Detailed analysis of JustRemote job containers"""
    
    print("🔍 Detailed JustRemote Analysis")
    print("=" * 40)
    
    try:
        url = "https://justremote.co/remote-developer-jobs"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Focus on the working selector: div[class*="job"]
        job_containers = soup.select('div[class*="job"]')
        
        print(f"📊 Found {len(job_containers)} containers with 'job' in class")
        
        for i, container in enumerate(job_containers[:3]):  # Analyze first 3
            classes = ' '.join(container.get('class', []))
            print(f"\n🔬 Container {i+1} - Classes: {classes}")
            
            # Look for title
            title_found = False
            title_selectors = ['h1', 'h2', 'h3', 'h4', 'h5', 'a']
            for selector in title_selectors:
                titles = container.select(selector)
                for title in titles:
                    text = title.get_text(strip=True)
                    href = title.get('href', '')
                    if text and len(text) > 5:  # Reasonable title length
                        print(f"  📋 Possible title ({selector}): '{text}'")
                        if href:
                            print(f"      Link: {href}")
                        title_found = True
                        break
                if title_found:
                    break
            
            # Look for company
            company_found = False
            all_text_elements = container.find_all(text=True)
            for text in all_text_elements:
                text_clean = text.strip()
                if text_clean and len(text_clean) > 2 and len(text_clean) < 50:
                    # Skip common words
                    if not any(word in text_clean.lower() for word in ['remote', 'job', 'apply', 'save', 'share']):
                        print(f"  🏢 Possible company: '{text_clean}'")
                        company_found = True
                        if company_found:  # Just show first potential company
                            break
            
            # Look for links
            links = container.find_all('a', href=True)
            print(f"  🔗 Links: {len(links)}")
            for j, link in enumerate(links[:2]):
                href = link.get('href')
                link_text = link.get_text(strip=True)
                print(f"    [{j}] '{link_text}' -> {href}")
            
            # Show container structure
            print(f"  📄 Container structure (first 200 chars):")
            print(f"     {str(container)[:200]}...")
        
        # Try to find a better selector
        print(f"\n🎯 Finding optimal selector...")
        
        # Test different combinations
        test_selectors = [
            'div[class*="job"]',
            'div[class*="Job"]',
            'div[class*="listing"]',
            'div[class*="card"]',
            '[class*="job-card"]',
            '[class*="job-listing"]'
        ]
        
        for selector in test_selectors:
            containers = soup.select(selector)
            if containers:
                print(f"  ✅ '{selector}': {len(containers)} containers")
                # Test if first container has reasonable content
                first = containers[0]
                text_content = first.get_text(strip=True)
                if len(text_content) > 50:  # Has substantial content
                    print(f"     Content length: {len(text_content)} chars - Good!")
                else:
                    print(f"     Content length: {len(text_content)} chars - Minimal")
            else:
                print(f"  ❌ '{selector}': 0 containers")
        
        return len(job_containers)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0

if __name__ == "__main__":
    detailed_justremote_analysis()