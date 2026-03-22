"""
Savills API - Full exploration of SearchByUrl endpoint
Goal: Find Mallorca properties via the livev6-searchapi.savills.com/Data/SearchByUrl endpoint
"""
import json
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import time

full_responses = []

def handle_savills(response):
    if 'livev6-searchapi.savills.com/Data/SearchByUrl' in response.url:
        try:
            data = response.json()
            full_responses.append({'url': response.url, 'data': data, 'req': None})
            print(f"SearchByUrl hit! Size: {len(str(data))} bytes")
        except Exception as e:
            print(f"Error parsing: {e}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    page = context.new_page()
    Stealth().apply_stealth_sync(page)
    page.on('response', handle_savills)
    
    # Navigate directly to Mallorca search
    page.goto('https://search.savills.com/property-search#/r/es/for-sale/residential/spain/balearic-islands/mallorca',
              wait_until='networkidle', timeout=90000)
    time.sleep(8)
    
    browser.close()

print(f"\n=== Got {len(full_responses)} SearchByUrl responses ===")
for i, resp in enumerate(full_responses):
    data = resp['data']
    results = data.get('Results', {})
    
    # Show search context
    ctx = results.get('SearchContext', {})
    criteria = ctx.get('Criteria', {})
    print(f"\n--- Response {i+1} ---")
    print(f"SearchList: {criteria.get('SearchList', [])}")
    print(f"Tenure: {criteria.get('Tenure')}")
    print(f"PropertyTypes: {criteria.get('PropertyTypes')}")
    
    # Count properties
    props = results.get('Properties', [])
    print(f"Properties count: {len(props)}")
    
    if props:
        print(f"\nFirst property sample:")
        print(json.dumps(props[0], indent=2)[:2000])

# Save full data
with open('/Users/robin/.openclaw/workspace/mallorca-projekt/savills_raw.json', 'w') as f:
    json.dump(full_responses, f, indent=2, default=str)
print("\nRaw data saved to savills_raw.json")
