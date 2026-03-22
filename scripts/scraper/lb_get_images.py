#!/usr/bin/env python3
"""Holt Thumbnails für alle 113 LivingBlue UUIDs via egorealestate API"""
from playwright.sync_api import sync_playwright
import json, requests, os, time, openpyxl

wb = openpyxl.load_workbook('mallorca-kandidaten-v2.xlsx', read_only=True)
ws = wb.active
headers = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
lb_entries = []
for row in ws.iter_rows(min_row=2, values_only=True):
    if not any(row): continue
    r = dict(zip(headers, row))
    if r.get('Makler') and 'living' in str(r.get('Makler','')).lower():
        uuid = (r.get('Link Objekt (URL)') or '').rstrip('/').split('/')[-1]
        if uuid:
            lb_entries.append({'nr': r['Ordnungsnummer'], 'uuid': uuid})

print(f"Verarbeite {len(lb_entries)} LivingBlue Objekte")
os.makedirs('bilder', exist_ok=True)

results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    
    for i, entry in enumerate(lb_entries):
        nr = entry['nr']
        uuid = entry['uuid']
        out_path = f"bilder/{nr}_main.jpg"
        
        # Skip wenn schon vorhanden (und nicht Platzhalter)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 50000:
            print(f"[{i+1}/{len(lb_entries)}] Nr.{nr} — bereits vorhanden, skip")
            results.append({'nr': nr, 'status': 'skip'})
            continue
        
        page = browser.new_page()
        thumb_box = [None]
        
        def on_response(resp):
            if 'websiteapi.egorealestate.com/v1/Properties' in resp.url:
                try:
                    data = resp.json()
                    props = data.get('Properties', [])
                    if props:
                        thumb_box[0] = props[0].get('Thumbnail')
                except: pass
        
        page.on('response', on_response)
        
        try:
            page.goto(f"https://www.livingblue-mallorca.com/de-de/immobilien/{uuid}",
                     wait_until='domcontentloaded', timeout=15000)
            page.wait_for_timeout(3000)
        except Exception as e:
            print(f"[{i+1}] Nr.{nr} — Timeout: {e}")
        finally:
            page.close()
        
        if thumb_box[0] and 'images.egorealestate.com' in thumb_box[0]:
            try:
                resp = requests.get(thumb_box[0], timeout=10)
                if resp.status_code == 200 and len(resp.content) > 10000:
                    with open(out_path, 'wb') as f:
                        f.write(resp.content)
                    print(f"[{i+1}/{len(lb_entries)}] Nr.{nr} ✅ {len(resp.content)//1024}KB → {thumb_box[0][-50:]}")
                    results.append({'nr': nr, 'status': 'ok', 'url': thumb_box[0]})
                else:
                    print(f"[{i+1}/{len(lb_entries)}] Nr.{nr} ❌ Download fehlgeschlagen ({resp.status_code})")
                    results.append({'nr': nr, 'status': 'fail'})
            except Exception as e:
                print(f"[{i+1}/{len(lb_entries)}] Nr.{nr} ❌ {e}")
                results.append({'nr': nr, 'status': 'error'})
        else:
            print(f"[{i+1}/{len(lb_entries)}] Nr.{nr} ❌ Kein Thumbnail (uuid={uuid[:20]}...)")
            results.append({'nr': nr, 'status': 'no_thumbnail', 'uuid': uuid})
    
    browser.close()

ok = sum(1 for r in results if r['status'] == 'ok')
fail = sum(1 for r in results if r['status'] not in ('ok', 'skip'))
print(f"\n✅ {ok} Bilder heruntergeladen | ❌ {fail} fehlgeschlagen")
with open('lb_results.json', 'w') as f:
    json.dump(results, f, indent=2)
