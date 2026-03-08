#!/usr/bin/env python3
"""
Isochrone Map — 4 Referenzpunkte Mallorca
Berechnet Fahrzeiten via Google Distance Matrix API
und generiert eine interaktive HTML-Karte mit Schnittmenge.
"""
import requests, json, time
from pathlib import Path

API_KEY = "AIzaSyAzplaFOGUrCygk3mrzS--wrHNIz0arKok"

# 4 Referenzpunkte
ORIGINS = {
    "Flughafen PMI":     (39.5517, 2.7388),
    "Daia (Hotel Corazón)": (39.7489, 2.6491),
    "Ses Salines":       (39.3490, 3.0500),
    "Andratx":           (39.5748, 2.3824),
}

# Thresholds in Minuten (aus Einstellungen)
THRESHOLDS = {
    "Flughafen PMI":        40,
    "Daia (Hotel Corazón)": 40,
    "Ses Salines":          45,
    "Andratx":              40,
}

COLORS = {
    "Flughafen PMI":        "#2196F3",  # blau
    "Daia (Hotel Corazón)": "#FF9800",  # orange
    "Ses Salines":          "#4CAF50",  # grün
    "Andratx":              "#9C27B0",  # lila
}

# Grid über Mallorca (ca. 80 Punkte)
import math

def mallorca_grid(lat_min=39.27, lat_max=39.95, lon_min=2.30, lon_max=3.48, steps=10):
    points = []
    for i in range(steps + 1):
        for j in range(steps + 1):
            lat = lat_min + (lat_max - lat_min) * i / steps
            lon = lon_min + (lon_max - lon_min) * j / steps
            points.append((round(lat, 4), round(lon, 4)))
    return points

def get_drive_times(origin_lat, origin_lon, destinations):
    """Google Distance Matrix API — max 25 destinations pro Request"""
    results = {}
    chunk_size = 25
    for i in range(0, len(destinations), chunk_size):
        chunk = destinations[i:i+chunk_size]
        dest_str = "|".join(f"{lat},{lon}" for lat, lon in chunk)
        url = (
            f"https://maps.googleapis.com/maps/api/distancematrix/json"
            f"?origins={origin_lat},{origin_lon}"
            f"&destinations={dest_str}"
            f"&mode=driving"
            f"&key={API_KEY}"
        )
        r = requests.get(url, timeout=15)
        data = r.json()
        if data.get("status") != "OK":
            print(f"  API Error: {data.get('status')}")
            continue
        for idx, element in enumerate(data["rows"][0]["elements"]):
            pt = chunk[idx]
            if element.get("status") == "OK":
                mins = element["duration"]["value"] / 60
                results[pt] = round(mins, 1)
            else:
                results[pt] = None
        time.sleep(0.1)
    return results

print("Berechne Grid...")
grid = mallorca_grid(steps=9)  # ~100 Punkte
print(f"  {len(grid)} Gridpunkte")

all_times = {}  # {origin_name: {(lat,lon): minutes}}

for name, (olat, olon) in ORIGINS.items():
    print(f"  → {name}...")
    times = get_drive_times(olat, olon, grid)
    all_times[name] = times
    print(f"     {sum(1 for v in times.values() if v is not None)} Punkte berechnet")

# Punkte in der Schnittmenge (alle 4 unter Threshold)
intersection = []
for pt in grid:
    in_all = True
    for name, threshold in THRESHOLDS.items():
        t = all_times[name].get(pt)
        if t is None or t > threshold:
            in_all = False
            break
    if in_all:
        intersection.append(pt)

print(f"\nSchnittmenge: {len(intersection)} Punkte")

# Konvex-Hülle der Schnittmenge für Polygon
def convex_hull(points):
    if len(points) < 3:
        return points
    points = sorted(points)
    def cross(O, A, B):
        return (A[0]-O[0])*(B[1]-O[1]) - (A[1]-O[1])*(B[0]-O[0])
    lower = []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]

hull = convex_hull(intersection) if len(intersection) >= 3 else intersection

# Einzelne Isochron-Polygone (konvexe Hülle der Punkte unter Threshold)
iso_hulls = {}
for name, threshold in THRESHOLDS.items():
    within = [pt for pt, t in all_times[name].items() if t is not None and t <= threshold]
    iso_hulls[name] = convex_hull(within) if len(within) >= 3 else within

# HTML generieren
grid_data = []
for pt in grid:
    times_for_pt = {name: all_times[name].get(pt) for name in ORIGINS}
    in_all = all(t is not None and t <= THRESHOLDS[name] for name, t in times_for_pt.items())
    grid_data.append({
        "lat": pt[0], "lon": pt[1],
        "times": {k: v for k, v in times_for_pt.items()},
        "in_all": in_all
    })

