#!/usr/bin/env python3
"""Debug: Dump E&V page HTML to inspect structure"""
import asyncio
from playwright.async_api import async_playwright

URL = "https://www.engelvoelkers.com/de/search/?q=mallorca&businessArea=residential&mode=buy&categories=villa,finca&rooms=5.0&i=0"

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="de-DE",
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        page = await context.new_page()
        
        await page.goto(URL, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(5)
        
        # Accept cookies
        try:
            await page.click("#onetrust-accept-btn-handler", timeout=3000)
            await asyncio.sleep(2)
        except:
            pass
        
        # Dump relevant part of HTML
        html = await page.content()
        # Find property-related chunks
        with open("/tmp/ev_page.html", "w") as f:
            f.write(html)
        print(f"HTML saved, length: {len(html)}")
        
        # Print all unique class names with "prop" or "card" or "result" or "listing"
        classes = await page.evaluate("""() => {
            const all = document.querySelectorAll('*');
            const names = new Set();
            all.forEach(el => {
                el.classList.forEach(c => {
                    if (/prop|card|result|listing|item|object|immobil/i.test(c)) names.add(c);
                });
            });
            return [...names].slice(0, 100);
        }""")
        print("Relevant classes:", classes)
        
        # Also look for data-testid
        testids = await page.evaluate("""() => {
            return [...document.querySelectorAll('[data-testid]')].map(el => el.getAttribute('data-testid')).slice(0, 50);
        }""")
        print("data-testid values:", testids)
        
        # Count articles/sections
        counts = await page.evaluate("""() => {
            return {
                articles: document.querySelectorAll('article').length,
                sections: document.querySelectorAll('section').length,
                lis: document.querySelectorAll('li').length,
                divs: document.querySelectorAll('div[class]').length,
                links: document.querySelectorAll('a[href*="kaufen"], a[href*="buy"]').length,
                links2: document.querySelectorAll('a[href*="/de/"]').length,
            };
        }""")
        print("Element counts:", counts)
        
        # Sample some links
        links = await page.evaluate("""() => {
            return [...document.querySelectorAll('a[href]')]
                .map(a => a.href)
                .filter(h => h.includes('engelvoelkers') && (h.includes('kaufen') || h.includes('mallorca') || h.includes('/de/')))
                .slice(0, 20);
        }""")
        print("Sample links:", links)
        
        await browser.close()

asyncio.run(main())
