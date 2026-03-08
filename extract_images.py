import re, base64, os

with open('mallorca-ranking-v7.html', 'r') as f:
    html = f.read()

print(f"V7 Größe: {len(html):,} Bytes")

pattern = r'data:image/([\w+]+);base64,([A-Za-z0-9+/=\s]+)'
matches = list(re.finditer(pattern, html))
print(f"Gefundene Base64-Bilder: {len(matches)}")

ext_map = {'jpeg': 'jpg', 'png': 'png', 'gif': 'gif', 'webp': 'webp', 'svg+xml': 'svg'}

for i, m in enumerate(reversed(matches), 1):
    idx = len(matches) - i + 1
    mime = m.group(1)
    data = m.group(2).replace('\n', '').replace('\r', '').replace(' ', '')
    ext = ext_map.get(mime, mime)
    fname = f"image_{idx:03d}.{ext}"
    
    with open(f"images/{fname}", 'wb') as f:
        f.write(base64.b64decode(data))
    
    html = html[:m.start()] + f"images/{fname}" + html[m.end():]
    fsize = os.path.getsize(f"images/{fname}")
    print(f"  {fname}: {fsize:,} Bytes")

with open('mallorca-ranking-v8.html', 'w') as f:
    f.write(html)

print(f"\nV8 Größe: {len(html):,} Bytes")
print(f"Ersparnis: {os.path.getsize('mallorca-ranking-v7.html') - len(html):,} Bytes")
