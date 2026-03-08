"""
Savills - Find Mallorca ID using the /list/ URL format
"""
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import json, time

request_bodies = []
responses = []

def handle_request(request):
    if 'livev6-searchapi.savills.com/Data/SearchByUrl' in request.url:
        try:
            body = request.post_data
            if body:
                try:
                    parsed = json.loads(body)
                    print(f"\n=== REQUEST BODY (SearchByUrl) ===")
                    print(json.dumps(parsed, indent=2))
                    request_bodies.append(parsed)
                except:
                    print(f"Raw body: {body[:500]}")
        except Exception as e:
            print(f"Req error: {e}")
    elif 'livev6-searchapi.savills.com' in request.url:
        print(f"Other API: {request.method} {request.url[:150]}")
        try:
            body = request.post_data
            if body:
                print(f"  Body: {body[:200]}")
        except:
            pass

def handle_response(response):
    if 'livev6-searchapi.savills.com/Data/SearchByUrl' in response.url:
        try:
            data = response.json()
            results = data.get('Results', {})
            ctx = results.get('SearchContext', {})
            props = results.get('Properties', [])
            total = results.get('TotalResults', ctx.get('TotalResults', '?'))
            criteria = ctx.get('Criteria', {})
            search_list = criteria.get('SearchList', [])
            print(f"\n=== RESPONSE: {len(props)} properties ===")
            print(f"SearchList: {search_list}")
            if props:
                p0 = props[0]
                print(f"First: {p0.get('ExternalPropertyID')} | {p0.get('MetaInformation',{}).get('Description','')[:80]}")
                loc = p0.get('Location', {})
                print(f"Location: {loc}")
            responses.append(data)
        except Exception as e:
            print(f"Resp error: {e}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    page = context.new_page()
    Stealth().apply_stealth_sync(page)
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    # Try the /list/ URL format for Mallorca
    urls_to_try = [
        'https://search.savills.com/es/en/list/property-for-sale/spain/mallorca',
        'https://search.savills.com/property-search#/r/es/for-sale/residential/spain/balearic-islands/mallorca',
        'https://search.savills.com/es/en/property-search#/r/es/for-sale/residential/spain/balearic-islands/mallorca',
    ]
    
    for url in urls_to_try:
        print(f"\n=== Navigating to: {url} ===")
        try:
            page.goto(url, wait_until='networkidle', timeout=60000)
            time.sleep(8)
            print(f"Current URL: {page.url}")
        except Exception as e:
            print(f"Error: {e}")
            try:
                page.wait_for_load_state('domcontentloaded', timeout=5000)
                time.sleep(5)
            except:
                pass
        
        if request_bodies and search_list and search_list[0]['Id'] != '46920':
            print("Found non-UK search!")
            break
    
    browser.close()

print(f"\n=== SUMMARY ===")
print(f"Request bodies: {len(request_bodies)}")
print(f"Responses: {len(responses)}")

# Now try autocomplete via requests session
print("\n=== Trying Savills suggestions API ===")
import requests
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Origin': 'https://search.savills.com',
    'Referer': 'https://search.savills.com/'
})

# Try various autocomplete endpoints
endpoints = [
    'https://livev6-searchapi.savills.com/api/suggest/list?query=mallorca&searchcategory=GRS_CAT_RES&tenure=GRS_T_B',
    'https://livev6-searchapi.savills.com/Suggest?query=mallorca',
    'https://livev6-searchapi.savills.com/api/Autocomplete?query=mallorca',
    'https://search.savills.com/api/search/suggest?query=mallorca',
    'https://search.savills.com/api/locations/autocomplete?query=mallorca',
]
for ep in endpoints:
    try:
        r = session.get(ep, timeout=10)
        print(f"\n{ep}")
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print(f"Data: {r.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
