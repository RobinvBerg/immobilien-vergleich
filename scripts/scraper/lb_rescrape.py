#!/usr/bin/env python3
"""
LivingBlue komplett neu scrapen:
- Alle 88 Übersichtsseiten durchlaufen
- Pro Karte: neuer Link, Bild, Preis, Ort, Titel
- Speichern als lb_fresh.json
- Dann: unsere 113 Kandidaten per Preis+Ort matchen
- Bilder downloaden
"""
from playwright.sync_api import sync_playwright
import json, requests, os, openpyxl, re, hashlib

def md5(c): return hashlib.md5(c).hexdigest()

# Platzhalter-Hash
PH_HASH = '006c72429c5164da387b1b1bfe4b250c'

print("=== LivingBlue Neu-Scrape ===")

all_props = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
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
                    if(!numId) return;
                    const container = link.closest('li') || link.parentElement?.parentElement?.parentElement;
                    if(!container) return;
                    const img = container.querySelector('img[src*="images.egorealestate"]')?.src || '';
                    const text = container.textContent.replace(/\\s+/g,' ').trim();
                    const priceMatch = text.match(/([\\d\\.]+\\.\\d{3})\\s*€|€\\s*([\\d\\.]+\\.\\d{3})/);
                    const locMatch = text.match(/^([A-ZÄÖÜ][a-zäöü]+(?:\\s+[a-zäöüA-ZÄÖÜ]+)*)/);
                    results.push({
                        href: link.href,
                        numId,
                        img,
                        text: text.substring(0, 300)
                    });
                });
                return results;
            }""")

            all_props.extend(cards)
            if cards:
                print(f"Seite {pg}/88: {len(cards)} Properties (+{len(all_props)} total)", flush=True)
            else:
                print(f"Seite {pg}/88: 0 (zu schnell geladen)", flush=True)

        except Exception as e:
            print(f"Seite {pg}: Error — {e}", flush=True)

    # Für jede gefundene Property: Detailseite laden und echtes Hauptbild holen
    print(f"\nGesamt gesammelt: {len(all_props)} Properties")
    print("\n=== Detailseiten + Bilder ===")

    for i, prop in enumerate(all_props):
        if prop.get('img_full'):
            continue
        try:
            page.goto(prop['href'], wait_until='domcontentloaded', timeout=15000)
            page.wait_for_timeout(2000)

            data = page.evaluate("""() => {
                const imgs = Array.from(document.querySelectorAll('img[src*="images.egorealestate"]'))
                    .filter(i => i.src.includes('/Z1280') || i.src.includes('/Z800'));
                imgs.sort((a,b) => {
                    const sa = parseInt(a.src.match(/Z(\\d+)/)?.[1]||0);
                    const sb = parseInt(b.src.match(/Z(\\d+)/)?.[1]||0);
                    return sb-sa;
                });
                const h1 = document.querySelector('h1')?.textContent?.trim() || '';
                const desc = document.querySelector('p')?.textContent?.trim()?.substring(0,200) || '';
                const priceEl = document.querySelector('[class*="price"],[class*="preco"],[class*="preis"]');
                return {
                    img: imgs[0]?.src || '',
                    title: h1,
                    desc: desc
                };
            }""")

            prop['img_full'] = data.get('img','')
            prop['title'] = data.get('title','')
            prop['desc'] = data.get('desc','')
            print(f"[{i+1}/{len(all_props)}] {prop['numId']} — {data.get('title','')[:50]}", flush=True)

        except Exception as e:
            prop['img_full'] = ''
            print(f"[{i+1}/{len(all_props)}] {prop['numId']} Error: {e}", flush=True)

    page.close()
    browser.close()

with open('lb_fresh.json', 'w') as f:
    json.dump(all_props, f, indent=2, ensure_ascii=False)

print(f"\nGespeichert: lb_fresh.json ({len(all_props)} Properties)")

# === MATCHING gegen unsere 113 Kandidaten ===
print("\n=== Matching gegen Kandidatenliste ===")

wb = openpyxl.load_workbook('mallorca-kandidaten-v2.xlsx', read_only=True)
ws = wb.active
headers = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
lb_candidates = []
for row in ws.iter_rows(min_row=2, values_only=True):
    if not any(row): continue
    r = dict(zip(headers, row))
    if r.get('Makler') and 'living' in str(r.get('Makler','')).lower():
        lb_candidates.append(r)

os.makedirs('bilder', exist_ok=True)
match_results = []

for cand in lb_candidates:
    nr = int(cand['Ordnungsnummer'])
    preis = cand.get('Preis (€)', 0) or 0
    ort = str(cand.get('Location') or '').lower()
    out_path = f"bilder/{nr}_main.jpg"

    # Skip wenn echtes Bild vorhanden
    if os.path.exists(out_path) and os.path.getsize(out_path) > 100000:
        with open(out_path,'rb') as f: h = md5(f.read())
        if h != PH_HASH:
            print(f"Nr.{nr} ⏭️ skip")
            match_results.append({'nr': nr, 'status': 'skip'})
            continue

    # Match per Preis (±3%) + Ort
    best = None
    for prop in all_props:
        ptext = prop.get('text','').lower()
        
        # Preis aus Text extrahieren
        prices = re.findall(r'(\d[\d\.]+)\s*€', ptext.replace(' ',''))
        card_prices = []
        for p in prices:
            try: card_prices.append(float(p.replace('.','')))
            except: pass
        
        price_ok = any(abs(cp - preis)/max(preis,1) < 0.03 for cp in card_prices if cp > 100000)
        ort_ok = ort.split()[0] in ptext if ort else False
        
        if price_ok and ort_ok:
            best = prop
            break
        elif price_ok and not best:
            best = prop

    if best and best.get('img_full'):
        try:
            resp = requests.get(best['img_full'], timeout=10)
            if resp.status_code == 200 and len(resp.content) > 20000:
                h = md5(resp.content)
                if h != PH_HASH:
                    with open(out_path, 'wb') as f: f.write(resp.content)
                    print(f"Nr.{nr} ✅ {len(resp.content)//1024}KB → {best['href'][-40:]}")
                    match_results.append({'nr': nr, 'status': 'ok', 'href': best['href']})
                else:
                    print(f"Nr.{nr} ⚠️ Platzhalter")
                    match_results.append({'nr': nr, 'status': 'placeholder'})
        except Exception as e:
            print(f"Nr.{nr} ❌ Download: {e}")
            match_results.append({'nr': nr, 'status': 'error'})
    else:
        print(f"Nr.{nr} ❌ kein Match (preis={preis:,}, ort={ort})")
        match_results.append({'nr': nr, 'status': 'no_match'})

ok = sum(1 for r in match_results if r['status'] == 'ok')
print(f"\n✅ {ok}/{len(lb_candidates)} Bilder erfolgreich")
with open('lb_match_results.json','w') as f:
    json.dump(match_results, f, indent=2)
