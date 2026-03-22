#!/usr/bin/env python3
import json, openpyxl, requests, time, re, random, sys
from pathlib import Path

EXCEL = '/Users/robin/.openclaw/workspace/mallorca-projekt/Mallorca_Markt_Gesamt.xlsx'
PROGRESS = '/Users/robin/.openclaw/workspace/mallorca-projekt/fetchdetails_progress.json'
PROXY_USER = 'sp1e6lma32-country-es'
PROXY_PASS = 'pxjc5K6_LBg3Is6vzo'
from urllib.parse import quote
PROXY = f'http://{quote(PROXY_USER, safe="")}:{quote(PROXY_PASS, safe="")}@gate.decodo.com:10001'
PROXIES = {'http': PROXY, 'https': PROXY}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
}

def extract_plot(html):
    patterns = [
        r'"superficieParcela"\s*:\s*(\d+)',
        r'"plotArea"\s*:\s*(\d+)',
        r'"superficie_parcela"\s*:\s*(\d+)',
        r'"surfacePlot"\s*:\s*(\d+)',
        r'"plotSurface"\s*:\s*(\d+)',
        r'"landSurface"\s*:\s*(\d+)',
        r'"terreno"\s*:\s*(\d+)',
    ]
    for p in patterns:
        m = re.search(p, html, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            if val > 0:
                return val
    return None

def fetch_url(url):
    try:
        r = requests.get(url, headers=HEADERS, proxies=PROXIES, timeout=20)
        if r.status_code == 200:
            return r.text
        print(f'  HTTP {r.status_code}')
        return None
    except Exception as e:
        print(f'  Error: {e}')
        return None

# Load progress
with open(PROGRESS) as f:
    progress = json.load(f)

# Load Excel
wb = openpyxl.load_workbook(EXCEL)
ws = wb.active
headers_row = [cell.value for cell in ws[1]]

url_col_idx = headers_row.index('URL')
plot_col_idx = headers_row.index('Grundstück (m²)')

# Collect pending Fotocasa rows
pending_rows = []
for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
    url = row[url_col_idx].value
    if url and 'fotocasa' in str(url) and url not in progress:
        pending_rows.append((row_idx, url, row))

print(f'Pending Fotocasa URLs: {len(pending_rows)}')

test_mode = '--test' in sys.argv
if test_mode:
    pending_rows = pending_rows[:3]
    print('TEST MODE: 3 URLs only')

save_counter = 0
found_plot = 0
for i, (row_idx, url, row) in enumerate(pending_rows):
    print(f'[{i+1}/{len(pending_rows)}] {url[:80]}')
    html = fetch_url(url)
    plot = None
    if html:
        plot = extract_plot(html)
        if plot:
            found_plot += 1
        print(f'  plot={plot}')

    progress[url] = {'plot': plot, 'done': True}

    if plot is not None:
        cell = row[plot_col_idx]
        if not cell.value or cell.value == 0:
            cell.value = plot

    save_counter += 1
    if save_counter >= 50 or i == len(pending_rows) - 1:
        with open(PROGRESS + '.tmp', 'w') as f:
            json.dump(progress, f)
        import os, shutil
        os.replace(PROGRESS + '.tmp', PROGRESS)
        EXCEL_TMP = EXCEL + '.tmp'
        wb.save(EXCEL_TMP)
        shutil.copy2(EXCEL_TMP, EXCEL)
        os.remove(EXCEL_TMP)
        print(f'  --> Saved ({i+1} done, {found_plot} plots found so far)')
        save_counter = 0

    if i < len(pending_rows) - 1:
        time.sleep(random.uniform(1.0, 2.0))

print(f'\nFertig! {len(pending_rows)} URLs verarbeitet, {found_plot} Grundstücksgrößen gefunden.')

# Final pool
print('\n=== NEUER POOL (>=5Z, >=2.9M€, kein Nordost, >=7000m²) ===')
pool = []
for row in ws.iter_rows(min_row=2, values_only=True):
    titel  = row[0] or ''
    preis  = row[3]
    zimmer = row[4]
    grund  = row[5]
    ort    = row[7] or ''

    if not (preis and zimmer and grund):
        continue
    try:
        preis_val  = float(str(preis).replace('.','').replace(',','.').replace('€','').strip())
        zimmer_val = float(str(zimmer))
        grund_val  = float(str(grund))
    except:
        continue

    nordost = ['alcudia','pollença','pollenca','artà','arta','can picafort','son serra']
    if any(kw in ort.lower() for kw in nordost):
        continue

    if zimmer_val >= 5 and preis_val >= 2_900_000 and grund_val >= 7_000:
        pool.append((titel, preis_val, zimmer_val, grund_val, ort))

pool.sort(key=lambda x: -x[1])
print(f'Treffer: {len(pool)}')
for p in pool[:40]:
    print(f'  {p[4]:<30} {p[0][:45]:<45} | {p[1]/1e6:.2f}M€ | {int(p[2])}Z | {int(p[3])}m²')
