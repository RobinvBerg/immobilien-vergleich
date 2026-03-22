#!/usr/bin/env python3
"""
Educated Guess für Nr.401-463: Charme, Gebäudestruktur, Gästehäuser, Anzeigename
Basis: Titel, Ort, Preis, Zimmer, Baujahr, Grundstück
Output: data/sandbox_educated_guess.xlsx (Kopie von v2 mit gefüllten Feldern)
"""
import openpyxl, shutil, re
from pathlib import Path

BASE = Path('/Users/robin/.openclaw/workspace/mallorca-projekt')
SRC = BASE / 'data' / 'mallorca-kandidaten-v2.xlsx'
DST = BASE / 'data' / 'sandbox_educated_guess.xlsx'

shutil.copy(SRC, DST)
print(f"Sandbox: {DST}")

wb = openpyxl.load_workbook(DST)
ws = wb.active

def guess_charme(titel, preis, baujahr, grundstueck):
    titel_l = (titel or '').lower()
    charme = 3  # default
    
    # Höherer Preis → tendenziell höherer Charme
    if preis and preis >= 6000000:
        charme = 4
    if preis and preis >= 8000000:
        charme = 4
    
    # Schlüsselwörter → Charme hoch
    if any(w in titel_l for w in ['historisch', 'historic', 'possessió', 'possessio', 'traditionell', 'original', 'authentisch', 'jahrhundert', 'weingut', 'luxuriös', 'luxuri']):
        charme = max(charme, 4)
    if any(w in titel_l for w in ['traumfinca', 'superlative', 'einzigartig', 'besonders', 'exklusiv', 'magnificent', 'spectacular']):
        charme = max(charme, 4)
    
    # Neubau → eher 3
    if any(w in titel_l for w in ['neubau', 'neu gebaut', 'newly built', 'new build', '2024', '2025']):
        charme = min(charme, 3)
    
    # Großes Grundstück → +
    if grundstueck and grundstueck >= 50000:
        charme = max(charme, 3)
    
    return charme

def guess_gebaeude(titel):
    titel_l = (titel or '').lower()
    if any(w in titel_l for w in ['villa', 'luxusvilla']):
        return 'Villa'
    if any(w in titel_l for w in ['possessió', 'possessio', 'landgut', 'anwesen']):
        return 'Finca'
    if any(w in titel_l for w in ['landhaus']):
        return 'Landhaus'
    return 'Finca'  # default für Kensington

def guess_gaeste(titel, zimmer):
    titel_l = (titel or '').lower()
    if any(w in titel_l for w in ['gästehaus', 'gaestehäuser', 'guesthouses', 'guest house', 'two houses', 'zwei häuser', 'nebengebäude']):
        if 'zwei' in titel_l or 'two' in titel_l or 'gästehäusern' in titel_l:
            return 2
        return 1
    if zimmer and zimmer >= 12:
        return 1  # große Anlage → wahrscheinlich Gästehaus
    return 0

def guess_anzeigename(titel, ort, preis, baujahr, grundstueck):
    # Ort bereinigen
    ort_clean = (ort or '').replace(' Mallorca', '').replace('Mallorca ', '').strip()
    ort_clean = re.sub(r'\s+', ' ', ort_clean).title()
    # Entferne bekannte Fehler
    ort_clean = ort_clean.replace('Der Naehe Von ', '')
    ort_clean = ort_clean.replace('Mit Lizenz Zur Ferienvermietung Pool Und Tennisplatz Zu Verkaufen', '')
    ort_clean = ort_clean.strip()
    
    titel_l = (titel or '').lower()
    
    # Highlight bestimmen
    highlights = []
    if grundstueck:
        ha = grundstueck / 10000
        if ha >= 1:
            highlights.append(f'{ha:.1f}ha')
    if baujahr and baujahr < 1950:
        highlights.append(f'Baujahr {baujahr}')
    elif baujahr and baujahr >= 2020:
        highlights.append('Neubau')
    if 'weingut' in titel_l or 'wein' in titel_l:
        highlights.append('Weingut')
    if 'pool' in titel_l:
        highlights.append('Pool')
    if 'meerblick' in titel_l or 'meer' in titel_l or 'sea view' in titel_l:
        highlights.append('Meerblick')
    if 'gästehaus' in titel_l or 'guest' in titel_l:
        highlights.append('Gästehaus')
    if 'tennis' in titel_l:
        highlights.append('Tennis')
    if 'lizenz' in titel_l or 'etv' in titel_l or 'licence' in titel_l:
        highlights.append('ETV-Lizenz')
    
    # Kurztitel aus Titel ableiten
    kurz = (titel or '')
    # Entferne Ortsnamen und generische Teile
    for rem in [', Mallorca', 'bei Mallorca', f'bei {ort_clean}', f'in {ort_clean}', ' - ', ' – ']:
        kurz = kurz.replace(rem, '')
    # Kürzen
    kurz = kurz.strip().rstrip(',').strip()
    if len(kurz) > 40:
        kurz = kurz[:37] + '...'
    
    highlight_str = ', '.join(highlights[:2]) if highlights else 'Kensington'
    return f'{ort_clean} — {kurz}; {highlight_str}'

# Process rows 401-463
count = 0
for row in ws.iter_rows(min_row=2):
    nr = row[0].value
    if not nr or not (401 <= nr <= 463):
        continue
    
    # Skip already filled (the 7 placeholders we did manually)
    if nr in (408, 414, 429, 433, 436, 455, 457):
        print(f'Nr.{nr}: bereits manuell gefüllt, skip')
        continue
    
    titel = row[1].value or ''
    ort = row[9].value or ''
    preis = row[18].value or 0
    zimmer = row[4].value or 0
    baujahr = row[29].value
    grundstueck = row[6].value or 0
    
    charme = guess_charme(titel, preis, baujahr, grundstueck)
    gebaeude = guess_gebaeude(titel)
    gaeste = guess_gaeste(titel, zimmer)
    anzeige = guess_anzeigename(titel, ort, preis, baujahr, grundstueck)
    
    row[3].value = charme       # col 4 Charme
    row[28].value = gebaeude    # col 29 Gebäudestruktur
    row[38].value = anzeige     # col 39 Anzeigename
    row[39].value = gaeste      # col 40 Gästehäuser
    
    print(f'Nr.{nr}: Charme={charme} | {gebaeude} | Gäste={gaeste} | {anzeige}')
    count += 1

wb.save(DST)
print(f'\n✅ {count} Objekte verarbeitet → {DST.name}')
