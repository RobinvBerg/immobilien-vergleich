#!/usr/bin/env python3
"""
LivingBlue Bilder via Playwright - klickt INFO dann holt Bild
"""
import json, os, re, time, requests, base64, io
from pathlib import Path
from PIL import Image
import anthropic, openpyxl
from playwright.sync_api import sync_playwright

BASE = Path(__file__).parent
BILDER_DIR = BASE / "bilder"
LOG = BASE / "livingblue_log.txt"
CHECKPOINT = BASE / "bilder_analyse_checkpoint.json"
EXCEL = BASE / "mallorca-kandidaten-v2.xlsx"
BILDER_JSON = BASE / "mallorca-bilder.json"

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

def download(url, path):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if r.status_code == 200 and len(r.content) > 20000:
            with open(path, "wb") as f:
                f.write(r.content)
            return True
    except: pass
    return False

def get_lb_image_playwright(obj_url, row, page):
    """Besuche Übersichtsseite, klicke auf INFO für dieses Objekt, hole Hauptbild"""
    path = BILDER_DIR / f"{row}_main.jpg"
    ref_id = obj_url.rstrip("/").split("/")[-1]
    
    try:
        # Gehe zur Übersichtsseite
        page.goto("https://www.livingblue-mallorca.com/de-de/immobilien", 
                  timeout=20000, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        
        # Direkt zu Detailseite
        page.goto(obj_url, timeout=20000, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        
        # Prüfe ob wir auf der Detailseite sind (nicht Übersicht)
        current_url = page.url
        if "immobilien/" in current_url and len(current_url) > 60:
            # Hole Hauptbild
            img_urls = page.evaluate("""() => {
                const imgs = Array.from(document.querySelectorAll('.property-detail img, .gallery img, .slider img, img.main-image, section img'));
                const all = Array.from(document.querySelectorAll('img'));
                const candidates = imgs.length > 0 ? imgs : all;
                return candidates
                    .map(i => i.src || i.getAttribute('data-src') || i.getAttribute('data-lazy') || '')
                    .filter(s => s && s.length > 40 
                               && !s.includes('logo') && !s.includes('placeholder')
                               && !s.includes('.svg') && !s.includes('.png')
                               && (s.includes('egorealestate') || s.includes('.jpg') || s.includes('.webp')))
                    .slice(0, 5);
            }""")
            
            for img_url in img_urls:
                if download(img_url, str(path)):
                    if path.stat().st_size > 20000:
                        # Prüfe ob nicht Platzhalter (gleicher Hash)
                        import hashlib
                        h = hashlib.sha1(open(path,"rb").read()).hexdigest()
                        if h != "c0c41ea71c62f73c8e9c73060a4fe81837713adb":  # bekannter Platzhalter
                            return str(path)
                    if path.exists(): path.unlink()
            
            # Fallback: Screenshot des Hauptbildes
            try:
                img_el = page.query_selector('.property-gallery img, .main-photo img, figure img, .carousel img')
                if img_el:
                    img_el.screenshot(path=str(path.with_suffix('.png')))
                    png_path = path.with_suffix('.png')
                    if png_path.stat().st_size > 20000:
                        # Konvertiere zu JPEG
                        img = Image.open(png_path).convert("RGB")
                        img.save(str(path), "JPEG", quality=80)
                        png_path.unlink()
                        return str(path)
            except: pass
                    
    except Exception as e:
        log(f"  Playwright: {e}")
    
    return None

def analyze(image_path, beschreibung=""):
    b64, mt = compress_and_encode(Path(image_path))
    if not b64:
        return None
    content = [
        {"type": "image", "source": {"type": "base64", "media_type": mt, "data": b64}},
        {"type": "text", "text": f"""Du bewertest eine Mallorca Immobilie für eine Familie mit 3 Kindern (Finca/Landgut).
Beschreibung: {beschreibung[:200] if beschreibung else 'keine'}

CHARME: [1-5] (1=hässlich, 3=ok, 5=außergewöhnlich)
RENOVIERUNG: [0-100] (0=perfekt, 60=mittel, 100=Rohbau)
GEBÄUDESTRUKTUR: [kurz, z.B. "Rustikale Finca + Gästehaus"]
GÄSTEHAUS: [ja/nein/unklar]
RENO_BEGRUENDUNG: [1 Satz]

Beispiel:
CHARME: 4
RENOVIERUNG: 30
GEBÄUDESTRUKTUR: Rustikale Steinfinca, Pool, Gästehaus
GÄSTEHAUS: ja
RENO_BEGRUENDUNG: Gut erhalten, nur kleinere Modernisierungen nötig."""}
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

def main():
    log("=== LIVINGBLUE PLAYWRIGHT ===")
    checkpoint = json.load(open(CHECKPOINT))
    bilder_data = json.load(open(BILDER_JSON))
    wb = openpyxl.load_workbook(EXCEL)
    ws = wb.active

    # Alle LivingBlue ohne echtes Bild
    import hashlib
    PLACEHOLDER_HASH = "c0c41ea71c62f73c8e9c73060a4fe81837713adb"
    
    todo = []
    for k, v in bilder_data.items():
        if "livingblue" not in v.get("url",""):
            continue
        row = int(k)
        # Prüfe ob bereits echtes Bild vorhanden
        has_real = False
        for ext in ["jpg","jpeg","webp"]:
            p = BILDER_DIR / f"{row}_main.{ext}"
            if p.exists() and p.stat().st_size > 20000:
                h = hashlib.sha1(open(p,"rb").read()).hexdigest()
                if h != PLACEHOLDER_HASH:
                    has_real = True
                    break
        if not has_real:
            todo.append((row, k, v))

    log(f"LivingBlue ohne echtes Bild: {len(todo)}")
    done = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 800}
        )
        # Erst Übersichtsseite besuchen um Session aufzubauen
        page = context.new_page()
        page.goto("https://www.livingblue-mallorca.com/de-de/immobilien", 
                  timeout=20000, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        
        for i, (row, k, entry) in enumerate(todo):
            obj_url = entry.get("url","")
            beschreibung = entry.get("desc","")
            log(f"\n[{i+1}/{len(todo)}] Zeile {row}")
            
            img_path = get_lb_image_playwright(obj_url, row, page)
            
            if not img_path:
                log(f"  ❌ kein Bild")
                continue
            
            result = analyze(img_path, beschreibung)
            if result:
                if "charme" in result: ws.cell(row, 4).value = result["charme"]
                if "renovierung" in result:
                    ws.cell(row, 22).value = result["renovierung"]
                    ws.cell(row, 32).value = result["renovierung"]
                if "gebaeude" in result: ws.cell(row, 29).value = result["gebaeude"]
                if "reno_begruendung" in result: ws.cell(row, 33).value = result["reno_begruendung"]
                ws.cell(row, 34).value = "Vision (LivingBlue-Playwright-v2)"
                checkpoint[k] = result
                done += 1
                log(f"  → Charme={result.get('charme')} Reno={result.get('renovierung')}")
            else:
                log(f"  ❌ Analyse fehlgeschlagen")
            
            if (i+1) % 10 == 0:
                wb.save(EXCEL)
                with open(CHECKPOINT,"w") as f: json.dump(checkpoint,f)
                log(f"  💾 gespeichert ({done} neu)")
            
            time.sleep(1)
        
        browser.close()

    wb.save(EXCEL)
    with open(CHECKPOINT,"w") as f: json.dump(checkpoint,f)
    total = sum(1 for v in checkpoint.values() if not v.get("failed") and not v.get("skipped"))
    log(f"\n=== FERTIG: {done} neu, gesamt {total}/309 ===")
    os.system(f'openclaw system event --text "LivingBlue fertig: {done} neue Bilder, gesamt {total}/309" --mode now')

if __name__ == "__main__":
    main()
