#!/usr/bin/env python3
"""Bank Portal Scraper: Servihabitat, Haya, Solvia, Sabadell, Imagin/CaixaBank"""

import requests
from bs4 import BeautifulSoup
import re
import time
import json
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9',
}

def parse_price(text):
    """Extrahiere Preis aus Text"""
    # Muster: 1.234.567,89 €
    m = re.search(r'([\d]{1,3}(?:[\.\s]?\d{3})*),(\d{2})\s*€', text)
    if m:
        try:
            return float(m.group(1).replace('.', '').replace(' ', '') + '.' + m.group(2))
        except:
            pass
    # € 1,234,567
    m = re.search(r'€\s*([\d,\.]+)', text)
    if m:
        try:
            s = m.group(1).replace(',', '')
            return float(s)
        except:
            pass
    return None

def parse_zimmer(text):
    for pattern in [r'(\d+)\s*(?:dormitorio|habitaci|bedroom|dorm\.)', r'(\d+)\s*hab\.']:
        m = re.search(pattern, text, re.I)
        if m:
            return int(m.group(1))
    return None

def parse_flaeche(text):
    m = re.search(r'(\d+(?:[\.,]\d+)?)\s*m[²2]', text)
    if m:
        try:
            return float(m.group(1).replace(',', '.'))
        except:
            pass
    return None

def parse_ort(text):
    mallorca_places = ['Palma', 'Calvià', 'Andratx', 'Pollença', 'Sóller', 'Deià', 
                       'Valldemossa', 'Alcúdia', 'Artà', 'Manacor', 'Inca', 'Llucmajor', 
                       'Santanyí', 'Felanitx', 'Muro', 'Petra', 'Santa Margalida',
                       'Marratxí', 'Binissalem', 'Campanet', 'Selva', 'Alaró',
                       'Portol', 'Esporles', 'Banyalbufar', 'Fornalutx', 'Sencelles',
                       'Consell', 'Bunyola', 'Orient', 'Caimari', 'Moscari']
    for place in mallorca_places:
        if place.lower() in text.lower():
            return place
    return 'Mallorca'

def scrape_servihabitat():
    """Servihabitat (CaixaBank) - Baleares"""
    objects = []
    
    # Servihabitat API/Web
    api_endpoints = [
        'https://www.servihabitat.com/api/properties?province=07&page=1&size=100',
        'https://www.servihabitat.com/api/v1/inmuebles?provincia=baleares&page=1',
    ]
    
    for api_url in api_endpoints:
        try:
            resp = requests.get(api_url, headers={**HEADERS, 'Accept': 'application/json'}, timeout=15)
            print(f"  Servihabitat API {api_url[:60]}: {resp.status_code}")
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print(f"  API Response: {str(data)[:200]}")
                except:
                    pass
        except Exception as e:
            print(f"  API Fehler: {e}")
    
    # Web Scraping
    web_urls = [
        'https://www.servihabitat.com/en/properties/?province=baleares&property_type=house',
        'https://www.servihabitat.com/es/inmuebles/?provincia=baleares',
        'https://www.servihabitat.com/en/buy/?province=illes-balears',
    ]
    
    for url in web_urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            print(f"  Servihabitat Web {url[:60]}: {resp.status_code}")
            if resp.status_code != 200:
                continue
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Cards
            cards = soup.find_all(['article', 'div', 'li'], class_=re.compile(r'property|card|inmueble|result|listing', re.I))
            print(f"    Cards: {len(cards)}")
            
            if cards:
                for card in cards[:3]:
                    print(f"    Sample: {card.get_text(' ', strip=True)[:120]}")
            
            # Links
            links = soup.find_all('a', href=re.compile(r'property|inmueble|detalle|detail', re.I))
            print(f"    Property Links: {len(links)}")
            
            for link in links[:30]:
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = 'https://www.servihabitat.com' + href
                
                parent = link.find_parent(['article', 'div', 'li'])
                parent_text = parent.get_text(' ', strip=True) if parent else link.get_text(strip=True)
                
                if not any(kw in parent_text.lower() for kw in ['balears', 'mallorca', 'palma', 'inca', 'manacor']):
                    # Möglicherweise anderes Gebiet, trotzdem aufnehmen wenn Link plausibel
                    pass
                
                objects.append({
                    'titel': link.get_text(strip=True)[:80] or 'Servihabitat Inmueble',
                    'quelle': 'Servihabitat',
                    'url': href,
                    'preis': parse_price(parent_text),
                    'zimmer': parse_zimmer(parent_text),
                    'grundstueck': None,
                    'wohnflaeche': parse_flaeche(parent_text),
                    'ort': parse_ort(parent_text),
                })
            
            if objects:
                break
                
        except Exception as e:
            print(f"  Servihabitat Fehler: {e}")
    
    return objects

