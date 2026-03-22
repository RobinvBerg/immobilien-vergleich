#!/usr/bin/env python3
"""
Mallorca Property Scout
- Scrapes Idealista (+ erweiterbar für Porta, EV, Makler-Sites)
- Deduplication via seen_ids.json
- Auto-appends neue Findings in Mallorca_Markt_Gesamt.xlsx
"""

import json
import time
import re
import sys
from pathlib import Path
from datetime import datetime

# --- Config ---
_SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT  = _SCRIPT_DIR.parent.parent
WORKSPACE     = PROJECT_ROOT  # kept for compatibility
SEEN_IDS_FILE = PROJECT_ROOT / "debug" / "mallorca_seen_ids.json"
EXCEL_FILE    = PROJECT_ROOT / "data"  / "Mallorca_Markt_Gesamt.xlsx"
OUTPUT_JSON   = PROJECT_ROOT / "debug" / "mallorca_new_findings.json"

CRITERIA = {
    "preis_min": 2_000_000,
    "preis_max": 6_500_000,
    "zimmer_min": 5,
    "grundstueck_min": 3_000,  # m²
}

IDEALISTA_URLS = [
    "https://www.idealista.com/geo/venta-casas/baleares/mallorca/con-precio-hasta_6500000,precio-desde_2000000,min-rooms_5/?ordenado-por=fecha-publicacion-desc",
]

# --- Dedup ---
def load_seen_ids():
    if SEEN_IDS_FILE.exists():
        return set(json.loads(SEEN_IDS_FILE.read_text()))
    return set()

def save_seen_ids(ids: set):
    SEEN_IDS_FILE.write_text(json.dumps(list(ids), indent=2))

# --- Scraper ---
def scrape_idealista(page) -> list[dict]:
    results = []
    for url in IDEALISTA_URLS:
        print(f"  → Scraping: {url}")
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(2)

            # Cookie-Banner wegklicken falls vorhanden
            try:
                page.click("button#didomi-notice-agree-button", timeout=3000)
                time.sleep(1)
            except:
                pass

            articles = page.query_selector_all("article.item")
            print(f"     {len(articles)} Artikel gefunden")

            for article in articles:
                try:
                    prop = parse_idealista_article(article, page)
                    if prop:
                        results.append(prop)
                except Exception as e:
                    print(f"     Fehler bei Artikel: {e}")

        except Exception as e:
            print(f"  ⚠️  Fehler beim Laden: {e}")

    return results


def parse_idealista_article(article, page) -> dict | None:
    try:
        # ID aus Link extrahieren
        link_el = article.query_selector("a.item-link")
        if not link_el:
            return None
        href = link_el.get_attribute("href") or ""
        prop_id = f"idealista_{href.strip('/').split('/')[-1]}"
        url = f"https://www.idealista.com{href}" if href.startswith("/") else href

        # Titel
        title = (link_el.get_attribute("title") or link_el.inner_text()).strip()

        # Preis
        preis_el = article.query_selector(".item-price")
        preis_text = preis_el.inner_text().strip() if preis_el else ""
        preis = parse_preis(preis_text)

        # Details (Zimmer, Bäder, m²)
        details = article.query_selector_all(".item-detail")
        zimmer = bäder = wohnflaeche = None
        for d in details:
            t = d.inner_text().strip()
            if "hab" in t.lower():
                zimmer = parse_zahl(t)
            elif "baño" in t.lower() or "baños" in t.lower():
                bäder = parse_zahl(t)
            elif "m²" in t and zimmer is not None:  # Wohnfläche kommt nach Zimmern
                wohnflaeche = parse_zahl(t)

        # Grundstück aus Beschreibung versuchen
        desc_el = article.query_selector(".item-description")
        desc = desc_el.inner_text() if desc_el else ""
        grundstueck = parse_grundstueck(desc)

        # Ort
        location_el = article.query_selector(".item-detail-char .item-detail")
        ort_el = article.query_selector("[class*='location']")
        ort = ort_el.inner_text().strip() if ort_el else "Mallorca"

        return {
            "id": prop_id,
            "titel": title,
            "quelle": "Idealista",
            "url": url,
            "preis": preis,
            "zimmer": zimmer,
            "bäder": bäder,
            "wohnflaeche_m2": wohnflaeche,
            "grundstueck_m2": grundstueck,
            "ort": ort,
            "beschreibung": desc[:300] if desc else "",
            "gefunden_am": datetime.now().strftime("%Y-%m-%d"),
            "status": "Neu",
        }
    except Exception as e:
        print(f"     Parse-Fehler: {e}")
        return None


