#!/usr/bin/env python3
"""
Holt Grundstück (G), berechnet Garten (I) und €/m² bebaut (T) für Kensington Nr.406-466
"""
import re, time, openpyxl
from camoufox.sync_api import Camoufox

wb = openpyxl.load_workbook('data/mallorca-kandidaten-v2.xlsx')
ws = wb['Mallorca Kandidaten']

# Sammle Zeilen 407-467 (Nr. 406-466)
kensington_rows = []
for row in ws.iter_rows(min_row=407, max_row=467):
    nr = row[0].value
    url = row[2].value
    flaeche = row[7].value   # H: bebaute Fläche
    preis = row[18].value    # S: Preis
    kensington_rows.append((row[0].row, nr, url, flaeche, preis))

print(f'{len(kensington_rows)} Zeilen zu verarbeiten')

with Camoufox(headless=True) as browser:
    page = browser.new_page()
    for i, (row_num, nr, url, flaeche, preis) in enumerate(kensington_rows):
        try:
            page.goto(url, timeout=45000, wait_until='domcontentloaded')
            time.sleep(2)
            text = page.inner_text('body')

            # Grundstück: suche nach Zahl vor "Plot size" oder "Grundstücksgröße"
            grundstueck = None
            m = re.search(r'~?\s*([\d,\.]+)\s*m²\s*\n\s*(?:Plot size|Grundstücksgröße|Grundstück)', text)
            if not m:
                m = re.search(r'(?:Plot size|Grundstücksgröße|Grundstück)\s*\n\s*~?\s*([\d,\.]+)\s*m²', text)
            if m:
                val = m.group(1).replace(',','').replace('.','')
                # Wenn mehr als 6 Stellen könnte es mit Dezimal sein
                raw = m.group(1)
                # Format: 23,457.00 → 23457
                clean = re.sub(r'[^\d\.]', '', raw.replace(',', ''))
                try:
                    grundstueck = int(float(clean))
                except:
                    pass

            # G: Grundstück
            ws.cell(row=row_num, column=7).value = grundstueck

            # I: Garten = Grundstück - bebaute Fläche
            if grundstueck and flaeche:
                garten = max(0, grundstueck - int(flaeche))
                ws.cell(row=row_num, column=9).value = garten

            # T: €/m² bebaut
            if preis and flaeche:
                eur_m2 = round(int(preis) / int(flaeche))
                ws.cell(row=row_num, column=20).value = eur_m2

            status = f'G={grundstueck or "?"}'
            print(f'[{i+1}/{len(kensington_rows)}] Nr.{nr} {status}')

        except Exception as e:
            print(f'[{i+1}] Nr.{nr} FEHLER: {str(e)[:60]}')

wb.save('data/mallorca-kandidaten-v2.xlsx')
print(f'\n✅ Fertig — Excel gespeichert')
