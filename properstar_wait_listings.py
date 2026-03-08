"""
Properstar - Wait for actual listing elements to appear in DOM
and capture ALL related API calls
"""
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import json, time, re

all_api = []
all_requests_raw = []

def capture_response(response):
    url = response.url
    status = response.status
    ct = response.headers.get('content-type', '')
    
    # Skip obvious static
    if any(ext in url for ext in ['.js', '.css', '.woff', '.ico', '.svg']):
        return
    if any(service in url for service in ['google-analytics', 'gtm.js', 'gstatic', 'facebook.net', 'giosg']):
        return
    
    if status == 200:
        try:
            data = response.json()
            size = len(str(data))
            if size > 200:
                all_api.append({'url': url, 'data': data, 'size': size})
                print(f"JSON [{status}]: {url[:130]} | {size} bytes")
        except:
            # Not JSON - check if it looks like it has listings
            try:
                text = response.text()
                if 'listing' in text.lower() and len(text) > 1000:
                    print(f"TEXT [{status}]: {url[:100]} | {len(text)} bytes (has 'listing')")
            except:
                pass

def capture_request(request):
    url = request.url
    if any(ext in url for ext in ['.js', '.css', '.woff', '.ico', '.svg', '.png', '.jpg']):
        return
    if any(service in url for service in ['google-analytics', 'gtm.js', 'gstatic', 'facebook.net']):
        return
    all_requests_raw.append({'method': request.method, 'url': url})

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1440, 'height': 900},
        locale='de-DE',
    )
    page = context.new_page()
    Stealth().apply_stealth_sync(page)
    page.on('request', capture_request)
    page.on('response', capture_response)
    
    # Try the most specific Properstar URL formats
    test_urls = [
        'https://www.properstar.de/suche/spanien/mallorca',
        'https://www.properstar.com/de/venta?country=ES&region=Baleares&type=house',
        'https://www.properstar.com/suche/spanien/mallorca',
    ]
    
    for test_url in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing: {test_url}")
        try:
            page.goto(test_url, wait_until='domcontentloaded', timeout=45000)
            print(f"Actual URL: {page.url}")
            print(f"Title: {page.title()}")
            
            # Wait up to 15s for listing cards to appear
            try:
                page.wait_for_selector('[class*="listing"], [class*="property-card"], [class*="PropertyCard"], article', timeout=15000)
                print("Found listing elements!")
            except:
                print("No listing elements found")
            
            # Scroll to trigger more loads
            for y in [400, 800, 1200, 1600]:
                page.evaluate(f"window.scrollTo(0, {y})")
                time.sleep(1)
            
            time.sleep(5)
            
            # Count listing elements
            listings = page.query_selector_all('[class*="listing"], [class*="property-card"], [class*="PropertyCard"], article')
            print(f"Listing elements found: {len(listings)}")
            
            if len(all_api) > 0:
                print(f"API calls so far: {len(all_api)}")
                break
        
        except Exception as e:
            print(f"Error: {e}")
    
    # Print all non-static requests
    print(f"\n=== ALL REQUESTS: {len(all_requests_raw)} ===")
    for r in all_requests_raw:
        print(f"  {r['method']} {r['url'][:150]}")
    
    browser.close()

print(f"\n=== TOTAL API CALLS: {len(all_api)} ===")
for item in all_api:
    print(f"\nURL: {item['url']}")
    print(f"Sample: {str(item['data'])[:800]}")
    print()
