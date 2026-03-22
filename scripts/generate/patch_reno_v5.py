#!/usr/bin/env python3
"""Patch mallorca-ranking-v4.html → v5 with new reno scores (0-100)."""
import re, json

with open('/Users/robin/.openclaw/workspace/mallorca-projekt/debug/reno_scores.json') as f:
    scores = json.load(f)

with open('/Users/robin/.openclaw/workspace/mallorca-projekt/html/mallorca-ranking-v4.html', 'r') as f:
    html = f.read()

# Build mapping: old reno values in order they appear
new_renos = [s['new_reno'] for s in scores]
baujahre = [s.get('baujahr_est', '?') for s in scores]

# 1. Replace "reno":X values in the properties array (in order)
reno_pattern = re.compile(r'"reno":\s*(\d+)')
matches = list(reno_pattern.finditer(html))

# We expect 13 matches for 13 properties
print(f"Found {len(matches)} reno values in HTML")

# Replace from end to preserve positions
for i in range(min(len(matches), len(new_renos)) - 1, -1, -1):
    m = matches[i]
    old = m.group(0)
    new = f'"reno":{new_renos[i]}'
    html = html[:m.start()] + new + html[m.end():]
    print(f"  {old} → {new}")

# 2. Add baujahr to each property object (after "reno":XX)
reno_pattern2 = re.compile(r'"reno":\s*(\d+)')
matches2 = list(reno_pattern2.finditer(html))
for i in range(min(len(matches2), len(baujahre)) - 1, -1, -1):
    m = matches2[i]
    insert = f'"reno":{new_renos[i]},"baujahr":"{baujahre[i]}"'
    html = html[:m.start()] + insert + html[m.end():]

# 3. Fix the scoring normalization for reno
# Old: reno was 1-5, normalized as (reno/5)*100 or similar
# New: reno is already 0-100
# Look for reno normalization patterns
# Common patterns: (p.reno / 5) * 100, p.reno * 20, p.reno / 5
html = re.sub(r'(\w+)\.reno\s*/\s*5\s*\*\s*100', r'\1.reno', html)
html = re.sub(r'(\w+)\.reno\s*\*\s*20', r'\1.reno', html)
html = re.sub(r'(\w+)\[.reno.\]\s*/\s*5\s*\*\s*100', r'\1["reno"]', html)
html = re.sub(r'(\w+)\[.reno.\]\s*\*\s*20', r'\1["reno"]', html)
# Also: (val / 5) patterns near reno
# Let's find the actual scoring function
score_match = re.search(r'function.*score|const.*score.*=.*function|reno.*weight|gewicht.*reno', html, re.IGNORECASE)
if score_match:
    print(f"Score function found near pos {score_match.start()}: {html[score_match.start():score_match.start()+200]}")

# Find all places where reno is divided or multiplied for normalization
reno_norm = re.findall(r'.{0,30}\.reno.{0,50}', html)
for r in reno_norm[:20]:
    print(f"  reno context: {r.strip()}")

# 4. Update card display: "Reno X/5" → "Reno XX/100"  
html = re.sub(r'Reno\s*\$\{[^}]*\}/5', r'Reno ${p.reno}/100', html)
html = re.sub(r'Reno\s*\$\{([^}]*)\}\s*/\s*5', r'Reno ${\1}/100', html)
# Also handle template literals
html = re.sub(r"'Reno '\s*\+\s*(\w+)\.reno\s*\+\s*'/5'", r"'Reno ' + \1.reno + '/100'", html)
html = re.sub(r"Reno (\d)/5", lambda m: f"Reno {new_renos[0]}/100", html)  # static fallback

# 5. Add baujahr display on cards - find where card details are rendered
# Look for pattern like "Zimmer" or "Fläche" in template literals
baujahr_added = False
# Try to add after the property name/location section
card_pattern = re.search(r'(Charme\s*\$\{[^}]*\}/5)', html)
if card_pattern:
    old_text = card_pattern.group(0)
    # Add baujahr before Charme line
    print(f"Found card detail pattern: {old_text}")

# Write output
with open('/Users/robin/.openclaw/workspace/mallorca-projekt/html/mallorca-ranking-v5.html', 'w') as f:
    f.write(html)

print("\nDone! Written to mallorca-ranking-v5.html")
print(f"File size: {len(html)} bytes")
