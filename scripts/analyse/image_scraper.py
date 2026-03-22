#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from PIL import Image
import base64
import io
import os
import re
import time

# URLs der 13 Immobilien
URLS = [
    "https://www.idealista.com/de/inmueble/106332052/",
    "https://www.engelvoelkers.com/es/de/exposes/6971ac2a-f182-5703-a001-2c6f306cd2ae",
    "https://www.idealista.com/de/inmueble/106744049/",
    "https://www.idealista.com/de/inmueble/109708161/",
    "https://www.idealista.com/de/inmueble/106300856/",
    "https://www.idealista.com/de/inmueble/81539590/",
    "https://www.idealista.com/de/inmueble/109467637/",
    "https://www.idealista.com/de/inmueble/106134268/",
    "https://ev-mallorca.com/en/mallorca-property/excellent-estate-with-its-own-vineyard-olive-grove-and-incredible-charm-W-02Q8YG",
    "https://ev-mallorca.com/en/mallorca-property/unique-designer-house-in-a-quiet-location-W-0475DS",
    "https://ev-mallorca.com/en/mallorca-property/where-contemporary-design-blends-in-perfect-harmony-with-the-mediterranean-landscape-W-02NQDS",
    "https://ev-mallorca.com/en/mallorca-property/dreamlike-finca-with-rental-license-near-es-trenc-W-02ZICD",
    "https://www.idealista.com/inmueble/110322709/"
]

# Namen für die Bilder (basierend auf den Objektnamen aus der HTML-Datei)
IMAGE_NAMES = [
    "casa-establiments",
    "ev-binissalem", 
    "gaestehaus-establiments",
    "modern-palmanyola",
    "santa-maria-unfertig",
    "gute-substanz-campos",
    "naehe-es-trenc",
    "kreativ-sa-rapita",
    "estate-sencelles",
    "designer-ses-salines",
    "contemporary-moscari",
    "finca-campos-lizenz",
    "villa-bunyola-lizenz"
]

def get_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'de,en-US;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    return session

def find_hero_image(html_content, base_url):
    """Findet das Haupt-/Hero-Bild in der HTML-Seite"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Verschiedene Selektoren für Hero-Bilder probieren
    selectors = [
        # Idealista spezifisch
        '.carousel-item img', '.main-image img', '.hero-image img',
        'img[data-src*="crop"]', 'img[src*="crop"]',
        # Engelvoelkers spezifisch
        '.image-gallery img', '.property-image img', '.hero img',
        # Allgemeine Selektoren
        'img[alt*="property"]', 'img[alt*="immobilie"]', 'img[alt*="house"]',
        # Als Fallback das erste große Bild
        'img'
    ]
    
    for selector in selectors:
        imgs = soup.select(selector)
        for img in imgs:
            src = img.get('data-src') or img.get('src')
            if src and ('crop' in src or 'property' in src.lower() or 'immobilie' in src.lower()):
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    domain = '/'.join(base_url.split('/')[:3])
                    src = domain + src
                return src
    
    # Fallback: Erstes Bild mit angemessener Größe
    for img in soup.find_all('img'):
        src = img.get('data-src') or img.get('src')
        if src and not src.endswith('.svg') and not 'logo' in src.lower():
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                domain = '/'.join(base_url.split('/')[:3])
                src = domain + src
            return src
    
    return None

def optimize_image(image_data, max_size_kb=100):
    """Optimiert das Bild für Web-Nutzung"""
    img = Image.open(io.BytesIO(image_data))
    
    # Auf RGB konvertieren falls RGBA
    if img.mode in ('RGBA', 'LA', 'P'):
        img = img.convert('RGB')
    
    # Auf reasonable Größe skalieren (max 1200px breit)
    if img.width > 1200:
        ratio = 1200 / img.width
        new_height = int(img.height * ratio)
        img = img.resize((1200, new_height), Image.LANCZOS)
    
    # JPEG mit verschiedenen Qualitätsstufen probieren
    for quality in [85, 70, 60, 50, 40]:
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        if len(output.getvalue()) <= max_size_kb * 1024:
            return output.getvalue()
    
    # Wenn immer noch zu groß, weiter verkleinern
    while len(output.getvalue()) > max_size_kb * 1024 and img.width > 400:
        new_width = int(img.width * 0.8)
        new_height = int(img.height * 0.8)
        img = img.resize((new_width, new_height), Image.LANCZOS)
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=40, optimize=True)
    
    return output.getvalue()

def scrape_images():
    session = get_session()
    images_data = {}
    
    for i, url in enumerate(URLS):
        print(f"Scraping {i+1}/{len(URLS)}: {url}")
        
        try:
            # HTML-Seite laden
            response = session.get(url, timeout=10)
            if response.status_code != 200:
                print(f"  Fehler: HTTP {response.status_code}")
                continue
                
            # Hero-Bild URL finden
            image_url = find_hero_image(response.text, url)
            if not image_url:
                print(f"  Kein Bild gefunden")
                continue
            
            print(f"  Bild gefunden: {image_url}")
            
            # Bild herunterladen
            img_response = session.get(image_url, timeout=10)
            if img_response.status_code != 200:
                print(f"  Fehler beim Laden des Bildes: HTTP {img_response.status_code}")
                continue
            
            # Bild optimieren
            optimized_data = optimize_image(img_response.content)
            
            # Als JPEG speichern
            filename = f"{IMAGE_NAMES[i]}.jpg"
            filepath = f"/Users/robin/.openclaw/workspace/mallorca-projekt/images/{filename}"
            with open(filepath, 'wb') as f:
                f.write(optimized_data)
            
            # Base64 für HTML-Einbettung
            base64_data = base64.b64encode(optimized_data).decode('utf-8')
            images_data[IMAGE_NAMES[i]] = f"data:image/jpeg;base64,{base64_data}"
            
            size_kb = len(optimized_data) / 1024
            print(f"  Gespeichert: {filename} ({size_kb:.1f} KB)")
            
        except Exception as e:
            print(f"  Fehler: {e}")
        
        # Kurze Pause zwischen Requests
        time.sleep(1)
    
    return images_data

def create_placeholder(name):
    """Erstellt ein Platzhalter-Bild als Base64"""
    img = Image.new('RGB', (400, 300), color='#2a2a4a')
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=80)
    base64_data = base64.b64encode(output.getvalue()).decode('utf-8')
    return f"data:image/jpeg;base64,{base64_data}"

if __name__ == "__main__":
    print("Starte Image Scraping...")
    images = scrape_images()
    
    # Platzhalter für fehlende Bilder erstellen
    for name in IMAGE_NAMES:
        if name not in images:
            print(f"Erstelle Platzhalter für: {name}")
            images[name] = create_placeholder(name)
    
    # Bild-Daten in Python-Dict für HTML speichern
    with open('/Users/robin/.openclaw/workspace/mallorca-projekt/images_data.py', 'w') as f:
        f.write("# Base64-kodierte Bilder für HTML-Einbettung\n")
        f.write("IMAGES_DATA = {\n")
        for name, data_uri in images.items():
            f.write(f'    "{name}": "{data_uri}",\n')
        f.write("}\n")
    
    print(f"\nFertig! {len(images)} Bilder verarbeitet.")