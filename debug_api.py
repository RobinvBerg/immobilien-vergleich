#!/usr/bin/env python3
"""Debug: Intercept API calls on E&V search page"""
import asyncio
import json
from playwright.async_api import async_playwright

URL = "https://www.engelvoelkers.com/de/search/?q=mallorca&businessArea=residential&mode=buy&categories=villa,finca&rooms=5.0&i=0"

async def main():
    api_calls = []
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="de-DE",
        )
        
        # Intercept API calls
        async def handle_request(request):
            url = request.url
            if any(x in url for x in ['api', 'graphql', 'search', 'listing', '/v1/', '/v2/']):
                if 'static' not in url and 'font' not in url and '_next' not in url:
                    api_calls.append({
                        'url': url,
                        'method': request.method,
                        'post_data': request.post_data if request.method == 'POST' else None
                    })
        
        async def handle_response(response):
            url = response.url
            if any(x in url for x in ['listing', 'property', 'expose', 'search/result']) and response.status == 200:
                try:
                    body = await response.json()
                    print(f"\n=== API RESPONSE: {url[:100]} ===")
                    print(json.dumps(body, indent=2)[:1000])
                except:
                    pass
        
        page = await context.new_page()
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        
        print(f"Opening: {URL}")
        await page.goto(URL, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(5)
        
        # Accept cookies
        try:
            await page.click("#onetrust-accept-btn-handler", timeout=3000)
            await asyncio.sleep(3)
        except:
            pass
        
        print("\n=== All API calls intercepted ===")
        for c in api_calls:
            print(f"  {c['method']} {c['url'][:120]}")
            if c['post_data']:
                print(f"    POST: {c['post_data'][:200]}")
        
        # Also check __NEXT_DATA__ for location-filtered results
        html = await page.content()
        import re
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            pp = data.get('props', {}).get('pageProps', {})
            ds = pp.get('dehydratedState', {})
            queries = ds.get('queries', [])
            for q in queries:
                qk = q.get('queryKey', '')
                ld = q.get('state', {}).get('data', {})
                if isinstance(ld, dict) and 'listings' in ld:
                    print(f"\nQuery: {str(qk)[:150]}")
                    print(f"Total listings: {ld.get('listingsTotal')}")
                    listings = ld.get('listings', [])
                    print(f"Listings on page: {len(listings)}")
                    if listings:
                        l = listings[0].get('listing', {})
                        print(f"Sample: country={l.get('countryAlpha2')}, title={l.get('profile', {}).get('title', '')[:50]}")
        
        await browser.close()

asyncio.run(main())
