#!/usr/bin/env python3
"""Privat / Direktverkauf: Wallapop, Milanuncios"""

import requests
from bs4 import BeautifulSoup
import re
import time
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, */*',
    'Accept-Language': 'es-ES,es;q=0.9',
}

def scrape_wallapop():
    """Wallapop API - Mallorca Immobilien"""
    objects = []
    
    # Verschiedene Suchbegriffe
    searches = [
        'mallorca+casa',
        'mallorca+chalet',
        'mallorca+finca',
        'mallorca+villa',
    ]
    
    seen_ids = set()
    
    for keyword in searches:
        api_url = f'https://api.wallapop.com/api/v3/general/search?keywords={keyword}&category_ids=200&filters_source=default_filters&order_by=price_desc&min_sale_price=500000'
        
        try:
            resp = requests.get(api_url, headers={
                **HEADERS,
                'Accept': 'application/json',
                'X-DeviceOS': '0',
            }, timeout=20)
            
            print(f"  Wallapop '{keyword}': {resp.status_code}")
            
            if resp.status_code != 200:
                continue
            
            data = resp.json()
            
            # Ergebnisse extrahieren
            items = []
            if isinstance(data, dict):
                # Wallapop gibt normalerweise data.search_objects zurück
                search_objects = data.get('search_objects', data.get('items', data.get('results', [])))
                if isinstance(search_objects, list):
                    items = search_objects
                elif isinstance(search_objects, dict):
                    items = search_objects.get('items', [])
            elif isinstance(data, list):
                items = data
            
            print(f"    Items: {len(items)}")
            
            for item in items:
                if not isinstance(item, dict):
                    continue
                
                item_id = item.get('id', '')
                if item_id in seen_ids:
                    continue
                seen_ids.add(item_id)
                
                titel = item.get('title', '')
                preis_raw = item.get('price', {})
                if isinstance(preis_raw, dict):
                    preis = float(preis_raw.get('amount', 0) or 0)
                else:
                    try:
                        preis = float(preis_raw or 0)
                    except:
                        preis = None
                
                # Nur hochpreisige Objekte
                if preis and preis < 100000:
                    continue
                
                # Location
                loc = item.get('location', {})
                if isinstance(loc, dict):
                    ort = loc.get('city', loc.get('location_label', 'Mallorca'))
                else:
                    ort = 'Mallorca'
                
                # URL
                slug = item.get('web_slug', item.get('slug', ''))
                url = f"https://es.wallapop.com/item/{slug}" if slug else ''
                
                # Content / Beschreibung für mehr Info
                content = item.get('description', '')
                
                # Zimmer aus Beschreibung
                zimmer = None
                bed_match = re.search(r'(\d+)\s*(?:dorm|hab|bedroom)', content, re.I)
                if bed_match:
                    zimmer = int(bed_match.group(1))
                
                # Fläche
                flaeche = None
                m2_match = re.search(r'(\d+)\s*m[²2]', content)
                if m2_match:
                    flaeche = float(m2_match.group(1))
                
                objects.append({
                    'titel': titel[:80],
                    'quelle': 'Wallapop',
                    'url': url,
                    'preis': preis if preis else None,
                    'zimmer': zimmer,
                    'grundstueck': None,
                    'wohnflaeche': flaeche,
                    'ort': str(ort)[:60],
                })
            
            time.sleep(1)
            
        except Exception as e:
            print(f"  Wallapop Fehler '{keyword}': {e}")
    
    return objects

def scrape_milanuncios():
    """Milanuncios - Casas en venta Mallorca"""
    objects = []
    
    urls = [
        'https://www.milanuncios.com/casas-venta/mallorca-baleares.htm?orden=relevance',
        'https://www.milanuncios.com/inmobiliaria/mallorca-baleares.htm?ti=2',
    ]
    
    for url in urls:
        try:
            resp = requests.get(url, headers={
                **HEADERS,
                'Accept': 'text/html,application/xhtml+xml',
            }, timeout=20)
            
            print(f"  Milanuncios {url[:60]}: {resp.status_code}")
            
            if resp.status_code != 200:
                continue
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Anzeigen-Cards
            ads = soup.find_all(['article', 'div', 'li'], class_=re.compile(r'ad-card|listing|anuncio|result', re.I))
            print(f"    Ads: {len(ads)}")
            
            # Alle Links zu Anzeigen
            links = soup.find_all('a', href=re.compile(r'casas|inmobiliaria|vivienda|chalet|villa'))
            print(f"    Links: {len(links)}")
            
            seen_hrefs = set()
            for link in links[:50]:
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = 'https://www.milanuncios.com' + href
                
                if href in seen_hrefs:
                    continue
                seen_hrefs.add(href)
                
                # Überspringe Navigations-Links
                if not re.search(r'/\d+\.htm', href):
                    continue
                
                parent = link.find_parent(['article', 'div', 'li', 'section'])
                parent_text = parent.get_text(' ', strip=True) if parent else ''
                
                titel = link.get_text(strip=True)[:80]
                if len(titel) < 5:
                    titel = parent_text[:60]
                
                preis = None
                preis_match = re.search(r'([\d\.]+)\s*€', parent_text.replace('.', '').replace(',', '.'))
                if not preis_match:
                    preis_match = re.search(r'€\s*([\d\.]+)', parent_text)
                if preis_match:
                    try:
                        p = float(preis_match.group(1))
                        if p > 10000:  # Mindestpreis
                            preis = p
                    except:
                        pass
                
                # Nur wenn Mallorca-Bezug
                if not any(kw in parent_text.lower() for kw in ['mallorca', 'palma', 'balears', 'inca', 'manacor', 'pollença']):
                    if not any(kw in href.lower() for kw in ['mallorca', 'baleares']):
                        continue
                
                objects.append({
                    'titel': titel,
                    'quelle': 'Milanuncios',
                    'url': href,
                    'preis': preis,
                    'zimmer': None,
                    'grundstueck': None,
                    'wohnflaeche': parse_flaeche(parent_text),
                    'ort': parse_ort(parent_text),
                })
            
            if objects:
                break
                
        except Exception as e:
            print(f"  Milanuncios Fehler: {e}")
    
    return objects

def parse_flaeche(text):
    m = re.search(r'(\d+)\s*m[²2]', text)
    return float(m.group(1)) if m else None

def parse_ort(text):
    mallorca_places = ['Palma', 'Calvià', 'Andratx', 'Pollença', 'Sóller', 'Deià', 
                       'Valldemossa', 'Alcúdia', 'Artà', 'Manacor', 'Inca', 'Llucmajor', 
                       'Santanyí', 'Felanitx', 'Muro', 'Petra', 'Santa Margalida', 'Marratxí']
    for place in mallorca_places:
        if place.lower() in text.lower():
            return place
    return 'Mallorca'

def main():
    all_objects = []
    
    print("=== Wallapop ===")
    wl = scrape_wallapop()
    print(f"  -> {len(wl)} Objekte")
    all_objects.extend(wl)
    
    print("\n=== Milanuncios ===")
    ml = scrape_milanuncios()
    print(f"  -> {len(ml)} Objekte")
    all_objects.extend(ml)
    
    return all_objects

if __name__ == '__main__':
    objects = main()
    print(f"\n=== Privat Gesamt: {len(objects)} ===")
    for obj in objects[:10]:
        print(f"  [{obj['quelle']}] {obj['titel'][:50]} | {obj['preis']} €")
