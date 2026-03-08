"""
Properstar deep discovery - capture ALL API calls when navigating a Mallorca search result
"""
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import json, time, re

all_api = []

def handle_response(response):
    url = response.url
    ct = response.headers.get('content-type', '')
    status = response.status
    
    # Skip static assets
    if any(x in url for x in ['.js', '.css', '.png', '.jpg', '.gif', '.woff', '.ico', '.svg', 'analytics', 'gtm', 'gstatic', 'facebook']):
        return
    
    if status == 200:
        try:
            data = response.json()
            size = len(str(data))
            if size > 100:
                all_api.append({'url': url, 'data': data, 'size': size})
                print(f"API [{status}]: {url[:130]} | {size} bytes")
        except:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1280, 'height': 800},
        locale='de-DE',
        extra_http_headers={'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8'}
    )
    page = context.new_page()
    Stealth().apply_stealth_sync(page)
    page.on('response', handle_response)
    
    # Try the German properstar.de domain with Mallorca search
    print("=== Test 1: Properstar.de Mallorca ===")
    page.goto('https://www.properstar.de/suche/spanien/mallorca?propertyTypes=house&transactionType=buy', 
              wait_until='domcontentloaded', timeout=60000)
    time.sleep(8)
    
    # Scroll
    for y in [300, 600, 900, 1200]:
        page.evaluate(f"window.scrollTo(0, {y})")
        time.sleep(1)
    
    try:
        page.wait_for_load_state('networkidle', timeout=10000)
    except:
        pass
    time.sleep(3)
    
    content = page.content()
    print(f"Page title: {page.title()}")
    print(f"URL: {page.url}")
    
    # Check for NEXT_DATA
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', content, re.DOTALL)
    if match:
        try:
            next_data = json.loads(match.group(1))
            print(f"NEXT_DATA keys: {list(next_data.keys())}")
            props_section = next_data.get('props', {})
            print(f"props keys: {list(props_section.keys())}")
            page_props = props_section.get('pageProps', {})
            print(f"pageProps keys: {list(page_props.keys())}")
            with open('/tmp/properstar_nextdata.json', 'w') as f:
                json.dump(next_data, f)
        except Exception as e:
            print(f"NEXT_DATA parse error: {e}")
    
    print(f"\n=== Test 2: Try direct listing search ===")
    page2 = context.new_page()
    page2.on('response', handle_response)
    # Try Spanish properstar.es
    page2.goto('https://www.properstar.es/es/sale/spain/mallorca?propertyTypes=house',
               wait_until='domcontentloaded', timeout=60000)
    time.sleep(8)
    page2.close()
    
    browser.close()

print(f"\n=== TOTAL API CALLS: {len(all_api)} ===")
for item in all_api:
    print(f"\n  URL: {item['url']}")
    print(f"  Sample: {str(item['data'])[:500]}")
    print()
