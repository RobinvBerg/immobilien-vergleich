#!/usr/bin/env python3
"""Scrape Von Poll Mallorca listings via Playwright (bypasses Cloudflare)."""

from playwright.sync_api import sync_playwright
import json
import re
import time
import os

PROXY = {
    'server': 'http://gate.decodo.com:10001',
    'username': 'sp1e6lma32',
    'password': 'pxjc5K6_LBg3Is6vzo'
}

OFFICES = {
    "Santa Maria": "https://www.von-poll.com/de/immobilienmakler/mallorca-santa-maria",
    "Andratx": "https://www.von-poll.com/de/immobilienmakler/mallorca-andratx",
    "Paguera": "https://www.von-poll.com/de/immobilienmakler/mallorca-paguera",
    "Llucmajor": "https://www.von-poll.com/de/immobilienmakler/mallorca-llucmajor",
    "Pollensa": "https://www.von-poll.com/de/immobilienmakler/mallorca-pollensa",
}

DEBUG_DIR = '/Users/robin/.openclaw/workspace/mallorca-projekt/debug'
DATA_DIR = '/Users/robin/.openclaw/workspace/mallorca-projekt/data'
os.makedirs(DEBUG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)


def parse_number(text):
    if not text:
        return None
    text = str(text)
    # Remove thousands separators (dots in German), keep decimal comma->dot
    text = re.sub(r'[^\d,\.]', '', text)
    # German: 1.234.567 or 1.234.567,00
    # Remove dots that are thousands sep (followed by 3 digits)
    text = re.sub(r'\.(?=\d{3})', '', text)
    text = text.replace(',', '.')
    m = re.search(r'\d+(?:\.\d+)?', text)
    if m:
        try:
            return float(m.group())
        except:
            return None
    return None


