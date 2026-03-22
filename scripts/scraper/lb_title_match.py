#!/usr/bin/env python3
"""
Für die 68 falsch gematchten LivingBlue-Objekte:
- Suche per Titel-Keywords auf LivingBlue
- Finde richtiges Objekt + Bild
- Speichere als bilder/NR_main.jpg
"""
import os, json, re, requests, hashlib, openpyxl
from playwright.sync_api import sync_playwright

os.chdir('/Users/robin/.openclaw/workspace/mallorca-projekt')

def md5f(p):
    with open(p,'rb') as f: return hashlib.md5(f.read()).hexdigest()

# Die 68 falschen Nummern
WRONG = [20,21,22,28,29,31,33,36,38,41,42,43,45,52,62,81,84,86,100,108,109,114,116,128,129,136,137,139,141,144,149,158,159,160,162,163,171,180,197,198,199,200,201,202,209,219,221,225,231,241,262,267,268,270,276,277,278,288,297,300,306,309,312,318,324,325,328,332]

# Excel laden
wb = openpyxl.load_workbook('mallorca-kandidaten-v2.xlsx', read_only=True)
ws = wb.active
headers = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
entries = {}
for row in ws.iter_rows(min_row=2, values_only=True):
    if not any(row): continue
    r = dict(zip(headers, row))
    nr = int(r['Ordnungsnummer'])
    if nr in WRONG:
        entries[nr] = r

# lb_fresh als Fallback
with open('lb_fresh.json') as f:
    lb = json.load(f)

BAD_HASHES = set()
# Alle aktuellen Bild-Hashes der falschen Nummern sammeln
for nr in WRONG:
    p = f'bilder/{nr}_main.jpg'
    if os.path.exists(p):
        BAD_HASHES.add(md5f(p))

print(f"Starte für {len(WRONG)} Objekte", flush=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    fixed = 0
    failed = []

    for nr in WRONG:
        r = entries.get(nr, {})
        name = str(r.get('Name') or '')
        ort = str(r.get('Location') or '').lower()
        preis = float(r.get('Preis (€)') or 0)

        # Suchbegriff: erste 3-4 markante Wörter aus dem Titel
        words = [w for w in re.split(r'\W+', name) if len(w) > 4][:4]
        query = ' '.join(words)

        if not query:
            failed.append(nr)
            print(f"Nr.{nr} ❌ kein Suchbegriff", flush=True)
            continue

        search_url = f"https://www.livingblue-mallorca.com/de-de/immobilien?q={requests.utils.quote(query)}"

        try:
            page.goto(search_url, wait_until='domcontentloaded', timeout=15000)
            page.wait_for_timeout(2500)

            # Alle Karten auf der Suchergebnisseite
            cards = page.evaluate("""() => {
                const results = [];
                document.querySelectorAll('a[href*="/immobilie/"]').forEach(link => {
                    const numId = link.href.match(/\\/(\\d+)$/)?.[1];
                    if (!numId) return;
                    const container = link.closest('li') || link.parentElement?.parentElement?.parentElement;
                    const img = container?.querySelector('img[src*="images.egorealestate"]')?.src || '';
                    const title = container?.querySelector('h2,h3,[class*="title"]')?.textContent?.trim() || '';
                    const text = container?.textContent?.replace(/\\s+/g,' ')?.trim()?.substring(0,200) || '';
                    results.push({href: link.href, numId, img, title, text});
                });
                return results;
            }""")

            if not cards:
                # Fallback: direkte LB-Suche ohne Filter, nimm lb_fresh
                best = None
                best_score = 0
                name_words = set(w.lower() for w in re.split(r'\W+', name) if len(w) > 4)
                for prop in lb:
                    if not prop.get('img_full'): continue
                    lb_words = set(re.split(r'\W+', (prop.get('title','') + ' ' + prop.get('text','')).lower()))
                    overlap = name_words & lb_words
                    sc = len(overlap)
                    if sc > best_score: best_score=sc; best=prop
                if best and best_score >= 2:
                    cards = [{'href': best['href'], 'img': best['img_full'], 'title': best.get('title',''), 'text': best.get('text','')}]

            # Bestes Match aus Karten wählen
            best_card = None
            best_score = 0
            name_lower = name.lower()
            for card in cards:
                card_text = (card.get('title','') + ' ' + card.get('text','')).lower()
                # Score: Wort-Overlap
                nw = set(w for w in re.split(r'\W+', name_lower) if len(w) > 4)
                cw = set(re.split(r'\W+', card_text))
                sc = len(nw & cw)
                if sc > best_score: best_score=sc; best_card=card

            if not best_card and cards:
                best_card = cards[0]

            if not best_card:
                failed.append(nr)
                print(f"Nr.{nr} ❌ keine Karten ({query})", flush=True)
                continue

            # Detailseite laden für bestes Bild
            img_url = best_card.get('img','')
            if best_card.get('href'):
                try:
                    page.goto(best_card['href'], wait_until='domcontentloaded', timeout=15000)
                    page.wait_for_timeout(2000)
                    detail_imgs = page.evaluate("""() => 
                        Array.from(document.querySelectorAll('img[src*="images.egorealestate"]'))
                        .filter(i=>i.src.includes('Z800')||i.src.includes('Z1280'))
                        .map(i=>i.src)
                    """)
                    if detail_imgs:
                        img_url = detail_imgs[0]
                except: pass

            if not img_url:
                failed.append(nr)
                print(f"Nr.{nr} ❌ kein Bild", flush=True)
                continue

            resp = requests.get(img_url, timeout=10)
            if resp.status_code == 200 and len(resp.content) > 20000:
                h = hashlib.md5(resp.content).hexdigest()
                if h not in BAD_HASHES:
                    with open(f'bilder/{nr}_main.jpg','wb') as f2: f2.write(resp.content)
                    # URL in Excel aktualisieren
                    fixed += 1
                    print(f"Nr.{nr} ✅ {len(resp.content)//1024}KB | {best_card.get('href','')[-45:]}", flush=True)
                else:
                    failed.append(nr)
                    print(f"Nr.{nr} ⚠️ Platzhalter-Bild", flush=True)
            else:
                failed.append(nr)
                print(f"Nr.{nr} ❌ {resp.status_code}", flush=True)

        except Exception as e:
            failed.append(nr)
            print(f"Nr.{nr} ❌ {str(e)[:60]}", flush=True)

    browser.close()

print(f"\n✅ Gefixt: {fixed}/{len(WRONG)}")
print(f"❌ Fehlgeschlagen: {len(failed)}: {failed}")
