#!/usr/bin/env python3
"""
LivingBlue Finale Lösung:
1. Hole für jede UUID die echte Beschreibung via egorealestate API (im Browser)
2. Scanne Übersichtsseiten und matche per Beschreibungstext
3. Lade Detailseite → extrahiere Hauptbild → speichere
"""
from playwright.sync_api import sync_playwright
import json, requests, os, openpyxl, hashlib

def md5(content): return hashlib.md5(content).hexdigest()

PLACEHOLDER_HASHES = {
    'ee05c5cf-f90a-4b1a-b532-56a6e66e7559',  # bekannter Platzhalter
}

# LivingBlue Einträge laden
wb = openpyxl.load_workbook('mallorca-kandidaten-v2.xlsx', read_only=True)
ws = wb.active
headers = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
lb_entries = []
for row in ws.iter_rows(min_row=2, values_only=True):
    if not any(row): continue
    r = dict(zip(headers, row))
    if r.get('Makler') and 'living' in str(r.get('Makler','')).lower():
        uuid = (r.get('Link Objekt (URL)') or '').rstrip('/').split('/')[-1]
        lb_entries.append({
            'nr': int(r['Ordnungsnummer']),
            'uuid': uuid,
            'name': r.get('Name',''),
            'preis': r.get('Preis (€)', 0),
            'ort': r.get('Location','')
        })

print(f"Verarbeite {len(lb_entries)} LivingBlue Objekte")

# Platzhalter-Hash ermitteln
placeholder_hash = None
ph_url = "https://images.egorealestate.com/Z800x600/OAYES/S5/C8157/P29529519/Tphoto/IDaf95c201-0000-0500-0000-00001898269d.jpg"
try:
    r = requests.get(ph_url, timeout=10)
    if r.status_code == 200:
        placeholder_hash = md5(r.content)
        print(f"Platzhalter-Hash: {placeholder_hash}")
except: pass

