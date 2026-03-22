#!/usr/bin/env python3
"""Type Mallorca in search, wait for results, extract from DOM"""
import asyncio, json
from playwright.async_api import async_playwright

URL = "https://www.engelvoelkers.com/de/search/?businessArea=residential&mode=buy&categories=villa,finca&rooms=5.0"

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, args=["--no-sandbox"])  # headful for debugging
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        
        captured_data = []
        
        async def on_response(resp):
            url = resp.url
            if 'engelvoelkers' in url and not any(x in url for x in ['.js', '.css', '.png', '.jpg', '.svg', '.woff', 'clerk', 'maptiler', 'uploadcare', 'speed', 'analytics']):
                try:
                    ct = resp.headers.get('content-type', '')
                    if 'json' in ct:
                        b = await resp.body()
                        j = json.loads(b)
                        js = json.dumps(j)
                        if 'listing' in js.lower() and len(js) > 500:
                            print(f"\n*** LISTING API: {url[:120]}")
                            print(js[:1000])
                            captured_data.append({'url': url, 'data': j})
                except: pass
        
        page = await context.new_page()
        page.on("response", on_response)
        
        await page.goto(URL, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        # Accept cookies
        try:
            btn = await page.wait_for_selector("#onetrust-accept-btn-handler", timeout=5000)
            await btn.click()
            await asyncio.sleep(2)
            print("Cookies accepted")
        except:
            print("No cookie banner")
        
        # Try to find and fill visible search input
        try:
            # Use evaluate to find visible inputs
            visible_input = await page.evaluate("""() => {
                const inputs = document.querySelectorAll('input[name="search"], input[data-testid*="autocomplete"]');
                for (const i of inputs) {
                    const rect = i.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) return i.id || i.name;
                }
                return null;
            }""")
            print(f"Visible input: {visible_input}")
            
            # Click and type
            await page.click(f'input[id="{visible_input}"]' if visible_input and visible_input != 'search' else 'input[data-testid="search-components_autocomplete_input"]', timeout=5000)
            await asyncio.sleep(1)
            await page.type('input[data-testid="search-components_autocomplete_input"]', 'Mallorca', delay=100)
            await asyncio.sleep(3)
            
            # Look for suggestions
            suggestions = await page.evaluate("""() => {
                const els = document.querySelectorAll('[role="option"], [class*="suggestion"]');
                return [...els].map(e => ({text: e.textContent.trim(), id: e.id})).slice(0, 10);
            }""")
            print("Suggestions:", suggestions)
            
            # Click first suggestion if any
            if suggestions:
                await page.click('[role="option"]:first-child', timeout=3000)
                await asyncio.sleep(5)
            else:
                await page.press('input[data-testid="search-components_autocomplete_input"]', 'Enter')
                await asyncio.sleep(5)
            
        except Exception as e:
            print(f"Input error: {e}")
        
        print(f"\nCurrent URL: {page.url}")
        count = await page.evaluate("() => document.querySelectorAll('article').length")
        print(f"Articles in DOM: {count}")
        
        await asyncio.sleep(5)
        await browser.close()

asyncio.run(main())
