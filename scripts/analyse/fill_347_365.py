#!/usr/bin/env python3
"""Fill objects 347-365 from Private Property Mallorca into Excel."""

import os, sys, json, time, re, math, requests
from pathlib import Path

WORKDIR = Path("/Users/robin/.openclaw/workspace/mallorca-projekt")
EXCEL_PATH = WORKDIR / "data" / "mallorca-kandidaten-v2.xlsx"
BILDER_DIR = WORKDIR / "bilder"
PROXY = "http://sp1e6lma32:pxjc5K6_LBg3Is6vzo@gate.decodo.com:10001"
GMAPS_KEY = "AIzaSyAzplaFOGUrCygk3mrzS--wrHNIz0arKok"

BILDER_DIR.mkdir(exist_ok=True)

OBJECTS = [
    {"nr": 347, "ort": "Llucmajor", "preis": 2595000, "zimmer": 5, "grundstueck": 15000, "bebaut": 361, "url": "https://www.privatepropertymallorca.com/immobilien/luxurioese-neubau-finca-in-llucmajor/", "coords": "39.4833,2.8833"},
    {"nr": 348, "ort": "Artà/Son Servera", "preis": 2655000, "zimmer": 6, "grundstueck": 92700, "bebaut": 488, "url": "https://www.privatepropertymallorca.com/immobilien/elegante-mediterrane-finca-in-son-servera-bei-arta-auf-grossem-grundstueck-mit-fern-meerblick/", "coords": "39.6983,3.3450"},
    {"nr": 349, "ort": "Calonge", "preis": 2800000, "zimmer": 6, "grundstueck": 5287, "bebaut": 444, "url": "https://www.privatepropertymallorca.com/immobilien/charmante-finca-in-calonge-mit-traumhaftem-parkaehnlichem-garten/", "coords": "39.3333,3.1667"},
    {"nr": 350, "ort": "Alqueria Blanca", "preis": 3150000, "zimmer": 5, "grundstueck": 28000, "bebaut": 800, "url": "https://www.privatepropertymallorca.com/immobilien/einzigartige-finca-in-lalqueria-blanca-in-einem-naturschutzgebiet-gelegen/", "coords": "39.3500,3.0833"},
    {"nr": 351, "ort": "Llucmajor", "preis": 3400000, "zimmer": 10, "grundstueck": 18500, "bebaut": 734, "url": "https://www.privatepropertymallorca.com/immobilien/herrschaftliche-naturstein-finca-in-llucmajor-mit-grossem-garten-pool-und-ferienvermietungslizenz/", "coords": "39.4833,2.8833"},
    {"nr": 352, "ort": "Santanyí", "preis": 3300000, "zimmer": 6, "grundstueck": 14955, "bebaut": 650, "url": "https://www.privatepropertymallorca.com/immobilien/mallorquinische-finca-mit-herrlichem-weitblick-ueber-die-landschaft-und-viel-privatsphaere-in-santanyi/", "coords": "39.3554,3.1243"},
    {"nr": 353, "ort": "Andratx", "preis": 3900000, "zimmer": 5, "grundstueck": 62507, "bebaut": 496, "url": "https://www.privatepropertymallorca.com/immobilien/charmante-finca-in-andratx-mit-pool-viel-privatsphaere-und-fern-meerblick/", "coords": "39.5747,2.3818"},
    {"nr": 354, "ort": "Manacor", "preis": 3975000, "zimmer": 5, "grundstueck": 30000, "bebaut": 844, "url": "https://www.privatepropertymallorca.com/immobilien/elegante-finca-nah-zu-manacor-mit-infinity-pool-und-herrlichen-fernblick-zum-meer-und-auf-die-berge/", "coords": "39.7067,3.2133"},
    {"nr": 355, "ort": "Ses Salines", "preis": 4295000, "zimmer": 5, "grundstueck": 16580, "bebaut": 680, "url": "https://www.privatepropertymallorca.com/immobilien/exclusive-neubaufinca-in-ses-salines-mit-viel-privatsphaere/", "coords": "39.3444,3.0503"},
    {"nr": 356, "ort": "Llucmajor", "preis": 4450000, "zimmer": 5, "grundstueck": 12500, "bebaut": 460, "url": "https://www.privatepropertymallorca.com/immobilien/anwesen-in-llucmajor-mit-privatem-golfplatz-gaestehaus/", "coords": "39.4833,2.8833"},
    {"nr": 357, "ort": "Sa Torre/Llucmajor", "preis": 4500000, "zimmer": 9, "grundstueck": 375533, "bebaut": 1350, "url": "https://www.privatepropertymallorca.com/immobilien/herrliches-grosszuegiges-fincaanwesen-auch-fuer-pferdeliebhaber-bei-llucmajor/", "coords": "39.4833,2.8833"},
    {"nr": 358, "ort": "Establiments", "preis": 4700000, "zimmer": 5, "grundstueck": 15010, "bebaut": 758, "url": "https://www.privatepropertymallorca.com/immobilien/stattliche-finca-in-establiments-mit-gr-pool-privatsphaere-und-herrlichem-blick-auf-die-bucht-von-palma/", "coords": "39.6167,2.6667"},
    {"nr": 359, "ort": "Porreres", "preis": 4950000, "zimmer": 5, "grundstueck": 70000, "bebaut": 682, "url": "https://www.privatepropertymallorca.com/immobilien/imposante-luxus-finca-in-porreres-mit-olivenplantage-weinberg-und-absoluter-privatsphaere/", "coords": "39.5167,3.0333"},
    {"nr": 360, "ort": "Santanyí", "preis": 5490000, "zimmer": 5, "grundstueck": 53567, "bebaut": 1045, "url": "https://www.privatepropertymallorca.com/immobilien/aussergewoehnliche-finca-in-santanyi-in-modernem-design-absoluter-privatsphaere/", "coords": "39.3554,3.1243"},
    {"nr": 361, "ort": "Bunyola", "preis": 6500000, "zimmer": 5, "grundstueck": 30100, "bebaut": 800, "url": "https://www.privatepropertymallorca.com/immobilien/einzigartige-finca-in-bunyola-mit-spektakulaerem-ausblick-und-ferienvermietungslizenz/", "coords": "39.6667,2.7167"},
    {"nr": 362, "ort": "Santa Maria", "preis": 7995000, "zimmer": 5, "grundstueck": 16347, "bebaut": 447, "url": "https://www.privatepropertymallorca.com/immobilien/exklusives-projekt-in-der-naehe-von-santa-maria/", "coords": "39.6333,2.7833"},
    {"nr": 363, "ort": "Sa Rapita", "preis": 9700000, "zimmer": 10, "grundstueck": 18000, "bebaut": 0, "url": "https://www.privatepropertymallorca.com/immobilien/finca-projekt-la-bastida-in-sa-rapita-die-perfektion-der-einfachheit/", "coords": "39.3667,2.9667"},
    {"nr": 364, "ort": "Llucmajor", "preis": 11670000, "zimmer": 9, "grundstueck": 1400000, "bebaut": 1780, "url": "https://www.privatepropertymallorca.com/immobilien/stattliches-herrenhaus-in-llucmajor-auf-riesigem-grundstueck-und-herrlichem-ausblick/", "coords": "39.4833,2.8833"},
    {"nr": 365, "ort": "Campos", "preis": 2250000, "zimmer": 9, "grundstueck": 15449, "bebaut": 560, "url": "https://www.privatepropertymallorca.com/immobilien/finca-bei-campos/", "coords": "39.4333,3.0167"},
]

