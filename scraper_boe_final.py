#!/usr/bin/env python3
"""BOE Subastas Scraper - Offizielle Zwangsversteigerungen Baleares"""

import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import date
from openpyxl import load_workbook

BASE_URL = "https://subastas.boe.es"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'es-ES,es;q=0.9',
}

def fetch_list():
    data = {
        'campo[2]': 'SUBASTA.ESTADO.CODIGO',
        'dato[2]': 'EJ',
        'campo[3]': 'BIEN.TIPO',
        'dato[3]': 'I',
        'campo[8]': 'BIEN.COD_PROVINCIA',
        'dato[8]': '07',
        'campo[18]': 'SUBASTA.FECHA_INICIO',
        'dato[18][0]': '',
        'dato[18][1]': '',
        'page_hits': '500',
        'sort_field[0]': 'SUBASTA.FECHA_FIN',
        'sort_order[0]': 'desc',
        'accion': 'Buscar',
    }
    resp = requests.post(f"{BASE_URL}/subastas_ava.php", headers=HEADERS, data=data, timeout=30)
    return resp.text

def parse_list(html):
    soup = BeautifulSoup(html, 'html.parser')
    seen = set()
    entries = []
    
    links = soup.find_all('a', href=re.compile(r'detalleSubasta'))
    for link in links:
        href = link.get('href', '')
        match = re.search(r'idSub=([A-Z0-9-]+)', href)
        if not match:
            continue
        subasta_id = match.group(1)
        if subasta_id in seen:
            continue
        seen.add(subasta_id)
        
        # Kontext-Text aus Parent-Element
        parent = link.parent
        ctx = parent.get_text(' ', strip=True) if parent else ''
        
        # Ort aus Kontext
        ort = 'Baleares'
        ort_match = re.search(r'-\s+([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ\s]+?)(?:\s+Expediente|\s+Estado)', ctx)
        if ort_match:
            ort = ort_match.group(1).strip()
        
        full_url = BASE_URL + '/' + href.lstrip('./')
        entries.append({'id': subasta_id, 'url': full_url, 'ort': ort, 'ctx': ctx})
    
    return entries

def fetch_detail(entry):
    try:
        resp = requests.get(entry['url'], headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text(' ', strip=True)
        
        obj = {
            'titel': f"BOE Subasta {entry['id']}",
            'quelle': 'BOE Subastas',
            'url': entry['url'],
            'preis': None,
            'zimmer': None,
            'grundstueck': None,
            'wohnflaeche': None,
            'ort': entry['ort'],
        }
        
        # Titel aus H2/H3
        for tag in ['h2', 'h3', 'h4']:
            t = soup.find(tag)
            if t:
                obj['titel'] = t.get_text(' ', strip=True)[:120]
                break
        
        # Preis: "Valor subasta: 123.456,78 €" oder "Importe: ..."
        for pattern in [
            r'Valor\s+subasta[^0-9]*([\d\.]+,\d{2})\s*€',
            r'Valor\s+tasaci[oó]n[^0-9]*([\d\.]+,\d{2})\s*€',
            r'Importe[^0-9]*([\d\.]+,\d{2})\s*€',
            r'Precio[^0-9]*([\d\.]+,\d{2})\s*€',
        ]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                try:
                    obj['preis'] = float(m.group(1).replace('.', '').replace(',', '.'))
                    break
                except:
                    pass
        
        # Superficie / Wohnfläche
        for pattern in [
            r'Superficie\s+construida[^0-9]*([\d,\.]+)\s*m',
            r'Superficie[^0-9]*([\d,\.]+)\s*m[²2]',
            r'superficie[^0-9]*([\d,\.]+)\s*m',
        ]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                try:
                    obj['wohnflaeche'] = float(m.group(1).replace(',', '.'))
                    break
                except:
                    pass
        
        # Municipio / Ort
        for pattern in [
            r'Municipio\s*[:]\s*([^\n\|]+)',
            r'Localidad\s*[:]\s*([^\n\|]+)',
            r'Poblaci[oó]n\s*[:]\s*([^\n\|]+)',
        ]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                obj['ort'] = m.group(1).strip()[:60]
                break
        
        # Habitaciones / Zimmer
        m = re.search(r'[Hh]abitaciones?\s*[:]\s*(\d+)', text)
        if m:
            try:
                obj['zimmer'] = int(m.group(1))
            except:
                pass
        
        return obj
    except Exception as e:
        print(f"  Fehler bei Detail {entry['id']}: {e}")
        return None

def main():
    print("=== BOE Subastas Baleares ===")
    
    print("  Hole Ergebnisliste...")
    html = fetch_list()
    entries = parse_list(html)
    print(f"  Gefunden: {len(entries)} Subastas")
    
    objects = []
    for i, entry in enumerate(entries):
        print(f"  [{i+1}/{len(entries)}] {entry['id']} - {entry['ort'][:40]}")
        obj = fetch_detail(entry)
        if obj:
            objects.append(obj)
            print(f"    Preis: {obj['preis']} | Fläche: {obj['wohnflaeche']} m² | Ort: {obj['ort'][:40]}")
        time.sleep(1.5)
    
    return objects

if __name__ == '__main__':
    objects = main()
    print(f"\n=== Ergebnis BOE: {len(objects)} Objekte ===")
    for obj in objects:
        print(f"  {obj['titel'][:50]} | {obj['preis']} € | {obj['ort']}")
