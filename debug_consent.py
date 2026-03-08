#!/usr/bin/env python3
"""Accept Didomi consent, search Mallorca, intercept API"""
import asyncio, json
from playwright.async_api import async_playwright

URL = "https://www.engelvoelkers.com/de/search/?businessArea=residential&mode=buy&categories=villa,finca&rooms=5.0"

async def main():
    api_calls = []
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        
        async def on_request(req):
            url = req.url
            if 'engelvoelkers' in url and not any(x in url for x in ['.js', '.css', '.png', '.jpg', '.svg', '.woff', 'clerk', 'maptiler', 'uploadcare', 'speed', 'analytics', 'criteo', 'google', '.pbf']):
                api_calls.append({'url': url, 'method': req.method, 'post': req.post_data})
                if req.method == 'POST':
                    print(f"POST: {url[:120]}")
                    print(f"  {req.post_data[:300] if req.post_data else ''}")
        
        async def on_response(resp):
            url = resp.url
            if 'engelvoelkers' in url and not any(x in url for x in ['.js', '.css', '.png', '.jpg', '.svg', '.woff', 'clerk', 'maptiler', 'uploadcare', 'speed', 'analytics']):
                ct = resp.headers.get('content-type', '')
                if 'json' in ct:
                    try:
                        b = await resp.body()
                        j = json.loads(b)
                        js = json.dumps(j)
                        if ('listing' in js.lower() or 'expose' in js.lower() or 'total' in js.lower()) and len(js) > 200:
                            print(f"JSON {resp.status} {url[:120]}")
                            print(js[:800])
                    except: pass
        
        page = await context.new_page()
        page.on("request", on_request)
        page.on("response", on_response)
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        
        await page.goto(URL, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        # Accept Didomi
        try:
            await page.wait_for_selector('#didomi-popup, [id*="didomi"]', timeout=5000)
            await page.evaluate("""() => {
                // Try all possible consent buttons
                const selectors = [
                    '#didomi-notice-agree-button',
                    'button[id*="didomi-notice-agree"]',
                    '.didomi-button-highlight',
                    'button[data-purposes]',
                ];
                for (const s of selectors) {
                    const btn = document.querySelector(s);
                    if (btn) { btn.click(); return s; }
                }
                return null;
            }""")
            await asyncio.sleep(2)
            print("Didomi handled")
        except Exception as e:
            print(f"Didomi error: {e}")
            # Try via JS directly
            await page.evaluate("document.querySelector('#didomi-popup, .didomi-popup')?.remove()")
        
        # Now find and fill search input
        await asyncio.sleep(1)
        
        # Try using JS to find visible input
        inputs_info = await page.evaluate("""() => {
            const result = [];
            document.querySelectorAll('input[name="search"]').forEach(i => {
                const rect = i.getBoundingClientRect();
                result.push({id: i.id, testid: i.dataset.testid, visible: rect.width > 0 && rect.height > 0, rect: {w: rect.width, h: rect.height, x: rect.x, y: rect.y}});
            });
            return result;
        }""")
        print("Inputs:", inputs_info)
        
        # Force focus and type
        try:
            await page.evaluate("""() => {
                const inputs = document.querySelectorAll('input[name="search"]');
                for (const i of inputs) {
                    const rect = i.getBoundingClientRect();
                    if (rect.width > 0) { i.focus(); break; }
                }
            }""")
            await asyncio.sleep(0.5)
            
            # Type character by character
            await page.keyboard.type('Mallorca', delay=150)
            await asyncio.sleep(3)
            
            # Check for suggestions
            suggestions = await page.evaluate("""() => {
                return [...document.querySelectorAll('[role="option"], [class*="suggestion"], [class*="listbox"] > *')].map(e => e.textContent.trim()).filter(t => t).slice(0,5);
            }""")
            print("Suggestions:", suggestions)
            
            if suggestions:
                # Click first suggestion
                await page.click('[role="option"]:first-of-type, [class*="listbox"] > *:first-child', timeout=3000)
            else:
                await page.keyboard.press('Enter')
            
            await asyncio.sleep(10)
            print(f"URL after search: {page.url}")
            
        except Exception as e:
            print(f"Search error: {e}")
        
        await browser.close()
        
        print(f"\nTotal API calls: {len(api_calls)}")
        for c in api_calls:
            print(f"  {c['method']} {c['url'][:100]}")

asyncio.run(main())
