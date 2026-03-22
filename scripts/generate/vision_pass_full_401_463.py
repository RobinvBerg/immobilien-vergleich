#!/usr/bin/env python3
"""
Full Vision Pass für Nr.401-463 — alle 7 Felder in einem API-Call
Output: data/sandbox_vision_full.xlsx
"""
import openpyxl, shutil, base64, json, re, time
from pathlib import Path
import anthropic

BASE = Path('/Users/robin/.openclaw/workspace/mallorca-projekt')
SRC = BASE / 'data' / 'mallorca-kandidaten-v2.xlsx'
DST = BASE / 'data' / 'sandbox_vision_full_v3.xlsx'
BILDER = BASE / 'bilder'

PLACEHOLDER_NRS = {408, 414, 429, 433, 436, 455, 457}

shutil.copy(SRC, DST)
print(f"Sandbox: {DST}")

client = anthropic.Anthropic(api_key='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')

wb = openpyxl.load_workbook(DST)
ws = wb.active

PROMPT = '''Analysiere dieses Mallorca Immobilienbild. Antworte NUR mit JSON (kein Markdown):
{
  "charme": <1-5>,
  "gebaeude": "<kurze strukturelle Beschreibung z.B. 'Zweigeschossige Natursteinfinca mit Pool und Gästehaus'>",
  "gaeste": <0|1|2>,
  "anzeigename": "Ort — Kurztitel; Highlight",
  "renovierung": <0-100>,
  "letzte_reno": <Jahr z.B. 2015 oder null>,
  "bewirtschaftung": <1-5>,
  "reno_begruendung": "<1 Satz warum dieser Renovierungsscore — z.B. 'Frisch renoviert, moderne Küche und neue Böden sichtbar'>",
  "kommentar": "<kurzer kreativer persönlicher Kommentar zu diesem Objekt — max 1 Satz, z.B. 'Sehr schön, könnte perfekter Familienrückzugsort sein'>",
  "beschreibung": "<poetische Kurzansprache aus Käuferperspektive — max 1 Satz, z.B. 'Morgens Kaffee auf der Terrasse, abends Sonnenuntergang über dem Meer — hier fühlt sich Urlaub nach Zuhause an'>"
}
Charme: 1=verfallen 2=einfach 3=solide 4=charmant 5=außergewöhnlich
Gebäude: Typ, Stockwerke, Nebengebäude, Besonderheiten. Max 1 Satz.
Renovierung: 0=Ruine 50=solide 100=top renoviert
Bewirtschaftung: 1=sehr aufwendig 5=pflegeleicht'''

count = 0
errors = []

for row in ws.iter_rows(min_row=2):
    nr = row[0].value
    if not nr or not (401 <= nr <= 463):
        continue
    if nr in PLACEHOLDER_NRS:
        print(f'Nr.{nr}: Platzhalter, skip', flush=True)
        continue

    img_path = BILDER / f'{nr}_main.jpg'
    if not img_path.exists():
        print(f'Nr.{nr}: kein Bild, skip', flush=True)
        continue

    img_bytes = img_path.read_bytes()
    media_type = 'image/webp' if b'WEBP' in img_bytes[:12] else 'image/jpeg'

    try:
        img_data = base64.standard_b64encode(img_bytes).decode()
        response = client.messages.create(
            model='claude-haiku-4-5',
            max_tokens=400,
            messages=[{'role': 'user', 'content': [
                {'type': 'image', 'source': {'type': 'base64', 'media_type': media_type, 'data': img_data}},
                {'type': 'text', 'text': PROMPT}
            ]}]
        )

        text = response.content[0].text.strip()
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$', '', text)

        data = json.loads(text)

        row[3].value = data.get('charme', 3)         # col 4  Charme
        row[28].value = data.get('gebaeude', 'Finca') # col 29 Gebäudestruktur
        row[38].value = data.get('anzeigename', '')   # col 39 Anzeigename
        row[39].value = data.get('gaeste', 0)         # col 40 Gästehäuser
        row[21].value = data.get('renovierung', 50)      # col 22 Renovierung
        row[30].value = data.get('letzte_reno')          # col 31 Letzte Reno
        row[22].value = data.get('bewirtschaftung', 3)   # col 23 Bewirtschaftung
        row[32].value = data.get('reno_begruendung', '') # col 33 Reno-Begründung
        row[33].value = data.get('kommentar', '')        # col 34 Kommentar
        row[34].value = data.get('beschreibung', '')     # col 35 Beschreibung

        print(f'Nr.{nr}: Charme={data.get("charme")} | {data.get("gebaeude")} | Reno={data.get("renovierung")} | LetzteReno={data.get("letzte_reno")} | Bewirt={data.get("bewirtschaftung")} | {data.get("anzeigename","")[:50]}', flush=True)
        count += 1

    except Exception as e:
        print(f'Nr.{nr}: ❌ {e}', flush=True)
        errors.append(nr)

    time.sleep(0.5)

wb.save(DST)
print(f'\n✅ {count} verarbeitet, {len(errors)} Fehler: {errors}')
print(f'→ {DST.name}')
