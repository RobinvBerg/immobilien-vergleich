#!/usr/bin/env python3
"""Developer/Neubau Scraper: Taylor Wimpey, Vives Pons, Barrau"""

import requests
from bs4 import BeautifulSoup
import re
import time
import json
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
}

def scrape_taylor_wimpey():
    """Taylor Wimpey España - Neubau Mallorca"""
    objects = []
    urls = [
        'https://www.taylorwimpeyspain.com/en/locations/mallorca/',
        'https://www.taylorwimpeyspain.com/es/ubicaciones/mallorca/',
        'https://www.taylorwimpeyspain.com/en/new-homes-mallorca/',
    ]
    
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            print(f"  TW {url[:60]}: {resp.status_code}")
            if resp.status_code != 200:
                continue
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Developments/Projects suchen
            devs = soup.find_all(['article', 'div', 'section'], class_=re.compile(r'development|project|property|card|home', re.I))
            print(f"    Developments: {len(devs)}")
            
            # Links zu Einzelprojekten
            links = soup.find_all('a', href=re.compile(r'mallorca|development|homes', re.I))
            print(f"    Links: {len(links)}")
            
            for link in links[:20]:
                href = link.get('href', '')
                if not href:
                    continue
                if not href.startswith('http'):
                    href = 'https://www.taylorwimpeyspain.com' + href
                
                # Nur Mallorca-Links
                if 'mallorca' not in href.lower() and 'mallorca' not in link.get_text().lower():
                    continue
                
                text = link.get_text(strip=True)
                if len(text) < 3:
                    continue
                
                # Parent für Kontext
                parent = link.find_parent(['article', 'div', 'li', 'section'])
                parent_text = parent.get_text(' ', strip=True) if parent else ''
                
                # Preis
                preis = None
                preis_match = re.search(r'(?:from|desde|price)[^\d]*([\d\.,]+)', parent_text, re.I)
                if preis_match:
                    try:
                        preis = float(re.sub(r'[^\d\.]', '', preis_match.group(1).replace(',', '.')))
                        if preis < 1000:  # Wahrscheinlich in k€
                            preis *= 1000
                    except:
                        pass
                
                # Zimmerzahl
                zimmer = None
                bed_match = re.search(r'(\d+)\s*(?:bed|dormitorio|habitaci)', parent_text, re.I)
                if bed_match:
                    zimmer = int(bed_match.group(1))
                
                # Fläche
                flaeche = None
                m2_match = re.search(r'(\d+)\s*m[²2]', parent_text, re.I)
                if m2_match:
                    flaeche = float(m2_match.group(1))
                
                objects.append({
                    'titel': text[:80],
                    'quelle': 'Taylor Wimpey España',
                    'url': href,
                    'preis': preis,
                    'zimmer': zimmer,
                    'grundstueck': None,
                    'wohnflaeche': flaeche,
                    'ort': 'Mallorca',
                })
            
            break  # Erste erfolgreiche URL reicht
        except Exception as e:
            print(f"  TW Fehler: {e}")
    
    # Playwright-Versuch wenn keine Ergebnisse
    if not objects:
        print("  Taylor Wimpey: Versuche Playwright...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=HEADERS['User-Agent'])
                page = context.new_page()
                Stealth().apply_stealth_sync(page)
                
                page.goto('https://www.taylorwimpeyspain.com/en/locations/mallorca/', timeout=30000)
                page.wait_for_load_state('networkidle', timeout=15000)
                
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Development cards
                cards = soup.find_all(['article', 'div'], class_=re.compile(r'development|card|project', re.I))
                print(f"    PW Cards: {len(cards)}")
                
                for card in cards[:10]:
                    card_text = card.get_text(' ', strip=True)
                    link_tag = card.find('a')
                    if not link_tag:
                        continue
                    
                    href = link_tag.get('href', '')
                    if not href.startswith('http'):
                        href = 'https://www.taylorwimpeyspain.com' + href
                    
                    titel = link_tag.get_text(strip=True) or card_text[:60]
                    
                    preis_match = re.search(r'[\d\.]+,\d{2}\s*€|\€\s*[\d,\.]+|from\s+[\d,\.]+', card_text, re.I)
                    preis = None
                    if preis_match:
                        nums = re.findall(r'[\d,\.]+', preis_match.group())
                        if nums:
                            try:
                                preis = float(nums[0].replace(',', '.').replace('.', '', nums[0].count('.') - 1))
                            except:
                                pass
                    
                    objects.append({
                        'titel': titel[:80],
                        'quelle': 'Taylor Wimpey España',
                        'url': href,
                        'preis': preis,
                        'zimmer': None,
                        'grundstueck': None,
                        'wohnflaeche': None,
                        'ort': 'Mallorca',
                    })
                
                browser.close()
        except Exception as e:
            print(f"  PW Fehler: {e}")
    
    return objects

def scrape_vivespons():
    """Vives Pons - Mallorca Developer"""
    objects = []
    urls = [
        'https://www.vivespons.com/en/',
        'https://www.vivespons.com/es/',
        'https://www.vivespons.com/',
    ]
    
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            print(f"  VivesPons {url[:50]}: {resp.status_code}")
            if resp.status_code != 200:
                continue
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            text = soup.get_text(' ', strip=True)
            
            # Projekte/Properties
            links = soup.find_all('a', href=True)
            property_links = [l for l in links if any(kw in l.get('href', '').lower() 
                              for kw in ['project', 'property', 'home', 'residencial', 'development'])]
            print(f"  VivesPons Property-Links: {len(property_links)}")
            
            for link in property_links[:20]:
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = 'https://www.vivespons.com' + href
                
                titel = link.get_text(strip=True)
                if len(titel) < 3:
                    continue
                
                parent = link.find_parent(['article', 'div', 'li'])
                parent_text = parent.get_text(' ', strip=True) if parent else ''
                
                preis = None
                preis_match = re.search(r'([\d\.]+),(\d{2})\s*€', parent_text)
                if preis_match:
                    try:
                        preis = float(preis_match.group(1).replace('.', '') + '.' + preis_match.group(2))
                    except:
                        pass
                
                objects.append({
                    'titel': titel[:80],
                    'quelle': 'Vives Pons',
                    'url': href,
                    'preis': preis,
                    'zimmer': None,
                    'grundstueck': None,
                    'wohnflaeche': None,
                    'ort': 'Mallorca',
                })
            
            break
        except Exception as e:
            print(f"  VivesPons Fehler: {e}")
    
    # Playwright wenn nötig
    if not objects:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                Stealth().apply_stealth_sync(page)
                
                for url in urls:
                    try:
                        page.goto(url, timeout=20000, wait_until='domcontentloaded')
                        time.sleep(2)
                        
                        content = page.content()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Alle externen Links zu Projekten
                        links = soup.find_all('a', href=re.compile(r'project|property|residencial|development', re.I))
                        print(f"  PW VivesPons Links: {len(links)}")
                        
                        for link in links[:10]:
                            href = link.get('href', '')
                            if not href.startswith('http'):
                                href = 'https://www.vivespons.com' + href
                            
                            objects.append({
                                'titel': link.get_text(strip=True)[:80] or 'Vives Pons Property',
                                'quelle': 'Vives Pons',
                                'url': href,
                                'preis': None,
                                'zimmer': None,
                                'grundstueck': None,
                                'wohnflaeche': None,
                                'ort': 'Mallorca',
                            })
                        
                        if objects:
                            break
                    except:
                        pass
                
                browser.close()
        except Exception as e:
            print(f"  VivesPons PW Fehler: {e}")
    
    return objects

def scrape_barrau():
    """Barrau Gestió - Mallorca"""
    objects = []
    
    urls_to_try = [
        'https://www.barrau.com/en/properties/',
        'https://www.barrau.com/es/propiedades/',
        'https://www.barrau.com/',
        'https://barrau.com/',
    ]
    
    for url in urls_to_try:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            print(f"  Barrau {url[:50]}: {resp.status_code}")
            if resp.status_code != 200:
                continue
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Property Cards
            cards = soup.find_all(['article', 'div', 'li'], class_=re.compile(r'property|inmueble|card|listing', re.I))
            print(f"  Barrau Cards: {len(cards)}")
            
            for card in cards[:30]:
                card_text = card.get_text(' ', strip=True)
                link_tag = card.find('a')
                if not link_tag:
                    continue
                
                href = link_tag.get('href', '')
                if not href.startswith('http'):
                    base = url.rstrip('/')
                    if href.startswith('/'):
                        href = base.split('//')[0] + '//' + base.split('//')[1].split('/')[0] + href
                    else:
                        href = base + '/' + href
                
                titel = link_tag.get_text(strip=True) or card_text[:60]
                
                preis = None
                preis_match = re.search(r'([\d\.]+),(\d{2})\s*€|\€\s*([\d\.]+)', card_text)
                if preis_match:
                    try:
                        if preis_match.group(1):
                            preis = float(preis_match.group(1).replace('.', '') + '.' + preis_match.group(2))
                        elif preis_match.group(3):
                            preis = float(preis_match.group(3).replace('.', ''))
                    except:
                        pass
                
                zimmer = None
                bed_match = re.search(r'(\d+)\s*(?:dorm|hab|bed|bdr)', card_text, re.I)
                if bed_match:
                    zimmer = int(bed_match.group(1))
                
                flaeche = None
                m2_match = re.search(r'(\d+)\s*m[²2]', card_text)
                if m2_match:
                    flaeche = float(m2_match.group(1))
                
                ort_match = re.search(r'(?:Palma|Calvià|Andratx|Pollença|Sóller|Deià|Valldemossa|Alcúdia|Artà|Manacor|Inca|Llucmajor|Santanyí|Felanitx|Muro|Petra)', card_text, re.I)
                ort = ort_match.group(0) if ort_match else 'Mallorca'
                
                if len(titel) < 3 or not href or href == url:
                    continue
                
                objects.append({
                    'titel': titel[:80],
                    'quelle': 'Barrau Gestió',
                    'url': href,
                    'preis': preis,
                    'zimmer': zimmer,
                    'grundstueck': None,
                    'wohnflaeche': flaeche,
                    'ort': ort,
                })
            
            if objects:
                break
                
        except Exception as e:
            print(f"  Barrau Fehler: {e}")
    
    return objects

def main():
    all_objects = []
    
    print("=== Taylor Wimpey España ===")
    tw = scrape_taylor_wimpey()
    print(f"  -> {len(tw)} Objekte")
    all_objects.extend(tw)
    
    print("\n=== Vives Pons ===")
    vp = scrape_vivespons()
    print(f"  -> {len(vp)} Objekte")
    all_objects.extend(vp)
    
    print("\n=== Barrau Gestió ===")
    br = scrape_barrau()
    print(f"  -> {len(br)} Objekte")
    all_objects.extend(br)
    
    return all_objects

if __name__ == '__main__':
    objects = main()
    print(f"\n=== Developer Gesamt: {len(objects)} ===")
    for obj in objects[:10]:
        print(f"  [{obj['quelle']}] {obj['titel'][:50]} | {obj['preis']} €")
