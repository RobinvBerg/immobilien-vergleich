"""
Properstar uses listglobally.com API
Intercept the actual search API calls and request bodies
"""
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import json, time, re

api_hits = []
post_bodies = []

def handle_request(request):
    url = request.url
    if 'listglobally.com' in url or 'properstar' in url:
        body = None
        try:
            body = request.post_data
        except:
            pass
        print(f"REQ {request.method}: {url[:150]}")
        if body:
            print(f"  BODY: {body[:300]}")
            post_bodies.append({'url': url, 'body': body})

def handle_response(response):
    url = response.url
    ct = response.headers.get('content-type', '')
    if 'listglobally.com' in url or ('properstar' in url and 'json' in ct):
        try:
            data = response.json()
            size = len(str(data))
            print(f"RESP: {url[:120]} | {size} bytes")
            api_hits.append({'url': url, 'data': data, 'size': size})
        except Exception as e:
            try:
                text = response.text()
                print(f"RESP (text): {url[:100]} | {text[:200]}")
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
    
    print("=== Loading Properstar Mallorca search page ===")
    page.goto('https://www.properstar.com/es/venta?country=ES&region=Baleares&type=house', 
              wait_until='domcontentloaded', timeout=60000)
    
    time.sleep(5)
    
    # Scroll to trigger more loads
    page.evaluate("window.scrollTo(0, 500)")
    time.sleep(3)
    page.evaluate("window.scrollTo(0, 1000)")
    time.sleep(3)
    
    try:
        page.wait_for_load_state('networkidle', timeout=10000)
    except:
        pass
    
    print("\n=== Also try direct Mallorca URL ===")
    page2 = context.new_page()
    page2.on('request', handle_request)
    page2.on('response', handle_response)
    page2.goto('https://www.properstar.es/es/venta?country=ES&island=Mallorca&type=house',
               wait_until='domcontentloaded', timeout=60000)
    time.sleep(5)
    page2.close()
    
    # Also extract embedded data from page
    print("\n=== Extracting embedded page state ===")
    content = page.content()
    
    # Look for __NEXT_DATA__ or similar
    match = re.search(r'window\.__(?:NEXT_DATA|STATE|INITIAL_STATE|nuxtState)__\s*=\s*(\{.+?\});?\s*</script>', content, re.DOTALL)
    if match:
        try:
            state_data = json.loads(match.group(1))
            print(f"Found embedded state! Keys: {list(state_data.keys())[:10]}")
            with open('/tmp/properstar_state.json', 'w') as f:
                json.dump(state_data, f, indent=2)
            print("State saved to /tmp/properstar_state.json")
        except Exception as e:
            print(f"Could not parse state: {e}")
    
    # Look for __NEXT_DATA__
    match2 = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', content, re.DOTALL)
    if match2:
        try:
            next_data = json.loads(match2.group(1))
            print(f"\nFound __NEXT_DATA__! Keys: {list(next_data.keys())}")
            with open('/tmp/properstar_nextdata.json', 'w') as f:
                json.dump(next_data, f, indent=2)
            print("NextData saved to /tmp/properstar_nextdata.json")
        except Exception as e:
            print(f"Could not parse NEXT_DATA: {e}")
    
    browser.close()

print(f"\n=== SUMMARY ===")
print(f"API hits: {len(api_hits)}")
print(f"POST bodies captured: {len(post_bodies)}")
for hit in api_hits:
    print(f"\nURL: {hit['url']}")
    print(f"Sample: {str(hit['data'])[:600]}")
