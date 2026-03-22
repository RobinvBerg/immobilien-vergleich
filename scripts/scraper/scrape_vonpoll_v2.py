#!/usr/bin/env python3
"""Von Poll Mallorca scraper v2 — handles Cloudflare via Playwright with proper waiting."""

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


def wait_for_cf(page, url, max_wait=15):
    """Navigate and wait for Cloudflare challenge to pass."""
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=30000)
    except Exception as e:
        print(f"    goto error: {e}")
        return False
    
    # Wait for CF to resolve (up to max_wait seconds)
    start = time.time()
    while time.time() - start < max_wait:
        title = page.title()
        content = page.content()
        # CF challenge titles
        if any(t in title for t in ['Just a moment', 'Nur einen Moment', 'moment', 'Checking']):
            time.sleep(2)
            continue
        # Check if we have actual content
        if len(content) > 50000 or 'von-poll' in content.lower():
            return True
        time.sleep(1)
    
    # Final check
    title = page.title()
    return 'moment' not in title.lower() and 'checking' not in title.lower()


def parse_number(text):
    if not text:
        return None
    text = str(text)
    # Remove non-numeric except . and ,
    text = re.sub(r'[^\d,\.]', '', text)
    # German thousands: 1.234.567
    # Remove dots used as thousands separators (followed by exactly 3 digits)
    while re.search(r'\d\.\d{3}(?:[,\.]|$)', text):
        text = re.sub(r'(\d)\.(\d{3})(?=[,\.]|$)', r'\1\2', text)
    text = text.replace(',', '.')
    m = re.search(r'\d+(?:\.\d+)?', text)
    if m:
        try:
            return float(m.group())
        except:
            return None
    return None


def extract_expose_data(page, url):
    """Extract property data from an expose page."""
    data = {'url': url}
    
    ok = wait_for_cf(page, url, max_wait=20)
    if not ok:
        print(f"    CF challenge not resolved for {url}")
        data['error'] = 'cloudflare'
        return data
    
    # Get title  
    try:
        h1_els = page.locator('h1').all()
        for h1 in h1_els:
            t = h1.text_content()
            if t and t.strip() and t.strip() != 'www.von-poll.com':
                data['title'] = t.strip()
                break
    except:
        pass
    
    if 'title' not in data:
        pt = page.title()
        if pt and 'Von Poll' not in pt and 'von-poll' not in pt:
            data['title'] = pt.split('–')[0].strip()
    
    # Get full page text
    try:
        body_text = page.locator('body').inner_text()
    except:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page.content(), 'html.parser')
        body_text = soup.get_text('\n', strip=True)
    
    content = page.content()
    
    # Debug: save first successful expose
    if 'title' in data and not os.path.exists(f'{DEBUG_DIR}/expose_ok.html'):
        with open(f'{DEBUG_DIR}/expose_ok.html', 'w', encoding='utf-8') as f:
            f.write(content)
        with open(f'{DEBUG_DIR}/expose_ok.txt', 'w', encoding='utf-8') as f:
            f.write(body_text)
    
    # --- JSON-LD ---
    for m in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL):
        try:
            jd = json.loads(m.group(1))
            if isinstance(jd, dict):
                if 'name' in jd and 'title' not in data:
                    data['title'] = jd['name']
                if 'offers' in jd:
                    offers = jd['offers']
                    if isinstance(offers, dict) and 'price' in offers:
                        try:
                            data['price'] = float(offers['price'])
                        except:
                            pass
                if 'address' in jd:
                    addr = jd['address']
                    if isinstance(addr, dict):
                        loc = addr.get('addressLocality') or addr.get('addressRegion') or ''
                        if loc:
                            data['location'] = loc
        except:
            pass
    
    # --- Price ---
    if 'price' not in data:
        patterns = [
            r'Kaufpreis\s*\n?\s*([\d.,]{6,})\s*(?:EUR|€|Euro)',
            r'([\d.,]{6,})\s*(?:EUR|€)',
            r'(?:EUR|€)\s*([\d.,]{6,})',
        ]
        for pat in patterns:
            m = re.search(pat, body_text)
            if m:
                val = parse_number(m.group(1))
                if val and 100_000 < val < 100_000_000:
                    data['price'] = val
                    break
    
    # --- Rooms ---
    patterns = [
        r'(\d+(?:[,.]\d+)?)\s*Zimmer',
        r'Zimmer\s*[:\-]\s*(\d+(?:[,.]\d+)?)',
        r'(\d+(?:[,.]\d+)?)\s*Räume',
    ]
    for pat in patterns:
        m = re.search(pat, body_text, re.I)
        if m:
            val = parse_number(m.group(1))
            if val and 0 < val < 50:
                data['rooms'] = val
                break
    
    # --- Plot ---
    patterns = [
        r'Grundst[üu]cksfläche\s*\n?\s*([\d.,]+)\s*m[²2]',
        r'Grundst[üu]ck\s*[:\-]\s*([\d.,]+)\s*m[²2]',
        r'([\d.,]+)\s*m[²2]\s*Grundst[üu]ck',
        r'Grundstück\s*\n\s*([\d.,]+)',
    ]
    for pat in patterns:
        m = re.search(pat, body_text, re.I)
        if m:
            val = parse_number(m.group(1))
            if val and 0 < val < 10_000_000:
                data['plot_m2'] = val
                break
    
    # --- Location ---
    if 'location' not in data:
        # Try to extract from URL
        url_m = re.search(r'/de/expose/mallorca-([^/]+)/', url)
        if url_m:
            office_from_url = url_m.group(1).replace('-', ' ').title()
            data['location_hint'] = office_from_url
        
        patterns = [
            r'Ort\s*\n\s*([^\n]{3,50})',
            r'Standort\s*\n\s*([^\n]{3,50})',
            r'Lage\s*[:\-]\s*([^\n,]{3,50})',
        ]
        for pat in patterns:
            m = re.search(pat, body_text, re.I)
            if m:
                loc = m.group(1).strip()
                if loc and 'mallorca' not in loc.lower() and len(loc) > 2:
                    data['location'] = loc[:60]
                    break
    
    # --- Type ---
    kws = ['Finca', 'Landhaus', 'Landsitz', 'Landgut', 'Agroturismo', 
           'Villa', 'Haus', 'Apartment', 'Wohnung', 'Stadthaus', 
           'Penthouse', 'Townhouse', 'Reihenhaus', 'Doppelhaus']
    title_low = data.get('title', '').lower()
    url_low = url.lower()
    for kw in kws:
        if kw.lower() in title_low or kw.lower() in url_low:
            data['obj_type'] = kw
            break
    
    return data