def scrape_haya():
    """Haya Real Estate - Baleares"""
    objects = []
    
    urls = [
        'https://www.hayainmuebles.com/en/homes-for-sale/?location=baleares&province=07',
        'https://www.hayainmuebles.com/es/casas-en-venta/?provincia=baleares',
        'https://www.hayainmuebles.com/en/homes-for-sale/',
    ]
    
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            print(f"  Haya {url[:60]}: {resp.status_code}")
            if resp.status_code != 200:
                continue
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            cards = soup.find_all(['article', 'div'], class_=re.compile(r'property|card|result|listing|inmueble', re.I))
            print(f"    Haya Cards: {len(cards)}")
            
            links = soup.find_all('a', href=re.compile(r'property|inmueble|casa|detalle|vivienda', re.I))
            print(f"    Haya Links: {len(links)}")
            
            for link in links[:30]:
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = 'https://www.hayainmuebles.com' + href
                
                parent = link.find_parent(['article', 'div', 'li'])
                parent_text = parent.get_text(' ', strip=True) if parent else ''
                
                objects.append({
                    'titel': link.get_text(strip=True)[:80] or 'Haya Inmueble',
                    'quelle': 'Haya Real Estate',
                    'url': href,
                    'preis': parse_price(parent_text),
                    'zimmer': parse_zimmer(parent_text),
                    'grundstueck': None,
                    'wohnflaeche': parse_flaeche(parent_text),
                    'ort': parse_ort(parent_text),
                })
            
            if objects:
                break
                
        except Exception as e:
            print(f"  Haya Fehler: {e}")
    
    return objects

def scrape_solvia():
    """Solvia (Sabadell) - Baleares"""
    objects = []
    
    # Solvia hat eine gute API
    api_urls = [
        'https://www.solvia.es/api/v1/properties?province=baleares&page=1&size=50',
        'https://www.solvia.es/api/properties?location=baleares',
    ]
    
    for api_url in api_urls:
        try:
            resp = requests.get(api_url, headers={**HEADERS, 'Accept': 'application/json'}, timeout=15)
            print(f"  Solvia API {api_url[:60]}: {resp.status_code}")
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print(f"  API Keys: {list(data.keys())[:5] if isinstance(data, dict) else 'List'}")
                    # Properties parsen
                    items = data.get('properties', data.get('items', data.get('results', [])))
                    if isinstance(data, list):
                        items = data
                    print(f"  Items: {len(items)}")
                except:
                    pass
        except Exception as e:
            print(f"  Solvia API Fehler: {e}")
    
    # Web
    web_urls = [
        'https://www.solvia.es/en/homes-for-sale/baleares/',
        'https://www.solvia.es/es/casas-en-venta/baleares/',
        'https://www.solvia.es/en/buy/',
    ]
    
    for url in web_urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            print(f"  Solvia Web {url[:60]}: {resp.status_code}")
            if resp.status_code != 200:
                continue
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            cards = soup.find_all(['article', 'div'], class_=re.compile(r'property|card|result|listing', re.I))
            print(f"    Solvia Cards: {len(cards)}")
            
            links = soup.find_all('a', href=re.compile(r'property|inmueble|vivienda|casa|detail', re.I))
            print(f"    Solvia Links: {len(links)}")
            
            for link in links[:30]:
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = 'https://www.solvia.es' + href
                
                parent = link.find_parent(['article', 'div', 'li'])
                parent_text = parent.get_text(' ', strip=True) if parent else ''
                
                objects.append({
                    'titel': link.get_text(strip=True)[:80] or 'Solvia Inmueble',
                    'quelle': 'Solvia (Sabadell)',
                    'url': href,
                    'preis': parse_price(parent_text),
                    'zimmer': parse_zimmer(parent_text),
                    'grundstueck': None,
                    'wohnflaeche': parse_flaeche(parent_text),
                    'ort': parse_ort(parent_text),
                })
            
            if objects:
                break
                
        except Exception as e:
            print(f"  Solvia Fehler: {e}")
    
    return objects