REFS = {
    "flughafen": "39.5517,2.7388",
    "daia": "39.7456,2.6489",
    "andratx": "39.5747,2.3818",
    "ses_salines": "39.3444,3.0503",
}

def fetch_url(url, timeout=20):
    proxies = {"http": PROXY, "https": PROXY}
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    try:
        r = requests.get(url, proxies=proxies, headers=headers, timeout=timeout)
        return r.text
    except Exception as e:
        print(f"  Fetch error {url}: {e}")
        return ""

def parse_page(html, nr, url):
    """Extract info from property page HTML."""
    result = {"title": "", "description": "", "baeder": None, "baujahr": None, "gaestehaeuser": 0, "vermietlizenz": 0, "img_url": ""}
    
    # Title
    tm = re.search(r'<title[^>]*>([^<]+)</title>', html, re.I)
    if tm:
        result["title"] = tm.group(1).strip().split("|")[0].strip().split("–")[0].strip()
    
    # Meta description
    dm = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
    if dm:
        result["description"] = dm.group(1).strip()
    
    # Try to find description in page
    # Look for property text areas
    desc_m = re.search(r'class="[^"]*description[^"]*"[^>]*>(.*?)</div>', html, re.I|re.S)
    if desc_m:
        text = re.sub(r'<[^>]+>', ' ', desc_m.group(1)).strip()
        if len(text) > 50:
            result["description"] = text[:500]
    
    # Bäder
    bad_m = re.search(r'(\d+)\s*[Bb][äae][dt]', html)
    if bad_m:
        result["baeder"] = int(bad_m.group(1))
    
    # Baujahr
    bj_m = re.search(r'[Bb]au[jJ]ahr[:\s]*(\d{4})', html)
    if bj_m:
        result["baujahr"] = int(bj_m.group(1))
    
    # Vermietlizenz
    if re.search(r'[Ff]erienvermiet|ETV|tourist.*licen|Vermietlizenz|Ferienvermietungslizenz', html, re.I):
        result["vermietlizenz"] = 100
    
    # Gästehäuser
    gh_m = re.search(r'(\d+)\s*[Gg][äa][su][st][te][^a-z]?haus', html)
    if gh_m:
        result["gaestehaeuser"] = int(gh_m.group(1))
    elif re.search(r'[Gg][äa]stehaus|[Gg]uest[- ]?house|[Nn]ebengebäude|[Aa]nnex', html, re.I):
        result["gaestehaeuser"] = 1
    
    # Main image - look for og:image or first property image
    img_m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
    if not img_m:
        img_m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I)
    if img_m:
        result["img_url"] = img_m.group(1)
    else:
        # Try to find first large image
        imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I)
        for img in imgs:
            if any(x in img.lower() for x in ['property', 'finca', 'house', 'immobil', 'uploads', 'wp-content']):
                result["img_url"] = img
                break
    
    return result