results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # SCHRITT 1: UUID → echte Beschreibung via API
    print("\n=== SCHRITT 1: Beschreibungen holen ===")
    uuid_to_desc = {}

    for i, entry in enumerate(lb_entries):
        uuid = entry['uuid']
        api_data = [None]

        def on_resp(resp):
            if 'websiteapi.egorealestate.com/v1/Properties' in resp.url:
                try:
                    d = resp.json()
                    if d.get('Properties'):
                        api_data[0] = d['Properties'][0]
                except: pass

        page.on('response', on_resp)
        try:
            page.goto(f"https://www.livingblue-mallorca.com/de-de/immobilien/{uuid}",
                     wait_until='domcontentloaded', timeout=12000)
            page.wait_for_timeout(2000)
        except: pass
        page.remove_listener('response', on_resp)

        if api_data[0]:
            desc = (api_data[0].get('Description') or '')[:120].strip()
            uuid_to_desc[uuid] = desc
            print(f"[{i+1}/{len(lb_entries)}] Nr.{entry['nr']} → {desc[:60]}...", flush=True)
        else:
            uuid_to_desc[uuid] = ''
            print(f"[{i+1}/{len(lb_entries)}] Nr.{entry['nr']} ❌ keine API-Antwort", flush=True)

    with open('lb_uuid_desc.json', 'w') as f:
        json.dump(uuid_to_desc, f, indent=2, ensure_ascii=False)
    print(f"\nBeschreibungen: {sum(1 for v in uuid_to_desc.values() if v)}/{len(lb_entries)} erfolgreich")

    # SCHRITT 2: Übersichtsseiten scannen → (infoHref, descSnippet) sammeln
    print("\n=== SCHRITT 2: Übersichtsseiten scannen ===")
    overview_cards = []

    for pg in range(1, 89):
        try:
            page.goto(f"https://www.livingblue-mallorca.com/de-de/immobilien?pag={pg}",
                     wait_until='domcontentloaded', timeout=15000)
            page.wait_for_timeout(2000)

            cards = page.evaluate("""() => {
                const results = [];
                const seen = new Set();
                document.querySelectorAll('a[href*="/immobilie/"]').forEach(link => {
                    if(seen.has(link.href)) return;
                    seen.add(link.href);
                    const numId = link.href.match(/\\/(\\d+)$/)?.[1];
                    const container = link.closest('li') || link.parentElement?.parentElement?.parentElement;
                    const desc = container?.querySelector('p')?.textContent?.trim()?.substring(0, 120) || '';
                    const img = container?.querySelector('img[src*="images.egorealestate"]')?.src || '';
                    if(numId) results.push({href: link.href, numId, desc, img});
                });
                return results;
            }""")
            overview_cards.extend(cards)
            if cards: print(f"  Seite {pg}/88: {len(cards)} Cards", flush=True)
        except: pass

    with open('lb_overview_cards.json', 'w') as f:
        json.dump(overview_cards, f, indent=2, ensure_ascii=False)
    print(f"Total Overview Cards: {len(overview_cards)}")

    # SCHRITT 3: Match + Bild laden
    print("\n=== SCHRITT 3: Match + Bilder laden ===")

    for i, entry in enumerate(lb_entries):
        nr = entry['nr']
        uuid = entry['uuid']
        out_path = f"bilder/{nr}_main.jpg"

        # Skip wenn echtes Bild vorhanden
        if os.path.exists(out_path) and os.path.getsize(out_path) > 100000:
            with open(out_path,'rb') as f: h = md5(f.read())
            if h != placeholder_hash:
                print(f"[{i+1}] Nr.{nr} ⏭️ skip (echtes Bild vorhanden)")
                results.append({'nr': nr, 'status': 'skip'})
                continue

        my_desc = uuid_to_desc.get(uuid, '')
        if not my_desc:
            print(f"[{i+1}] Nr.{nr} ❌ keine Beschreibung für Match")
            results.append({'nr': nr, 'status': 'no_desc'})
            continue

        # Finde besten Match in overview_cards per Beschreibungstext
        best_score = 0
        best_card = None
        my_words = set(my_desc.lower().split())

        for card in overview_cards:
            card_words = set(card.get('desc','').lower().split())
            if not card_words: continue
            overlap = len(my_words & card_words)
            score = overlap / max(len(my_words), 1)
            if score > best_score:
                best_score = score
                best_card = card

        if not best_card or best_score < 0.3:
            print(f"[{i+1}] Nr.{nr} ❌ kein Match (best={best_score:.2f})")
            results.append({'nr': nr, 'status': 'no_match'})
            continue

        # Detailseite laden
        try:
            page.goto(best_card['href'], wait_until='domcontentloaded', timeout=15000)
            page.wait_for_timeout(2500)

            img_url = page.evaluate("""() => {
                const imgs = Array.from(document.querySelectorAll('img[src*="images.egorealestate"]'))
                    .filter(i => i.src.includes('/Z1280') || i.src.includes('/Z800'));
                imgs.sort((a,b) => {
                    const sa = parseInt(a.src.match(/Z(\\d+)/)?.[1]||0);
                    const sb = parseInt(b.src.match(/Z(\\d+)/)?.[1]||0);
                    return sb-sa;
                });
                return imgs[0]?.src || null;
            }""")

            if not img_url:
                print(f"[{i+1}] Nr.{nr} ❌ kein Bild auf Detailseite")
                results.append({'nr': nr, 'status': 'no_img'})
                continue

            resp = requests.get(img_url, timeout=10)
            if resp.status_code == 200 and len(resp.content) > 20000:
                h = md5(resp.content)
                if h == placeholder_hash:
                    print(f"[{i+1}] Nr.{nr} ⚠️ Platzhalter")
                    results.append({'nr': nr, 'status': 'placeholder'})
                else:
                    with open(out_path, 'wb') as f: f.write(resp.content)
                    print(f"[{i+1}/{len(lb_entries)}] Nr.{nr} ✅ {len(resp.content)//1024}KB (match={best_score:.2f})")
                    results.append({'nr': nr, 'status': 'ok', 'url': img_url, 'score': best_score})
            else:
                print(f"[{i+1}] Nr.{nr} ❌ Download fail ({resp.status_code})")
                results.append({'nr': nr, 'status': 'fail'})
        except Exception as e:
            print(f"[{i+1}] Nr.{nr} ❌ {e}")
            results.append({'nr': nr, 'status': 'error'})

    page.close()
    browser.close()

ok = sum(1 for r in results if r['status'] == 'ok')
skip = sum(1 for r in results if r['status'] == 'skip')
fail = len(results) - ok - skip
print(f"\n✅ {ok} Bilder | ⏭️ {skip} skip | ❌ {fail} Problem")
with open('lb_final_results.json','w') as f:
    json.dump(results, f, indent=2)
