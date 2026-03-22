#!/usr/bin/env python3
"""Fetch main images for Kensington Nr.401-463 via Camoufox"""
import openpyxl, time, requests
from pathlib import Path
from camoufox.sync_api import Camoufox

BASE = Path('/Users/robin/.openclaw/workspace/mallorca-projekt')
XLSX = BASE / 'data' / 'mallorca-kandidaten-v2.xlsx'
BILDER = BASE / 'bilder'
BILDER.mkdir(exist_ok=True)

# Load URLs for 401-463
wb = openpyxl.load_workbook(XLSX)
ws = wb.active
objects = []
for row in ws.iter_rows(min_row=2, values_only=True):
    nr = row[0]
    if nr and 401 <= nr <= 463:
        objects.append({'nr': nr, 'url': row[2]})
wb.close()

print(f"Objekte zu verarbeiten: {len(objects)}")

with Camoufox(headless=True) as browser:
    page = browser.new_page()
    
    for obj in objects:
        nr = obj['nr']
        url = obj['url']
        out_path = BILDER / f'{nr}_main.jpg'
        
        if out_path.exists():
            print(f"Nr.{nr}: bereits vorhanden, skip")
            continue
        
        if not url:
            print(f"Nr.{nr}: keine URL, skip")
            continue
        
        print(f"Nr.{nr}: lade {url[:60]}...", flush=True)
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=20000)
            time.sleep(2)
            
            # Use picture source srcset (verified working)
            img_url = None
            src_el = page.query_selector('picture source')
            if src_el:
                srcset = src_el.get_attribute('srcset')
                if srcset:
                    img_url = srcset.split(',')[0].strip().split(' ')[0]
            
            # Fallback: picture img src
            if not img_url:
                el = page.query_selector('picture img')
                if el:
                    img_url = el.get_attribute('src')
            
            if img_url:
                if img_url.startswith('/'):
                    img_url = 'https://kensington-international.com' + img_url
                
                r = requests.get(img_url, timeout=15, headers={'Referer': 'https://kensington-international.com/'})
                if r.status_code == 200 and len(r.content) > 5000:
                    out_path.write_bytes(r.content)
                    print(f"  ✅ gespeichert ({len(r.content)//1024}KB)")
                else:
                    print(f"  ❌ Download fehlgeschlagen: {r.status_code}")
            else:
                print(f"  ❌ kein Bild gefunden")
                
        except Exception as e:
            print(f"  ❌ Fehler: {e}")
        
        time.sleep(1)

print("\n=== FERTIG ===")
# Check results
found = sum(1 for o in objects if (BILDER / f"{o['nr']}_main.jpg").exists())
print(f"Bilder vorhanden: {found}/{len(objects)}")
missing = [o['nr'] for o in objects if not (BILDER / f"{o['nr']}_main.jpg").exists()]
if missing:
    print(f"Fehlen noch: {missing}")
