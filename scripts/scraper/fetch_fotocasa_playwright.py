#!/usr/bin/env python3
"""
Fotocasa Playwright Fetcher mit Decodo Residential Proxy (ES)
Extrahiert superficieParcela / plotArea aus __INITIAL_PROPS__ oder JSON-LD
"""

import json
import re
import time
import sys
import os
from pathlib import Path

PROGRESS_FILE = Path("/Users/robin/.openclaw/workspace/mallorca-projekt/fetchdetails_progress.json")
PROXY = {
    "server": "http://gate.decodo.com:10001",
    "username": "sp1e6lma32-country-es",
    "password": "pxjc5K6_LBg3Is6vzo"
}
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
DELAY = 2
SAVE_EVERY = 50
MAX_RETRIES = 2

def load_progress():
    with open(PROGRESS_FILE) as f:
        return json.load(f)

def save_progress(data):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_plot(html: str) -> float | None:
    """Extract plot area from page HTML."""
    # 1) Try __INITIAL_PROPS__
    m = re.search(r'window\.__INITIAL_PROPS__\s*=\s*(\{.+?\});\s*</script>', html, re.DOTALL)
    if m:
        try:
            props = json.loads(m.group(1))
            # Navigate to find superficieParcela
            def find_key(obj, key):
                if isinstance(obj, dict):
                    if key in obj:
                        return obj[key]
                    for v in obj.values():
                        r = find_key(v, key)
                        if r is not None:
                            return r
                elif isinstance(obj, list):
                    for item in obj:
                        r = find_key(item, key)
                        if r is not None:
                            return r
                return None
            
            val = find_key(props, "superficieParcela")
            if val is None:
                val = find_key(props, "plotArea")
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    pass
        except json.JSONDecodeError:
            pass

    # 2) Try JSON-LD
    for m in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL):
        try:
            obj = json.loads(m.group(1))
            if isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict) and "plotSize" in item:
                        return float(item["plotSize"])
            elif isinstance(obj, dict):
                if "plotSize" in obj:
                    return float(obj["plotSize"])
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    # 3) Try regex patterns for superficieParcela in raw HTML
    patterns = [
        r'"superficieParcela"\s*:\s*(\d+(?:\.\d+)?)',
        r'"plotArea"\s*:\s*(\d+(?:\.\d+)?)',
        r'"plotSize"\s*:\s*(\d+(?:\.\d+)?)',
        r'superficieParcela["\s:]+(\d+(?:\.\d+)?)',
    ]
    for pat in patterns:
        m = re.search(pat, html)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass

    return None

def is_cloudflare_block(html: str) -> bool:
    return (
        "cf-browser-verification" in html
        or "challenge-platform" in html
        or "Checking your browser" in html
        or "Ray ID" in html and "cloudflare" in html.lower()
        or len(html) < 5000 and "403" in html
    )

def fetch_url(page, url: str, retry=0) -> str | None:
    """Fetch URL and return HTML, handling Cloudflare blocks."""
    try:
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        # Wait a bit for JS to render
        time.sleep(2)
        html = page.content()
        
        if is_cloudflare_block(html):
            if retry < MAX_RETRIES:
                print(f"  ⚠️  Cloudflare block, waiting 30s... (retry {retry+1}/{MAX_RETRIES})")
                time.sleep(30)
                return None  # Signal to create new context
            else:
                print(f"  ❌ Cloudflare block after {MAX_RETRIES} retries")
                return ""  # Empty = skip
        return html
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return ""

def create_context(browser):
    return browser.new_context(
        user_agent=USER_AGENT,
        locale="es-ES",
        viewport={"width": 1366, "height": 768},
        extra_http_headers={
            "Accept-Language": "es-ES,es;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
    )

def main(test_mode=False, test_urls=None):
    from playwright.sync_api import sync_playwright

    progress = load_progress()
    
    # Get fotocasa URLs that need fetching
    if test_urls:
        to_fetch = test_urls
    else:
        to_fetch = [
            url for url, val in progress.items()
            if "fotocasa" in url and val.get("plot") is None
        ]
    
    print(f"📋 URLs to fetch: {len(to_fetch)}")
    if test_mode:
        print("🧪 TEST MODE — only 3 URLs")
        to_fetch = to_fetch[:3]

    results = {"found": 0, "not_found": 0, "errors": 0}
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            proxy=PROXY
        )
        context = create_context(browser)
        page = context.new_page()
        
        for i, url in enumerate(to_fetch, 1):
            print(f"\n[{i}/{len(to_fetch)}] {url}")
            
            # Fetch with retry/new-context logic
            html = None
            for attempt in range(MAX_RETRIES + 1):
                html = fetch_url(page, url, retry=attempt)
                if html is None:
                    # Cloudflare block → new context
                    print("  🔄 Creating new browser context...")
                    try:
                        page.close()
                        context.close()
                    except:
                        pass
                    context = create_context(browser)
                    page = context.new_page()
                    time.sleep(5)
                    continue
                break
            
            if html is None or html == "":
                progress[url] = {"plot": None, "done": True, "error": "cloudflare_block"}
                results["errors"] += 1
                print(f"  ⚠️  Skipped (block/error)")
            else:
                plot = extract_plot(html)
                progress[url] = {"plot": plot, "done": True}
                if plot is not None:
                    results["found"] += 1
                    print(f"  ✅ plot = {plot} m²")
                else:
                    results["not_found"] += 1
                    print(f"  ℹ️  No plot data found")
            
            # Save every N items
            if i % SAVE_EVERY == 0:
                save_progress(progress)
                print(f"  💾 Progress saved ({i} done)")
            
            # Delay between requests
            if i < len(to_fetch):
                time.sleep(DELAY)
        
        page.close()
        context.close()
        browser.close()
    
    # Final save
    save_progress(progress)
    
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print(f"  ✅ Plot found:     {results['found']}")
    print(f"  ℹ️  No plot:        {results['not_found']}")
    print(f"  ❌ Errors/blocked: {results['errors']}")
    print(f"  📝 Total:          {len(to_fetch)}")
    
    # Summary of all fotocasa with plot
    total_with_plot = sum(
        1 for url, val in progress.items()
        if "fotocasa" in url and val.get("plot") is not None
    )
    print(f"\n📈 All fotocasa with plot data: {total_with_plot}")
    
    return results

if __name__ == "__main__":
    test = "--test" in sys.argv
    main(test_mode=test)
