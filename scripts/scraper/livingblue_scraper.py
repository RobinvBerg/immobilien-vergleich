#!/usr/bin/env python3
"""Living Blue Mallorca - Neue Objekte finden via EgoRealEstate API"""

import requests
import re
import json
import openpyxl
import time

PROXY = "http://sp1e6lma32:pxjc5K6_LBg3Is6vzo@gate.decodo.com:10001"
LISTING_URL = "https://www.livingblue-mallorca.com/de-de/immobilien?pag=1"
API_URL = "https://websiteapi.egorealestate.com/v1/Properties"
EXCEL_PATH = "/Users/robin/.openclaw/workspace/mallorca-projekt/data/mallorca-kandidaten-v2.xlsx"
PAGE_SIZE = 20

PROXIES = {"http": PROXY, "https": PROXY}
BASE_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def extract_property_id(url):
    """Extrahiert die numerische Property-ID aus einer URL."""
    m = re.search(r'/(\d{6,})(?:[/?#]|$)', str(url))
    return m.group(1) if m else None


def get_api_credentials():
    resp = requests.get(LISTING_URL, headers=BASE_HEADERS, proxies=PROXIES, timeout=30)
    html = resp.text
    rid = re.search(r"requestID':'([^']+)'", html)
    tok = re.search(r'"APIToken":"([^"]+)"', html)
    return (rid.group(1) if rid else ""), (tok.group(1) if tok else "")


def load_existing_ids():
    """Lädt alle Property-IDs aus der Excel-Datei (aus LivingBlue-URLs in Spalte C)."""
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb.active
    ids = set()
    urls = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[2] and "livingblue" in str(row[2]).lower():
            url = str(row[2]).strip()
            urls.add(url)
            pid = extract_property_id(url)
            if pid:
                ids.add(pid)
    print(f"✅ {len(urls)} LivingBlue-URLs aus Excel geladen → {len(ids)} eindeutige Property-IDs")
    return ids


def build_property_url(prop):
    """URL aus Property-Daten zusammenbauen."""
    for key in ["URL", "Url", "url", "DetailUrl", "detailUrl", "Link"]:
        if prop.get(key):
            u = str(prop[key])
            if not u.startswith("http"):
                u = "https://www.livingblue-mallorca.com" + u
            return u
    pid = prop.get("PropertyID") or prop.get("ID") or prop.get("id") or ""
    if pid:
        return f"https://www.livingblue-mallorca.com/de-de/immobilien/detail/{pid}"
    return ""


def get_price(prop):
    """Preis aus dem Property-Objekt."""
    for key in ["PriceValue", "PriceFormatted", "price_value", "Price", "price"]:
        v = prop.get(key)
        if v and str(v) not in ("0", "", "None", "null"):
            return str(v)
    return "N/A"


def fetch_page(session, api_headers, page):
    params = {"pageIndex": page, "pageSize": PAGE_SIZE, "lng": "de-DE", "oar": 1}
    resp = session.get(API_URL, headers=api_headers, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("Properties", [])


def main():
    print("🔍 Living Blue Mallorca Scraper startet...\n")

    print("📡 Lade API-Credentials...")
    request_id, api_token = get_api_credentials()
    print(f"   RequestID: {request_id[:40]}...")
    print(f"   Token:     {api_token[:30]}...\n")

    existing_ids = load_existing_ids()

    session = requests.Session()
    session.proxies = PROXIES
    session.headers.update(BASE_HEADERS)

    api_headers = {
        "AuthorizationToken": api_token,
        "x-async": "true",
        "X-Served-By": "JanelaDigital",
        "x-requestid": request_id,
        "Accept": "application/json",
        "Referer": "https://www.livingblue-mallorca.com/de-de/immobilien",
        "Origin": "https://www.livingblue-mallorca.com",
    }

    all_props = {}   # property_id → prop dict
    page = 1

    while True:
        print(f"\n📄 Seite {page}...")
        try:
            props = fetch_page(session, api_headers, page)
        except Exception as e:
            print(f"  ⚠️  Fehler: {e}")
            break

        if not props:
            print(f"  → Keine weiteren Objekte. Ende nach {page-1} Seiten.")
            break

        new_on_page = 0
        for p in props:
            url = build_property_url(p)
            pid = extract_property_id(url) or str(p.get("PropertyID", ""))
            if pid and pid not in all_props:
                all_props[pid] = (url, p)
                if pid not in existing_ids:
                    new_on_page += 1

        print(f"  → {len(props)} Objekte geladen | {new_on_page} davon NEU")

        if len(props) < PAGE_SIZE:
            print(f"  → Letzte Seite (< {PAGE_SIZE} Ergebnisse)")
            break

        page += 1
        time.sleep(1)

        if page > 100:
            print("  ⚠️  Sicherheits-Stopp bei 100 Seiten")
            break

    # Neue Objekte filtern
    new_objects = [(pid, url, p) for pid, (url, p) in all_props.items() if pid not in existing_ids]

    print(f"\n{'='*65}")
    print(f"🏠 ERGEBNIS: {len(new_objects)} neue Objekte (von {len(all_props)} gesamt gescrapt)")
    print(f"{'='*65}\n")

    if not new_objects:
        print("✅ Keine neuen Objekte — alles bereits in der Excel-Datei!")
    else:
        for i, (pid, url, p) in enumerate(new_objects, 1):
            title = p.get("Title") or p.get("title") or p.get("Name") or "N/A"
            price = get_price(p)
            rooms = p.get("Bedrooms") or p.get("Rooms") or p.get("bedrooms") or "N/A"
            location = p.get("Municipality") or p.get("City") or p.get("Zone") or "N/A"
            ref = p.get("Reference") or p.get("reference") or ""
            sqm = p.get("UsefulArea") or p.get("Area") or p.get("Meters") or ""

            print(f"[{i}] {title}")
            if ref:
                print(f"    Ref:    LB-{ref}")
            print(f"    URL:    {url}")
            print(f"    Preis:  {price}")
            print(f"    Zimmer: {rooms} Schlafzimmer | {sqm} m²")
            print(f"    Ort:    {location}")
            print()


if __name__ == "__main__":
    main()
