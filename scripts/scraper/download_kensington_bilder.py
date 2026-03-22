#!/usr/bin/env python3
"""
Lädt Bilder von Kensington-Seiten via Camoufox (mit Session/Cookies)
"""
import csv, re, time, sys
from pathlib import Path
from camoufox.sync_api import Camoufox

rows = list(csv.DictReader(open('/tmp/kensington_scraped.csv')))

raus_slugs = ['charmante-finca-in-der-naehe-des-renommierten-port-dandratx','charmantes-haus-auf-dem-land','charmantes-haus-mit-weitem-blick','eine-neu-erbaute-natursteinfinca-in-sineu','grundstueck-mit-projekt','kpo01754','kpo01842','luxus-neubau-villa-mit-privatem-pool-im-herzen-von-andratx','mediterrane-villa-mit-pool-und-meerblick-in-bester-lage','raffinierte-mediterrane-neubau-eleganz','wunderschoen-sanierte-villa','zeitlos-moderner-bungalow','refurbished-villa-with-pool-large-garden']
rein_slugs = ['exklusive-neubauvilla-mit-pool-und-elegantem-design-in-marratxi','finca-anwesen-bei-manacor-mit-panoramablick','kpp07070','leben-in-perfekter-harmonie','luxus-oase-fuer-pferdeliebhaber-in-calvia','mediterraner-luxus-mit-atemberaubendem-meerblick-ksp01785','high-quality-modernized-finca-in-arta','impressive-new-build-property-with-panoramic-views-and-pool-in-costitx']

outdir = Path('html/kensington_bilder')
outdir.mkdir(exist_ok=True)

candidates = []
for r in rows:
    slug = r['URL'].split('/expose/')[-1].split('?')[0]
    if any(k in slug for k in raus_slugs): continue
    zimmer = int(r['Bedrooms']) + 2 if r['Bedrooms'] else 0
    flaeche = float(re.sub(r'[^\d\.]','',r['Wohnfläche'])) if r['Wohnfläche'] else 0
    if (zimmer >= 6 and flaeche >= 250) or any(k in slug for k in rein_slugs):
        candidates.append(r)

print(f'{len(candidates)} Bilder laden via Camoufox...')
ok = 0

with Camoufox(headless=True) as browser:
    page = browser.new_page()
    for i, r in enumerate(candidates):
        fname = outdir / f'{i:03d}.jpg'
        # Seite laden
        page.goto(r['URL'], timeout=30000, wait_until='domcontentloaded')
        time.sleep(2)
        
        # Bild-URL aus geladener Seite holen
        bild_url = r['Bild']
        if not bild_url:
            # Versuche og:image aus aktuellem HTML
            html = page.content()
            m = re.search(r'property="og:image"\s+content="([^"]+)"', html)
            if not m:
                m = re.search(r'content="([^"]+)"\s+property="og:image"', html)
            bild_url = m.group(1) if m else None

        if not bild_url:
            print(f'[{i}] kein Bild-URL')
            continue

        # Bild mit Session-Cookies laden
        try:
            resp = page.request.get(bild_url, headers={
                'Referer': r['URL'],
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            })
            data = resp.body()
            # Prüfen ob echtes Bild (JPG/PNG/WebP fangen mit bytes)
            if data[:3] in [b'\xff\xd8\xff', b'\x89PN', b'RIF'] or data[:4] == b'RIFF':
                fname.write_bytes(data)
                ok += 1
                if i % 10 == 0: print(f'[{i}/{len(candidates)}] {ok} ok')
            else:
                print(f'[{i}] kein Bild-Daten ({len(data)} bytes)')
        except Exception as e:
            print(f'[{i}] FEHLER: {e}')

print(f'\n✅ {ok}/{len(candidates)} Bilder gespeichert')
