#!/usr/bin/env python3
"""
Holt LivingBlue Bilder via Playwright Browser:
- Lädt jede Detailseite über INFO-Link
- Extrahiert das erste echte Bild aus dem DOM
- Speichert als bilder/NR_main.jpg
"""
from playwright.sync_api import sync_playwright
import json, requests, os, openpyxl, hashlib

PLACEHOLDER_HASH = None  # wird beim ersten Bild gesetzt

def get_img_hash(content):
    return hashlib.md5(content).hexdigest()

wb = openpyxl.load_workbook('mallorca-kandidaten-v2.xlsx', read_only=True)
ws = wb.active
headers = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
lb_entries = []
for row in ws.iter_rows(min_row=2, values_only=True):
    if not any(row): continue
    r = dict(zip(headers, row))
    if r.get('Makler') and 'living' in str(r.get('Makler','')).lower():
        lb_entries.append({'nr': int(r['Ordnungsnummer']), 'url': r.get('Link Objekt (URL)',''), 'name': r.get('Name','')})

print(f"Verarbeite {len(lb_entries)} LivingBlue Objekte via Browser")

# Bekannte Platzhalter-Hashes
KNOWN_PLACEHOLDERS = set()
placeholder_file = 'bilder/20_main.jpg'  # war vorher Platzhalter
if os.path.exists(placeholder_file):
    with open(placeholder_file, 'rb') as f:
        KNOWN_PLACEHOLDERS.add(get_img_hash(f.read()))

results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    
    # Erst alle INFO-Links von Übersichtsseiten sammeln
    print("Schritt 1: Sammle alle INFO-Links von Übersicht...")
    info_links = []  # (numericId, href, imgSrc)
    
    page = browser.new_page()
    for pg in range(1, 89):
        try:
            page.goto(f"https://www.livingblue-mallorca.com/de-de/immobilien?pag={pg}",
                     wait_until='domcontentloaded', timeout=15000)
            page.wait_for_timeout(2500)
            
            cards = page.evaluate("""() => {
                const results = [];
                const seen = new Set();
                document.querySelectorAll('a[href*="/immobilie/"]').forEach(link => {
                    if(seen.has(link.href)) return;
                    seen.add(link.href);
                    const numId = link.href.match(/\\/(\\d+)$/)?.[1];
                    if(numId) results.push({href: link.href, numId});
                });
                return results;
            }""")
            
            info_links.extend(cards)
            if cards:
                print(f"  Seite {pg}/88: {len(cards)} Links (+{len(info_links)} total)", flush=True)
        except Exception as e:
            print(f"  Seite {pg}: Fehler — {e}", flush=True)
    
    page.close()
    print(f"Schritt 1 fertig: {len(info_links)} unique INFO-Links gesammelt")
    
    # Jetzt für jedes LivingBlue-Objekt: finde passenden INFO-Link via Beschreibungstext
    # Da wir keinen direkten UUID→numericID Mapping haben, besuchen wir die Detailseiten direkt
    # und vergleichen den Beschreibungstext
    
    print("\nSchritt 2: Lade Detailseiten und hole Bilder...")
    page = browser.new_page()
    
    for i, entry in enumerate(lb_entries):
        nr = entry['nr']
        uuid = entry['url'].rstrip('/').split('/')[-1]
        out_path = f"bilder/{nr}_main.jpg"
        
        # Skip wenn bereits echtes Bild (>50KB, nicht Platzhalter)
        if os.path.exists(out_path):
            with open(out_path, 'rb') as f:
                content = f.read()
            img_hash = get_img_hash(content)
            if len(content) > 50000 and img_hash not in KNOWN_PLACEHOLDERS:
                print(f"[{i+1}/{len(lb_entries)}] Nr.{nr} — echtes Bild vorhanden, skip")
                results.append({'nr': nr, 'status': 'skip'})
                continue
        
        # UUID-URL laden → Overview lädt, dann ersten INFO-Link auf Detailseite
        # Stattdessen: Suche in info_links nach passendem Objekt via Preis/Ort aus Name
        # Oder: lade die UUID-URL und klicke auf den ersten sichtbaren INFO-Button
        
        try:
            page.goto(f"https://www.livingblue-mallorca.com/de-de/immobilien/{uuid}",
                     wait_until='domcontentloaded', timeout=15000)
            page.wait_for_timeout(2000)
            
            # Klicke auf ersten INFO-Link der Übersicht  
            info_href = page.evaluate("""() => {
                const links = document.querySelectorAll('a[href*="/immobilie/"]');
                return links[0]?.href || null;
            }""")
            
            if not info_href:
                print(f"[{i+1}] Nr.{nr} ❌ Kein INFO-Link gefunden")
                results.append({'nr': nr, 'status': 'no_info_link'})
                continue
            
            # Detailseite laden
            page.goto(info_href, wait_until='domcontentloaded', timeout=15000)
            page.wait_for_timeout(2500)
            
            # Hauptbild extrahieren (größtes Bild auf der Seite)
            img_url = page.evaluate("""() => {
                const imgs = Array.from(document.querySelectorAll('img[src*="images.egorealestate"]'));
                // Sortiere nach Größe (größte zuerst, Z1280 > Z800)
                imgs.sort((a, b) => {
                    const sizeA = parseInt(a.src.match(/Z(\\d+)/)?.[1] || '0');
                    const sizeB = parseInt(b.src.match(/Z(\\d+)/)?.[1] || '0');
                    return sizeB - sizeA;
                });
                return imgs[0]?.src || null;
            }""")
            
            if not img_url:
                print(f"[{i+1}] Nr.{nr} ❌ Kein Bild auf Detailseite ({info_href[-40:]})")
                results.append({'nr': nr, 'status': 'no_img'})
                continue
            
            # Download
            resp = requests.get(img_url, timeout=10)
            if resp.status_code == 200 and len(resp.content) > 20000:
                img_hash = get_img_hash(resp.content)
                if img_hash in KNOWN_PLACEHOLDERS:
                    print(f"[{i+1}] Nr.{nr} ⚠️ Platzhalter ({img_url[-40:]})")
                    results.append({'nr': nr, 'status': 'placeholder'})
                else:
                    with open(out_path, 'wb') as f:
                        f.write(resp.content)
                    KNOWN_PLACEHOLDERS_CHECK = len(resp.content)
                    print(f"[{i+1}/{len(lb_entries)}] Nr.{nr} ✅ {len(resp.content)//1024}KB")
                    results.append({'nr': nr, 'status': 'ok', 'url': img_url})
            else:
                print(f"[{i+1}] Nr.{nr} ❌ Download fehlgeschlagen ({resp.status_code})")
                results.append({'nr': nr, 'status': 'fail'})
                
        except Exception as e:
            print(f"[{i+1}] Nr.{nr} ❌ Error: {e}")
            results.append({'nr': nr, 'status': 'error', 'msg': str(e)})
    
    page.close()
    browser.close()

ok = sum(1 for r in results if r['status'] == 'ok')
skip = sum(1 for r in results if r['status'] == 'skip')
fail = sum(1 for r in results if r['status'] not in ('ok', 'skip'))
print(f"\n✅ {ok} neue Bilder | ⏭️ {skip} skip | ❌ {fail} fehlgeschlagen")

with open('lb_browser_results.json', 'w') as f:
    json.dump(results, f, indent=2)
