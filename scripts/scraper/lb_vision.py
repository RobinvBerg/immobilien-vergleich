#!/usr/bin/env python3
"""
Vision-Analyse für 113 LivingBlue Objekte.
Schreibt Charme + Reno direkt in mallorca-kandidaten-v2.xlsx
"""
import anthropic, base64, json, openpyxl, os, time

client = anthropic.Anthropic()

LB_NRS = [20,21,22,25,28,29,31,33,34,36,38,41,42,43,45,46,52,54,57,61,62,64,70,73,74,78,81,83,84,86,87,93,100,103,105,108,109,110,114,116,121,125,128,129,136,137,139,140,141,144,149,150,153,157,158,159,160,162,163,171,172,173,179,180,191,192,194,196,197,198,199,200,201,202,207,209,216,219,221,225,230,231,236,237,241,262,267,268,269,270,274,275,276,277,278,285,288,296,297,298,300,301,304,306,308,309,312,318,324,325,328,331,332]

PROMPT = """Analysiere dieses Immobilienbild aus Mallorca.

Antworte NUR mit JSON (kein Text davor/danach):
{
  "charme": <1-5>,
  "reno": <0-100>,
  "begruendung": "<max 1 Satz>"
}

charme: Ästhetik/Charme (1=sehr schlecht, 5=außergewöhnlich schön)
reno: Renovierungsbedarf in % (0=bezugsfertig/neuwertig, 100=komplette Ruine)"""

wb = openpyxl.load_workbook('mallorca-kandidaten-v2.xlsx')
ws = wb.active
headers = [ws.cell(1, c).value for c in range(1, ws.max_column+1)]
col_charme = headers.index('Charme/Ästhetik (1-5)') + 1
col_reno = headers.index('Renovierung (0-100)') + 1
col_reno_begr = headers.index('Reno-Begründung') + 1

# Zeilen-Index aufbauen
row_map = {}
for r in range(2, ws.max_row+1):
    nr = ws.cell(r, 1).value
    if nr: row_map[int(nr)] = r

done = 0
errors = 0

for nr in LB_NRS:
    img_path = f"bilder/{nr}_main.jpg"
    if not os.path.exists(img_path):
        print(f"Nr.{nr} ❌ Bild fehlt")
        errors += 1
        continue

    with open(img_path, 'rb') as f:
        img_b64 = base64.standard_b64encode(f.read()).decode()

    try:
        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}},
                    {"type": "text", "text": PROMPT}
                ]
            }]
        )
        text = resp.content[0].text.strip()
        # JSON extrahieren
        start = text.find('{')
        end = text.rfind('}') + 1
        data = json.loads(text[start:end])
        charme = int(data['charme'])
        reno = int(data['reno'])
        begr = data.get('begruendung', '')

        row = row_map[nr]
        ws.cell(row, col_charme).value = charme
        ws.cell(row, col_reno).value = reno
        ws.cell(row, col_reno_begr).value = begr

        done += 1
        print(f"Nr.{nr} ✅ Charme={charme} Reno={reno} — {begr[:60]}")

        if done % 10 == 0:
            wb.save('mallorca-kandidaten-v2.xlsx')
            print(f"  💾 Gespeichert ({done}/{len(LB_NRS)})")

        time.sleep(0.3)

    except Exception as e:
        print(f"Nr.{nr} ❌ {e}")
        errors += 1

wb.save('mallorca-kandidaten-v2.xlsx')
print(f"\n✅ Fertig: {done} analysiert, {errors} Fehler")
print("mallorca-kandidaten-v2.xlsx gespeichert.")
