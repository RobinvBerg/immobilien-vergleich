#!/usr/bin/env python3
"""Find correct LivingBlue URLs for Nr.147 (Santa Maria 4.1M) and Nr.203 (Moscari 3.95M)"""
from playwright.sync_api import sync_playwright
import json, time, re
from pathlib import Path

PROXY = {"server": "http://gate.decodo.com:10001", "username": "sp1e6lma32", "password": "pxjc5K6_LBg3Is6vzo"}

collected = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, proxy=PROXY)
    context = browser.new_context(user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36')
    pg = context.new_page()
    
    def on_response(resp):
        if 'egorealestate.com/v1/Properties' in resp.url and resp.status == 200:
            try:
                data = resp.json()
                props = data.get('Properties', [])
                collected.extend(props)
            except:
                pass
    
    pg.on('response', on_response)
    
    for page_num in range(1, 90):
        url = f'https://www.livingblue-mallorca.com/de-de/immobilien?pag={page_num}'
        try:
            pg.goto(url, wait_until='domcontentloaded', timeout=20000)
            time.sleep(3)
        except Exception as e:
            print(f"Seite {page_num}: {e}", flush=True)
            continue
        
        print(f"Seite {page_num}/89: {len(collected)} total", flush=True)
        
        # Check after each page
        for prop in collected[-20:]:
            muni = (prop.get('Municipality') or '').lower()
            title = (prop.get('Title') or '')
            pid = str(prop.get('ID',''))
            rooms = prop.get('Rooms', 0)
            
            price = 0
            if prop.get('Taxes'):
                for t in prop['Taxes']:
                    if t.get('Value'):
                        try: price = int(float(str(t['Value']).replace(',','').replace(' ','')))
                        except: pass
                        break
            
            if 'santa maria' in muni and 3800000 <= price <= 4400000:
                slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:80]
                real_url = f"https://www.livingblue-mallorca.com/de-de/immobilie/{slug}/{pid}"
                print(f"✅ Nr.147 KANDIDAT: {title} | {muni} | {price}€ | {rooms} Zimmer | ID:{pid}", flush=True)
                print(f"   URL: {real_url}", flush=True)
            
            if 'moscari' in muni and 3700000 <= price <= 4200000:
                slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:80]
                real_url = f"https://www.livingblue-mallorca.com/de-de/immobilie/{slug}/{pid}"
                print(f"✅ Nr.203 KANDIDAT: {title} | {muni} | {price}€ | {rooms} Zimmer | ID:{pid}", flush=True)
                print(f"   URL: {real_url}", flush=True)
    
    browser.close()

print(f"\n=== FERTIG: {len(collected)} Objekte gescannt ===", flush=True)

# Final pass over all
print("\n--- Alle Santa Maria / Moscari Objekte ---")
for prop in collected:
    muni = (prop.get('Municipality') or '').lower()
    if 'santa maria' in muni or 'moscari' in muni:
        pid = str(prop.get('ID',''))
        title = prop.get('Title','')
        price = 0
        if prop.get('Taxes'):
            for t in prop['Taxes']:
                if t.get('Value'):
                    try: price = int(float(str(t['Value']).replace(',','').replace(' ','')))
                    except: pass
                    break
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:80]
        real_url = f"https://www.livingblue-mallorca.com/de-de/immobilie/{slug}/{pid}"
        print(f"  {muni} | {price}€ | {prop.get('Rooms')}Z | {title} | {real_url}")