def scrape_sabadell():
    """Banco Sabadell Inmuebles"""
    objects = []
    
    urls = [
        'https://inmuebles.sabadell.com/venta/?location=baleares',
        'https://inmuebles.sabadell.com/es/venta/baleares/',
        'https://inmuebles.sabadell.com/',
    ]
    
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            print(f"  Sabadell {url[:60]}: {resp.status_code}")
            if resp.status_code != 200:
                continue
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            cards = soup.find_all(['article', 'div'], class_=re.compile(r'property|card|inmueble|result', re.I))
            print(f"    Sabadell Cards: {len(cards)}")
            
            links = soup.find_all('a', href=re.compile(r'inmueble|property|detail|vivienda', re.I))
            print(f"    Sabadell Links: {len(links)}")
            
            for link in links[:30]:
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = 'https://inmuebles.sabadell.com' + href
                
                parent = link.find_parent(['article', 'div', 'li'])
                parent_text = parent.get_text(' ', strip=True) if parent else ''
                
                objects.append({
                    'titel': link.get_text(strip=True)[:80] or 'Sabadell Inmueble',
                    'quelle': 'Banco Sabadell',
                    'url': href,
                    'preis': parse_price(parent_text),
                    'zimmer': parse_zimmer(parent_text),
                    'grundstueck': None,
                    'wohnflaeche': parse_flaeche(parent_text),
                    'ort': parse_ort(parent_text),
                })
            
            if objects:
                break
        except Exception as e:
            print(f"  Sabadell Fehler: {e}")
    
    return objects

