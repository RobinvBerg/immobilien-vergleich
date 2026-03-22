#!/usr/bin/env python3
"""
Kensington Full Scraper mit Camoufox — alle Felder via werte-Div Parser
Usage: python scrape_kensington_full.py --urls /tmp/kensington_candidates.txt --out /tmp/kensington_scraped.csv
"""
import re, time, csv, argparse
from camoufox.sync_api import Camoufox

ETV_KW = ['etv', 'tourist licence', 'rental licence', 'holiday rental', 'ferienvermiet', 'vermietlizenz', 'agrotourismo', 'lizenz zur ferienvermietung']
GUEST_KW = ['gästehaus', 'gaeste', 'gaestehaus', 'annexe', 'nebengebäude', 'nebengebaeude', 'zweites haus', 'guest house', 'guest apartment', 'two houses', 'zwei häuser']

def clean(s):
    return re.sub(r'\s+', ' ', s).strip() if s else ''

def parse_werte(html):
    """Extrahiert alle Label=Wert Paare aus den .werte Divs"""
    pairs = re.findall(
        r'<div class="werte"[^>]*>.*?<div class="high"[^>]*>(.*?)</div>.*?<span>([^<]+)</span>.*?</div>',
        html, re.DOTALL
    )
    data = {}
    for val_html, label in pairs:
        val = clean(re.sub(r'<[^>]+>', ' ', val_html))
        val = re.sub(r'[~\s]+', ' ', val).strip()
        label = label.strip()
        if label and val:
            data[label] = val
    return data

def parse(html, url):
    tl = html.lower()
    w = parse_werte(html)

    # Titel
    titel_m = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
    titel = clean(titel_m.group(1).replace('Kensington','').replace('|','').strip()) if titel_m else ''

    # Preis
    preis = ''
    pm = re.search(r'([\d\.]+)\s*EUR\s*(?:Purchase price|Kaufpreis)', re.sub(r'<[^>]+>',' ',html))
    if pm:
        preis = pm.group(1).replace('.','').replace(',','')

    # Felder aus werte-Divs
    haustyp  = w.get('Type of property', w.get('Objektart', ''))
    wohnfl   = w.get('Living space', w.get('Wohnfläche', '')).replace('m²','').strip()
    grundst  = w.get('Plot size', w.get('Grundstück', '')).replace('m²','').strip()
    baujahr  = w.get('Year of construction', w.get('Baujahr', ''))
    zustand  = w.get('Condition', w.get('Zustand', ''))
    baeder   = w.get('Bathrooms', w.get('Badezimmer', ''))
    bedrooms = w.get('Bedrooms', w.get('Schlafzimmer', ''))
    parking  = w.get('Parking space', w.get('Stellplätze', ''))

    # Zimmer: Kensington hat nur Bedrooms, kein Total-Zimmer Feld
    # Schätzen: Bedrooms + 2 (Wohn+Küche) wenn vorhanden
    zimmer = ''
    if bedrooms:
        try: zimmer = str(int(bedrooms) + 2)
        except: zimmer = bedrooms

    # Ref
    ref_m = re.search(r'([A-Z]{2,}[A-Z0-9]{3,})\s*Ref\.Nr\.', re.sub(r'<[^>]+>',' ',html))
    ref = ref_m.group(1) if ref_m else ''

    # Ort aus Slug
    slug = url.split('/expose/')[-1].split('?')[0]
    ort_m = re.search(r'(?:^|-)(?:in|bei|naehe|near|in-der-naehe-von)-([a-z][a-z\-]+?)(?:-k[a-z]{1,3}\d|\?|$)', slug)
    ort = ort_m.group(1).replace('-',' ').title() if ort_m else ''

    # ETV / Gästehaus aus Volltext
    text = re.sub(r'<[^>]+>', ' ', html).lower()
    etv    = 'Ja' if any(k in text for k in ETV_KW) else ''
    gaeste = 'Ja' if any(k in text for k in GUEST_KW) else ''

    # Beschreibung — nach "Description:" im Text
    text_plain = re.sub(r'<[^>]+>', ' ', html)
    text_plain = re.sub(r'\s+', ' ', text_plain)
    desc = ''
    for pat in [r'Description:\s*(.{80,600}?)(?:\s{3,})', r'Objektbeschreibung\s+(.{80,600}?)(?:\s{3,})']:
        dm = re.search(pat, text_plain, re.IGNORECASE | re.DOTALL)
        if dm:
            desc = clean(dm.group(1))[:400]
            break

    # Bild (og:image)
    img_m = re.search(r'property="og:image"\s+content="([^"]+)"', html)
    if not img_m:
        img_m = re.search(r'content="([^"]+)"\s+property="og:image"', html)
    bild = img_m.group(1) if img_m else ''

    return {
        'URL': url, 'Titel': titel, 'Ort': ort,
        'Haustyp': haustyp, 'Preis': preis,
        'Zimmer_gesamt': zimmer, 'Bedrooms': bedrooms, 'Bäder': baeder,
        'Wohnfläche': wohnfl, 'Grundstück': grundst,
        'Baujahr': baujahr, 'Zustand': zustand, 'Parking': parking,
        'ETV': etv, 'Gästehaus': gaeste,
        'Ref': ref, 'Beschreibung': desc, 'Bild': bild
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--urls', required=True)
    ap.add_argument('--out', default='/tmp/kensington_scraped.csv')
    args = ap.parse_args()

    urls = [l.strip() for l in open(args.urls) if l.strip().startswith('http')]
    print(f'{len(urls)} URLs')

    fields = ['URL','Titel','Ort','Haustyp','Preis','Zimmer_gesamt','Bedrooms','Bäder','Wohnfläche','Grundstück','Baujahr','Zustand','Parking','ETV','Gästehaus','Ref','Beschreibung','Bild']

    with open(args.out, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        with Camoufox(headless=True) as browser:
            page = browser.new_page()
            for i, url in enumerate(urls, 1):
                slug = url.split('/expose/')[-1][:55]
                print(f'[{i}/{len(urls)}] {slug}')
                try:
                    page.goto(url, timeout=30000, wait_until='domcontentloaded')
                    time.sleep(2)
                    html = page.content()
                    row = parse(html, url)
                    writer.writerow(row)
                    f.flush()
                    print(f'  → {row["Haustyp"]:12} {row["Preis"]:>10}€  {row["Bedrooms"]}Bed/{row["Bäder"]}Bad  {row["Wohnfläche"]}m²  {row["Ort"]}')
                except Exception as e:
                    print(f'  → FEHLER: {e}')
                    writer.writerow({k: '' for k in fields} | {'URL': url, 'Titel': f'FEHLER: {e}'})
                    f.flush()

    print(f'\n✅ Fertig → {args.out}')

if __name__ == '__main__':
    main()
