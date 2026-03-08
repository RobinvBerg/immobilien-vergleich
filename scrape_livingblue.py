#!/usr/bin/env python3
"""
Scraper für Living Blue Mallorca (livingblue-mallorca.com)
Nutzt Playwright um JS-rendered Content zu laden + API-Requests zu intercepten
"""
import json, time, re
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

BASE_URL = "https://www.livingblue-mallorca.com/de-de/immobilien"
RESULTS = []
API_RESPONSES = []

def scrape():
    with Stealth().use_sync(sync_playwright()) as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="de-DE"
        )
        page = ctx.new_page()

        # Intercept API responses
        def handle_response(response):
            url = response.url
            if 'egorealestate.com' in url or 'api' in url.lower():
                try:
                    ct = response.headers.get('content-type', '')
                    if 'json' in ct:
                        data = response.json()
                        API_RESPONSES.append({'url': url, 'data': data})
                        print(f"[API] {url} -> {str(data)[:200]}")
                except:
                    pass

        page.on("response", handle_response)

        print(f"Loading {BASE_URL} ...")
        page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        time.sleep(3)

        # Try to find property count
        try:
            count_el = page.query_selector('[class*="count"], [class*="results"], [class*="total"]')
            if count_el:
                print(f"Count element: {count_el.inner_text()}")
        except:
            pass

        # Scrape visible properties
        props = page.query_selector_all('[class*="property"], [class*="listing"], [class*="card"], article')
        print(f"Found {len(props)} property elements on page")

        for prop in props[:5]:
            try:
                text = prop.inner_text()[:300]
                href = None
                a = prop.query_selector('a')
                if a:
                    href = a.get_attribute('href')
                print(f"  -> {text[:100]} | {href}")
            except:
                pass

        # Dump all API responses
        print(f"\n=== {len(API_RESPONSES)} API responses captured ===")
        for resp in API_RESPONSES:
            print(f"URL: {resp['url']}")
            print(f"Data keys: {list(resp['data'].keys()) if isinstance(resp['data'], dict) else type(resp['data'])}")

        # Save API responses
        with open('/tmp/livingblue_api.json', 'w') as f:
            json.dump(API_RESPONSES, f, indent=2, default=str)

        browser.close()

if __name__ == '__main__':
    scrape()
