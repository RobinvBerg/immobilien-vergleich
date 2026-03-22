#!/usr/bin/env python3
"""Debug: Wait for Mallorca-filtered API response"""
import asyncio
import json
from playwright.async_api import async_playwright

URL = "https://www.engelvoelkers.com/de/search/?q=mallorca&businessArea=residential&mode=buy&categories=villa,finca&rooms=5.0&i=0"

async def main():
    search_calls = []
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="de-DE",
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        
        async def handle_response(response):
            url = response.url
            if 'search-bff' in url or 'bff' in url or ('/api/' in url and 'maptiler' not in url and 'tracking' not in url and 'clerk' not in url):
                print(f"\n[RESPONSE] {response.status} {url[:150]}")
                try:
                    body = await response.body()
                    try:
                        jbody = json.loads(body)
                        print(json.dumps(jbody, indent=2)[:500])
                        search_calls.append({'url': url, 'body': jbody})
                    except:
                        print(body[:200])
                except:
                    pass
        
        async def handle_request(req):
            url = req.url
            if 'search-bff' in url or ('bff' in url and 'pbf' not in url):
                print(f"\n[REQUEST] {req.method} {url[:150]}")
                if req.method == 'POST':
                    print(f"  Body: {req.post_data[:300] if req.post_data else 'none'}")
        
        page = await context.new_page()
        page.on("response", handle_response)
        page.on("request", handle_request)
        
        await page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        
        # Accept cookies quickly
        try:
            await page.click("#onetrust-accept-btn-handler", timeout=5000)
        except:
            pass
        
        # Wait longer for JS to execute and make API calls
        print("Waiting for JS search to execute...")
        await asyncio.sleep(15)
        
        # Check current page state
        count = await page.evaluate("""() => {
            return document.querySelectorAll('article').length;
        }""")
        print(f"\nArticle count in DOM: {count}")
        
        # Dump fresh HTML
        html = await page.content()
        import re
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            pp = data.get('props', {}).get('pageProps', {})
            ds = pp.get('dehydratedState', {})
            queries = ds.get('queries', [])
            for q in queries:
                ld = q.get('state', {}).get('data', {})
                if isinstance(ld, dict) and 'listings' in ld:
                    listings = ld.get('listings', [])
                    print(f"Total: {ld.get('listingsTotal')}, on page: {len(listings)}")
                    if listings:
                        l = listings[0].get('listing', {})
                        print(f"Sample: country={l.get('countryAlpha2')}, city={l.get('address', {}).get('city', '')}")
        
        # Try to find search-bff URLs in JS source
        scripts = await page.evaluate("""() => {
            return [...document.querySelectorAll('script[src]')].map(s => s.src).filter(s => s.includes('search'));
        }""")
        print("Search scripts:", scripts)
        
        await browser.close()

asyncio.run(main())
