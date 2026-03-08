#!/usr/bin/env python3
"""
Mallorca Scout — Kyero + Fotocasa
Läuft mit: source mallorca-venv/bin/activate && python3 mallorca_scraper_kyero.py
"""

import json
import time
import re
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent
SEEN_IDS_FILE = WORKSPACE / "mallorca_seen_ids.json"
OUTPUT_JSON = WORKSPACE / "mallorca_new_findings.json"
EXCEL_FILE = WORKSPACE / "Mallorca_Markt_Gesamt.xlsx"

CRITERIA = {
    "preis_min": 2_000_000,
    "preis_max": 6_500_000,
    "zimmer_min": 5,
}

KYERO_PAGES = [
    "https://www.kyero.com/en/mallorca-property-for-sale-0l55563?min_price=2000000&max_price=6500000&min_bedrooms=5",
    "https://www.kyero.com/en/mallorca-property-for-sale-0l55563?min_price=2000000&max_price=6500000&min_bedrooms=5&page=2",
    "https://www.kyero.com/en/mallorca-property-for-sale-0l55563?min_price=2000000&max_price=6500000&min_bedrooms=5&page=3",
    "https://www.kyero.com/en/mallorca-country-houses-for-sale-0l55563g4?min_price=2000000&max_price=6500000&min_bedrooms=5",
]

FOTOCASA_PAGES = [
    "https://www.fotocasa.es/es/comprar/casas/mallorca/todas-las-zonas/l?maxPrice=6500000&minPrice=2000000&minRooms=5",
]


def load_seen_ids():
    if SEEN_IDS_FILE.exists():
        return set(json.loads(SEEN_IDS_FILE.read_text()))
    return set()

def save_seen_ids(ids: set):
    SEEN_IDS_FILE.write_text(json.dumps(list(ids), indent=2))

def parse_preis(text: str):
    text = re.sub(r"[^\d]", "", text)
    if text:
        val = int(text)
        if val < 10000:
            val *= 1000
        return val
    return None

def parse_zahl(text: str):
    nums = re.findall(r"\d+", text)
    return int(nums[0]) if nums else None


# ========== KYERO ==========
def scrape_kyero(page) -> list[dict]:
    results = []
    for url in KYERO_PAGES:
        print(f"  → {url[:90]}")
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(3)
            try:
                page.click("#onetrust-accept-btn-handler", timeout=3000)
                time.sleep(1)
            except:
                pass

            articles = page.query_selector_all("li[class*='property']")
            print(f"     {len(articles)} Listings")

            for art in articles:
                prop = parse_kyero_article(art)
                if prop:
                    results.append(prop)

        except Exception as e:
            print(f"  ⚠️  {e}")
    return results


