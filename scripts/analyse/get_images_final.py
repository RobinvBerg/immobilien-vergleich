#!/usr/bin/env python3
"""
Holt fehlende Bilder für 85 Objekte:
- 83 LivingBlue: Decodo Site Unblocker + direkte CDN URLs
- 2 andere: direkt download
Dann Vision-Analyse für alle neuen Bilder.
"""
import json, os, re, time, requests, base64, io
from pathlib import Path
from PIL import Image
import anthropic, openpyxl

BASE = Path(__file__).parent
BILDER_DIR = BASE / "bilder"
LOG = BASE / "get_images_final_log.txt"
CHECKPOINT = BASE / "bilder_analyse_checkpoint.json"
EXCEL = BASE / "mallorca-kandidaten-v2.xlsx"
BILDER_JSON = BASE / "mallorca-bilder.json"

# Decodo Site Unblocker
UNBLOCKER = "http://U0000364062:PW_1047072161848b0d67b68ff1b160986e6@unblock.decodo.com:60000"
PROXIES = {"https": UNBLOCKER, "http": UNBLOCKER}
HEADERS = {"X-Decodo-JS-Render": "true", "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def log(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")

def compress_and_encode(path):
    try:
        img = Image.open(path).convert("RGB")
        img.thumbnail((1200, 1200), Image.LANCZOS)
        for quality in [75, 60, 45, 30]:
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality, optimize=True)
            data = buf.getvalue()
            if len(data) < 4_000_000:
                return base64.standard_b64encode(data).decode("utf-8"), "image/jpeg"
    except Exception as e:
        log(f"  Encode fehler: {e}")
    return None, None

def download_direct(url, path):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if r.status_code == 200 and len(r.content) > 20000:
            with open(path, "wb") as f:
                f.write(r.content)
            return True
    except: pass
    return False