def download_image(img_url, nr):
    if not img_url:
        print(f"  No image URL for {nr}")
        return False
    path = BILDER_DIR / f"{nr}_main.jpg"
    if path.exists():
        print(f"  Image already exists: {path}")
        return True
    try:
        proxies = {"http": PROXY, "https": PROXY}
        r = requests.get(img_url, proxies=proxies, timeout=30, stream=True)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            print(f"  Saved image: {path}")
            return True
    except Exception as e:
        print(f"  Image download error: {e}")
    return False

def get_distances_gmaps(coords_str):
    """Get driving distances to all 4 reference points."""
    results = {}
    origins = coords_str
    for ref_name, ref_coords in REFS.items():
        url = (f"https://maps.googleapis.com/maps/api/distancematrix/json"
               f"?origins={origins}&destinations={ref_coords}"
               f"&mode=driving&key={GMAPS_KEY}")
        try:
            r = requests.get(url, timeout=10)
            data = r.json()
            elem = data["rows"][0]["elements"][0]
            if elem["status"] == "OK":
                km = round(elem["distance"]["value"] / 1000, 1)
                mins = round(elem["duration"]["value"] / 60)
                results[ref_name] = (km, mins)
            else:
                results[ref_name] = (None, None)
        except Exception as e:
            print(f"  GMaps error for {ref_name}: {e}")
            results[ref_name] = (None, None)
        time.sleep(0.1)
    return results

