#!/usr/bin/env python3
"""
Vision Pass für Nr.401-463 (nur echte Bilder, keine Platzhalter)
Output: data/sandbox_vision.xlsx
"""
import openpyxl, shutil, base64, json, re, time
from pathlib import Path
import anthropic

BASE = Path('/Users/robin/.openclaw/workspace/mallorca-projekt')
SRC = BASE / 'data' / 'mallorca-kandidaten-v2.xlsx'
DST = BASE / 'data' / 'sandbox_vision.xlsx'
BILDER = BASE / 'bilder'

PLACEHOLDER_NRS = {408, 414, 429, 433, 436, 455, 457}

shutil.copy(SRC, DST)
print(f"Sandbox: {DST}")

client = anthropic.Anthropic(api_key='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')

wb = openpyxl.load_workbook(DST)
ws = wb.active

count = 0
errors = []

for row in ws.iter_rows(min_row=2):
    nr = row[0].value
    if not nr or not (401 <= nr <= 463):
        continue
    if nr in PLACEHOLDER_NRS:
        print(f'Nr.{nr}: Platzhalter, skip')
        continue

    img_path = BILDER / f'{nr}_main.jpg'
    if not img_path.exists():
        print(f'Nr.{nr}: kein Bild, skip')
        continue

    img_bytes = img_path.read_bytes()
    media_type = 'image/webp' if b'WEBP' in img_bytes[:12] else 'image/jpeg'

    try:
        img_data = base64.standard_b64encode(img_bytes).decode()
        response = client.messages.create(
            model='claude-haiku-4-5',
            max_tokens=300,
            messages=[{'role': 'user', 'content': [
                {'type': 'image', 'source': {'type': 'base64', 'media_type': media_type, 'data': img_data}},
                {'type': 'text', 'text': 'Analysiere dieses Mallorca Immobilienbild. Antworte NUR mit JSON (kein Markdown): {"charme": <1-5>, "gebaeude": "Finca|Villa|Landhaus|Possessio", "gaeste": <0|1|2>, "anzeigename": "Ort — Kurztitel; Highlight"}. Charme: 1=verfallen 2=einfach 3=solide 4=charmant 5=außergewöhnlich. Gäste: sichtbare Nebengebäude.'}
            ]}]
        )

        text = response.content[0].text.strip()
        # Strip markdown if present
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$', '', text)

        data = json.loads(text)
        charme = data.get('charme', 3)
        gebaeude = data.get('gebaeude', 'Finca')
        gaeste = data.get('gaeste', 0)
        anzeige = data.get('anzeigename', '')

        row[3].value = charme
        row[28].value = gebaeude
        row[38].value = anzeige
        row[39].value = gaeste

        print(f'Nr.{nr}: Charme={charme} | {gebaeude} | Gäste={gaeste} | {anzeige}', flush=True)
        count += 1

    except Exception as e:
        print(f'Nr.{nr}: ❌ {e}', flush=True)
        errors.append(nr)

    time.sleep(0.5)

wb.save(DST)
print(f'\n✅ {count} verarbeitet, {len(errors)} Fehler: {errors}')
print(f'→ {DST.name}')
