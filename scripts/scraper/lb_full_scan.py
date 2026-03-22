#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import json, re, time
from pathlib import Path
import openpyxl

BASE_DIR = Path('/Users/robin/.openclaw/workspace/mallorca-projekt')
XLSX_PATH = BASE_DIR / 'data' / 'mallorca-kandidaten-v2.xlsx'

# Load existing IDs
wb = openpyxl.load_workbook(XLSX_PATH, read_only=True)
ws = wb.active
existing_ids = set()
for i, row in enumerate(ws.iter_rows(values_only=True)):
    if i == 0:
        continue
    if row[2]:
        m = re.search(r'/(\d{5,})(?:/|$|\?)', str(row[2]))
        if m:
            existing_ids.add(m.group(1))
wb.close()
print(f"Bestehende IDs in xlsx: {len(existing_ids)}")

PROXY = {"server": "http://gate.decodo.com:10001", "username": "sp1e6lma32", "password": "pxjc5K6_LBg3Is6vzo"}

all_props = {}
total_records = [0]
PAGES = 89

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, proxy=PROXY)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
    )
    pg = context.new_page()
    
    pending = {}

    def on_response(resp):
        if 'egorealestate.com/v1/Properties' in resp.url and resp.status == 200:
            try:
                data = resp.json()
                m2 = re.search(r'pag=(\d+)', resp.url)
                pg_num = int(m2.group(1)) if m2 else 0
                props = data.get('Properties', [])
                if props:  # Only update if we got actual data
                    pending[pg_num] = props
                if data.get('TotalRecords'):
                    total_records[0] = data['TotalRecords']
            except:
                pass

    pg.on('response', on_response)

    for page_num in range(1, PAGES + 1):
        url = f'https://www.livingblue-mallorca.com/de-de/immobilien?pag={page_num}'
        try:
            pg.goto(url, wait_until='networkidle', timeout=30000)
            pg.wait_for_timeout(2000)
        except Exception as e:
            print(f"Seite {page_num}: {e}")
            continue

        props = pending.get(page_num, [])
        for prop in props:
            pid = str(prop.get('ID', ''))
            if pid:
                all_props[pid] = prop

        print(f"Seite {page_num}/{PAGES}: {len(props)} Objekte → gesamt unique: {len(all_props)}", flush=True)

        if len(props) == 0 and page_num > 5:
            print("Keine Objekte mehr, breche ab")
            break

    browser.close()

print(f"\nGesamt unique Objekte gescannt: {len(all_props)}")
print(f"Total laut API: {total_records[0]}")

# Find new objects
new_props = []
for pid, prop in all_props.items():
    if pid not in existing_ids:
        slug = re.sub(r'[^a-z0-9]+', '-', (prop.get('Title') or '').lower()).strip('-')[:80]
        url = f"https://www.livingblue-mallorca.com/de-de/immobilie/{slug}/{pid}" if slug else f"https://www.livingblue-mallorca.com/de-de/immobilie/{pid}"
        price = ''
        if prop.get('Taxes'):
            for t in prop['Taxes']:
                if t.get('Value'):
                    price = t['Value']
                    break
        new_props.append({
            'id': pid,
            'title': prop.get('Title', ''),
            'url': url,
            'price': price,
            'rooms': prop.get('Rooms', ''),
            'bathrooms': prop.get('Bathrooms', ''),
            'municipality': prop.get('Municipality', ''),
            'type': prop.get('Type', ''),
            'area_gross': prop.get('GrossArea', ''),
        })

print(f"Neue Objekte (nicht in xlsx): {len(new_props)}")
print("\n" + "="*70)
for i, p_obj in enumerate(new_props, 1):
    print(f"\n{i:3}. {p_obj['title']}")
    print(f"     URL:    {p_obj['url']}")
    print(f"     Preis:  {p_obj['price']}")
    print(f"     Zimmer: {p_obj['rooms']} | Bäder: {p_obj['bathrooms']} | Typ: {p_obj['type']}")
    print(f"     Ort:    {p_obj['municipality']} | Fläche: {p_obj['area_gross']} m²")

(BASE_DIR / 'data' / 'lb_new_objects.json').write_text(json.dumps(new_props, indent=2, ensure_ascii=False))
(BASE_DIR / 'data' / 'lb_all_scraped.json').write_text(json.dumps(list(all_props.values()), indent=2, ensure_ascii=False))
print(f"\nSaved: lb_new_objects.json ({len(new_props)} neue), lb_all_scraped.json ({len(all_props)} gesamt)")
