#!/usr/bin/env python3
"""
LivingBlue Komplett-Rebuild:
- Alle ~1050 Objekte via API (verschiedene Sort-Parameter)
- Korrekte URLs (numericId-Format)
- Bilder herunterladen
- 113 Kandidaten matchen
"""
import json, re, requests, os, openpyxl
from difflib import SequenceMatcher
from playwright.sync_api import sync_playwright

os.makedirs('lb_bilder', exist_ok=True)

def sim(a, b):
    return SequenceMatcher(None, a.lower()[:100], b.lower()[:100]).ratio()

def make_url(slug, nid):
    s = re.sub(r'[^a-z0-9]+', '-', str(slug).lower().strip()).strip('-')
    return f"https://www.livingblue-mallorca.com/de-de/immobilie/{s}/{nid}" if s and nid else ''

# ── Schritt 1: Session + API-URL holen ──────────────────────────────────────
print("Schritt 1: Browser-Session holen...", flush=True)
session_data = {}

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()

    def capture(resp):
        if 'egorealestate.com/v1/Properties' in resp.url and 'SearchOptions' not in resp.url:
            if 'base_url' not in session_data:
                session_data['base_url'] = resp.url
                session_data['headers'] = dict(resp.request.headers)
                print(f"  API gefangen: ...{resp.url[-80:]}", flush=True)

    page.on('response', capture)
    page.goto('https://www.livingblue-mallorca.com/de-de/immobilien',
              wait_until='domcontentloaded', timeout=20000)
    page.wait_for_timeout(5000)
    cookies = page.context.cookies()
    b.close()

if 'base_url' not in session_data:
    print("❌ API nicht gefangen!")
    exit(1)

hdrs = session_data['headers']
hdrs['cookie'] = '; '.join([f"{c['name']}={c['value']}" for c in cookies])
base = re.sub(r'nre=\d+', 'nre=250', session_data['base_url'])
# _= timestamp entfernen (kann veralten)
base = re.sub(r'&_=\d+', '', base)

# ── Schritt 2: Alle Objekte via verschiedene Sort-Parameter ─────────────────
# srt= 25=Standard, 1=Preis↑, 2=Preis↓, 3=Datum↓, 4=Datum↑, 5=Zimmer↓
SORT_PARAMS = [25, 1, 2, 3, 4, 5, 6, 7]
all_props = {}

print("\nSchritt 2: Alle Objekte laden...", flush=True)
for srt in SORT_PARAMS:
    url = re.sub(r'srt=\d+', f'srt={srt}', base)
    try:
        r = requests.get(url, headers=hdrs, timeout=30)
        if r.status_code == 200:
            d = r.json()
            props = d.get('Properties', [])
            new = 0
            for prop in props:
                nid = str(prop.get('ID', '')).strip()
                if nid and nid not in all_props:
                    all_props[nid] = prop
                    new += 1
            print(f"  srt={srt}: {len(props)} props, {new} neu → gesamt {len(all_props)}", flush=True)
        else:
            print(f"  srt={srt}: HTTP {r.status_code}", flush=True)
    except Exception as e:
        print(f"  srt={srt}: Fehler {e}", flush=True)

print(f"\nGesamt unique Objekte: {len(all_props)}", flush=True)

# ── Schritt 3: Daten normalisieren + Bilder laden ───────────────────────────
print("\nSchritt 3: Bilder laden...", flush=True)
lb_complete = []
downloaded = 0