def calc_erreichbarkeit(dists):
    """Calculate Erreichbarkeit score (0-100) from distances."""
    # Ideal/Akzeptabel/Dealbreaker from settings:
    # Flughafen: 15/25/40, Daia: 20/40/70, SesSalines: 15/30/45, Andratx: 25/40/60
    weights = {"flughafen": 0.30, "daia": 0.30, "ses_salines": 0.30, "andratx": 0.10}
    ideals = {"flughafen": 15, "daia": 20, "ses_salines": 15, "andratx": 25}
    akzept = {"flughafen": 25, "daia": 40, "ses_salines": 30, "andratx": 40}
    deal   = {"flughafen": 40, "daia": 70, "ses_salines": 45, "andratx": 60}
    
    total_w = 0
    total_score = 0
    for ref, (_, mins) in dists.items():
        if mins is None:
            # Use 50 as default
            mins = 50
        w = weights[ref]
        i = ideals[ref]; a = akzept[ref]; d = deal[ref]
        if mins <= i:
            s = 100
        elif mins <= a:
            s = 100 - 50 * (mins - i) / (a - i)
        elif mins <= d:
            s = 50 - 50 * (mins - a) / (d - a)
        else:
            s = 0
        total_score += w * s
        total_w += w
    
    return round(total_score / total_w) if total_w > 0 else 50

def calc_bewirtschaftung(grundstueck):
    if grundstueck < 5000: return 1
    elif grundstueck < 20000: return 2
    elif grundstueck < 50000: return 3
    elif grundstueck < 100000: return 4
    else: return 5

def calc_score(obj_data, erreichbarkeit):
    """Calculate overall score based on Einstellungen weights."""
    # Weights: Zimmer&Platz 20, Preis-Leistung 15, Gästehaus 15, Erreichbarkeit 15,
    # Grundstück 10, Vermietlizenz 5, Bewirtschaftung 5, Charme 10, Renovierung 5
    
    zimmer = obj_data.get("zimmer", 5)
    # Zimmer score: min=5, ideal=8
    if zimmer >= 8: z_score = 100
    elif zimmer >= 5: z_score = 50 + 50 * (zimmer - 5) / 3
    else: z_score = max(0, zimmer / 5 * 50)
    
    # Preis-Leistung: €/m²bebaut - lower is better
    # Reference: ~5000 = avg, ~2500 = excellent, ~10000 = poor
    bebaut = obj_data.get("bebaut", 1) or 1
    preis = obj_data.get("preis", 5000000)
    eur_m2 = preis / bebaut
    if eur_m2 <= 3000: pl_score = 100
    elif eur_m2 <= 6000: pl_score = 100 - 50 * (eur_m2 - 3000) / 3000
    elif eur_m2 <= 12000: pl_score = 50 - 50 * (eur_m2 - 6000) / 6000
    else: pl_score = 0
    
    # Gästehaus: 0=0, 1=50, 2+=100
    gh = obj_data.get("gaestehaeuser", 0)
    if gh >= 2: gh_score = 100
    elif gh == 1: gh_score = 50
    else: gh_score = 0
    
    # Erreichbarkeit: already 0-100
    err_score = erreichbarkeit
    
    # Grundstück: min=3000, ideal=15000
    grund = obj_data.get("grundstueck", 5000)
    if grund >= 15000: g_score = 100
    elif grund >= 3000: g_score = 50 + 50 * (grund - 3000) / 12000
    else: g_score = max(0, grund / 3000 * 50)
    
    # Vermietlizenz: 0/50/100 → normalize
    vl = obj_data.get("vermietlizenz", 0)
    vl_score = vl  # already 0-100
    
    # Bewirtschaftung: 1-5 → score (higher=better → 5=pflegeleicht=100, 1=worst=0)
    bew = obj_data.get("bewirtschaftung", 2)
    bew_score = (bew - 1) * 25  # 1→0, 2→25, 3→50, 4→75, 5→100
    
    # Charme: 1-5 → 0-100
    charme = obj_data.get("charme", 3)
    ch_score = (charme - 1) * 25
    
    # Renovierung: 0-100
    reno = obj_data.get("renovierung", 70)
    reno_score = reno
    
    score = (
        z_score * 0.20 +
        pl_score * 0.15 +
        gh_score * 0.15 +
        err_score * 0.15 +
        g_score * 0.10 +
        vl_score * 0.05 +
        bew_score * 0.05 +
        ch_score * 0.10 +
        reno_score * 0.05
    )
    return round(score, 2)

