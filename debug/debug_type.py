#!/usr/bin/env python3
"""Type Mallorca in search, intercept result API"""
import asyncio, json
from playwright.async_api import async_playwright

BASE_URL = "https://www.engelvoelkers.com/de/search/?businessArea=residential&mode=buy&categories=villa,finca&rooms=5.0&i=0"

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        
        api_responses = []
        
        async def on_request(req):
            url = req.url
            if any(x in url for x in ['engelvoelkers']) and not any(x in url for x in ['.js', '.css', '.png', '.svg', 'clerk', 'maptiler', 'uploadcare', 'speed', 'analytics', 'criteo']):
                print(f"REQ {req.method} {url[:150]}")
                if req.method == 'POST':
                    print(f"  BODY: {req.post_data[:300] if req.post_data else ''}")
        
        async def on_response(resp):
            url = resp.url
            if any(x in url for x in ['engelvoelkers']) and not any(x in url for x in ['.js', '.css', '.png', '.jpg', '.svg', 'clerk', 'maptiler', 'uploadcare', 'speed']):
                try:
                    b = await resp.body()
                    if b and len(b) > 100:
                        try:
                            j = json.loads(b)
                            js = json.dumps(j)
                            if 'listing' in js or 'total' in js:
                                print(f"\n** LISTING RESPONSE {url[:120]} **")
                                print(js[:600])
                                api_responses.append({'url': url, 'data': j})
                        except: pass
                except: pass
        
        page = await context.new_page()
        page.on("request", on_request)
        page.on("response", on_response)
        
        await page.goto(BASE_URL, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        try: await page.click("#onetrust-accept-btn-handler", timeout=3000)
        except: pass
        await asyncio.sleep(2)
        
        # Type Mallorca in search input
        print("\n--- Typing Mallorca ---")
        await page.fill('input[name="search"]', 'Mallorca')
        await asyncio.sleep(3)
        
        # Look for autocomplete suggestions
        suggestions = await page.evaluate("""() => {
            const els = document.querySelectorAll('[role="option"], [class*="suggestion"], [class*="Suggestion"], [class*="autocomplete"]');
            return [...els].map(e => e.textContent.trim()).slice(0, 10);
        }""")
        print("Suggestions:", suggestions)
        
        # Press Enter or click search
        await page.press('input[name="search"]', 'Enter')
        await asyncio.sleep(8)
        
        print("\n--- Current URL ---")
        print(page.url)
        
        # Check for listings in page
        count = await page.evaluate("() => document.querySelectorAll('article').length")
        print(f"Articles: {count}")
        
        # Check __NEXT_DATA__ for total
        html = await page.content()
        import re
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
        if match:
            d = json.loads(match.group(1))
            pp = d.get('props', {}).get('pageProps', {})
            for q in pp.get('dehydratedState', {}).get('queries', []):
                ld = q.get('state', {}).get('data', {})
                if isinstance(ld, dict) and 'listings' in ld:
                    listings = ld.get('listings', [])
                    print(f"Total: {ld.get('listingsTotal')}, Page: {len(listings)}")
                    if listings:
                        l = listings[0].get('listing', {})
                        print(f"Sample country={l.get('countryAlpha2')}")
        
        await browser.close()

asyncio.run(main())