def extract_details_from_expose(page, url):
    """Navigate to expose page and extract all details."""
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=45000)
        time.sleep(1)
    except Exception as e:
        print(f"    Error loading {url}: {e}")
        return {}

    content = page.content()
    data = {'url': url}

    # Save first expose for debugging
    if not os.path.exists(f'{DEBUG_DIR}/expose_sample.html'):
        with open(f'{DEBUG_DIR}/expose_sample.html', 'w', encoding='utf-8') as f:
            f.write(content)

    # Title from h1
    try:
        h1 = page.locator('h1').first.text_content(timeout=3000)
        if h1:
            data['title'] = h1.strip()
    except:
        pass

    # Try JSON-LD
    scripts = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL)
    for s in scripts:
        try:
            jd = json.loads(s)
            if isinstance(jd, dict):
                if 'name' in jd and 'title' not in data:
                    data['title'] = jd['name']
                if 'offers' in jd:
                    offers = jd['offers']
                    if isinstance(offers, dict) and 'price' in offers:
                        data['price'] = float(offers['price'])
                if 'address' in jd:
                    addr = jd['address']
                    if isinstance(addr, dict):
                        loc = addr.get('addressLocality') or addr.get('addressRegion') or ''
                        if loc:
                            data['location'] = loc
        except:
            pass

    # Full text for regex extraction
    text = page.inner_text('body') if page.url else ''
    if not text:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text(' ', strip=True)

    # --- Price ---
    if 'price' not in data:
        # Patterns: "2.500.000 €" or "€ 2.500.000" or "Kaufpreis: 2.500.000 €"
        price_patterns = [
            r'Kaufpreis[^\d]*?(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)\s*(?:EUR|€)',
            r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*(?:EUR|€)',
            r'(?:EUR|€)\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)',
            r'Preis[^\d]*?(\d{1,3}(?:[.,]\d{3})*)',
        ]
        for pat in price_patterns:
            m = re.search(pat, text, re.I)
            if m:
                val = parse_number(m.group(1))
                if val and val > 100000:  # sanity check
                    data['price'] = val
                    break

    # --- Rooms ---
    room_patterns = [
        r'(\d+(?:[,\.]\d+)?)\s+Zimmer',
        r'Zimmer\s*[:\-]?\s*(\d+(?:[,\.]\d+)?)',
        r'(\d+(?:[,\.]\d+)?)\s+Räume',
        r'Anzahl\s+Zimmer\s*[:\-]?\s*(\d+)',
    ]
    for pat in room_patterns:
        m = re.search(pat, text, re.I)
        if m:
            val = parse_number(m.group(1))
            if val and val > 0:
                data['rooms'] = val
                break

    # --- Plot size ---
    plot_patterns = [
        r'Grundst[üu]cksfläche\s*[:\-]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*m[²2]',
        r'Grundst[üu]ck\s*[:\-]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*m[²2]',
        r'Grundst[üu]ck\s*[:\-]?\s*ca\.\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*m[²2]',
        r'Grundstück[sfläche]*[:\s]*(\d[\d.,]*)\s*m',
        r'(\d{4,6})\s*m[²2]\s*(?:Grundst|Garten|Grund)',
    ]
    for pat in plot_patterns:
        m = re.search(pat, text, re.I)
        if m:
            val = parse_number(m.group(1))
            if val and val > 0:
                data['plot_m2'] = val
                break

    # --- Location ---
    if 'location' not in data:
        loc_patterns = [
            r'Ort\s*[:\-]\s*([^\n\r,]{3,50})',
            r'Standort\s*[:\-]\s*([^\n\r,]{3,50})',
            r'Lage\s*[:\-]\s*([^\n\r,]{3,50})',
            r'(?:Mallorca|Mallorca,)\s+([A-Z][a-züäöÜÄÖ\s\-]{2,40})',
        ]
        for pat in loc_patterns:
            m = re.search(pat, text, re.I)
            if m:
                loc = m.group(1).strip()
                if len(loc) > 2 and 'mallorca' not in loc.lower():
                    data['location'] = loc[:60]
                    break

    # --- Object type from title/text ---
    type_kws = ['Finca', 'Landhaus', 'Landsitz', 'Landgut', 'Agroturismo', 
                'Villa', 'Haus', 'Apartment', 'Wohnung', 'Stadthaus', 
                'Penthouse', 'Townhouse', 'Reihenhaus']
    combined = (data.get('title', '') + ' ' + text[:500]).lower()
    for kw in type_kws:
        if kw.lower() in combined:
            data['obj_type'] = kw
            break

    # Try to get title from page title if missing
    if 'title' not in data:
        try:
            pt = page.title()
            if pt and 'Von Poll' not in pt:
                data['title'] = pt.split('–')[0].strip()
        except:
            pass

    return data


def get_expose_urls_from_page(page, url, office_name):
    """Get all expose URLs from a listing page."""
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=45000)
        time.sleep(2)
    except Exception as e:
        print(f"  Error loading {url}: {e}")
        return {}

    content = page.content()
    
    # Save for debug
    safe_name = office_name.lower().replace(' ', '_')
    with open(f'{DEBUG_DIR}/page_{safe_name}.html', 'w', encoding='utf-8') as f:
        f.write(content)

    # Extract expose links
    expose_links = re.findall(r'href="(/de/expose/[^"?#]+)"', content)
    unique_links = list(dict.fromkeys(expose_links))  # preserve order, deduplicate
    
    result = {}
    for link in unique_links:
        full_url = 'https://www.von-poll.com' + link
        result[full_url] = office_name
    
    print(f"  [{office_name}] Found {len(result)} unique exposes on {page.url}")
    return result