html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>Mallorca Isochrone — 4 Referenzpunkte</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: -apple-system, sans-serif; background: #0d0d1a; color: #eee; }}
  #map {{ height: 100vh; width: 100%; }}
  #legend {{
    position: fixed; top: 20px; right: 20px; z-index: 1000;
    background: rgba(13,13,26,0.92); border: 1px solid #2a2a3e;
    border-radius: 12px; padding: 16px 20px; min-width: 240px;
    backdrop-filter: blur(8px);
  }}
  #legend h3 {{ font-size: 0.9rem; color: #f0a500; margin-bottom: 12px; letter-spacing: 0.05em; }}
  .leg-item {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; font-size: 0.82rem; }}
  .leg-dot {{ width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; }}
  .leg-line {{ width: 24px; height: 3px; border-radius: 2px; flex-shrink: 0; }}
  .leg-sep {{ border-top: 1px solid #2a2a3e; margin: 10px 0; }}
  #title {{
    position: fixed; top: 20px; left: 60px; z-index: 1000;
    background: rgba(13,13,26,0.92); border: 1px solid #2a2a3e;
    border-radius: 12px; padding: 12px 18px;
    backdrop-filter: blur(8px);
  }}
  #title h2 {{ font-size: 1rem; color: #f0a500; }}
  #title p {{ font-size: 0.75rem; color: #888; margin-top: 4px; }}
</style>
</head>
<body>
<div id="map"></div>
<div id="title">
  <h2>🗺️ Mallorca Erreichbarkeit</h2>
  <p>Schnittmenge aller 4 Referenzpunkte</p>
</div>
<div id="legend">
  <h3>LEGENDE</h3>
  <div class="leg-item"><div class="leg-line" style="background:#2196F3;opacity:0.7"></div> Flughafen ≤40 min</div>
  <div class="leg-item"><div class="leg-line" style="background:#FF9800;opacity:0.7"></div> Daia ≤40 min</div>
  <div class="leg-item"><div class="leg-line" style="background:#4CAF50;opacity:0.7"></div> Ses Salines ≤45 min</div>
  <div class="leg-item"><div class="leg-line" style="background:#9C27B0;opacity:0.7"></div> Andratx ≤40 min</div>
  <div class="leg-sep"></div>
  <div class="leg-item"><div class="leg-dot" style="background:#FFD700"></div> Schnittmenge (alle ✓)</div>
  <div class="leg-item"><div class="leg-dot" style="background:#e74c3c;opacity:0.5"></div> Außerhalb mind. 1</div>
  <div class="leg-sep"></div>
  <div class="leg-item" style="color:#888;font-size:0.75rem">📍 Klick auf Punkt = Fahrzeiten</div>
</div>
<script>
const map = L.map('map', {{
  center: [39.62, 2.89],
  zoom: 9,
  zoomControl: true
}});

L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
  attribution: '©OpenStreetMap ©CARTO',
  maxZoom: 15
}}).addTo(map);

const ORIGINS = {json.dumps({k: list(v) for k,v in ORIGINS.items()})};
const COLORS = {json.dumps(COLORS)};
const THRESHOLDS = {json.dumps(THRESHOLDS)};
const ISO_HULLS = {json.dumps({k: [list(p) for p in v] for k,v in iso_hulls.items()})};
const HULL = {json.dumps([list(p) for p in hull])};
const GRID = {json.dumps(grid_data)};

// Isochrone Polygone (halbtransparent)
Object.entries(ISO_HULLS).forEach(([name, pts]) => {{
  if (pts.length < 3) return;
  L.polygon(pts, {{
    color: COLORS[name],
    fillColor: COLORS[name],
    fillOpacity: 0.08,
    weight: 2,
    opacity: 0.6,
    dashArray: '6,4'
  }}).addTo(map).bindTooltip(name + ' ≤' + THRESHOLDS[name] + ' min', {{sticky: true}});
}});

// Schnittmenge Polygon (ausgefüllt)
if (HULL.length >= 3) {{
  L.polygon(HULL, {{
    color: '#FFD700',
    fillColor: '#FFD700',
    fillOpacity: 0.15,
    weight: 2.5,
    opacity: 0.9
  }}).addTo(map).bindTooltip('✅ Idealzone — alle 4 Kriterien erfüllt', {{sticky: true}});
}}

// Grid Punkte
GRID.forEach(pt => {{
  const color = pt.in_all ? '#FFD700' : '#e74c3c';
  const opacity = pt.in_all ? 0.9 : 0.3;
  const r = pt.in_all ? 5 : 3;

  const times = Object.entries(pt.times)
    .map(([k,v]) => `<b>${{k}}</b>: ${{v ? v.toFixed(0)+' min' : '—'}} ${{v && v <= THRESHOLDS[k] ? '✅' : '❌'}}`)
    .join('<br>');

  L.circleMarker([pt.lat, pt.lon], {{
    radius: r, color: color, fillColor: color,
    fillOpacity: opacity, weight: 1
  }}).addTo(map).bindPopup(`<div style="font-size:0.82rem;line-height:1.6">${{times}}</div>`);
}});

// Referenzpunkt-Marker
Object.entries(ORIGINS).forEach(([name, [lat, lon]]) => {{
  L.circleMarker([lat, lon], {{
    radius: 10, color: '#fff', fillColor: COLORS[name],
    fillOpacity: 1, weight: 2
  }}).addTo(map)
    .bindTooltip(`<b>${{name}}</b>`, {{permanent: true, direction: 'top', className: 'ref-label'}});
}});
</script>
</body>
</html>"""

out = Path(__file__).parent / "isochrone_mallorca.html"
out.write_text(html, encoding='utf-8')
print(f"\n✅ Gespeichert: {out}")
print("Im Browser öffnen: open isochrone_mallorca.html")
