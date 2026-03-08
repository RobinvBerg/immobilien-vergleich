"""
Savills - Intercept the POST request body sent to SearchByUrl
We need to find what parameters produce Mallorca results
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
                print(f"\n=== SearchByUrl REQUEST BODY ===")
                try:
                    parsed = json.loads(body)
                    print(json.dumps(parsed, indent=2)[:2000])
                    request_bodies.append(parsed)
                except:
                    print(body[:1000])
        except Exception as e:
            print(f"Req body error: {e}")

def handle_response(response):
    if 'livev6-searchapi.savills.com/Data/SearchByUrl' in response.url:
        try:
            data = response.json()
            results = data.get('Results', {})
            props = results.get('Properties', [])
            total = results.get('SearchContext', {}).get('TotalResults', 0)
            print(f"\nSearchByUrl RESPONSE: {len(props)} props, total={total}")
            search_list = results.get('SearchContext', {}).get('Criteria', {}).get('SearchList', [])
            print(f"SearchList: {search_list}")
            if props:
                p = props[0]
                print(f"First prop: {p.get('ExternalPropertyID')} | {p.get('MetaInformation', {}).get('Description', '')[:100]}")
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
    
    print("Navigating to Savills Mallorca search...")
    # Try a more specific URL
    page.goto('https://search.savills.com/property-search#/r/es/for-sale/residential/spain/balearic-islands/mallorca',
              wait_until='networkidle', timeout=90000)
    time.sleep(10)
    
    # Check if we can find an autocomplete URL for Mallorca
    print("\n=== Checking autocomplete for Mallorca ===")
    page2 = context.new_page()
    
    import urllib.request
    try:
        # Try the Savills autocomplete/suggest API
        req = urllib.request.Request(
            'https://search.savills.com/api/search/suggest?query=mallorca&country=es&searchcategory=GRS_CAT_RES&tenure=GRS_T_B',
            headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            print(f"Autocomplete result: {json.dumps(data, indent=2)[:1000]}")
    except Exception as e:
        print(f"Autocomplete error: {e}")
    
    page2.close()
    browser.close()

print(f"\n=== SUMMARY ===")
print(f"Request bodies captured: {len(request_bodies)}")
print(f"Responses captured: {len(responses)}")

# Try to make a direct API call with Mallorca parameters
print("\n=== Trying direct API calls for Mallorca ===")
import urllib.request, urllib.parse

# Try autocomplete first
for query in ['mallorca', 'Mallorca', 'Balearic']:
    try:
        url = f'https://livev6-searchapi.savills.com/api/Autocomplete/List?query={query}'
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Origin': 'https://search.savills.com',
            'Referer': 'https://search.savills.com/'
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            print(f"Autocomplete '{query}': {json.dumps(data, indent=2)[:500]}")
    except Exception as e:
        print(f"Autocomplete '{query}' error: {e}")