def get_all_expose_urls_with_pagination(page, base_url, office_name):
    """Get exposes from all pages of a listing."""
    all_exposes = {}
    
    # Page 1
    exposes = get_expose_urls_from_page(page, base_url, office_name)
    all_exposes.update(exposes)
    
    # Check for pagination
    for page_num in range(2, 20):
        # Try common pagination patterns
        content = page.content()
        
        # Look for next page link
        next_links = re.findall(r'href="([^"]*(?:page|seite|p)=' + str(page_num) + r'[^"]*)"', content, re.I)
        if not next_links:
            # Try URL-based pagination
            if '?' in base_url:
                paged_url = base_url + f'&page={page_num}'
            else:
                paged_url = base_url + f'?page={page_num}'
            
            # Check if there's actually a next page indicator
            has_next = bool(re.search(r'(?:class|aria)[^>]*(?:next|weiter|›|»)', content, re.I))
            if not has_next and page_num > 2:
                break
                
            new_exposes = get_expose_urls_from_page(page, paged_url, office_name)
            if not new_exposes or all(url in all_exposes for url in new_exposes):
                break
            all_exposes.update(new_exposes)
        else:
            new_exposes = get_expose_urls_from_page(page, 'https://www.von-poll.com' + next_links[0], office_name)
            if not new_exposes:
                break
            all_exposes.update(new_exposes)
    
    return all_exposes


def is_rural(data):
    """True if rural, False if explicitly urban, None if unknown."""
    title = (data.get('title', '') + ' ' + data.get('obj_type', '')).lower()
    url = data.get('url', '').lower()
    
    exclude = ['apartment', 'wohnung', 'stadthaus', 'townhouse', 'penthouse', 'piso', 'erdgeschoss']
    for kw in exclude:
        if kw in title or kw in url:
            return False
    
    rural = ['finca', 'landhaus', 'landsitz', 'landgut', 'agroturismo', 'rustico', 'rustica', 'country', 'ländlich']
    for kw in rural:
        if kw in title or kw in url:
            return True
    
    # Big plot suggests rural
    plot = data.get('plot_m2', 0) or 0
    if plot >= 3000:
        return True
    
    return None  # unknown


def matches_profile(data):
    """Check search profile criteria."""
    reasons_fail = []
    
    price = data.get('price')
    rooms = data.get('rooms')
    plot = data.get('plot_m2', 0) or 0
    
    if price is not None:
        if price < 2_000_000:
            reasons_fail.append(f"Preis zu niedrig: {price/1e6:.2f}M")
        elif price > 20_000_000:
            reasons_fail.append(f"Preis zu hoch: {price/1e6:.2f}M")
    
    if rooms is not None and rooms < 5:
        reasons_fail.append(f"Zu wenig Zimmer: {rooms}")
    
    if plot > 0 and plot < 3000:
        reasons_fail.append(f"Grundstück zu klein: {plot:,.0f} m²")
    
    return reasons_fail


