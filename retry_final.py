#!/usr/bin/env python3
"""
Final Retry — zwei Strategien:
1. Nicht-LivingBlue: echte Bilder vorhanden, PIL komprimieren + Vision
2. LivingBlue (62): Playwright lädt Detailseite, extrahiert echtes Bild, dann Vision
"""
import json, os, re, time, requests, base64, io
from pathlib import Path
from PIL import Image
import anthropic, openpyxl

BASE = Path(__file__).parent
BILDER_DIR = BASE / "bilder"
LOG = BASE / "retry_final_log.txt"
CHECKPOINT = BASE / "bilder_analyse_checkpoint.json"
EXCEL = BASE / "mallorca-kandidaten-v2.xlsx"
BILDER_JSON = BASE / "mallorca-bilder.json"

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def log(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")

def compress_and_encode(path):
    """PIL komprimieren auf <4MB, dann base64"""
    img = Image.open(path).convert("RGB")
    img.thumbnail((1200, 1200), Image.LANCZOS)
    for quality in [75, 60, 45, 30]:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        data = buf.getvalue()
        if len(data) < 4_000_000:
            return base64.standard_b64encode(data).decode("utf-8"), "image/jpeg"
    return None, None

def download_image(url, path):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200 and len(r.content) > 5000:
            with open(path, "wb") as f:
                f.write(r.content)
            return True
    except: pass
    return False

def get_livingblue_image(url, row):
    """Playwright für LivingBlue"""
    from playwright.sync_api import sync_playwright
    path = BILDER_DIR / f"{row}_main.jpg"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            
            # Suche nach echten Bild-URLs
            img_urls = page.evaluate("""() => {
                const imgs = Array.from(document.querySelectorAll('img'));
                return imgs
                    .map(i => i.src || i.getAttribute('data-src') || '')
                    .filter(s => s && s.length > 30 && !s.includes('logo') && !s.includes('placeholder') && (s.includes('.jpg') || s.includes('.jpeg') || s.includes('.webp')))
                    .slice(0, 3);
            }""")
            browser.close()
            
            for img_url in img_urls:
                if download_image(img_url, str(path)):
                    # Prüfe ob echtes Foto (>20KB)
                    if path.stat().st_size > 20000:
                        log(f"  ✅ LivingBlue Bild: {img_url[:60]}")
                        return str(path)
                    path.unlink()
    except Exception as e:
        log(f"  Playwright Fehler: {e}")
    return None

def analyze(image_path, beschreibung=""):
    b64, mt = compress_and_encode(image_path)
    if not b64:
        return None
    content = [
        {"type": "image", "source": {"type": "base64", "media_type": mt, "data": b64}},
        {"type": "text", "text": f"""Du bewertest eine Mallorca Immobilie für eine Familie mit 3 Kindern (sucht Finca/Landgut).
Beschreibung: {beschreibung[:200] if beschreibung else 'keine'}

Bewerte auf Basis des Bildes. Antworte EXAKT in diesem Format:

CHARME: [Zahl 1-5]
(1=hässlich/banal, 2=durchschnittlich, 3=ansprechend, 4=schön, 5=außergewöhnlich)

RENOVIERUNG: [Zahl 0-100]
(0=einzugsbereit perfekt, 30=kleine Arbeiten, 60=mittlere Renovierung, 80=große Renovierung, 100=Rohbau)

GEBÄUDESTRUKTUR: [kurze Beschreibung z.B. "Rustikale Finca, Haupthaus + Gästehaus, Pool"]
GÄSTEHAUS: [ja/nein/unklar]
RENO_BEGRUENDUNG: [1 Satz Begründung]

Beispiel korrekte Antwort:
CHARME: 4
RENOVIERUNG: 45
GEBÄUDESTRUKTUR: Rustikale Steinfinca, 2-stöckig, Pool sichtbar
GÄSTEHAUS: ja
RENO_BEGRUENDUNG: Gebäude in gutem Zustand, kleinere Modernisierungen nötig."""}
    ]
    try:
        r = client.messages.create(model="claude-haiku-4-5", max_tokens=200,
            messages=[{"role": "user", "content": content}])
        text = r.content[0].text
        result = {}
        for line in text.strip().split("\n"):
            if line.startswith("CHARME:"):
                try: result["charme"] = int(line.split(":")[1].strip())
                except: pass
            elif line.startswith("RENOVIERUNG:"):
                try: result["renovierung"] = int(line.split(":")[1].strip())
                except: pass
            elif line.startswith("GEBÄUDESTRUKTUR:"): result["gebaeude"] = line.split(":",1)[1].strip()
            elif line.startswith("GÄSTEHAUS:"): result["gaestehaus"] = line.split(":",1)[1].strip()
            elif line.startswith("RENO_BEGRUENDUNG:"): result["reno_begruendung"] = line.split(":",1)[1].strip()
        return result if result else None
    except Exception as e:
        log(f"  API: {e}")
        return None

def write_to_excel(ws, row, result, note=""):
    if "charme" in result: ws.cell(row, 4).value = result["charme"]
    if "renovierung" in result:
        ws.cell(row, 22).value = result["renovierung"]
        ws.cell(row, 32).value = result["renovierung"]
    if "gebaeude" in result: ws.cell(row, 29).value = result["gebaeude"]
    if "reno_begruendung" in result: ws.cell(row, 33).value = result["reno_begruendung"]
    ws.cell(row, 34).value = note

def main():
    log("=== FINAL RETRY ===")
    checkpoint = json.load(open(CHECKPOINT))
    bilder_data = json.load(open(BILDER_JSON))
    wb = openpyxl.load_workbook(EXCEL)
    ws = wb.active

    failed = [(int(k), k) for k, v in checkpoint.items() if v.get("failed")]
    log(f"Zu verarbeiten: {len(failed)}")

    # Trenne LivingBlue von anderen
    livingblue = [(r, k) for r, k in failed if "livingblue" in bilder_data.get(k, {}).get("url", "")]
    others = [(r, k) for r, k in failed if "livingblue" not in bilder_data.get(k, {}).get("url", "")]
    log(f"LivingBlue: {len(livingblue)}, Andere: {len(others)}")

    done = 0

    # === RUNDE 1: Andere (echte Bilder, PIL komprimieren) ===
    log("\n--- Runde 1: Nicht-LivingBlue ---")
    for i, (row, k) in enumerate(others):
        beschreibung = bilder_data.get(k, {}).get("desc", "")
        local = None
        for ext in ["jpg", "jpeg", "webp", "png"]:
            p = BILDER_DIR / f"{row}_main.{ext}"
            if p.exists() and p.stat().st_size > 5000:
                local = p
                break
        
        if not local:
            log(f"  [{i+1}/{len(others)}] Zeile {row}: kein Bild")
            continue
        
        log(f"  [{i+1}/{len(others)}] Zeile {row}: {local.name} ({local.stat().st_size//1024}KB)")
        result = analyze(local, beschreibung)
        if result:
            write_to_excel(ws, row, result, "Vision-Analyse (retry-final)")
            checkpoint[k] = result
            done += 1
            log(f"    → Charme={result.get('charme')} Reno={result.get('renovierung')}")
        else:
            log(f"    ❌ fehlgeschlagen")
        time.sleep(0.3)

    # Zwischenspeichern
    wb.save(EXCEL)
    with open(CHECKPOINT, "w") as f:
        json.dump(checkpoint, f)
    log(f"\nRunde 1 fertig: {done} neu bewertet")

    # === RUNDE 2: LivingBlue via Playwright ===
    log("\n--- Runde 2: LivingBlue via Playwright ---")
    lb_done = 0
    for i, (row, k) in enumerate(livingblue):
        obj_url = bilder_data.get(k, {}).get("url", "")
        beschreibung = bilder_data.get(k, {}).get("desc", "")
        
        log(f"  [{i+1}/{len(livingblue)}] Zeile {row}")
        
        img_path = get_livingblue_image(obj_url, row)
        if not img_path:
            log(f"    ❌ kein Bild gefunden")
            continue
        
        result = analyze(Path(img_path), beschreibung)
        if result:
            write_to_excel(ws, row, result, "Vision-Analyse (LivingBlue-Playwright)")
            checkpoint[k] = result
            done += 1
            lb_done += 1
            log(f"    → Charme={result.get('charme')} Reno={result.get('renovierung')}")
        else:
            log(f"    ❌ Analyse fehlgeschlagen")
        
        if (i+1) % 10 == 0:
            wb.save(EXCEL)
            with open(CHECKPOINT, "w") as f:
                json.dump(checkpoint, f)
        
        time.sleep(1)

    wb.save(EXCEL)
    with open(CHECKPOINT, "w") as f:
        json.dump(checkpoint, f)
    
    log(f"\n=== FINAL RETRY FERTIG ===")
    log(f"Neu bewertet: {done} (davon LivingBlue: {lb_done})")
    os.system(f'openclaw system event --text "Final Retry fertig: {done} zusätzliche Objekte bewertet" --mode now')

if __name__ == "__main__":
    main()
