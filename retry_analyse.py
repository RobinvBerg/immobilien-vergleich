#!/usr/bin/env python3
"""Retry für fehlgeschlagene Bilder-Analysen"""
import json, os, re, time, requests, base64
from pathlib import Path

BASE = Path(__file__).parent
BILDER_DIR = BASE / "bilder"
LOG = BASE / "retry_log.txt"
CHECKPOINT = BASE / "bilder_analyse_checkpoint.json"
EXCEL = BASE / "mallorca-kandidaten-v2.xlsx"
BILDER_JSON = BASE / "mallorca-bilder.json"

import anthropic, openpyxl

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def log(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")

def encode_image(path):
    from PIL import Image
    import io
    # Komprimiere auf max 4MB / max 1600px
    img = Image.open(path).convert("RGB")
    max_size = 1600
    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75, optimize=True)
    data = buf.getvalue()
    # Falls immer noch zu groß, weiter komprimieren
    q = 60
    while len(data) > 4_000_000 and q > 20:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=q, optimize=True)
        data = buf.getvalue()
        q -= 10
    return base64.standard_b64encode(data).decode("utf-8"), "image/jpeg"

def download_image(url, path, timeout=15):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code == 200 and len(r.content) > 5000:
            with open(path, "wb") as f:
                f.write(r.content)
            return True
    except Exception as e:
        log(f"  Download fehler: {e}")
    return False

def try_get_image_url(obj_url, fallback_url):
    """Versuche bessere Bild-URL zu finden"""
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    try:
        r = requests.get(obj_url, headers=headers, timeout=15)
        if r.status_code != 200:
            return fallback_url
        
        if "livingblue-mallorca.com" in obj_url:
            # LivingBlue: suche nach egorealestate CDN URLs mit echten IDs
            matches = re.findall(r'https://media\.egorealestate\.com/[A-Z0-9_/]+/[a-f0-9\-]+\.[a-z]+', r.text)
            if matches and matches[0] != fallback_url:
                return matches[0]
            # Alternativ: suche nach property-spezifischen Bild-URLs
            matches2 = re.findall(r'"(https://[^"]+(?:jpg|jpeg|webp|png))"', r.text)
            for m in matches2:
                if "placeholder" not in m.lower() and "logo" not in m.lower():
                    return m
        elif "kyero.com" in obj_url:
            matches = re.findall(r'https://[^"\']+(?:jpg|jpeg|webp)[^"\']*', r.text)
            for m in matches:
                if "property" in m.lower() or "listing" in m.lower():
                    return m
    except Exception as e:
        log(f"  URL-Suche Fehler: {e}")
    return fallback_url

def analyze_image(path, beschreibung=""):
    b64, mt = encode_image(path)
    content = [
        {"type": "image", "source": {"type": "base64", "media_type": mt, "data": b64}},
        {"type": "text", "text": f"""Mallorca Immobilie bewerten (Familie, 3 Kinder, Finca/Landgut).
Beschreibung: {beschreibung[:200] if beschreibung else 'keine'}

CHARME: X (1-5, Ästhetik/Charakter)
RENOVIERUNG: XX (0=perfekt, 60=mittel, 100=Rohbau)
GEBÄUDESTRUKTUR: ... (kurz, z.B. "Rustikale Finca + Gästehaus, Pool")
GÄSTEHAUS: ja/nein/unklar
RENO_BEGRUENDUNG: ... (1 Satz)"""}
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
        log(f"  API Fehler: {e}")
        return None

def main():
    log("=== RETRY Analyse ===")
    checkpoint = json.load(open(CHECKPOINT))
    bilder_data = json.load(open(BILDER_JSON))
    wb = openpyxl.load_workbook(EXCEL)
    ws = wb.active
    
    failed = [k for k,v in checkpoint.items() if v.get("failed")]
    log(f"Fehler zu retrying: {len(failed)}")
    
    done = 0
    for i, row_str in enumerate(failed):
        row = int(row_str)
        entry = bilder_data.get(row_str, {})
        obj_url = entry.get("url", "")
        img_url = entry.get("img_url", "")
        beschreibung = entry.get("desc", "")
        
        log(f"\n[{i+1}/{len(failed)}] Zeile {row}")
        
        # Prüfe ob Bild schon lokal
        local = None
        for ext in ["jpg", "jpeg", "webp", "png"]:
            p = BILDER_DIR / f"{row}_main.{ext}"
            if p.exists() and p.stat().st_size > 5000:
                local = str(p)
                break
        
        if not local:
            # Versuche bessere URL
            if obj_url:
                better_url = try_get_image_url(obj_url, img_url)
                if better_url and better_url != img_url:
                    log(f"  Neue URL gefunden")
                    img_url = better_url
            
            if img_url:
                p = BILDER_DIR / f"{row}_main.jpg"
                if download_image(img_url, str(p)):
                    local = str(p)
                    log(f"  ✅ Bild heruntergeladen")
                else:
                    log(f"  ❌ Bild nicht ladbar")
        else:
            log(f"  📁 Bild bereits lokal")
        
        if not local:
            log(f"  ⏭️ Kein Bild — skip")
            continue
        
        result = analyze_image(local, beschreibung)
        if result:
            if "charme" in result: ws.cell(row, 4).value = result["charme"]
            if "renovierung" in result:
                ws.cell(row, 22).value = result["renovierung"]
                ws.cell(row, 32).value = result["renovierung"]
            if "gebaeude" in result: ws.cell(row, 29).value = result["gebaeude"]
            if "reno_begruendung" in result: ws.cell(row, 33).value = result["reno_begruendung"]
            ws.cell(row, 34).value = "Vision-Analyse (retry)"
            checkpoint[row_str] = result
            done += 1
            log(f"  → Charme={result.get('charme','?')} Reno={result.get('renovierung','?')}")
        else:
            log(f"  ❌ Analyse fehlgeschlagen")
        
        time.sleep(0.3)
    
    wb.save(EXCEL)
    log(f"\n=== RETRY FERTIG: {done}/{len(failed)} erfolgreich ===")
    import json as _json
    with open(CHECKPOINT, "w") as f:
        _json.dump(checkpoint, f)
    os.system(f'openclaw system event --text "Retry fertig: {done} zusätzliche Objekte bewertet" --mode now')

if __name__ == "__main__":
    main()
