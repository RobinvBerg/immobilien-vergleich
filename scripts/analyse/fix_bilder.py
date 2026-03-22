import os, hashlib, openpyxl, requests, sys
from collections import defaultdict
from playwright.sync_api import sync_playwright

os.chdir('/Users/robin/.openclaw/workspace/mallorca-projekt')

def md5(path):
    with open(path,'rb') as f: return hashlib.md5(f.read()).hexdigest()

hashes = defaultdict(list)
for f in os.listdir('bilder'):
    if f.endswith('_main.jpg'):
        nr = int(f.replace('_main.jpg',''))
        hashes[md5(f'bilder/{f}')].append(nr)

dupe_nrs = set()
for h, nrs in hashes.items():
    if len(nrs) > 1:
        for nr in nrs: dupe_nrs.add(nr)

print(f"Zu fixen: {len(dupe_nrs)} Objekte", flush=True)

wb = openpyxl.load_workbook('mallorca-kandidaten-v2.xlsx', read_only=True)
ws = wb.active
headers = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
targets = []
for row in ws.iter_rows(min_row=2, values_only=True):
    if not any(row): continue
    r = dict(zip(headers, row))
    nr = int(r['Ordnungsnummer'])
    if nr in dupe_nrs:
        targets.append({'nr': nr, 'url': r.get('Link Objekt (URL)') or '', 'makler': r.get('Makler') or ''})

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(extra_http_headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'})

    for t in targets:
        nr, url, makler = t['nr'], t['url'], t['makler']
        if not url:
            print(f"Nr.{nr} keine URL", flush=True)
            continue
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=20000)
            page.wait_for_timeout(2500)

            img_url = page.evaluate("""() => {
                const selectors = [
                    '.swiper-slide-active img', '.swiper-wrapper .swiper-slide:first-child img',
                    '[class*="gallery"] img:first-child', '[class*="slider"] img:first-child',
                    '.property-image img', '.hero img', 'figure img',
                    '[class*="photo"] img', '.carousel img'
                ];
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el?.src?.startsWith('http') && !el.src.includes('logo') && !el.src.includes('icon') && !el.src.includes('avatar')) return el.src;
                }
                const all = Array.from(document.querySelectorAll('img'))
                    .filter(i => i.src.startsWith('http') && (i.naturalWidth > 500 || i.width > 500))
                    .sort((a,b) => (b.naturalWidth*b.naturalHeight||0)-(a.naturalWidth*a.naturalHeight||0));
                return all[0]?.src || '';
            }""")

            if not img_url:
                print(f"Nr.{nr} kein Bild ({makler})", flush=True)
                continue

            resp = requests.get(img_url, timeout=15, headers={'Referer': url, 'User-Agent': 'Mozilla/5.0'})
            if resp.status_code == 200 and len(resp.content) > 30000:
                with open(f'bilder/{nr}_main.jpg', 'wb') as f: f.write(resp.content)
                print(f"Nr.{nr} ✅ {len(resp.content)//1024}KB ({makler})", flush=True)
            else:
                print(f"Nr.{nr} ❌ {resp.status_code}/{len(resp.content)}b", flush=True)

        except Exception as e:
            print(f"Nr.{nr} ❌ {str(e)[:60]}", flush=True)

    browser.close()

still = defaultdict(list)
for f in os.listdir('bilder'):
    if f.endswith('_main.jpg'):
        still[md5(f'bilder/{f}')].append(f)
remaining = sum(len(v) for v in still.values() if len(v) > 1)
print(f"\nNoch Duplikate: {remaining}", flush=True)
