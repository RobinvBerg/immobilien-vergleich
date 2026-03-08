#!/usr/bin/env python3
"""Intercept ALL network requests and look for listings API"""
import asyncio
import json
from playwright.async_api import async_playwright

URL = "https://www.engelvoelkers.com/de/search/?q=mallorca&businessArea=residential&mode=buy&categories=villa,finca&rooms=5.0&i=0"

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        
        async def on_response(resp):
            url = resp.url
            skip = ['maptiler', 'clerk', 'speed-insights', 'uploadcare', '.js', '.css', '.svg', '.png', '.jpg', '.ico', '.woff', 'pbf', 'gtm', 'ga.js', 'analytics', 'hotjar', 'criteo', 'facebook']
            if any(s in url for s in skip): return
            try:
                b = await resp.body()
                if len(b) > 200 and resp.status == 200:
                    try:
                        j = json.loads(b)
                        # Only print if it looks like listing data
                        js = json.dumps(j)
                        if any(k in js for k in ['listings', 'listing', 'properties', 'property', 'expose']):
                            print(f"\n*** JSON RESPONSE: {resp.status} {url[:120]}")
                            print(js[:800])
                    except:
                        pass
            except: pass
        
        page = await context.new_page()
        page.on("response", on_response)
        
        await page.goto(URL, wait_until="domcontentloaded")
        try: await page.click("#onetrust-accept-btn-handler", timeout=4000)
        except: pass
        
        # Wait for search to initialize
        await asyncio.sleep(10)
        
        # Try triggering search by navigating within the page
        # Check if there's a location input we can fill
        inputs = await page.evaluate("""() => {
            return [...document.querySelectorAll('input')].map(i => ({
                name: i.name, placeholder: i.placeholder, value: i.value, id: i.id
            }));
        }""")
        print("Inputs:", inputs[:10])
        
        # Check React/query cache
        listings = await page.evaluate("""() => {
            // Try to find React Query cache or similar
            if (window.__REACT_QUERY_DEVTOOLS_GLOBAL_HOOK__) return 'has devtools';
            if (window.queryClient) return JSON.stringify(window.queryClient.getQueryCache().getAll().length);
            return 'no cache found';
        }""")
        print("React query:", listings)
        
        await asyncio.sleep(10)
        await browser.close()

asyncio.run(main())
