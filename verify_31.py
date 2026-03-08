#!/usr/bin/env python3
"""
Verify 31 unverified images via Playwright.
Downloads live images, compares hashes to stored bilder/X_main.jpg
"""
import asyncio, json, hashlib, sys
from pathlib import Path
from playwright.async_api import async_playwright

BASE = Path(__file__).parent
DATA = json.load(open(BASE / 'pruef_31.json'))

async def get_main_image(page, url):
    """Try to extract main property image from page."""
    try:
        await page.goto(url, timeout=30000, wait_until='domcontentloaded')
        await asyncio.sleep(2)
        
        # Try various image selectors
        selectors = [
            'img.main-image', 'img[class*="main"]', 'img[class*="hero"]',
            '.gallery img:first-child', '.photos img:first-child',
            'picture img', '.slider img:first-child',
            'img[src*="cdn"]', 'img[src*="photo"]', 'img[src*="image"]',
            'img[width][height]',
        ]
        
        img_url = None
        for sel in selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    src = await el.get_attribute('src') or await el.get_attribute('data-src')
                    if src and ('jpg' in src.lower() or 'jpeg' in src.lower() or 'webp' in src.lower()):
                        img_url = src
                        break
            except:
                pass
        
        if not img_url:
            # Try largest img on page
            imgs = await page.query_selector_all('img')
            best = (0, None)
            for img in imgs[:20]:
                try:
                    w = await page.evaluate('(el) => el.naturalWidth', img)
                    src = await img.get_attribute('src')
                    if w > best[0] and src and w > 200:
                        best = (w, src)
                except:
                    pass
            img_url = best[1]
        
        return img_url
    except Exception as e:
        return None

async def download_image(page, img_url):
    """Download image bytes."""
    try:
        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        resp = await page.request.get(img_url, timeout=15000)
        if resp.status == 200:
            return await resp.body()
    except:
        pass
    return None

def file_hash(path):
    return hashlib.md5(path.read_bytes()).hexdigest() if path.exists() else None

async def main():
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        
        for entry in DATA:
            nr = entry['nr']
            url = entry.get('url', '')
            name = entry['name']
            img_path = BASE / entry['img']
            
            if not url or url == '—':
                results.append({'nr': nr, 'status': 'NO_URL', 'name': name})
                print(f"Nr.{nr:3d} NO_URL   {name[:50]}")
                continue
            
            local_hash = file_hash(img_path)
            
            page = await context.new_page()
            try:
                img_url = await get_main_image(page, url)
                
                if not img_url:
                    results.append({'nr': nr, 'status': 'NO_IMG_FOUND', 'name': name, 'url': url})
                    print(f"Nr.{nr:3d} NO_IMG   {name[:50]}")
                    await page.close()
                    continue
                
                # Download live image
                live_bytes = await download_image(page, img_url)
                if not live_bytes:
                    results.append({'nr': nr, 'status': 'DOWNLOAD_FAIL', 'name': name, 'url': url})
                    print(f"Nr.{nr:3d} DL_FAIL  {name[:50]}")
                    await page.close()
                    continue
                
                live_hash = hashlib.md5(live_bytes).hexdigest()
                
                if local_hash == live_hash:
                    results.append({'nr': nr, 'status': 'MATCH', 'name': name})
                    print(f"Nr.{nr:3d} ✅ MATCH  {name[:50]}")
                else:
                    # Save live image as candidate
                    live_path = BASE / f'bilder/{nr}_live.jpg'
                    live_path.write_bytes(live_bytes)
                    results.append({'nr': nr, 'status': 'MISMATCH', 'name': name, 'live_img': str(live_path), 'live_url': img_url})
                    print(f"Nr.{nr:3d} ❌ MISMATCH {name[:50]}")
                    print(f"         local={local_hash[:8]} live={live_hash[:8]}")
                
            except Exception as e:
                results.append({'nr': nr, 'status': f'ERR: {e}', 'name': name})
                print(f"Nr.{nr:3d} ERR      {str(e)[:60]}")
            finally:
                await page.close()
        
        await browser.close()
    
    json.dump(results, open(BASE / 'verify_31_results.json', 'w'), indent=2)
    
    mismatches = [r for r in results if r['status'] == 'MISMATCH']
    print(f"\n{'='*60}")
    print(f"MISMATCH ({len(mismatches)}):")
    for m in mismatches:
        print(f"  Nr.{m['nr']:3d} {m['name'][:50]}")
    
    no_url = [r for r in results if r['status'] == 'NO_URL']
    print(f"\nNO_URL ({len(no_url)}): {[r['nr'] for r in no_url]}")

asyncio.run(main())
