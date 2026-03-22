#!/usr/bin/env python3
"""BOE Subastas Scraper - Offizielle Zwangsversteigerungen Baleares"""

import requests
from bs4 import BeautifulSoup
import time
import re

def scrape_boe_subastas():
    objects = []
    base_url = "https://subastas.boe.es"
    
    # Provinz 07 = Baleares, verschiedene Bietetypen
    search_urls = [
        "https://subastas.boe.es/buscar.php?campo[0]=SUBASTA_PROVINCIA&dato[0]=07&campo[1]=BIEN_TIPO&dato[1]=BR&page_hits=500",
        "https://subastas.boe.es/buscar.php?campo[0]=SUBASTA_PROVINCIA&dato[0]=07&campo[1]=BIEN_TIPO&dato[1]=BV&page_hits=500",
        "https://subastas.boe.es/buscar.php?campo[0]=SUBASTA_PROVINCIA&dato[0]=07&page_hits=500",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept-Language': 'es-ES,es;q=0.9',
    }
    
    seen_ids = set()
    
    for url in search_urls:
        try:
            print(f"  BOE URL: {url[:80]}...")
            resp = requests.get(url, headers=headers, timeout=30)
            print(f"  Status: {resp.status_code}")
            
            if resp.status_code != 200:
                continue
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # BOE hat Tabelle mit Suchergebnissen
            # Suche nach Links zu Einzelsubasta
            links = soup.find_all('a', href=re.compile(r'detalleSubasta\.php'))
            print(f"  Gefundene Subasta-Links: {len(links)}")
            
            # Auch direkt in Tabellen suchen
            tables = soup.find_all('table')
            print(f"  Tabellen auf Seite: {len(tables)}")
            
            # Alle Subasta-Detail-Links sammeln
            subasta_ids = set()
            for link in links:
                href = link.get('href', '')
                match = re.search(r'idSub=([A-Z0-9-]+)', href)
                if match:
                    subasta_ids.add(match.group(1))
            
            print(f"  Einzigartige Subasta-IDs: {len(subasta_ids)}")
            
            # Jeden Eintrag parsen aus der Tabelle
            # BOE Struktur: Tabelle mit Zeilen pro Subasta
            rows = soup.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 3:
                    continue
                    
                row_text = row.get_text(' ', strip=True)
                
                # Link zur Subasta-Detailseite
                link_tag = row.find('a', href=re.compile(r'detalleSubasta'))
                if not link_tag:
                    continue
                
                href = link_tag.get('href', '')
                match = re.search(r'idSub=([A-Z0-9-]+)', href)
                if not match:
                    continue
                    
                subasta_id = match.group(1)
                if subasta_id in seen_ids:
                    continue
                seen_ids.add(subasta_id)
                
                detail_url = f"{base_url}/{href}" if not href.startswith('http') else href
                
                # Grundinfos aus der Listenzeile
                titel = link_tag.get_text(strip=True)
                
                # Preis aus Zellen extrahieren
                preis = None
                ort = None
                for cell in cells:
                    cell_text = cell.get_text(strip=True)
                    # Preis-Pattern: 1.234.567,00 €
                    preis_match = re.search(r'([\d\.]+,\d{2})\s*€', cell_text)
                    if preis_match and not preis:
                        preis_str = preis_match.group(1).replace('.', '').replace(',', '.')
                        try:
                            preis = float(preis_str)
                        except:
                            pass
                
                objects.append({
                    'titel': titel or f"BOE Subasta {subasta_id}",
                    'quelle': 'BOE Subastas',
                    'url': detail_url,
                    'preis': preis,
                    'zimmer': None,
                    'grundstueck': None,
                    'wohnflaeche': None,
                    'ort': 'Baleares',
                })
            
            time.sleep(2)
            
        except Exception as e:
            print(f"  Fehler bei {url}: {e}")
    
    # Jetzt Detail-Pages für erste 20 Objekte abrufen um mehr Info zu bekommen
    print(f"\n  Hole Details für erste 20 Subastas...")
    for obj in objects[:20]:
        try:
            resp = requests.get(obj['url'], headers=headers, timeout=30)
            if resp.status_code != 200:
                continue
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Titel
            h1 = soup.find('h1')
            if h1:
                obj['titel'] = h1.get_text(strip=True)
            
            # Infos aus Tabelle
            content = soup.get_text(' ', strip=True)
            
            # Preis
            preis_match = re.search(r'Valor[^:]*:\s*([\d\.]+,\d{2})\s*€', content)
            if preis_match:
                preis_str = preis_match.group(1).replace('.', '').replace(',', '.')
                try:
                    obj['preis'] = float(preis_str)
                except:
                    pass
            
            # Ort
            ort_match = re.search(r'Municipio[^:]*:\s*([^\n]+)', content)
            if ort_match:
                obj['ort'] = ort_match.group(1).strip()[:50]
            
            # Superficie
            sup_match = re.search(r'Superficie[^:]*:\s*([\d,\.]+)\s*m', content)
            if sup_match:
                try:
                    obj['wohnflaeche'] = float(sup_match.group(1).replace(',', '.'))
                except:
                    pass
            
            time.sleep(1)
            
        except Exception as e:
            pass
    
    return objects

if __name__ == '__main__':
    print("=== BOE Subastas ===")
    objects = scrape_boe_subastas()
    print(f"\nGefunden: {len(objects)} Objekte")
    for obj in objects[:5]:
        print(f"  {obj['titel'][:50]} | {obj['preis']} € | {obj['ort']}")
