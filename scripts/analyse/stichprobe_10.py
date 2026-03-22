#!/usr/bin/env python3
"""10 Stichproben: URL öffnen, Bild laden, mit gespeichertem vergleichen (Vision)."""
import asyncio, base64, json
from pathlib import Path
from playwright.async_api import async_playwright
import anthropic

BASE = Path(__file__).parent
CLIENT = anthropic.Anthropic()

SAMPLE = [
    {'nr': 14,  'url': 'https://www.balearic-properties.com/en/property/id/874083-historic-estate-seavie'},
    {'nr': 46,  'url': 'https://www.livingblue-mallorca.com/de-de/immobilie/18167677'},
    {'nr': 54,  'url': 'https://www.livingblue-mallorca.com/de-de/immobilie/17830877'},
    {'nr': 59,  'url': None},
    {'nr': 73,  'url': 'https://www.livingblue-mallorca.com/de-de/immobilie/finca-hotel-aus-dem-xvii-jahrhundert-in-santanyi'},
    {'nr': 117, 'url': 'https://www.engelvoelkers.com/de/de/exposes/4a65b22e-ac88-5106-a424-cc468d37eb68'},
    {'nr': 128, 'url': 'https://www.livingblue-mallorca.com/de-de/immobilie/perfekte-harmonie-traumhaftes-landhaus-am-fuss-der-tramuntana'},
    {'nr': 143, 'url': 'https://www.balearic-properties.com/en/property/id/766153-alqueria-blanca-finca'},
    {'nr': 288, 'url': 'https://www.livingblue-mallorca.com/de-de/immobilie/hochwertiges-refugium-in-erhohter-lage-mit-panoramablick'},
    {'nr': 314, 'url': None},
]

async def get_main_image_bytes(page, url):
    """Load page, extract + download main property image."""
    await page.goto(url, timeout=30000, wait_until='domcontentloaded')
    await asyncio.sleep(3)
    
    selectors = [
        'img[src*="photo"]', 'img[src*="image"]', 'img[src*="foto"]',
        '.gallery img:first-child', '.slider img:first-child',
        'picture source', 'img[src*="cdn"]',
        'img[width][height]',
    ]
    
    img_url = None
    for sel in selectors:
        try:
            els = await page.query_selector_all(sel)
            for el in els[:5]:
                src = (await el.get_attribute('src') or 
                       await el.get_attribute('srcset') or
                       await el.get_attribute('data-src') or '')
                src = src.split(',')[0].split(' ')[0]  # handle srcset
                if src and any(x in src.lower() for x in ['jpg','jpeg','webp','png']) and len(src) > 20:
                    img_url = src
                    break
        except: pass
        if img_url: break
    
    if not img_url:
        # Fallback: largest img
        imgs = await page.query_selector_all('img')
        best = (0, None)
        for img in imgs[:30]:
            try:
                w = await page.evaluate('(el) => el.naturalWidth', img)
                src = await img.get_attribute('src') or ''
                if w > best[0] and w > 300 and src:
                    best = (w, src)
            except: pass
        img_url = best[1]
    
    if not img_url:
        return None, None
    
    if img_url.startswith('//'):
        img_url = 'https:' + img_url
    elif img_url.startswith('/'):
        from urllib.parse import urlparse
        parsed = urlparse(url)
        img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
    
    resp = await page.request.get(img_url, timeout=15000)
    if resp.status == 200:
        return await resp.body(), img_url
    return None, img_url

def compare_images_vision(stored_bytes, live_bytes, nr):
    """Use Claude Vision to compare two images."""
    stored_b64 = base64.b64encode(stored_bytes).decode()
    live_b64 = base64.b64encode(live_bytes).decode()
    
    resp = CLIENT.messages.create(
        model="claude-haiku-4-5",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Sind diese zwei Bilder dasselbe Objekt/Haus? Kurze Antwort: JA oder NEIN + 1 Satz Begründung."},
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": stored_b64}},
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": live_b64}},
            ]
        }]
    )
    return resp.content[0].text.strip()

async def main():
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 900}
        )
        
        for entry in SAMPLE:
            nr = entry['nr']
            url = entry['url']
            stored_path = BASE / f'bilder/{nr}_main.jpg'
            
            print(f"\nNr.{nr:3d} ...", flush=True)
            
            if not url:
                print(f"Nr.{nr:3d} ⬜ KEIN URL (privates Exposé)")
                results.append({'nr': nr, 'status': 'NO_URL'})
                continue
            
            if not stored_path.exists():
                print(f"Nr.{nr:3d} ⬜ KEIN BILD GESPEICHERT")
                results.append({'nr': nr, 'status': 'NO_STORED_IMG'})
                continue
            
            page = await ctx.new_page()
            try:
                live_bytes, img_url = await get_main_image_bytes(page, url)
                
                if not live_bytes:
                    print(f"Nr.{nr:3d} ❓ Kein Live-Bild extrahierbar (Bot-Block?)")
                    results.append({'nr': nr, 'status': 'NO_LIVE_IMG', 'url': url})
                    continue
                
                stored_bytes = stored_path.read_bytes()
                verdict = compare_images_vision(stored_bytes, live_bytes, nr)
                
                ok = verdict.upper().startswith('JA')
                icon = '✅' if ok else '❌'
                print(f"Nr.{nr:3d} {icon} {verdict}")
                results.append({'nr': nr, 'status': 'MATCH' if ok else 'MISMATCH', 'verdict': verdict, 'url': url})
                
            except Exception as e:
                print(f"Nr.{nr:3d} ⚠️  Fehler: {e}")
                results.append({'nr': nr, 'status': f'ERR', 'error': str(e)})
            finally:
                await page.close()
        
        await browser.close()
    
    print("\n" + "="*60)
    print("ZUSAMMENFASSUNG:")
    for r in results:
        icon = {'MATCH':'✅','MISMATCH':'❌','NO_URL':'⬜','NO_LIVE_IMG':'❓','NO_STORED_IMG':'⬜'}.get(r['status'],'⚠️')
        print(f"  Nr.{r['nr']:3d} {icon} {r['status']}")
    
    json.dump(results, open(BASE / 'stichprobe_results.json', 'w'), indent=2)

asyncio.run(main())