def parse_kyero_article(art) -> dict | None:
    try:
        link_el = art.query_selector("a[href*='/en/property/']")
        if not link_el:
            return None
        href = link_el.get_attribute("href") or ""
        # ID aus href extrahieren (z.B. /en/property/12345678-villa-for-sale-...)
        id_match = re.search(r"/property/(\d+)-", href)
        if not id_match:
            return None
        prop_id = f"kyero_{id_match.group(1)}"
        url = f"https://www.kyero.com{href}"

        text = art.inner_text()

        # Titel — Zeile mit "in Mallorca" oder Typ-Beschreibung
        title_match = re.search(r"(Villa|Country house|Finca|Casa|House|Chalet)[^\n]*Mallorca[^\n]*", text)
        title = title_match.group(0).strip() if title_match else ""
        if not title:
            # Fallback: erste nicht-leere Zeile nach "Featured"/"slide"
            for line in text.split("\n"):
                line = line.strip()
                if len(line) > 15 and "slide" not in line.lower() and "featured" not in line.lower():
                    title = line
                    break

        # Preis
        preis_match = re.search(r"€\s*([\d\s,\.]+)", text)
        preis = parse_preis(preis_match.group(1)) if preis_match else None

        # Zimmer aus Text
        bed_match = re.search(r"(\d+)\s*bed", text, re.IGNORECASE)
        zimmer = int(bed_match.group(1)) if bed_match else None

        # Grundstück
        plot_match = re.search(r"([\d,\.]+)\s*m²?\s*(plot|land|terreno|garden|finca)", text, re.IGNORECASE)
        grundstueck = parse_zahl(plot_match.group(1).replace(",", "").replace(".", "")) if plot_match else None

        # Ort
        loc_match = re.search(r"(Andratx|Pollença|Sóller|Palma|Calvià|Deià|Valldemossa|Esporles|Puigpunyent|Alaró|Bunyola|Inca|Alcúdia|Artà|Manacor|Santanyí|Felanitx|Campos|Llucmajor|Son Servera|Santa Ponsa|Portals Nous|Portals|Bendinat|Galilea|Peguera|Camp de Mar|Port d'Andratx|Banyalbufar|Marratxí)", text, re.IGNORECASE)
        ort = loc_match.group(0) if loc_match else "Mallorca"

        return {
            "id": prop_id,
            "titel": title[:80],
            "quelle": "Kyero",
            "url": url,
            "preis": preis,
            "zimmer": zimmer,
            "grundstueck_m2": grundstueck,
            "ort": ort,
            "gefunden_am": datetime.now().strftime("%Y-%m-%d"),
            "status": "Neu",
        }
    except Exception as e:
        return None


# ========== FOTOCASA ==========
def scrape_fotocasa(page) -> list[dict]:
    results = []
    for url in FOTOCASA_PAGES:
        print(f"  → {url[:90]}")
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(4)
            try:
                page.click("#didomi-notice-agree-button", timeout=3000)
                time.sleep(1)
            except:
                pass

            cards = page.query_selector_all("article")
            print(f"     {len(cards)} Cards")

            for card in cards:
                prop = parse_fotocasa_card(card)
                if prop:
                    results.append(prop)

        except Exception as e:
            print(f"  ⚠️  {e}")
    return results


def parse_fotocasa_card(card) -> dict | None:
    try:
        link_el = card.query_selector("a[href*='/inmueble/'], a[href*='fotocasa']")
        if not link_el:
            link_el = card.query_selector("a")
        if not link_el:
            return None

        href = link_el.get_attribute("href") or ""
        if len(href) < 5:
            return None

        url = href if href.startswith("http") else f"https://www.fotocasa.es{href}"
        slug = href.strip("/").split("/")[-1][:30]
        prop_id = f"fotocasa_{slug}"

        text = card.inner_text()

        preis_match = re.search(r"([\d\.]+)\s*€", text)
        preis = parse_preis(preis_match.group(1)) if preis_match else None

        hab_match = re.search(r"(\d+)\s*hab", text, re.IGNORECASE)
        zimmer = int(hab_match.group(1)) if hab_match else None

        title_el = card.query_selector("h2, h3, [class*='title']")
        title = title_el.inner_text().strip()[:80] if title_el else text[:60].strip()

        loc_match = re.search(r"(Andratx|Pollença|Sóller|Palma|Calvià|Deià|Valldemossa|Esporles|Alaró|Bunyola|Inca|Alcúdia|Artà|Manacor|Santanyí|Felanitx|Campos|Llucmajor|Mallorca)", text, re.IGNORECASE)
        ort = loc_match.group(0) if loc_match else "Mallorca"

        return {
            "id": prop_id,
            "titel": title,
            "quelle": "Fotocasa",
            "url": url,
            "preis": preis,
            "zimmer": zimmer,
            "grundstueck_m2": None,
            "ort": ort,
            "gefunden_am": datetime.now().strftime("%Y-%m-%d"),
            "status": "Neu",
        }
    except:
        return None


