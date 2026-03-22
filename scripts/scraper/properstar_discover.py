from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import json, time

api_data = []

def handle_response(response):
    ct = response.headers.get('content-type', '')
    if 'json' in ct and response.status == 200:
        try:
            data = response.json()
            if isinstance(data, (list, dict)) and len(str(data)) > 200:
                api_data.append({'url': response.url, 'data': data})
                print(f"API: {response.url[:120]} | {len(str(data))} bytes")
        except: pass

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    page = context.new_page()
    Stealth().apply_stealth_sync(page)
    page.on('response', handle_response)
    
    page.goto('https://www.properstar.com/es/venta?country=ES&region=Baleares&type=house', 
              wait_until='networkidle', timeout=60000)
    time.sleep(5)
    
    print(f"\n=== TOTAL API CALLS: {len(api_data)} ===")
    for item in api_data:
        print(f"\nURL: {item['url']}")
        print(f"Data sample: {str(item['data'])[:800]}")
    
    browser.close()