def scrape_playwright_generic(site_name, quelle, start_urls, base_url):
    """Generischer Playwright-Scraper für JS-heavy Sites"""
    objects = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                locale='es-ES',
            )
            page = context.new_page()
            Stealth().apply_stealth_sync(page)
            
            # API-Calls abfangen
            api_data_collected = []
            def handle_response(response):
                ct = response.headers.get('content-type', '')
                if 'json' in ct and response.status == 200:
                    try:
                        data = response.json()
                        if isinstance(data, (list, dict)):
                            api_data_collected.append({'url': response.url, 'data': data})
                    except:
                        pass
            page.on('response', handle_response)
            
            for url in start_urls:
                try:
                    print(f"  PW {site_name}: {url}")
                    page.goto(url, timeout=30000, wait_until='domcontentloaded')
                    time.sleep(3)
                    
                    # API-Daten verarbeiten
                    for api_resp in api_data_collected:
                        data = api_resp['data']
                        items = []
                        if isinstance(data, list):
                            items = data
                        elif isinstance(data, dict):
                            for key in ['properties', 'items', 'results', 'data', 'inmuebles']:
                                if key in data and isinstance(data[key], list):
                                    items = data[key]
                                    break
                        
                        for item in items[:50]:
                            if not isinstance(item, dict):
                                continue
                            
                            # Verschiedene Feldnamen versuchen
                            titel = (item.get('title') or item.get('name') or item.get('titulo') or 
                                     item.get('description', '')[:60] or site_name)
                            url_item = item.get('url') or item.get('link') or item.get('permalink')
                            preis = item.get('price') or item.get('precio') or item.get('valor')
                            zimmer = item.get('bedrooms') or item.get('dormitorios') or item.get('habitaciones')
                            flaeche = item.get('area') or item.get('superficie') or item.get('size')
                            ort = item.get('city') or item.get('ciudad') or item.get('municipio') or item.get('location', 'Mallorca')
                            
                            if url_item and not url_item.startswith('http'):
                                url_item = base_url + url_item
                            
                            objects.append({
                                'titel': str(titel)[:80],
                                'quelle': quelle,
                                'url': url_item or api_resp['url'],
                                'preis': float(preis) if preis else None,
                                'zimmer': int(zimmer) if zimmer else None,
                                'grundstueck': None,
                                'wohnflaeche': float(flaeche) if flaeche else None,
                                'ort': str(ort)[:60],
                            })
                    
                    if api_data_collected:
                        print(f"  {site_name} API: {len(api_data_collected)} Responses, {len(objects)} Objekte")
                        break
                    
                    # HTML-Fallback
                    content = page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    cards = soup.find_all(['article', 'div', 'li'], class_=re.compile(r'property|card|result|inmueble|listing', re.I))
                    for card in cards[:30]:
                        link_tag = card.find('a')
                        if not link_tag:
                            continue
                        href = link_tag.get('href', '')
                        if not href.startswith('http'):
                            href = base_url + href
                        card_text = card.get_text(' ', strip=True)
                        titel = link_tag.get_text(strip=True)[:80] or card_text[:60]
                        
                        if len(titel) < 3:
                            continue
                        
                        objects.append({
                            'titel': titel,
                            'quelle': quelle,
                            'url': href,
                            'preis': parse_price(card_text),
                            'zimmer': parse_zimmer(card_text),
                            'grundstueck': None,
                            'wohnflaeche': parse_flaeche(card_text),
                            'ort': parse_ort(card_text),
                        })
                    
                    print(f"  {site_name} HTML: {len(cards)} Cards -> {len(objects)} Objekte")
                    
                    if objects:
                        break
                except Exception as e:
                    print(f"  {site_name} PW Fehler bei {url}: {e}")
            
            browser.close()
    except Exception as e:
        print(f"  {site_name} PW Global Fehler: {e}")
    
    return objects

def scrape_imaginedge():
    """CaixaBank Inmobiliaria (imaginedge.es)"""
    objects = scrape_playwright_generic(
        'imaginedge',
        'CaixaBank Inmobiliaria',
        [
            'https://www.imaginedge.es/es/propiedades/?provincia=baleares',
            'https://www.imaginedge.es/propiedades/baleares/',
            'https://www.imaginedge.es/',
        ],
        'https://www.imaginedge.es'
    )
    return objects

def main():
    all_objects = []
    
    print("=== Servihabitat (CaixaBank) ===")
    sv = scrape_servihabitat()
    print(f"  -> {len(sv)} Objekte")
    all_objects.extend(sv)
    
    print("\n=== Haya Real Estate ===")
    hy = scrape_haya()
    print(f"  -> {len(hy)} Objekte")
    all_objects.extend(hy)
    
    print("\n=== Solvia (Sabadell) ===")
    so = scrape_solvia()
    print(f"  -> {len(so)} Objekte")
    all_objects.extend(so)
    
    print("\n=== Banco Sabadell ===")
    sb = scrape_sabadell()
    print(f"  -> {len(sb)} Objekte")
    all_objects.extend(sb)
    
    print("\n=== CaixaBank Inmobiliaria (imaginedge) ===")
    ig = scrape_imaginedge()
    print(f"  -> {len(ig)} Objekte")
    all_objects.extend(ig)
    
    return all_objects

if __name__ == '__main__':
    objects = main()
    print(f"\n=== Bankportale Gesamt: {len(objects)} ===")
    for obj in objects[:10]:
        print(f"  [{obj['quelle']}] {obj['titel'][:50]} | {obj['preis']} €")