# Charme/Renovierung defaults (will be updated by vision analysis separately)
CHARME_DEFAULTS = {
    347: 4, 348: 4, 349: 4, 350: 3, 351: 4, 352: 3, 353: 4, 354: 4,
    355: 4, 356: 4, 357: 3, 358: 4, 359: 4, 360: 5, 361: 5, 362: 3,
    363: 4, 364: 4, 365: 3
}
RENO_DEFAULTS = {
    347: 95, 348: 80, 349: 80, 350: 75, 351: 70, 352: 80, 353: 80, 354: 85,
    355: 90, 356: 80, 357: 70, 358: 80, 359: 75, 360: 90, 361: 85, 362: 40,
    363: 30, 364: 70, 365: 75
}
RENO_BEGRUENDUNG = {
    347: "Neubau-Finca, einzugsbereit",
    348: "Mediterrane Finca, gut erhalten",
    349: "Charmante Finca mit Garten, gepflegt",
    350: "Finca in Naturschutzgebiet, teilweise renoviert",
    351: "Naturstein-Finca, klassisch, teilw. renovierungsbedürftig",
    352: "Mallorquinische Finca, gepflegt",
    353: "Charmante Finca Andratx, gut erhalten",
    354: "Elegante Finca, modern ausgebaut",
    355: "Exklusive Neubau-Finca, einzugsbereit",
    356: "Anwesen mit Golf, gepflegt",
    357: "Großzügiges Fincaanwesen, älterer Bestand",
    358: "Stattliche Finca Establiments, gut erhalten",
    359: "Luxus-Finca mit Olivenplantage, gepflegt",
    360: "Außergewöhnliche Finca, modernes Design",
    361: "Einzigartige Finca Bunyola, modern renoviert",
    362: "Exklusives Neubauprojekt, Rohbau/Planung",
    363: "Finca-Projekt La Bastida, Planungsphase",
    364: "Herrschaftliches Gut, älterer Bestand, teils renovierungsbedürftig",
    365: "Finca bei Campos, renovierungsbedürftig",
}

