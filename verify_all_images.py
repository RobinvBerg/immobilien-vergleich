#!/usr/bin/env python3
"""
Verifiziert alle 332 Bilder: lädt aktuelles Hauptbild von der URL,
vergleicht Hash mit unserem gespeicherten Bild.
"""
import os, json, hashlib, requests, openpyxl
from playwright.sync_api import sync_playwright
from collections import defaultdict

def md5(p):
    with open(p,'rb') as f: return hashlib.md5(f.read()).hexdigest()

def get_main_image(page, url, makler):
    """Lädt Hauptbild je nach Makler-Typ"""
    makler = makler.lower()
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=20000)
        page.wait_for_timeout(3000)

        if 'living' in makler:
            imgs = page.evaluate("""()=>Array.from(document.querySelectorAll('img[src*="images.egorealestate"]'))
                .filter(i=>i.src.includes('Z800')||i.src.includes('Z1280'))
                .sort((a,b)=>parseInt(b.src.match(/Z(\\d+)/)?.[1]||0)-parseInt(a.src.match(/Z(\\d+)/)?.[1]||0))
                .map(i=>i.src)""")
        else:
            # Allgemein: größtes Bild auf der Seite
            imgs = page.evaluate("""()=>Array.from(document.querySelectorAll('img'))
                .filter(i=>i.src.startsWith('http')&&(i.naturalWidth>400||i.width>400)
                    &&!i.src.includes('logo')&&!i.src.includes('icon')&&!i.src.includes('avatar')
                    &&!i.src.includes('map')&&!i.src.includes('flag'))
                .sort((a,b)=>(b.naturalWidth*b.naturalHeight||0)-(a.naturalWidth*a.naturalHeight||0))
                .slice(0,3).map(i=>i.src)""")
        return imgs[0] if imgs else ''
    except:
        return ''

wb = openpyxl.load_workbook('mallorca-kandidaten-v2.xlsx', read_only=True)
ws = wb.active
headers = [c.value for c in ws[1]]

entries = []
for row in ws.iter_rows(min_row=2):
    if not row[0].value: continue
    nr = int(row[0].value)
    url = str(row[headers.index('Link Objekt (URL)')].value or '')
    makler = str(row[headers.index('Makler')].value or '')
    name = str(row[headers.index('Name')].value or '')[:60]
    entries.append((nr, url, makler, name))

print(f"Prüfe {len(entries)} Einträge...\n", flush=True)

results = {'ok': [], 'mismatch': [], 'no_url': [], 'no_img': [], 'error': []}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for i, (nr, url, makler, name) in enumerate(entries):
        our_img = f'bilder/{nr}_main.jpg'

        if not url:
            results['no_url'].append(nr)
            continue
        if not os.path.exists(our_img):
            results['no_img'].append(nr)
            continue

        try:
            live_url = get_main_image(page, url, makler)
            if not live_url:
                results['error'].append((nr, 'kein Bild auf Seite'))
                print(f"Nr.{nr:3d} ❓ kein Bild auf Seite | {name[:40]}", flush=True)
                continue

            r = requests.get(live_url, timeout=10,
                           headers={'User-Agent':'Mozilla/5.0','Referer':url})
            if r.status_code != 200 or len(r.content) < 10000:
                results['error'].append((nr, f'HTTP {r.status_code}'))
                continue

            live_hash = hashlib.md5(r.content).hexdigest()
            our_hash = md5(our_img)

            if live_hash == our_hash:
                results['ok'].append(nr)
                if i % 20 == 0:
                    print(f"[{i+1}/332] ✅ Nr.{nr} ok", flush=True)
            else:
                # Speichere korrigiertes Bild
                open(our_img, 'wb').write(r.content)
                results['mismatch'].append((nr, name))
                print(f"Nr.{nr:3d} 🔄 Bild korrigiert | {name[:40]}", flush=True)

        except Exception as e:
            results['error'].append((nr, str(e)[:40]))
            print(f"Nr.{nr:3d} ❌ {str(e)[:50]}", flush=True)

    browser.close()

print(f"""
╔══════════════════════════════════════════════╗
║  BILD-VERIFIKATION ABGESCHLOSSEN             ║
╠══════════════════════════════════════════════╣
║  ✅ Korrekt:     {len(results['ok']):3d}/332                    ║
║  🔄 Korrigiert:  {len(results['mismatch']):3d}                         ║
║  ❓ Fehler:      {len(results['error']):3d}                         ║
║  🔗 Kein URL:    {len(results['no_url']):3d}                         ║
║  🖼 Kein Bild:   {len(results['no_img']):3d}                         ║
╚══════════════════════════════════════════════╝
""", flush=True)

if results['mismatch']:
    print("Korrigierte Objekte:")
    for nr, name in results['mismatch']:
        print(f"  Nr.{nr}: {name}")
