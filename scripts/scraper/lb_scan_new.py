#!/usr/bin/env python3
"""Scannt LivingBlue Mallorca und findet neue Objekte vs. mallorca-kandidaten-v2.xlsx"""
import json, time, re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import openpyxl

BASE_DIR = Path('/Users/robin/.openclaw/workspace/mallorca-projekt')
XLSX_PATH = BASE_DIR / 'data' / 'mallorca-kandidaten-v2.xlsx'
OUTPUT_JSON = BASE_DIR / 'data' / 'lb_all_cards.json'

PROXY = {
    "server": "http://gate.decodo.com:10001",
    "username": "sp1e6lma32",
    "password": "pxjc5K6_LBg3Is6vzo"
}

# Bestehende URLs aus xlsx laden (Spalte C = Index 2)
wb = openpyxl.load_workbook(XLSX_PATH, read_only=True)
ws = wb.active
existing_urls = set()
headers = None
for i, row in enumerate(ws.iter_rows(values_only=True)):
    if i == 0:
        headers = list(row)
        print(f"Headers: {headers[:5]}")
        continue
    if row[2]:  # Spalte C
        existing_urls.add(str(row[2]).strip().rstrip('/'))
wb.close()

print(f"Bestehende URLs in xlsx: {len(existing_urls)}")

all_cards = []

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        proxy=PROXY
    )
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    )
    page = context.new_page()
    
    for pg in range(1, 100):
        url = f"https://www.livingblue-mallorca.com/de-de/immobilien?pag={pg}"
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(2500)
        except Exception as e:
            print(f"Seite {pg} Error: {e}, weiter...")
            continue
        
        cards = page.evaluate("""() => {
            const results = [];
            const infoLinks = document.querySelectorAll('a[href*="/immobilie/"]');
            const seen = new Set();
            infoLinks.forEach(link => {
                const href = link.href.split('?')[0].replace(/\\/$/, '');
                if(seen.has(href)) return;
                seen.add(href);
                const container = link.closest('li') || link.closest('article') || link.closest('.property-card') || link.parentElement?.parentElement?.parentElement;
                const text = (container?.textContent || link.closest('body')?.textContent || '').replace(/\\s+/g,' ').trim();
                const priceMatch = text.match(/([\\d\\.]+)\\s*€|€\\s*([\\d\\.]+)/);
                const price = priceMatch ? priceMatch[0] : '';
                const roomMatch = text.match(/(\\d+)\\s*(Schlafzimmer|Zimmer|bed)/i);
                const rooms = roomMatch ? roomMatch[1] : '';
                const imgEl = container?.querySelector('img');
                const titleEl = container?.querySelector('h2,h3,h4,.title,.name');
                results.push({
                    href,
                    price,
                    rooms,
                    title: titleEl?.textContent?.trim() || '',
                    img: imgEl?.src || ''
                });
            });
            return results;
        }""")
        
        if not cards:
            print(f"Seite {pg}: Keine Cards gefunden — Ende des Listings")
            break
        
        all_cards.extend(cards)
        print(f"Seite {pg} — {len(cards)} Cards — Total: {len(all_cards)}", flush=True)
        time.sleep(0.5)
    
    browser.close()

# Deduplizieren
seen = set()
unique_cards = []
for c in all_cards:
    if c['href'] not in seen and c['href']:
        seen.add(c['href'])
        unique_cards.append(c)

print(f"\nGesamt unique Cards: {len(unique_cards)}")

# Neue finden
new_cards = []
for c in unique_cards:
    href_norm = c['href'].rstrip('/')
    if href_norm not in existing_urls and href_norm + '/' not in existing_urls:
        new_cards.append(c)

print(f"Neue Objekte (nicht in xlsx): {len(new_cards)}")
print("\n" + "="*60)
print("NEUE OBJEKTE:")
print("="*60)
for i, c in enumerate(new_cards, 1):
    print(f"\n{i}. {c.get('title') or '(kein Titel)'}")
    print(f"   URL:   {c['href']}")
    print(f"   Preis: {c.get('price') or '–'}")
    print(f"   Zimmer: {c.get('rooms') or '–'}")

# JSON speichern
OUTPUT_JSON.write_text(json.dumps(unique_cards, indent=2, ensure_ascii=False))
print(f"\nAlle Cards gespeichert: {OUTPUT_JSON}")

new_json = BASE_DIR / 'data' / 'lb_new_objects.json'
new_json.write_text(json.dumps(new_cards, indent=2, ensure_ascii=False))
print(f"Neue Objekte gespeichert: {new_json}")
