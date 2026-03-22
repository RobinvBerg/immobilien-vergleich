#!/usr/bin/env python3
"""
LivingBlue Vollscraper — alle Objekte mit allen Daten + Bilder
Output: lb_full.json + lb_bilder/NR.jpg
"""
import os, json, re, requests, time
from playwright.sync_api import sync_playwright

os.makedirs('lb_bilder', exist_ok=True)
BASE = 'https://www.livingblue-mallorca.com/de-de'

def extract_number(s):
    if not s: return 0
    m = re.search(r'[\d\.]+', str(s).replace('.',''))
    return float(m.group()) if m else 0

results = []
seen_hrefs = set()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Seiten scrapen
    page_num = 1
    total_pages = 99

    while page_num <= total_pages:
        url = f"{BASE}/immobilien?page={page_num}"
        print(f"\n📄 Seite {page_num}/{total_pages} ...", flush=True)

        try:
            page.goto(url, wait_until='domcontentloaded', timeout=20000)
            page.wait_for_timeout(3000)

            # Gesamtanzahl Seiten
            if page_num == 1:
                pager = page.evaluate("""() => {
                    const last = document.querySelector('[aria-label="Letzte Seite"], a[href*="page="]:last-of-type');
                    if (last) { const m = last.href.match(/page=(\\d+)/); return m ? parseInt(m[1]) : 0; }
                    const pages = Array.from(document.querySelectorAll('a[href*="page="]')).map(a=>parseInt(a.href.match(/page=(\\d+)/)?.[1]||0));
                    return pages.length ? Math.max(...pages) : 0;
                }""")
                if pager > 0:
                    total_pages = pager
                    print(f"  Gesamt: {total_pages} Seiten", flush=True)

            # Karten auf dieser Seite
            cards = page.evaluate("""() => {
                const results = [];
                document.querySelectorAll('a[href*="/immobilie/"]').forEach(link => {
                    const href = link.href;
                    const numId = href.match(/\\/(\\d+)$/)?.[1];
                    if (!numId) return;
                    const c = link.closest('li') || link.closest('article') || link.parentElement?.parentElement?.parentElement;
                    if (!c) return;
                    const img = c.querySelector('img[src*="images.egorealestate"]')?.src || '';
                    const title = (c.querySelector('h2,h3,[class*="title"],[class*="Title"]')?.textContent || '').trim();
                    const text = (c.textContent || '').replace(/\\s+/g,' ').trim().substring(0,400);
                    const priceEl = c.querySelector('[class*="price"],[class*="Price"]');
                    const price = (priceEl?.textContent || text).match(/[\\d\\.]{5,}/)?.[0]?.replace(/\\./g,'') || '0';
                    results.push({href, numId, img, title, text, price});
                });
                return results;
            }""")

            new_on_page = 0
            for card in cards:
                if card['href'] in seen_hrefs: continue
                seen_hrefs.add(card['href'])
                new_on_page += 1

                obj = {
                    'href': card['href'],
                    'numId': card['numId'],
                    'title': card['title'],
                    'price': int(card['price']) if card['price'].isdigit() else 0,
                    'img_thumb': card['img'],
                    'img_full': '',
                    'zimmer': 0, 'baeder': 0, 'flaeche': 0, 'grundst': 0,
                    'ort': '', 'beschreibung': '',
                    'local_img': '',
                }

                # Detail-Seite laden
                try:
                    dp = browser.new_page()
                    dp.goto(card['href'], wait_until='domcontentloaded', timeout=15000)
                    dp.wait_for_timeout(2000)

                    detail = dp.evaluate("""() => {
                        const imgs = Array.from(document.querySelectorAll('img[src*="images.egorealestate"]'))
                            .filter(i => i.src.includes('Z800') || i.src.includes('Z1280') || i.src.includes('Z1920'))
                            .sort((a,b) => {
                                const sa = parseInt(a.src.match(/Z(\\d+)/)?.[1]||0);
                                const sb = parseInt(b.src.match(/Z(\\d+)/)?.[1]||0);
                                return sb-sa;
                            });
                        const img_full = imgs[0]?.src || '';
                        const all_imgs = imgs.slice(0,5).map(i=>i.src);

                        // Daten aus Tabellen/Icons
                        const text = document.body.innerText.replace(/\\s+/g,' ');
                        
                        const zimmer = text.match(/(\\d+)\\s*(?:Schlafzimmer|Zimmer|Bedrooms?)/i)?.[1] || '0';
                        const baeder = text.match(/(\\d+)\\s*(?:Badezimmer|Bäder|Bathrooms?)/i)?.[1] || '0';
                        
                        const flaeche_m = text.match(/(\\d[\\d\\.]+)\\s*m²\\s*(?:Wohnfl|Nutzfl|Living|Built)/i);
                        const flaeche = flaeche_m?.[1]?.replace('.','') || '0';
                        
                        const grundst_m = text.match(/(\\d[\\d\\.]+)\\s*m²\\s*(?:Grundst|Plot|Land|Grundfl)/i);
                        const grundst = grundst_m?.[1]?.replace('.','') || '0';

                        // Ort aus Breadcrumb oder Meta
                        const breadcrumb = Array.from(document.querySelectorAll('nav a, [class*="breadcrumb"] a')).map(a=>a.textContent.trim()).filter(t=>t&&t!='Home'&&t!='Immobilien').join(', ');
                        const ort = breadcrumb || document.querySelector('meta[property="og:locality"]')?.content || '';

                        const desc = document.querySelector('[class*="description"],[class*="Description"],#description')?.textContent?.trim()?.substring(0,500) || '';

                        const price_els = Array.from(document.querySelectorAll('[class*="price"],[class*="Price"]')).map(e=>e.textContent.replace(/\\s+/g,' ').trim());
                        
                        return {img_full, all_imgs, zimmer, baeder, flaeche, grundst, ort, desc, prices: price_els};
                    }""")

                    obj['img_full'] = detail.get('img_full', '')
                    obj['all_imgs'] = detail.get('all_imgs', [])
                    obj['zimmer'] = int(detail.get('zimmer', 0) or 0)
                    obj['baeder'] = int(detail.get('baeder', 0) or 0)
                    obj['flaeche'] = float(str(detail.get('flaeche', 0) or '0').replace('.',''))
                    obj['grundst'] = float(str(detail.get('grundst', 0) or '0').replace('.',''))
                    obj['ort'] = detail.get('ort', '')
                    obj['beschreibung'] = detail.get('desc', '')

                    dp.close()

                    # Bild herunterladen
                    img_url = obj['img_full'] or obj['img_thumb']
                    if img_url:
                        try:
                            r = requests.get(img_url, timeout=8)
                            if r.status_code == 200 and len(r.content) > 10000:
                                fname = f"lb_bilder/{obj['numId']}.jpg"
                                open(fname, 'wb').write(r.content)
                                obj['local_img'] = fname
                        except: pass

                except Exception as e:
                    try: dp.close()
                    except: pass
                    print(f"    ⚠️ Detail-Fehler {card['numId']}: {str(e)[:40]}", flush=True)

                results.append(obj)

            print(f"  +{new_on_page} neu | Gesamt: {len(results)}", flush=True)

            # Zwischenspeichern alle 5 Seiten
            if page_num % 5 == 0:
                with open('lb_full.json', 'w') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                print(f"  💾 Zwischenstand gespeichert ({len(results)} Objekte)", flush=True)

            if new_on_page == 0:
                print("  Keine neuen Objekte — fertig!", flush=True)
                break

        except Exception as e:
            print(f"  ❌ Seiten-Fehler: {e}", flush=True)
            time.sleep(5)

        page_num += 1

    browser.close()

# Final speichern
with open('lb_full.json', 'w') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n✅ FERTIG: {len(results)} Objekte in lb_full.json")
print(f"   Bilder: {len([r for r in results if r['local_img']])} heruntergeladen")
