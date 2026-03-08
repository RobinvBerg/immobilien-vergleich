"""
Properstar — More aggressive API discovery
Try with interactions + check ALL network requests (including XHR/fetch)
"""
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import json, time

all_requests = []
api_data = []

def handle_request(request):
    if request.method in ['GET', 'POST']:
        url = request.url
        # Skip static resources
        if any(x in url for x in ['.js', '.css', '.png', '.jpg', '.gif', '.woff', '.ico', 'google', 'facebook', 'analytics']):
            return
        all_requests.append({'method': request.method, 'url': url[:200]})

def handle_response(response):
    ct = response.headers.get('content-type', '')
    if response.status == 200:
        url = response.url
        # Skip static
        if any(x in url for x in ['.js', '.css', '.png', '.jpg', '.gif', '.woff', '.ico']):
            return
        if 'json' in ct or 'graphql' in url.lower() or 'api' in url.lower():
            try:
                data = response.json()
                size = len(str(data))
                if size > 100:
                    api_data.append({'url': url, 'data': data, 'size': size})
                    print(f"API: {url[:120]} | {size} bytes | ct={ct[:40]}")
            except: 
                pass

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1280, 'height': 800}
    )
    page = context.new_page()
    Stealth().apply_stealth_sync(page)
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    print("Loading Properstar Mallorca...")
    page.goto('https://www.properstar.com/es/venta?country=ES&region=Baleares&type=house', 
              wait_until='domcontentloaded', timeout=60000)
    
    # Wait and scroll to trigger lazy loading
    time.sleep(5)
    page.evaluate("window.scrollTo(0, 300)")
    time.sleep(2)
    page.evaluate("window.scrollTo(0, 600)")
    time.sleep(2)
    
    # Try to wait for network to settle
    try:
        page.wait_for_load_state('networkidle', timeout=15000)
    except:
        pass
    time.sleep(3)
    
    print(f"\n=== All non-static requests: {len(all_requests)} ===")
    for r in all_requests[:50]:
        print(f"  {r['method']} {r['url']}")
    
    print(f"\n=== API responses: {len(api_data)} ===")
    for item in api_data:
        print(f"\nURL: {item['url']}")
        print(f"Data sample: {str(item['data'])[:800]}")
    
    # Check page source for API hints
    content = page.content()
    print(f"\nPage source size: {len(content)}")
    
    # Look for API hints in page source
    for keyword in ['api/', '/search', 'graphql', 'listings', 'properties']:
        idx = content.lower().find(keyword)
        if idx != -1:
            print(f"\nFound '{keyword}' at {idx}: ...{content[max(0,idx-50):idx+100]}...")
    
    browser.close()
