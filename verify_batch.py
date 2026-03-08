#!/usr/bin/env python3
"""
Batch-Verifikation: URL-Test + Bild-Test
Aufruf: python3 verify_batch.py <batch_id> <total_batches>
"""
import os, sys, json, hashlib, requests, openpyxl
from playwright.sync_api import sync_playwright

batch_id = int(sys.argv[1])
total_batches = int(sys.argv[2])

def md5(p):
    with open(p,'rb') as f: return hashlib.md5(f.read()).hexdigest()

def get_main_image(page, url, makler):
    makler = makler.lower()
    try:
        resp = page.goto(url, wait_until='domcontentloaded', timeout=20000)
        status = resp.status if resp else 0
        if status in [404, 410]:
            return '', status
        page.wait_for_timeout(2500)
        if 'living' in makler:
            imgs = page.evaluate("""()=>Array.from(document.querySelectorAll('img[src*="images.egorealestate"]'))
                .filter(i=>i.src.includes('Z800')||i.src.includes('Z1280'))
                .sort((a,b)=>parseInt(b.src.match(/Z(\\d+)/)?.[1]||0)-parseInt(a.src.match(/Z(\\d+)/)?.[1]||0))
                .map(i=>i.src)""")
        else:
            imgs = page.evaluate("""()=>Array.from(document.querySelectorAll('img'))
                .filter(i=>i.src.startsWith('http')
                    &&(i.naturalWidth>400||i.width>400)
                    &&!i.src.includes('logo')&&!i.src.includes('icon')
                    &&!i.src.includes('map')&&!i.src.includes('avatar'))
                .sort((a,b)=>(b.naturalWidth*b.naturalHeight||0)-(a.naturalWidth*a.naturalHeight||0))
                .slice(0,3).map(i=>i.src)""")
        return (imgs[0] if imgs else ''), status
    except Exception as e:
        return '', str(e)[:40]

# Einträge laden
wb = openpyxl.load_workbook('mallorca-kandidaten-v2.xlsx', read_only=True)
ws = wb.active
headers = [c.value for c in ws[1]]
all_entries = []
for row in ws.iter_rows(min_row=2):
    if not row[0].value: continue
    nr = int(row[0].value)
    all_entries.append({
        'nr': nr,
        'url': str(row[headers.index('Link Objekt (URL)')].value or ''),
        'makler': str(row[headers.index('Makler')].value or ''),
        'name': str(row[headers.index('Name')].value or '')[:60],
    })

# Batch aufteilen
batch_entries = [e for i,e in enumerate(all_entries) if i % total_batches == batch_id]
log = f"verify_batch_{batch_id}.log"

results = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for e in batch_entries:
        nr, url, makler, name = e['nr'], e['url'], e['makler'], e['name']
        our_img = f'bilder/{nr}_main.jpg'
        result = {'nr': nr, 'name': name, 'status': '', 'img_match': None}

        if not url:
            result['status'] = 'NO_URL'
            results.append(result)
            print(f"Nr.{nr:3d} 🔗 kein URL", flush=True)
            continue

        img_url, http_status = get_main_image(page, url, makler)

        if http_status in [404, 410]:
            result['status'] = f'DELISTED ({http_status})'
            results.append(result)
            print(f"Nr.{nr:3d} ❌ DELISTED {http_status} | {name[:40]}", flush=True)
            continue

        if not img_url:
            result['status'] = f'NO_IMG ({http_status})'
            results.append(result)
            print(f"Nr.{nr:3d} ❓ kein Bild | {name[:40]}", flush=True)
            continue

        result['status'] = 'OK'
        result['live_img'] = img_url

        if not os.path.exists(our_img):
            result['img_match'] = 'NO_LOCAL'
            results.append(result)
            continue

        try:
            r = requests.get(img_url, timeout=10,
                           headers={'User-Agent':'Mozilla/5.0','Referer':url})
            if r.status_code == 200 and len(r.content) > 10000:
                live_hash = hashlib.md5(r.content).hexdigest()
                our_hash = md5(our_img)
                if live_hash == our_hash:
                    result['img_match'] = 'MATCH'
                    print(f"Nr.{nr:3d} ✅ | {name[:40]}", flush=True)
                else:
                    open(our_img, 'wb').write(r.content)
                    result['img_match'] = 'FIXED'
                    print(f"Nr.{nr:3d} 🔄 BILD KORRIGIERT | {name[:40]}", flush=True)
            else:
                result['img_match'] = f'IMG_ERR {r.status_code}'
        except Exception as ex:
            result['img_match'] = f'ERR: {str(ex)[:30]}'

        results.append(result)

    browser.close()

with open(f'verify_result_{batch_id}.json', 'w') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

ok = sum(1 for r in results if r.get('img_match')=='MATCH')
fixed = sum(1 for r in results if r.get('img_match')=='FIXED')
delisted = sum(1 for r in results if 'DELISTED' in r.get('status',''))
print(f"\nBatch {batch_id}: ✅{ok} 🔄{fixed} ❌{delisted} von {len(results)}", flush=True)