for nid, prop in all_props.items():
    imgs = prop.get('Images') or []
    img_url = ''
    if imgs:
        img_url = imgs[0].get('Thumbnail', '').replace('Z800x600', 'Z1280x960').replace('Z400x300', 'Z1280x960')

    local_img = ''
    if img_url:
        try:
            r = requests.get(img_url, timeout=8)
            if r.status_code == 200 and len(r.content) > 10000:
                fname = f"lb_bilder/{nid}.jpg"
                open(fname, 'wb').write(r.content)
                local_img = fname
                downloaded += 1
        except:
            pass

    url = make_url(prop.get('Slug', ''), nid)
    preis_raw = str(prop.get('Price') or '0').replace(',', '.').replace(' ', '')
    try:
        preis = float(preis_raw) if preis_raw else 0
    except:
        preis = 0

    lb_complete.append({
        'numId': nid,
        'uid': str(prop.get('UID', '')),
        'title': str(prop.get('Title', '')).strip(),
        'price': preis,
        'zimmer': int(prop.get('Rooms') or 0),
        'baeder': int(prop.get('Bathrooms') or 0),
        'flaeche': float(prop.get('NetArea') or prop.get('GrossArea') or 0),
        'grundst': float(prop.get('LandArea') or 0),
        'ort': str(prop.get('Municipality', '')).strip(),
        'url': url,
        'img_url': img_url,
        'local_img': local_img,
        'typ': str(prop.get('Type', '')),
    })
    if downloaded % 50 == 0 and downloaded > 0:
        print(f"  {downloaded}/{len(all_props)} Bilder...", flush=True)

with open('lb_complete.json', 'w') as f:
    json.dump(lb_complete, f, ensure_ascii=False, indent=2)

print(f"  ✅ {downloaded}/{len(lb_complete)} Bilder geladen", flush=True)
print(f"  lb_complete.json: {len(lb_complete)} Objekte", flush=True)

# ── Schritt 4: 113 Kandidaten matchen ───────────────────────────────────────
print("\nSchritt 4: Kandidaten matchen...", flush=True)

wb = openpyxl.load_workbook('mallorca-kandidaten-v2.xlsx', read_only=True)
ws = wb.active
hk = [c.value for c in ws[1]]
kandidaten = {}
for row in ws.iter_rows(min_row=2):
    if not row[0].value: continue
    if 'living' not in str(row[hk.index('Makler')].value or '').lower(): continue
    kandidaten[int(row[0].value)] = {
        'name': str(row[hk.index('Name')].value or '').strip(),
        'preis': float(row[hk.index('Preis (€)')].value or 0),
        'ort': str(row[hk.index('Location')].value or '').lower(),
    }

# Alle Scores berechnen
scores = []
for nr, k in kandidaten.items():
    for prop in lb_complete:
        title_sc = sim(k['name'], prop['title'])
        preis_ok = abs(prop['price'] - k['preis']) / max(k['preis'], 1) < 0.03 if prop['price'] > 0 and k['preis'] > 0 else False
        ort_ok = k['ort'].split()[0] in prop['ort'].lower() if k['ort'] else False
        sc = title_sc * 5 + (3 if preis_ok else 0) + (1 if ort_ok else 0)
        scores.append((sc, nr, prop['numId']))

scores.sort(key=lambda x: -x[0])

# Greedy 1:1 Assignment
used_nr = set()
used_nid = set()
final = {}

for sc, nr, nid in scores:
    if nr in used_nr or nid in used_nid: continue
    final[nr] = {'nid': nid, 'score': sc}
    used_nr.add(nr)
    used_nid.add(nid)
    if len(final) == len(kandidaten): break

# Ergebnisse
high = {nr: d for nr, d in final.items() if d['score'] >= 4}
mid  = {nr: d for nr, d in final.items() if 3 <= d['score'] < 4}
low  = {nr: d for nr, d in final.items() if d['score'] < 3}

print(f"  ✅ High-confidence (≥4): {len(high)}", flush=True)
print(f"  ⚠️  Mid-confidence (3–4): {len(mid)}", flush=True)
print(f"  ❌ Low-confidence (<3, delisted?): {len(low)}", flush=True)

# ── Schritt 5: Excel + bilder/ + HTML aktualisieren ─────────────────────────
print("\nSchritt 5: Excel + Bilder aktualisieren...", flush=True)

prop_by_nid = {p['numId']: p for p in lb_complete}

wb = openpyxl.load_workbook('mallorca-kandidaten-v2.xlsx')
ws = wb.active
headers = [c.value for c in ws[1]]
url_col = headers.index('Link Objekt (URL)') + 1
komm_col = headers.index('Kommentar') + 1

