from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import json, time

api_data_savills = []

def handle_savills(response):
    ct = response.headers.get('content-type', '')
    if 'json' in ct and response.status == 200:
        try:
            data = response.json()
            body_str = str(data)
            if any(k in body_str.lower() for k in ['price', 'bedroom', 'property', 'listing']):
                if len(body_str) > 500:
                    api_data_savills.append({'url': response.url, 'data': data})
                    print(f"Savills API: {response.url[:120]} | {len(body_str)} bytes")
        except: pass

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    page = context.new_page()
    Stealth().apply_stealth_sync(page)
    page.on('response', handle_savills)
    
    page.goto('https://search.savills.com/property-search#/r/es/for-sale/residential/spain/balearic-islands/mallorca',
              wait_until='networkidle', timeout=90000)
    time.sleep(8)
    
    print(f"\n=== TOTAL SAVILLS API CALLS: {len(api_data_savills)} ===")
    for item in api_data_savills[:10]:
        print(f"\nURL: {item['url']}")
        print(f"Data: {str(item['data'])[:1000]}")
    
    browser.close()
