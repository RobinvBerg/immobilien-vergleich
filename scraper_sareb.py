#!/usr/bin/env python3
"""SAREB Scraper - Spanische Bad Bank"""

import requests
from bs4 import BeautifulSoup
import re
import time
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'es-ES,es;q=0.9',
    'Referer': 'https://www.sareb.es/',
}

def try_sareb_api():
    """Versuche SAREB API"""
    objects = []
    
    # Mögliche API-Endpunkte
    api_urls = [
        'https://www.sareb.es/api/inmuebles?provincia=illes-balears&tipo=vivienda&page=1&size=100',
        'https://www.sareb.es/api/v1/properties?province=07&type=house',
        'https://api.sareb.es/v1/properties?province=Baleares',
    ]
    
    for url in api_urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            print(f"  SAREB API {url[:60]}: {resp.status_code}")
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print(f"    JSON Keys: {list(data.keys())[:5] if isinstance(data, dict) else 'List'}")
                    return data, url
                except:
                    pass
        except Exception as e:
            print(f"  Fehler: {e}")
    
    return None, None

def scrape_sareb_web():
    """Scrape SAREB Website direkt"""
    objects = []
    
    # SAREB Suchseite
    urls = [
        'https://www.sareb.es/es/encuentra-tu-inmueble?provincia=illes-balears&tipo=vivienda',
        'https://www.sareb.es/es/encuentra-tu-inmueble?comunidad=illes-balears',
        'https://www.sareb.es/encuentra-tu-inmueble',
    ]
    
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            print(f"  SAREB Web {url[:60]}: {resp.status_code}")
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Nach Immobilien-Cards suchen
                cards = soup.find_all(['article', 'div'], class_=re.compile(r'card|inmueble|property|result', re.I))
                print(f"    Cards gefunden: {len(cards)}")
                
                if cards:
                    for card in cards[:5]:
                        print(f"    Card: {card.get_text(' ', strip=True)[:100]}")
                
                # Alle Links
                links = soup.find_all('a', href=re.compile(r'inmueble|property', re.I))
                print(f"    Property-Links: {len(links)}")
                
                # JSON-LD suchen
                json_scripts = soup.find_all('script', type='application/ld+json')
                for script in json_scripts:
                    try:
                        data = json.loads(script.string)
                        print(f"    JSON-LD: {json.dumps(data)[:200]}")
                    except:
                        pass
                
                # Alle script-Tags nach API-Calls durchsuchen
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'balears' in script.string.lower():
                        print(f"    Script mit Baleares: {script.string[:200]}")
                        
        except Exception as e:
            print(f"  Fehler bei SAREB: {e}")
    
    return objects

def try_sareb_playwright():
    """Playwright für JavaScript-heavy SAREB"""
    from playwright.sync_api import sync_playwright
    from playwright_stealth import Stealth
    
    objects = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            locale='es-ES',
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        
        # API-Requests abfangen
        api_responses = []
        def on_response(response):
            if 'api' in response.url or 'inmueble' in response.url:
                try:
                    if 'json' in response.headers.get('content-type', ''):
                        data = response.json()
                        api_responses.append({'url': response.url, 'data': data})
                        print(f"  API Response: {response.url[:60]} -> {str(data)[:100]}")
                except:
                    pass
        
        page.on('response', on_response)
        
        url = 'https://www.sareb.es/es/encuentra-tu-inmueble?provincia=illes-balears&tipo=vivienda'
        print(f"  Playwright -> {url}")
        
        try:
            page.goto(url, timeout=30000, wait_until='networkidle')
            time.sleep(3)
            
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Cards suchen
            cards = soup.find_all(['article', 'div', 'li'], class_=re.compile(r'card|result|property|inmueble', re.I))
            print(f"  Playwright Cards: {len(cards)}")
            
            for card in cards[:3]:
                print(f"  Card Text: {card.get_text(' ', strip=True)[:150]}")
            
            # Alle Texte nach Preis-Pattern suchen
            text = page.inner_text('body')
            prices = re.findall(r'[\d\.]+,\d{2}\s*€', text)
            print(f"  Preise gefunden: {prices[:10]}")
            
            # Links zu Einzelobjekten
            links = page.query_selector_all('a[href*="inmueble"], a[href*="property"], a[href*="detalle"]')
            print(f"  Property-Links: {len(links)}")
            
            for link in links[:10]:
                href = link.get_attribute('href')
                text_link = link.inner_text()
                print(f"  Link: {href} -> {text_link[:50]}")
                
                if href and not href.startswith('http'):
                    href = 'https://www.sareb.es' + href
                
                # Preis extrahieren
                parent_text = ''
                try:
                    parent = page.evaluate('el => el.closest("article, .card, li, .result")?.textContent', link.element_handle())
                    parent_text = parent or ''
                except:
                    pass
                
                preis_match = re.search(r'([\d\.]+),(\d{2})\s*€', parent_text)
                preis = None
                if preis_match:
                    try:
                        preis = float(preis_match.group(1).replace('.', '') + '.' + preis_match.group(2))
                    except:
                        pass
                
                if href and 'inmueble' in href:
                    objects.append({
                        'titel': text_link[:80] or 'SAREB Inmueble',
                        'quelle': 'SAREB',
                        'url': href,
                        'preis': preis,
                        'zimmer': None,
                        'grundstueck': None,
                        'wohnflaeche': None,
                        'ort': 'Baleares',
                    })
            
            # Screenshot für Debugging
            page.screenshot(path='/tmp/sareb_screenshot.png')
            print("  Screenshot gespeichert: /tmp/sareb_screenshot.png")
            
        except Exception as e:
            print(f"  Playwright Fehler: {e}")
        finally:
            browser.close()
    
    return objects, api_responses

def main():
    print("=== SAREB Scraper ===")
    
    # 1. API versuchen
    print("\n1. SAREB API...")
    api_data, api_url = try_sareb_api()
    
    # 2. Requests direkt
    print("\n2. SAREB Web-Scraping...")
    objects = scrape_sareb_web()
    
    # 3. Playwright
    print("\n3. SAREB Playwright...")
    pw_objects, api_responses = try_sareb_playwright()
    
    all_objects = objects + pw_objects
    print(f"\n=== SAREB Gesamt: {len(all_objects)} Objekte ===")
    return all_objects

if __name__ == '__main__':
    objects = main()
    for obj in objects[:5]:
        print(f"  {obj['titel'][:60]} | {obj['preis']} €")