for row in ws.iter_rows(min_row=2):
    if not row[0].value: continue
    nr = int(row[0].value)
    if nr not in final: continue
    d = final[nr]
    prop = prop_by_nid.get(d['nid'], {})

    if d['score'] >= 3:
        row[url_col-1].value = prop.get('url', '')
        # Kommentar bereinigen
        if '⚠️ delisted' in str(row[komm_col-1].value or ''):
            row[komm_col-1].value = ''
        # Bild kopieren
        src = prop.get('local_img', '')
        if src and os.path.exists(src):
            import shutil
            shutil.copy(src, f'bilder/{nr}_main.jpg')
    else:
        row[url_col-1].value = ''
        row[komm_col-1].value = '⚠️ delisted / nicht mehr auf LivingBlue'

wb.save('mallorca-kandidaten-v2.xlsx')
print("  Excel gespeichert", flush=True)

# HTML
import re as _re
wb = openpyxl.load_workbook('mallorca-kandidaten-v2.xlsx', read_only=True)
ws = wb.active
headers = [c.value for c in ws[1]]
html_props = []
for row in ws.iter_rows(min_row=2):
    if not row[0].value: continue
    nr = int(row[0].value)
    komm = str(row[headers.index('Kommentar')].value or '')
    html_props.append({
        "nr": nr,
        "name": row[headers.index("Name")].value or "",
        "url": row[headers.index("Link Objekt (URL)")].value or "",
        "charme": int(row[headers.index("Charme/Ästhetik (1-5)")].value or 0),
        "zimmer": int(row[headers.index("Zimmer")].value or 0),
        "grundst": float(row[headers.index("Grundstücksgröße (m²)")].value or 0),
        "flaeche": float(row[headers.index("Bebaute Fläche (m²)")].value or 0),
        "ort": row[headers.index("Location")].value or "",
        "flughafen_min": float(row[headers.index("Entfernung Flughafen (min)")].value or 0),
        "daia_min": float(row[headers.index("Entfernung Daia Haus (min)")].value or 0),
        "andratx_km": float(row[headers.index("Entfernung Andratx (km)")].value or 0),
        "andratx_min": float(row[headers.index("Entfernung Andratx (min)")].value or 0),
        "salines_km": float(row[headers.index("Entfernung Ses Salines (km)")].value or 0),
        "salines_min": float(row[headers.index("Entfernung Ses Salines (min)")].value or 0),
        "preis": float(row[headers.index("Preis (€)")].value or 0),
        "preis_m2_bebaut": float(row[headers.index("€/m² (bebaut)")].value or 0),
        "reno": int(row[headers.index("Renovierung (0-100)")].value or 0),
        "makler": row[headers.index("Makler")].value or "",
        "score": float(row[headers.index("Score (0-100)")].value or 0),
        "rang": int(row[headers.index("Rang")].value or 999),
        "img": f"bilder/{nr}_main.jpg" if os.path.exists(f"bilder/{nr}_main.jpg") else "",
        "delisted": '⚠️ delisted' in komm,
    })

html_props.sort(key=lambda x: x["rang"])
with open('mallorca.html', 'r') as f: html = f.read()
html = _re.sub(r'const DATA = \[.*?\];', 'const DATA = ' + json.dumps(html_props, ensure_ascii=False) + ';', html, flags=_re.DOTALL)
with open('mallorca.html', 'w') as f: f.write(html)

print("  mallorca.html aktualisiert", flush=True)

print(f"""
╔══════════════════════════════════════════════════════╗
║  LivingBlue Rebuild FERTIG                           ║
╠══════════════════════════════════════════════════════╣
║  DB:      {len(lb_complete):4d} Objekte in lb_complete.json         ║
║  Bilder:  {downloaded:4d} in lb_bilder/                       ║
║  Matches: {len(high):4d} high / {len(mid):4d} mid / {len(low):4d} delisted           ║
╚══════════════════════════════════════════════════════╝
""", flush=True)
