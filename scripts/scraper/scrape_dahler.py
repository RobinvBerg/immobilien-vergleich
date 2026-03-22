#!/usr/bin/env python3
"""
DAHLER Scraper mit Camoufox
Filter: ≥2,9M €, ≥5 Zimmer, Grundstück ≥7.000m²
Regionen: Zentrum + Süden (kein Nordosten, kein Calvià/Andratx/Palma)
"""
import re, time, csv, json
from camoufox.sync_api import Camoufox

ZIEL_URL = "https://www.dahlercompany.com/de/mallorca/immobilie-kaufen"

AUSSCHLUSS_ORTE = [
    'calvià', 'andratx', 'palma', 'son vida', 'paguera', 'santa ponsa',
    'pollença', 'pollensa', 'alcúdia', 'alcudia', 'manacor', 'artà', 'arta',
    'capdepera', 'son servera', 'portals', 'bendinat'
]

MIN_PREIS = 2_900_000
MIN_ZIMMER = 5
MIN_GRUNDSTUECK = 7_000

def clean(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()

def parse_zahl(s):
    if not s: return None
    s = re.sub(r'[^\d]', '', str(s))
    return int(s) if s else None

results = []

with Camoufox(headless=True) as browser:
    page = browser.new_page()
    print(f"Lade {ZIEL_URL}...")
    page.goto(ZIEL_URL, wait_until="networkidle", timeout=30000)
    time.sleep(2)

    # Alle Objekt-Links sammeln
    links = page.eval_on_selector_all(
        'a[href*="/immobilie-kaufen/"]',
        'els => [...new Set(els.map(e => e.href))]'
    )
    object_links = [l for l in links if re.search(r'/immobilie-kaufen/[^/]+/[^/]+', l)]
    print(f"Gefunden: {len(object_links)} Objekt-Links")

    for url in object_links:
        try:
            page.goto(url, wait_until="networkidle", timeout=20000)
            time.sleep(1)

            titel = clean(page.title().split('|')[0])
            html = page.content()

            # Preis
            preis_match = re.search(r'([\d\.]+)\s*€', html.replace('\xa0', ''))
            preis = parse_zahl(preis_match.group(1)) if preis_match else None

            # Zimmer
            zimmer_match = re.search(r'(\d+)\s*Zimmer', html)
            zimmer = int(zimmer_match.group(1)) if zimmer_match else None

            # Grundstück
            grundstueck_match = re.search(r'([\d\.]+)\s*m².*?Grundstück|Grundstück.*?([\d\.]+)\s*m²', html)
            grundstueck = None
            if grundstueck_match:
                g = grundstueck_match.group(1) or grundstueck_match.group(2)
                grundstueck = parse_zahl(g)

            # Ort
            ort_match = re.search(r'"addressLocality"\s*:\s*"([^"]+)"', html)
            ort = ort_match.group(1) if ort_match else ''

            # Filter
            if preis and preis < MIN_PREIS:
                print(f"  SKIP (Preis {preis:,}): {titel[:50]}")
                continue
            if zimmer and zimmer < MIN_ZIMMER:
                print(f"  SKIP (Zimmer {zimmer}): {titel[:50]}")
                continue
            if any(a in ort.lower() for a in AUSSCHLUSS_ORTE):
                print(f"  SKIP (Ort {ort}): {titel[:50]}")
                continue

            print(f"  ✅ {titel[:50]} | {preis:,}€ | {zimmer}Zi | {grundstueck}m² | {ort}")
            results.append({
                'titel': titel,
                'url': url,
                'preis': preis,
                'zimmer': zimmer,
                'grundstueck': grundstueck,
                'ort': ort,
            })

        except Exception as e:
            print(f"  FEHLER {url}: {e}")
            continue

# CSV speichern
out = "/tmp/dahler_kandidaten.csv"
with open(out, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['titel','url','preis','zimmer','grundstueck','ort'])
    writer.writeheader()
    writer.writerows(results)

print(f"\n✅ {len(results)} Kandidaten → {out}")