def main():
    import openpyxl
    
    print("Loading Excel...")
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb['Mallorca Kandidaten']
    
    all_data = []
    
    for obj in OBJECTS:
        nr = obj["nr"]
        print(f"\n=== Processing {nr} - {obj['ort']} ===")
        
        # Fetch page
        print(f"  Fetching {obj['url']}...")
        html = fetch_url(obj["url"])
        page_data = parse_page(html, nr, obj["url"])
        print(f"  Title: {page_data['title'][:60]}")
        print(f"  Bäder: {page_data['baeder']}, Baujahr: {page_data['baujahr']}, VL: {page_data['vermietlizenz']}, GH: {page_data['gaestehaeuser']}")
        
        # URL-based fallback for vermietlizenz
        if "ferienvermietungslizenz" in obj["url"].lower() or "etv" in obj["url"].lower():
            page_data["vermietlizenz"] = 100
        
        # Download image
        if page_data["img_url"]:
            download_image(page_data["img_url"], nr)
        
        # Google Maps distances
        print(f"  Getting distances from GMaps...")
        dists = get_distances_gmaps(obj["coords"])
        print(f"  Dists: {dists}")
        
        # Calculate fields
        bebaut = obj["bebaut"]
        grundstueck = obj["grundstueck"]
        preis = obj["preis"]
        
        eur_m2_bebaut = round(preis / bebaut) if bebaut > 0 else None
        eur_m2_grund = round(preis / grundstueck, 1) if grundstueck > 0 else None
        garten = grundstueck - bebaut if bebaut > 0 else grundstueck
        bewirtschaftung = calc_bewirtschaftung(grundstueck)
        erreichbarkeit = calc_erreichbarkeit(dists)
        
        charme = CHARME_DEFAULTS.get(nr, 3)
        renovierung = RENO_DEFAULTS.get(nr, 70)
        
        # Gästehaus hints from title/url
        gh = page_data["gaestehaeuser"]
        if "gaestehaus" in obj["url"].lower() or "gastehaus" in obj["url"].lower():
            gh = max(gh, 1)
        if nr == 356:  # "mit privatem golfplatz gaestehaus" in URL
            gh = max(gh, 1)
        
        obj_full = {
            "nr": nr,
            "ort": obj["ort"],
            "preis": preis,
            "zimmer": obj["zimmer"],
            "grundstueck": grundstueck,
            "bebaut": bebaut,
            "gaestehaeuser": gh,
            "vermietlizenz": page_data["vermietlizenz"],
            "bewirtschaftung": bewirtschaftung,
            "charme": charme,
            "renovierung": renovierung,
        }
        erreichbarkeit = calc_erreichbarkeit(dists)
        score = calc_score(obj_full, erreichbarkeit)
        
        # Anzeigename
        title = page_data["title"] or obj["url"].split("/")[-2].replace("-", " ").title()
        # Shorten title
        anzeige = f"{obj['ort']} — {title[:60]}"
        
        # Gebäudestruktur
        struktur = "Finca"
        if "herrenhaus" in obj["url"].lower(): struktur = "Herrenhaus"
        elif "anwesen" in obj["url"].lower(): struktur = "Anwesen"
        elif "projekt" in obj["url"].lower(): struktur = "Neubauprojekt"
        
        row_data = [
            nr,                                    # 1 Ordnungsnummer
            page_data["title"] or f"{obj['ort']} — Finca",  # 2 Name
            obj["url"],                            # 3 URL
            charme,                                # 4 Charme
            obj["zimmer"],                         # 5 Zimmer
            page_data["baeder"],                   # 6 Bäder
            grundstueck,                           # 7 Grundstück
            bebaut if bebaut > 0 else None,        # 8 Bebaut
            garten,                                # 9 Garten
            obj["ort"],                            # 10 Location
            dists["flughafen"][0],                 # 11 Flughafen km
            dists["flughafen"][1],                 # 12 Flughafen min
            dists["daia"][0],                      # 13 Daia km
            dists["daia"][1],                      # 14 Daia min
            dists["andratx"][0],                   # 15 Andratx km
            dists["andratx"][1],                   # 16 Andratx min
            dists["ses_salines"][0],               # 17 SesSalines km
            dists["ses_salines"][1],               # 18 SesSalines min
            preis,                                 # 19 Preis
            eur_m2_bebaut,                         # 20 €/m²bebaut
            eur_m2_grund,                          # 21 €/m²Grund
            renovierung,                           # 22 Renovierung
            bewirtschaftung,                       # 23 Bewirtschaftung
            page_data["vermietlizenz"],            # 24 Vermietlizenz
            erreichbarkeit,                        # 25 Erreichbarkeit
            score,                                 # 26 Score
            None,                                  # 27 SortKey
            None,                                  # 28 Rang
            struktur,                              # 29 Gebäudestruktur
            page_data["baujahr"],                  # 30 Baujahr
            None,                                  # 31 LetzteReno
            renovierung,                           # 32 Reno-Score
            RENO_BEGRUENDUNG.get(nr, ""),          # 33 Reno-Begründung
            None,                                  # 34 Kommentar
            page_data["description"][:500] if page_data["description"] else None,  # 35 Beschreibung
            "Private Property Mallorca",           # 36 Makler
            None,                                  # 37 Makler-Ref
            "Neu",                                 # 38 Link Status
            anzeige,                               # 39 Anzeigename
            gh,                                    # 40 Gästehäuser
        ]
        
        all_data.append({"nr": nr, "score": score, "charme": charme, "ort": obj["ort"], "preis": preis, "row": row_data})
        
        ws.append(row_data)
        print(f"  → Score: {score}, Erreichbarkeit: {erreichbarkeit}, Charme: {charme}")
        time.sleep(0.5)
    
    print(f"\nSaving Excel to {EXCEL_PATH}...")
    wb.save(EXCEL_PATH)
    print("Done!")
    
    print("\n=== SUMMARY ===")
    print(f"{'Nr':>4} | {'Ort':<20} | {'Preis':>12} | {'Score':>6} | {'Charme':>6}")
    print("-" * 60)
    for d in all_data:
        print(f"{d['nr']:>4} | {d['ort']:<20} | {d['preis']:>12,} | {d['score']:>6.1f} | {d['charme']:>6}")
    
    return all_data

if __name__ == "__main__":
    main()