# --- Helper Parser ---
def parse_preis(text: str) -> int | None:
    text = text.replace(".", "").replace(",", "").replace("€", "").replace(" ", "")
    nums = re.findall(r"\d+", text)
    if nums:
        val = int(nums[0])
        # Wenn wenig Stellen → wahrscheinlich in Tausend
        if val < 10000:
            val *= 1000
        return val
    return None

def parse_zahl(text: str) -> int | None:
    nums = re.findall(r"\d+", text)
    return int(nums[0]) if nums else None

def parse_grundstueck(text: str) -> int | None:
    # Sucht "XXX m² parcela" oder "XXX m² de terreno" etc.
    match = re.search(r"(\d[\d.,]*)\s*m²?\s*(parcela|terreno|solar|finca|grundst)", text, re.IGNORECASE)
    if match:
        return parse_zahl(match.group(1))
    return None


# --- Filter ---
def filter_criteria(props: list[dict]) -> list[dict]:
    valid = []
    for p in props:
        preis = p.get("preis")
        zimmer = p.get("zimmer")
        gs = p.get("grundstueck_m2")

        if preis and (preis < CRITERIA["preis_min"] or preis > CRITERIA["preis_max"]):
            continue
        if zimmer and zimmer < CRITERIA["zimmer_min"]:
            continue
        # Grundstück nur filtern wenn wir einen Wert haben
        if gs and gs < CRITERIA["grundstueck_min"]:
            continue

        valid.append(p)
    return valid


# --- Excel Update ---
def update_excel(new_props: list[dict]):
    try:
        import openpyxl
    except ImportError:
        print("  ⚠️  openpyxl nicht installiert — Excel-Update übersprungen")
        print("       pip install openpyxl")
        return

    if EXCEL_FILE.exists():
        wb = openpyxl.load_workbook(EXCEL_FILE)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Titel", "Quelle", "URL", "Preis (€)", "Zimmer", "Grundstück (m²)", "Wohnfläche (m²)", "Ort", "Gefunden am", "Status"])

    added = 0
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
        added += 1

    wb.save(EXCEL_FILE)
    print(f"  ✅ {added} neue Einträge in Excel gespeichert")


# --- Main ---
def main():
    print("🏡 Mallorca Property Scout")
    print(f"   Kriterien: €{CRITERIA['preis_min']:,}–{CRITERIA['preis_max']:,} | min. {CRITERIA['zimmer_min']} Zimmer | min. {CRITERIA['grundstueck_min']}m² Grundstück")
    print()

    seen_ids = load_seen_ids()
    print(f"   Bekannte IDs: {len(seen_ids)}")

    from playwright.sync_api import sync_playwright
    all_new = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="es-ES",
        )
        page = context.new_page()

        print("📍 Idealista scrapen...")
        raw = scrape_idealista(page)
        print(f"   Roh-Ergebnisse: {len(raw)}")

        browser.close()

    # Filter + Dedup
    filtered = filter_criteria(raw)
    print(f"   Nach Kriterien-Filter: {len(filtered)}")

    new_props = [p for p in filtered if p["id"] not in seen_ids]
    print(f"   Davon neu (nicht gesehen): {len(new_props)}")

    if new_props:
        # Seen IDs updaten
        for p in new_props:
            seen_ids.add(p["id"])
        save_seen_ids(seen_ids)

        # JSON speichern
        OUTPUT_JSON.write_text(json.dumps(new_props, indent=2, ensure_ascii=False))
        print(f"\n📄 Neue Findings gespeichert: {OUTPUT_JSON}")

        # Excel updaten
        print("\n📊 Excel updaten...")
        update_excel(new_props)

        print(f"\n🎯 {len(new_props)} neue Objekte gefunden!")
        for p in new_props:
            preis_str = f"€{p['preis']:,}" if p.get('preis') else "Preis unbekannt"
            print(f"   • {p['titel'][:60]} | {preis_str} | {p.get('ort', '')}")
    else:
        print("\n✅ Keine neuen Objekte seit letztem Run.")

    print("\nFertig.")


if __name__ == "__main__":
    main()