# ========== FILTER ==========
def filter_criteria(props: list[dict]) -> list[dict]:
    valid = []
    for p in props:
        preis = p.get("preis")
        zimmer = p.get("zimmer")
        # Preis-Filter nur wenn wir einen Wert haben
        if preis and (preis < CRITERIA["preis_min"] or preis > CRITERIA["preis_max"]):
            continue
        # Zimmer-Filter nur wenn wir einen Wert haben
        if zimmer and zimmer < CRITERIA["zimmer_min"]:
            continue
        valid.append(p)
    return valid


# ========== EXCEL ==========
def update_excel(new_props: list[dict]):
    try:
        import openpyxl
    except ImportError:
        print("  ⚠️  openpyxl fehlt — pip install openpyxl")
        return

    if EXCEL_FILE.exists():
        wb = openpyxl.load_workbook(EXCEL_FILE)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Titel", "Quelle", "URL", "Preis (€)", "Zimmer", "Grundstück (m²)", "Wohnfläche (m²)", "Ort", "Gefunden am", "Status"])

    for p in new_props:
        ws.append([
            p.get("titel", ""),
            p.get("quelle", ""),
            p.get("url", ""),
            p.get("preis", ""),
            p.get("zimmer", ""),
            p.get("grundstueck_m2", ""),
            p.get("wohnflaeche_m2", ""),
            p.get("ort", ""),
            p.get("gefunden_am", ""),
            p.get("status", "Neu"),
        ])

    wb.save(EXCEL_FILE)
    print(f"  ✅ {len(new_props)} Einträge in Excel → {EXCEL_FILE.name}")


# ========== MAIN ==========
def main():
    print("🏡 Mallorca Scout — Kyero + Fotocasa")
    print(f"   Filter: €{CRITERIA['preis_min']:,}–{CRITERIA['preis_max']:,} | min. {CRITERIA['zimmer_min']} Zimmer\n")

    seen_ids = load_seen_ids()
    print(f"   Bekannte IDs: {len(seen_ids)}\n")

    from playwright.sync_api import sync_playwright
    all_raw = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-GB",
        )
        page = ctx.new_page()

        print("🔍 Kyero...")
        kyero = scrape_kyero(page)
        print(f"   → {len(kyero)} geparst\n")
        all_raw.extend(kyero)

        print("🔍 Fotocasa...")
        fotocasa = scrape_fotocasa(page)
        print(f"   → {len(fotocasa)} geparst\n")
        all_raw.extend(fotocasa)

        browser.close()

    print(f"📦 Gesamt roh: {len(all_raw)}")

    # Duplikate aus diesem Run entfernen
    seen_this_run = set()
    deduped = []
    for p in all_raw:
        if p["id"] not in seen_this_run:
            seen_this_run.add(p["id"])
            deduped.append(p)

    filtered = filter_criteria(deduped)
    print(f"   Nach Filter: {len(filtered)}")

    new_props = [p for p in filtered if p["id"] not in seen_ids]
    print(f"   Davon neu: {len(new_props)}\n")

    if new_props:
        for p in new_props:
            seen_ids.add(p["id"])
        save_seen_ids(seen_ids)

        OUTPUT_JSON.write_text(json.dumps(new_props, indent=2, ensure_ascii=False))
        print(f"📄 {OUTPUT_JSON.name} gespeichert")

        update_excel(new_props)

        print(f"\n🎯 {len(new_props)} neue Objekte:\n")
        for p in new_props:
            preis_str = f"€{p['preis']:,}" if p.get("preis") else "Preis?"
            zim = f"{p['zimmer']} Zi." if p.get("zimmer") else ""
            print(f"   [{p['quelle']}] {p['titel'][:50]:50s} | {preis_str:>15} | {zim:6} | {p.get('ort','')}")
    else:
        print("ℹ️  Keine neuen Objekte (alle bereits bekannt oder gefiltert).")

    print("\nFertig.")


if __name__ == "__main__":
    main()