def main():
    all_expose_urls = {}  # url -> office_name
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            proxy=PROXY,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )
        ctx = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            locale='de-DE',
            viewport={'width': 1280, 'height': 900},
        )
        page = ctx.new_page()

        # Step 1: Collect expose URLs from all 5 office pages
        print("=" * 60)
        print("PHASE 1: Collecting expose URLs from all offices")
        print("=" * 60)
        
        for office_name, office_url in OFFICES.items():
            exposes = get_all_expose_urls_with_pagination(page, office_url, office_name)
            for url, off in exposes.items():
                if url not in all_expose_urls:
                    all_expose_urls[url] = off
                else:
                    # Already exists — add office if different
                    existing = all_expose_urls[url]
                    if off not in existing:
                        all_expose_urls[url] = existing + f', {off}'
            time.sleep(1)
        
        print(f"\nTotal unique expose URLs: {len(all_expose_urls)}")
        
        # Also check the main Mallorca immobilien page
        print("\n[Mallorca Main] Trying additional pages...")
        # The redirect goes to /de/immobilien-mallorca — let's use that
        mallorca_pages = [
            'https://www.von-poll.com/de/immobilien-mallorca',
        ]
        for murl in mallorca_pages:
            exposes = get_expose_urls_from_page(page, murl, 'Mallorca-Übersicht')
            for url, off in exposes.items():
                if url not in all_expose_urls:
                    all_expose_urls[url] = off
        
        # Save URL list
        with open(f'{DATA_DIR}/vonpoll_urls.json', 'w') as f:
            json.dump(all_expose_urls, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(all_expose_urls)} URLs to {DATA_DIR}/vonpoll_urls.json")
        
        # Step 2: Scrape each expose
        print("\n" + "=" * 60)
        print(f"PHASE 2: Scraping {len(all_expose_urls)} expose pages")
        print("=" * 60)
        
        results = []
        for i, (url, office) in enumerate(all_expose_urls.items()):
            print(f"\n[{i+1}/{len(all_expose_urls)}] {office} | {url}")
            details = extract_details_from_expose(page, url)
            details['office'] = office
            if 'url' not in details:
                details['url'] = url
            results.append(details)
            
            # Quick preview
            print(f"    Title: {details.get('title', 'n/a')[:60]}")
            print(f"    Price: {details.get('price', 'n/a')} | Rooms: {details.get('rooms', 'n/a')} | Plot: {details.get('plot_m2', 'n/a')} m²")
            
            time.sleep(0.8)
        
        browser.close()
    
    # Save raw
    with open(f'{DATA_DIR}/vonpoll_raw.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nRaw data saved: {len(results)} properties")
    
    # Step 3: Filter
    print("\n" + "=" * 60)
    print("PHASE 3: Filtering")
    print("=" * 60)
    
    filtered = []
    skipped_type = []
    skipped_criteria = []
    unknown_data = []
    
    for r in results:
        rural = is_rural(r)
        fail_reasons = matches_profile(r)
        
        if rural is False:
            skipped_type.append(r)
            continue
        
        if fail_reasons:
            skipped_criteria.append((r, fail_reasons))
            continue
        
        # If rural is None (unknown) but no criteria failures, keep for review
        filtered.append(r)
    
    print(f"✅ Matching/Unknown-type: {len(filtered)}")
    print(f"❌ Skipped (type): {len(skipped_type)}")
    print(f"❌ Skipped (criteria): {len(skipped_criteria)}")
    
    # Save filtered
    with open(f'{DATA_DIR}/vonpoll_filtered.json', 'w', encoding='utf-8') as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)
    
    # Final output
    print("\n" + "=" * 80)
    print("ERGEBNISSE — Von Poll Mallorca (Suchprofil: 5+ Zimmer, 3000+ m², 2-20 Mio. €, ländlich)")
    print("=" * 80)
    
    for i, r in enumerate(filtered, 1):
        price = r.get('price')
        rooms = r.get('rooms')
        plot = r.get('plot_m2')
        
        price_str = f"{price/1_000_000:.2f} Mio. €" if price else 'Preis: n/a'
        rooms_str = str(int(rooms)) if rooms and rooms == int(rooms) else (str(rooms) if rooms else 'n/a')
        plot_str = f"{int(plot):,} m²".replace(',', '.') if plot else 'n/a'
        
        print(f"\n{'─'*70}")
        print(f"#{i} | {r.get('office', 'n/a')}")
        print(f"Titel:      {r.get('title', 'n/a')}")
        print(f"Ort:        {r.get('location', 'n/a')}")
        print(f"Preis:      {price_str}")
        print(f"Zimmer:     {rooms_str}")
        print(f"Grundstück: {plot_str}")
        print(f"Typ:        {r.get('obj_type', 'n/a')}")
        print(f"URL:        {r.get('url', 'n/a')}")
    
    print(f"\n{'='*80}")
    print(f"GESAMT: {len(filtered)} passende Objekte (von {len(results)} gescrapt)")
    print(f"{'='*80}")
    
    return filtered


if __name__ == '__main__':
    main()