def get_expose_urls_from_page(page, url, office_name):
    """Get all expose URLs from an office listing page."""
    print(f"\n  [{office_name}] Fetching: {url}")
    
    ok = wait_for_cf(page, url, max_wait=20)
    if not ok:
        print(f"    CF not resolved!")
        return {}
    
    content = page.content()
    
    # Save debug
    with open(f'{DEBUG_DIR}/listing_{office_name.lower().replace(" ", "_")}.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    expose_links = re.findall(r'href="(/de/expose/[^"?#]+)"', content)
    unique = list(dict.fromkeys(expose_links))
    
    result = {}
    for link in unique:
        full_url = 'https://www.von-poll.com' + link
        result[full_url] = office_name
    
    print(f"    Found {len(result)} unique expose URLs")
    return result


def is_rural(data):
    title = (data.get('title', '') + ' ' + data.get('obj_type', '') + ' ' + data.get('url', '')).lower()
    
    exclude = ['apartment', 'wohnung', 'stadthaus', 'townhouse', 'penthouse', 'piso', 'reihenhaus', 'doppelhaus', 'etagenwohnung']
    for kw in exclude:
        if kw in title:
            return False
    
    rural = ['finca', 'landhaus', 'landsitz', 'landgut', 'agroturismo', 'rustico', 'rustica', 'country', 'herrenhaus', 'herrenhau', 'gutshaus']
    for kw in rural:
        if kw in title:
            return True
    
    plot = data.get('plot_m2', 0) or 0
    if plot >= 3000:
        return True
    
    return None


def passes_filter(data):
    """Returns (pass: bool, reasons_fail: list)."""
    fails = []
    price = data.get('price')
    rooms = data.get('rooms')
    plot = data.get('plot_m2', 0) or 0
    
    if price is not None:
        if price < 2_000_000:
            fails.append(f"Preis {price/1e6:.2f}M < 2M")
        elif price > 20_000_000:
            fails.append(f"Preis {price/1e6:.2f}M > 20M")
    
    if rooms is not None and rooms < 5:
        fails.append(f"Zimmer {rooms} < 5")
    
    if plot > 0 and plot < 3000:
        fails.append(f"Grundstück {plot:,.0f} m² < 3.000")
    
    return len(fails) == 0, fails


def main():
    all_expose_urls = {}  # url -> office
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            proxy=PROXY,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
            ]
        )
        ctx = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            locale='de-DE',
            viewport={'width': 1280, 'height': 900},
            extra_http_headers={
                'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            }
        )
        
        # Disable webdriver flag
        ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = ctx.new_page()
        
        print("="*60)
        print("PHASE 1: Listing pages — collecting expose URLs")
        print("="*60)
        
        for office_name, office_url in OFFICES.items():
            exposes = get_expose_urls_from_page(page, office_url, office_name)
            for url, off in exposes.items():
                if url not in all_expose_urls:
                    all_expose_urls[url] = off
                else:
                    existing = all_expose_urls[url]
                    if off not in existing:
                        all_expose_urls[url] = existing + f', {off}'
            time.sleep(2)
        
        print(f"\nTotal unique URLs: {len(all_expose_urls)}")
        
        # Save URL list
        with open(f'{DATA_DIR}/vonpoll_urls.json', 'w', encoding='utf-8') as f:
            json.dump(all_expose_urls, f, ensure_ascii=False, indent=2)
        
        # Phase 2: scrape exposes
        print("\n" + "="*60)
        print(f"PHASE 2: Scraping {len(all_expose_urls)} expose pages")
        print("="*60)
        
        results = []
        errors = 0
        
        for i, (url, office) in enumerate(all_expose_urls.items()):
            print(f"\n[{i+1}/{len(all_expose_urls)}] {office}")
            print(f"  {url}")
            
            data = extract_expose_data(page, url)
            data['office'] = office
            results.append(data)
            
            if data.get('error'):
                errors += 1
                print(f"  ❌ Error: {data['error']}")
            else:
                print(f"  ✅ Title: {data.get('title', 'n/a')[:60]}")
                print(f"     Price: {data.get('price', 'n/a')} | Rooms: {data.get('rooms', 'n/a')} | Plot: {data.get('plot_m2', 'n/a')} m²")
            
            time.sleep(1.5)
        
        browser.close()
    
    print(f"\nErrors: {errors}/{len(results)}")
    
    # Save raw
    with open(f'{DATA_DIR}/vonpoll_raw_v2.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Filter
    print("\n" + "="*60)
    print("PHASE 3: Filtering")
    print("="*60)
    
    matched = []
    skipped_rural = []
    skipped_criteria = []
    no_data = []
    
    for r in results:
        if r.get('error'):
            no_data.append(r)
            continue
        
        rural = is_rural(r)
        if rural is False:
            skipped_rural.append(r)
            continue
        
        ok, fails = passes_filter(r)
        if not ok:
            skipped_criteria.append((r, fails))
            continue
        
        matched.append(r)
    
    print(f"✅ Matches (incl. unknowns): {len(matched)}")
    print(f"❌ Skipped urban type: {len(skipped_rural)}")
    print(f"❌ Skipped criteria: {len(skipped_criteria)}")
    print(f"⚠️  No data (CF error): {len(no_data)}")
    
    with open(f'{DATA_DIR}/vonpoll_filtered_v2.json', 'w', encoding='utf-8') as f:
        json.dump(matched, f, ensure_ascii=False, indent=2)
    
    # Output
    print("\n" + "="*80)
    print("ERGEBNISSE — Von Poll Mallorca")
    print("Filter: ≥5 Zimmer | ≥3.000 m² Grundstück | 2–20 Mio. € | Ländlich")
    print("="*80)
    
    for i, r in enumerate(matched, 1):
        price = r.get('price')
        rooms = r.get('rooms')
        plot = r.get('plot_m2')
        
        price_str = f"{price/1_000_000:.2f} Mio. €" if price else '–'
        rooms_str = str(int(rooms)) if rooms and rooms == int(rooms) else (f"{rooms}" if rooms else '–')
        plot_str = f"{int(plot):,} m²".replace(',', '.') if plot else '–'
        loc_str = r.get('location') or r.get('location_hint') or '–'
        
        print(f"\n{'─'*72}")
        print(f"#{i:02d} | Büro: {r.get('office', '–')}")
        print(f"Titel:      {r.get('title', '–')}")
        print(f"Ort:        {loc_str}")
        print(f"Typ:        {r.get('obj_type', '–')}")
        print(f"Preis:      {price_str}")
        print(f"Zimmer:     {rooms_str}")
        print(f"Grundstück: {plot_str}")
        print(f"URL:        {r.get('url', '–')}")
    
    print(f"\n{'='*80}")
    print(f"GESAMT: {len(matched)} Treffer von {len(results)} gescrapten Objekten")
    print(f"{'='*80}")
    
    if no_data:
        print(f"\n⚠️  {len(no_data)} Objekte konnten nicht geladen werden (Cloudflare):")
        for r in no_data[:10]:
            print(f"  {r.get('url', '?')}")
    
    return matched


if __name__ == '__main__':
    main()
