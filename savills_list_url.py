"""
Savills - Navigate to /list/ URL format (which loaded successfully)
and capture ALL API calls
"""
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import json, time

api_calls = []
request_data = []

def handle_request(request):
    url = request.url
    if 'livev6-searchapi' in url or 'savills' in url:
        if '.js' not in url and '.css' not in url:
            method = request.method
            body = None
            try:
                body = request.post_data
            except:
                pass
            print(f"REQ {method}: {url[:150]}")
            if body:
                print(f"  BODY: {body[:400]}")
                request_data.append({'url': url, 'body': body, 'method': method})

def handle_response(response):
    url = response.url
    status = response.status
    ct = response.headers.get('content-type', '')
    
    if 'livev6-searchapi' in url or ('savills' in url and status == 200):
        if '.js' not in url and '.css' not in url:
            try:
                data = response.json()
                size = len(str(data))
                print(f"RESP [{status}]: {url[:130]} | {size} bytes")
                api_calls.append({'url': url, 'data': data, 'status': status, 'size': size})
            except:
                try:
                    text = response.text()
                    if len(text) > 100:
                        print(f"TEXT [{status}]: {url[:100]} | {len(text)} bytes | {text[:100]}")
                except:
                    pass

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    page = context.new_page()
    Stealth().apply_stealth_sync(page)
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    # Navigate to the /list/ format for all Mallorca
    url = 'https://search.savills.com/es/en/list/property-for-sale/spain/mallorca'
    print(f"=== Navigating to: {url} ===")
    
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=60000)
        print(f"Actual URL: {page.url}")
        print(f"Title: {page.title()}")
    except Exception as e:
        print(f"Navigation error: {e}")
    
    # Wait longer for API calls
    print("Waiting for API calls...")
    time.sleep(15)
    
    # Try to wait for property listings to appear
    try:
        page.wait_for_selector('[class*="property"], [class*="listing"], [data-testid*="property"]', timeout=20000)
        print("Property elements found!")
    except:
        print("No property elements found after 20s")
    
    time.sleep(5)
    
    # Scroll
    for y in [400, 800, 1200]:
        page.evaluate(f"window.scrollTo(0, {y})")
        time.sleep(2)
    
    time.sleep(5)
    
    print(f"\n=== API Calls captured: {len(api_calls)} ===")
    print(f"Request data captured: {len(request_data)} ===")
    
    # Look at page source for data
    content = page.content()
    print(f"Page source length: {len(content)}")
    
    # Search for property data in source
    import re
    # Look for JSON data embedded
    matches = re.findall(r'"ExternalPropertyID":\s*"([^"]+)"', content)
    if matches:
        print(f"Found ExternalPropertyIDs in page: {matches[:10]}")
    
    # Look for SearchList ID
    id_matches = re.findall(r'"Id":\s*"(\d+)"', content)
    if id_matches:
        print(f"Found IDs in page: {id_matches[:10]}")
    
    browser.close()

print(f"\n=== FINAL SUMMARY ===")
for call in api_calls:
    print(f"\nURL: {call['url']}")
    data = call['data']
    if 'Results' in data:
        results = data['Results']
        ctx = results.get('SearchContext', {})
        criteria = ctx.get('Criteria', {})
        print(f"SearchList: {criteria.get('SearchList')}")
        props = results.get('Properties', [])
        print(f"Properties: {len(props)}")
        if props:
            p0 = props[0]
            print(f"First: {p0.get('ExternalPropertyID')} | {p0.get('MetaInformation',{}).get('Description','')[:80]}")
    else:
        print(f"Data: {str(data)[:300]}")

# Try direct SearchByUrl with Mallorca parameters
print("\n=== Direct API calls with Mallorca params ===")
import requests

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json',
    'Origin': 'https://search.savills.com',
    'Referer': 'https://search.savills.com/es/en/list/property-for-sale/spain/mallorca',
})

# Try various Mallorca-related SearchList IDs
# Mallorca might be an island/region with a different category
# Common Savills category types: RegionCountyCountry, City, Area, PostCode
test_params = [
    '?SearchList=Id_mallorca+Category_Area&Tenure=GRS_T_B&Currency=EUR&Category=GRS_CAT_RES',
    '?SearchList=Id_spain+Category_RegionCountyCountry&Tenure=GRS_T_B&Currency=EUR&Category=GRS_CAT_RES',
]

for param in test_params:
    try:
        r = session.post(
            'https://livev6-searchapi.savills.com/Data/SearchByUrl',
            json={'url': param},
            timeout=15
        )
        print(f"\nParam: {param[:100]}")
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            results = data.get('Results', {})
            ctx = results.get('SearchContext', {})
            criteria = ctx.get('Criteria', {})
            props = results.get('Properties', [])
            print(f"SearchList: {criteria.get('SearchList')}")
            print(f"Properties: {len(props)}")
    except Exception as e:
        print(f"Error: {e}")