def get_livingblue_via_unblocker(obj_url, row):
    """Decodo Site Unblocker für LivingBlue"""
    # Strategie 1: Direkt CDN-URL aus bilder.json probieren (egorealestate CDN)
    path = BILDER_DIR / f"{row}_main.jpg"
    
    # Versuche Seite via Unblocker laden
    try:
        r = requests.get(obj_url, proxies=PROXIES, headers=HEADERS, timeout=30, verify=False)
        if r.status_code == 200:
            html = r.text
            # Suche nach echten Bild-URLs im CDN
            patterns = [
                r'https://images\.egorealestate\.com/[A-Za-z0-9/_\-\.]+\.(?:jpg|jpeg|webp)',
                r'https://media\.egorealestate\.com/[A-Za-z0-9/_\-\.]+\.(?:jpg|jpeg|webp)',
                r'"(https://[^"]+(?:jpg|jpeg|webp))"',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, html, re.I)
                for m in matches:
                    if isinstance(m, tuple): m = m[0]
                    if any(skip in m.lower() for skip in ["logo","placeholder","icon","flag","thumb"]): 
                        continue
                    # Direkt herunterladen (kein Proxy nötig für CDN)
                    if download_direct(m, str(path)):
                        if path.stat().st_size > 20000:
                            log(f"  ✅ Unblocker→CDN: {m[:60]}")
                            return str(path)
                        path.unlink()
    except Exception as e:
        log(f"  Unblocker fehler: {e}")
    
    # Strategie 2: Playwright fallback
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(obj_url, timeout=25000, wait_until="networkidle")
            page.wait_for_timeout(2000)
            img_urls = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('img'))
                    .map(i => i.src || i.getAttribute('data-src') || '')
                    .filter(s => s && s.length > 30 && !s.includes('logo') && !s.includes('placeholder') 
                               && (s.includes('.jpg') || s.includes('.jpeg') || s.includes('.webp')))
                    .slice(0, 5);
            }""")
            browser.close()
            for url in img_urls:
                if download_direct(url, str(path)):
                    if path.stat().st_size > 20000:
                        log(f"  ✅ Playwright: {url[:60]}")
                        return str(path)
                    if path.exists(): path.unlink()
    except Exception as e:
        log(f"  Playwright fehler: {e}")
    
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

GEBÄUDESTRUKTUR: [kurze Beschreibung]
GÄSTEHAUS: [ja/nein/unklar]
RENO_BEGRUENDUNG: [1 Satz]

Beispiel:
CHARME: 4
RENOVIERUNG: 45
GEBÄUDESTRUKTUR: Rustikale Steinfinca, Pool sichtbar
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
                try: 
                    val = int(re.search(r'\d+', line.split(":",1)[1]).group())
                    result["charme"] = min(5, max(1, val))
                except: pass
            elif line.startswith("RENOVIERUNG:"):
                try: 
                    val = int(re.search(r'\d+', line.split(":",1)[1]).group())
                    result["renovierung"] = min(100, max(0, val))
                except: pass
            elif line.startswith("GEBÄUDESTRUKTUR:"): result["gebaeude"] = line.split(":",1)[1].strip()
            elif line.startswith("GÄSTEHAUS:"): result["gaestehaus"] = line.split(":",1)[1].strip()
            elif line.startswith("RENO_BEGRUENDUNG:"): result["reno_begruendung"] = line.split(":",1)[1].strip()
        return result if len(result) >= 2 else None
    except Exception as e:
        log(f"  API: {e}")
        return None

def write_excel(ws, row, result, note):
    if "charme" in result: ws.cell(row, 4).value = result["charme"]
    if "renovierung" in result:
        ws.cell(row, 22).value = result["renovierung"]
        ws.cell(row, 32).value = result["renovierung"]
    if "gebaeude" in result: ws.cell(row, 29).value = result["gebaeude"]
    if "reno_begruendung" in result: ws.cell(row, 33).value = result["reno_begruendung"]
    ws.cell(row, 34).value = note

def main():
    import warnings
    warnings.filterwarnings("ignore")
    
    log("=== GET IMAGES FINAL ===")
    checkpoint = json.load(open(CHECKPOINT))
    bilder_data = json.load(open(BILDER_JSON))
    wb = openpyxl.load_workbook(EXCEL)
    ws = wb.active

    # Baue Todo-Liste
    todo = []
    for k, v in checkpoint.items():
        row = int(k)
        has_local = any(
            (BILDER_DIR / f"{row}_main.{ext}").exists() and 
            (BILDER_DIR / f"{row}_main.{ext}").stat().st_size > 20000
            for ext in ["jpg","jpeg","webp","png"]
        )
        if not has_local:
            todo.append((row, k, bilder_data.get(k, {})))

    log(f"Fehlende Bilder: {len(todo)}")
    done = 0

    for i, (row, k, entry) in enumerate(todo):
        obj_url = entry.get("url", "")
        img_url = entry.get("img_url", "")
        beschreibung = entry.get("desc", "")
        is_lb = "livingblue" in obj_url

        log(f"\n[{i+1}/{len(todo)}] Zeile {row} {'(LivingBlue)' if is_lb else ''}")

        # Bild holen
        local_path = None
        
        if is_lb:
            local_path = get_livingblue_via_unblocker(obj_url, row)
        else:
            # Direkt download
            if img_url:
                p = BILDER_DIR / f"{row}_main.jpg"
                if download_direct(img_url, str(p)) and p.stat().st_size > 20000:
                    local_path = str(p)
                    log(f"  ✅ Direkt: {img_url[:60]}")

        if not local_path:
            log(f"  ❌ kein Bild — skip")
            continue

        # Analysieren
        result = analyze(Path(local_path), beschreibung)
        if result:
            write_excel(ws, row, result, "Vision (get_images_final)")
            checkpoint[k] = result
            done += 1
            log(f"  → Charme={result.get('charme')} Reno={result.get('renovierung')}")
        else:
            log(f"  ❌ Analyse fehlgeschlagen")
            checkpoint[k] = {"failed": True}

        if (i+1) % 10 == 0:
            wb.save(EXCEL)
            with open(CHECKPOINT, "w") as f:
                json.dump(checkpoint, f)
            log(f"  💾 gespeichert ({done} neu)")

        time.sleep(0.5)

    wb.save(EXCEL)
    with open(CHECKPOINT, "w") as f:
        json.dump(checkpoint, f)

    total = sum(1 for v in checkpoint.values() if not v.get("failed") and not v.get("skipped"))
    log(f"\n=== FERTIG: {done} neu, gesamt {total}/309 ===")
    os.system(f'openclaw system event --text "Bilder final: {done} neue Bilder + Analyse, gesamt {total}/309" --mode now')

if __name__ == "__main__":
    main()
