#!/usr/bin/env python3
"""Patch mallorca-ranking-v4.html mit Deckblatt, Buttons, Ort-Normalisierung, Vergleichstabelle, Karten."""

HTML = 'mallorca-ranking-v4.html'

with open(HTML, encoding='utf-8') as f:
    content = f.read()

# ─── 1. DECKBLATT ────────────────────────────────────────────────────────────
DECKBLATT = '''
<!-- DECKBLATT -->
<div id="deckblatt" style="position:fixed;inset:0;z-index:500;background:linear-gradient(135deg,#0a0a14 0%,#0f1624 50%,#0a0a14 100%);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px;text-align:center;overflow-y:auto;">
  <div style="font-size:13px;color:#f0a500;letter-spacing:3px;text-transform:uppercase;margin-bottom:16px;">Mallorca Immobilien · Privat</div>
  <h1 style="font-size:clamp(2rem,5vw,3.5rem);font-weight:800;color:#fff;line-height:1.15;margin-bottom:8px;">🏝️ Mallorca<br><span style="color:#f0a500">Ranking V4</span></h1>
  <div style="font-size:14px;color:#64748b;margin-bottom:40px;">Stand: 22. März 2026 · Neue Bewertungsgewichtung</div>

  <div style="display:flex;gap:24px;flex-wrap:wrap;justify-content:center;margin-bottom:48px;">
    <div style="background:rgba(255,255,255,0.04);border:1px solid #2d3148;border-radius:12px;padding:20px 32px;">
      <div style="font-size:2.2rem;font-weight:800;color:#f0a500">469</div>
      <div style="font-size:12px;color:#64748b;margin-top:4px;">Objekte gesamt</div>
    </div>
    <div style="background:rgba(255,255,255,0.04);border:1px solid #2d3148;border-radius:12px;padding:20px 32px;">
      <div style="font-size:2.2rem;font-weight:800;color:#22c55e">+136</div>
      <div style="font-size:12px;color:#64748b;margin-top:4px;">neu seit letztem Deploy</div>
    </div>
    <div style="background:rgba(255,255,255,0.04);border:1px solid #2d3148;border-radius:12px;padding:20px 32px;">
      <div style="font-size:2.2rem;font-weight:800;color:#60a5fa">11</div>
      <div style="font-size:12px;color:#64748b;margin-top:4px;">Makler-Quellen</div>
    </div>
  </div>

  <div style="background:rgba(255,255,255,0.03);border:1px solid #2d3148;border-radius:12px;padding:16px 24px;margin-bottom:32px;max-width:620px;width:100%;">
    <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:2px;margin-bottom:14px;">Bewertungsgewichtung — V3 vs. V4</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 20px;font-size:12px;text-align:left;">
      <div style="background:rgba(34,197,94,0.07);border:1px solid rgba(34,197,94,0.2);border-radius:8px;padding:8px 12px;display:flex;align-items:center;justify-content:space-between;">
        <span style="color:#e2e8f0;">🏚 Renovierung</span>
        <span><span style="color:#64748b;text-decoration:line-through;font-size:11px;">5%</span> <span style="color:#22c55e;font-weight:700">▲ 15%</span></span>
      </div>
      <div style="background:rgba(34,197,94,0.07);border:1px solid rgba(34,197,94,0.2);border-radius:8px;padding:8px 12px;display:flex;align-items:center;justify-content:space-between;">
        <span style="color:#e2e8f0;">🔧 Bewirtschaftung</span>
        <span><span style="color:#64748b;text-decoration:line-through;font-size:11px;">5%</span> <span style="color:#22c55e;font-weight:700">▲ 10%</span></span>
      </div>
      <div style="background:rgba(239,68,68,0.07);border:1px solid rgba(239,68,68,0.2);border-radius:8px;padding:8px 12px;display:flex;align-items:center;justify-content:space-between;">
        <span style="color:#e2e8f0;">📍 Erreichbarkeit</span>
        <span><span style="color:#64748b;text-decoration:line-through;font-size:11px;">15%</span> <span style="color:#ef4444;font-weight:700">▼ 5%</span></span>
      </div>
      <div style="background:rgba(239,68,68,0.07);border:1px solid rgba(239,68,68,0.2);border-radius:8px;padding:8px 12px;display:flex;align-items:center;justify-content:space-between;">
        <div>
          <span style="color:#e2e8f0;">💶 Preis & Effizienz</span>
          <div style="font-size:10px;color:#64748b;margin-top:2px;">50% Gesamtpreis · 50% €/m²</div>
        </div>
        <span><span style="color:#64748b;text-decoration:line-through;font-size:11px;">15%</span> <span style="color:#ef4444;font-weight:700">▼ 10%</span></span>
      </div>
      <div style="background:rgba(255,255,255,0.02);border:1px solid #2d3148;border-radius:8px;padding:8px 12px;display:flex;align-items:center;justify-content:space-between;">
        <span style="color:#94a3b8;">🛏 Zimmer</span><span style="color:#94a3b8;font-weight:600">= 20%</span>
      </div>
      <div style="background:rgba(255,255,255,0.02);border:1px solid #2d3148;border-radius:8px;padding:8px 12px;display:flex;align-items:center;justify-content:space-between;">
        <span style="color:#94a3b8;">🏡 Gästehaus</span><span style="color:#94a3b8;font-weight:600">= 15%</span>
      </div>
      <div style="background:rgba(255,255,255,0.02);border:1px solid #2d3148;border-radius:8px;padding:8px 12px;display:flex;align-items:center;justify-content:space-between;">
        <span style="color:#94a3b8;">✨ Charme</span><span style="color:#94a3b8;font-weight:600">= 10%</span>
      </div>
      <div style="background:rgba(255,255,255,0.02);border:1px solid #2d3148;border-radius:8px;padding:8px 12px;display:flex;align-items:center;justify-content:space-between;">
        <span style="color:#94a3b8;">🌿 Grundstück</span><span style="color:#94a3b8;font-weight:600">= 10%</span>
      </div>
      <div style="background:rgba(255,255,255,0.02);border:1px solid #2d3148;border-radius:8px;padding:8px 12px;display:flex;align-items:center;justify-content:space-between;">
        <span style="color:#94a3b8;">🔑 Vermietlizenz</span><span style="color:#94a3b8;font-weight:600">= 5%</span>
      </div>
      <div style="background:rgba(239,68,68,0.07);border:1px solid rgba(239,68,68,0.2);border-radius:8px;padding:8px 12px;display:flex;align-items:center;justify-content:space-between;">
        <span style="color:#e2e8f0;">⛰ Andratx (Erreichb.)</span>
        <span><span style="color:#64748b;text-decoration:line-through;font-size:11px;">10%</span> <span style="color:#ef4444;font-weight:700">✕ gestrichen</span></span>
      </div>
    </div>
  </div>

  <div style="display:flex;gap:12px;flex-wrap:wrap;justify-content:center;margin-bottom:32px;">
    <div style="font-size:10px;color:#64748b;width:100%;text-transform:uppercase;letter-spacing:2px;text-align:center;margin-bottom:2px;">Neu in V4 — direkt hier abrufbar</div>
    <button onclick="document.getElementById('deckblatt').style.display='none';setTimeout(openKarten,150)" style="background:rgba(96,165,250,0.1);border:1px solid rgba(96,165,250,0.3);border-radius:20px;padding:7px 18px;font-size:12px;color:#93c5fd;cursor:pointer;">🗺 Erreichbarkeits-Karte</button>
    <button onclick="document.getElementById('deckblatt').style.display='none';setTimeout(openVergleich,150)" style="background:rgba(96,165,250,0.1);border:1px solid rgba(96,165,250,0.3);border-radius:20px;padding:7px 18px;font-size:12px;color:#93c5fd;cursor:pointer;">📊 V3 vs. V4 Vergleich</button>
  </div>

  <button onclick="document.getElementById('deckblatt').style.display='none'" style="background:#f0a500;color:#000;border:none;padding:14px 40px;border-radius:8px;font-size:15px;font-weight:700;cursor:pointer;" onmouseover="this.style.background='#ffc107'" onmouseout="this.style.background='#f0a500'">
    Ranking öffnen →
  </button>
  <div style="margin-top:16px;font-size:11px;color:#374151;cursor:pointer;" onclick="document.getElementById('deckblatt').style.display='none'">oder klicken zum Schließen</div>
</div>
'''

# ─── 2. HEADER BUTTONS ───────────────────────────────────────────────────────
HEADER_OLD = '<div>\n    <div id="count">469 Objekte</div>\n    <div class="meta">'
HEADER_NEW = '''<div style="display:flex;align-items:center;gap:12px;">
    <button onclick="document.getElementById('deckblatt').style.display='flex'" style="background:rgba(255,255,255,0.07);border:1px solid #2d3148;color:#94a3b8;padding:5px 12px;border-radius:6px;cursor:pointer;font-size:12px;">ℹ️ Info</button>
    <div>
      <div id="count">469 Objekte</div>
      <div class="meta">'''

# ─── 3. FILTER BUTTONS ───────────────────────────────────────────────────────
FILTER_OLD = '<button class="btn" onclick="applyFilters()">Filter</button>\n  <button class="btn sec" onclick="resetFilters()">Reset</button>'
FILTER_NEW = '''<button class="btn" onclick="applyFilters()">Filter</button>
  <button class="btn sec" onclick="resetFilters()">Reset</button>
  <button class="btn sec" onclick="openKarten()" style="margin-left:8px">🗺 Erreichbarkeit</button>
  <button class="btn sec" onclick="openVergleich()" style="margin-left:4px">📊 V3 vs V4</button>'''

# ─── 4. ORT NORMALISIERUNG ───────────────────────────────────────────────────
ORT_OLD = '// Populate ort filter\nconst orte = [...new Set(DATA.map(o => o.ort).filter(Boolean))].sort();\nconst ortSel = document.getElementById(\'filt-ort\');\norte.forEach(o => { const op = document.createElement(\'option\'); op.value = o; op.textContent = o; ortSel.appendChild(op); });'

ORT_NEW = '''const ORT_MAP = {
  'Alaro Mit Panoramablick':'Alaró','Algaida Mallorca':'Algaida','Andratx Mallorca':'Andratx',
  'Arta':'Artà','Artà/Son Servera':'Artà','Binissalem ,Finca':'Binissalem','Bunyola ,Villa':'Bunyola',
  'Cala Santanyí ,Villa':'Cala Santanyí','Calvia':'Calvià','Colonia De Sant Pere':'Colònia de Sant Pere',
  'Colonia Sant Pere':'Colònia de Sant Pere','Establiments Mallorca':'Establiments',
  'Lloret De Vistalegre Mallorca':'Lloret de Vistalegre','Llubi':'Llubí','Llucmajor interior':'Llucmajor',
  'Sa Torre/Llucmajor':'Llucmajor','Manacor Mit Panoramablick Ueber Die Berge Bis Hin Zum Glitzernden Meer':'Manacor',
  'Montuiri':'Montuïri','Muro Mallorca Mit Pool':'Muro','Palma de Mallorca':'Palma',
  'Son Vida Palma De Mallorca':'Son Vida','Portol ,Villa':'Pòrtol','Petra Mallorca':'Petra',
  'Pina Mallorca':'Pina','Pollensa':'Pollença','Marratxí - Sa Cabaneta':'Sa Cabaneta',
  'Sa Rapita':'Sa Ràpita','Sa Rapita Mallorca':'Sa Ràpita','Sant Llorenç Des Cardassar':'Sant Llorenç',
  'Santa Maria ,':'Santa Maria','Santa Maria Mallorca':'Santa Maria','Santa Maria del Cami':'Santa Maria del Camí',
  'Santa María Del Camí':'Santa Maria del Camí','Santa María del Camí':'Santa Maria del Camí',
  'Santa Maria Del Camí':'Santa Maria del Camí','Sta. Maria':'Santa Maria',
  'Der Naehe Von Santa Maria':'Santa Maria','Bester Lage In Santa Maria Mallorca':'Santa Maria',
  'A Class Of Its Own Near Santa Maria Mallorca':'Santa Maria','Santanyí ,Finca':'Santanyí',
  "S´Arraco":"S'Arracó",'Der Naehe Von Golf Pollensa Mit Lizenz Zur Ferienvermietung':'Pollença',
  'Der Exklusiven Gegend Von La Font Pollensa Mit Herrlichem Blick Ueber Das Tal':'Pollença',
  'Der Naehe Von Badia Gran Bei Llucmajor Mallorca':'Llucmajor',
  'Mallorca Alcudia Mit Lizenz Zur Ferienvermietung Pool Und Tennisplatz Zu Verkaufen':'Alcúdia',
  'Einer Spektakulaeren Laendlichen Umgebung':'Mallorca (Sonstige)',
  'Harmonie Mit Der Natur':'Mallorca (Sonstige)',
  'Erhoehter Alleinlage Mit Meerblick Naturstein Energieplaetzen':'Mallorca (Sonstige)',
};
function normalizeOrt(raw) { if(!raw) return '–'; return ORT_MAP[raw.trim()] || raw.trim(); }
DATA.forEach(o => { o.ortNorm = normalizeOrt(o.ort); });
const orte = [...new Set(DATA.map(o => o.ortNorm).filter(v => v && v !== '–'))].sort((a,b) => a.localeCompare(b,'de'));
const ortSel = document.getElementById('filt-ort');
orte.forEach(v => { const op = document.createElement('option'); op.value = v; op.textContent = v; ortSel.appendChild(op); });'''

# ─── 5. VERGLEICH + KARTEN MODALS + SCRIPTS ──────────────────────────────────
EXTRA = '''
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<!-- VERGLEICH MODAL -->
<div id="vergleich-overlay" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.88);z-index:200;overflow-y:auto;padding:20px;" onclick="if(event.target===this)closeVergleich()">
  <div style="max-width:900px;margin:0 auto;background:#181828;border-radius:12px;border:1px solid #2a2a3e;overflow:hidden;">
    <div style="padding:16px 20px;border-bottom:1px solid #2a2a3e;display:flex;align-items:center;justify-content:space-between;">
      <div>
        <div style="font-size:15px;font-weight:700;color:#f1f5f9;">📊 Ranking-Vergleich V3 vs. V4 — Top 50</div>
        <div style="font-size:11px;color:#64748b;margin-top:2px;">25 Objekte in beiden Top-50 · 25 neue Einsteiger in V4</div>
      </div>
      <button onclick="closeVergleich()" style="background:#22223a;border:none;color:#e8e8e8;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:13px;">✕ Schließen</button>
    </div>
    <div style="padding:10px 16px;background:#0f1117;font-size:11.5px;color:#94a3b8;line-height:1.6;border-bottom:1px solid #2a2a3e;">
      Nur Objekte die in <strong style="color:#f0a500">beiden Versionen unter den Top 50</strong> lagen.
      Große Aufsteiger profitieren vom höheren Renovierungs- und Bewirtschaftungsgewicht + neuer Preis-Kurve.
    </div>
    <div style="padding:16px;overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead>
          <tr style="border-bottom:2px solid #2d3148;color:#64748b;font-size:11px;text-transform:uppercase;">
            <th style="padding:6px 10px;text-align:center;">Rang V4</th>
            <th style="padding:6px 10px;text-align:center;">Rang V3</th>
            <th style="padding:6px 10px;text-align:center;">±</th>
            <th style="padding:6px 10px;text-align:right;">Score V4</th>
            <th style="padding:6px 24px 6px 10px;text-align:right;">Score V3</th>
            <th style="padding:6px 10px 6px 20px;">Objekt</th>
          </tr>
        </thead>
        <tbody id="vtbody"></tbody>
      </table>
    </div>
  </div>
</div>

<!-- KARTEN MODAL -->
<div id="karten-overlay" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.88);z-index:200;overflow-y:auto;padding:20px;" onclick="if(event.target===this)closeKarten()">
  <div style="max-width:1100px;margin:0 auto;background:#181828;border-radius:12px;border:1px solid #2a2a3e;overflow:hidden;">
    <div style="padding:16px 20px;border-bottom:1px solid #2a2a3e;display:flex;align-items:center;justify-content:space-between;">
      <div>
        <div style="font-size:15px;font-weight:700;color:#f1f5f9;">🗺 Erreichbarkeit — Zonenvergleich V3 vs. V4</div>
        <div style="font-size:11px;color:#64748b;margin-top:2px;">Grün = Ideal · Gelb = Akzeptabel · Rot = Dealbreaker</div>
      </div>
      <button onclick="closeKarten()" style="background:#22223a;border:none;color:#e8e8e8;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:13px;">✕ Schließen</button>
    </div>
    <div style="margin:12px 16px;padding:10px 14px;background:#0f1117;border-radius:8px;border:1px solid #2d3148;font-size:11.5px;color:#94a3b8;line-height:1.7;">
      <strong style="color:#f1f5f9">Wie lesen?</strong> Jeder Kreis hat seinen <strong style="color:#60a5fa">Ursprung am Referenzpunkt</strong>. Ein Objekt innerhalb des grünen Kreises = Idealzone · gelb = akzeptabel · außerhalb = Dealbreaker.
      ⚠️ <strong style="color:#fbbf24">Kreise sind Annäherungen</strong> (Luftlinie 50 km/h) — echte Fahrzeiten aus Excel präziser.<br>
      <strong style="color:#f1f5f9">Einfluss aufs Ranking:</strong> V3: <strong style="color:#ef4444">15%</strong> → V4: <strong style="color:#22c55e">5%</strong>. Erreichbarkeit spielt kaum noch eine Rolle. Dealbreaker PMI + Ses Salines von 40/45 auf 60 min erweitert.
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:0 16px 16px;">
      <div style="background:#1e2130;border-radius:8px;overflow:hidden;border:1px solid #2d3148;">
        <div style="padding:8px 12px;border-bottom:1px solid #2d3148;">
          <div style="font-size:12px;font-weight:700;color:#f1f5f9;">🗂 V3 — Alt (mit Andratx)</div>
          <div style="font-size:10px;color:#64748b;">PMI 30% DB40 · Daia 30% DB70 · SeS 30% DB45 · Andratx 10% DB60</div>
        </div>
        <div id="kmap-alt" style="height:380px;"></div>
      </div>
      <div style="background:#1e2130;border-radius:8px;overflow:hidden;border:1px solid #2d3148;">
        <div style="padding:8px 12px;border-bottom:1px solid #2d3148;">
          <div style="font-size:12px;font-weight:700;color:#f1f5f9;">🆕 V4 — Neu (ohne Andratx)</div>
          <div style="font-size:10px;color:#64748b;">PMI 33% DB60 · Daia 33% DB70 · SeS 33% DB60 · Andratx gestrichen</div>
        </div>
        <div id="kmap-neu" style="height:380px;"></div>
      </div>
    </div>
  </div>
</div>

<script>
// ── VERGLEICH ──
const VERGLEICH = [
  {neu:1, alt:4, diff:3, s4:88.2, s3:79.5, nr:409, name:"Porreres — Luxus-Finca mit Pool; mediterranes Paradies"},
  {neu:2, alt:19, diff:17, s4:85.2, s3:72.5, nr:416, name:"Mallorca — Luxus-Finca mit Infinity-Pool; Zeitlose Eleganz"},
  {neu:3, alt:12, diff:9, s4:85.2, s3:75.6, nr:417, name:"Südostmallorca — Luxus-Finca mit Pool; Meerblick und Gästehaus"},
  {neu:4, alt:3, diff:-1, s4:82.8, s3:80.3, nr:364, name:"Llucmajor — Stattliches Herrenhaus auf riesigem Grundstück"},
  {neu:5, alt:7, diff:2, s4:82.2, s3:77.2, nr:467, name:"Campos — Neun Zimmer und Gästehaus; Meerblick-Finca"},
  {neu:6, alt:20, diff:14, s4:81.4, s3:72.2, nr:403, name:"Mallorca — Finca mit Pool; Mediterrane Eleganz"},
  {neu:7, alt:6, diff:-1, s4:81.3, s3:79.2, nr:335, name:"Santanyí — Hist. Naturstein-Finca; 9 Zi, 300 Jahre alt"},
  {neu:8, alt:29, diff:21, s4:81.1, s3:71.0, nr:432, name:"Mallorca — Luxus-Finca mit Infinity-Pool; Mediterraner Traum"},
  {neu:9, alt:14, diff:5, s4:81.1, s3:74.0, nr:442, name:"Küstenregion — Modernes Penthouse; Meerblick & Luxus"},
  {neu:10, alt:43, diff:33, s4:80.2, s3:68.5, nr:405, name:"Südostküste — Cliff Villa mit Pool; Meerblick und moderne Architektur"},
  {neu:11, alt:1, diff:-10, s4:80.2, s3:82.3, nr:357, name:"Sa Torre/Llucmajor — Grosszügiges Finca-Anwesen (ehem. #1)"},
  {neu:12, alt:9, diff:-3, s4:80.1, s3:76.7, nr:411, name:"Mallorca Inland — Finca mit Pool; Mediterrane Oase"},
  {neu:14, alt:10, diff:-4, s4:78.7, s3:76.7, nr:469, name:"Santanyí — Rustikal und echt; Finca mit Annexe, Olivengarten"},
  {neu:18, alt:16, diff:-2, s4:77.4, s3:73.9, nr:427, name:"Südostmallorca — Mediterrane Familienfinca"},
  {neu:20, alt:26, diff:6, s4:77.3, s3:71.5, nr:456, name:"Mallorca — Luxus-Poolresidenz mit Bergpanorama"},
  {neu:21, alt:33, diff:12, s4:77.2, s3:70.5, nr:419, name:"Mallorca-Inland — Luxus-Finca mit Palmengarten"},
  {neu:22, alt:23, diff:1, s4:77.1, s3:71.7, nr:366, name:"Santa Maria — Finca Panorama; Meerblick"},
  {neu:27, alt:18, diff:-9, s4:75.1, s3:73.6, nr:307, name:"Inca — Inselfinca; 1.3 Hektar"},
  {neu:28, alt:5, diff:-23, s4:75.0, s3:79.3, nr:208, name:"Llucmajor — Arbeitsfinca; 1.8 Hektar"},
  {neu:29, alt:2, diff:-27, s4:74.9, s3:81.9, nr:365, name:"Campos — Finca mit Weingut (ehem. #2)"},
  {neu:34, alt:42, diff:8, s4:73.7, s3:68.7, nr:368, name:"Santa Maria — Finca Tramuntana; Panoramablick"},
  {neu:35, alt:11, diff:-24, s4:73.7, s3:76.4, nr:351, name:"Llucmajor — Herrschaftliche Naturstein-Finca"},
  {neu:38, alt:48, diff:10, s4:73.2, s3:67.4, nr:2, name:"Binissalem — Platz für alle; 8 Zimmer, endlose Gärten"},
  {neu:44, alt:8, diff:-36, s4:72.8, s3:76.8, nr:32, name:"Algaida — 54 Hektar historisches Herrenhaus"},
  {neu:47, alt:25, diff:-22, s4:72.1, s3:71.6, nr:443, name:"Mallorca — Mediterrane Natursteinfinca; Bougainvillea-Pracht"},
];

function openByNr(nr) {
  const obj = DATA.find(o => o.nr === nr);
  if (!obj) return;
  closeVergleich();
  setTimeout(() => openModal(obj), 150);
}
function openVergleich() {
  const tbody = document.getElementById('vtbody');
  tbody.innerHTML = '';
  VERGLEICH.forEach(o => {
    const diff = o.diff;
    let arrow, color;
    if (diff > 0)      { arrow = `▲ +${diff}`; color = '#22c55e'; }
    else if (diff < 0) { arrow = `▼ ${diff}`;  color = '#ef4444'; }
    else               { arrow = '─ =';         color = '#64748b'; }
    tbody.innerHTML += `<tr style="border-bottom:1px solid #1e2130;">
      <td style="text-align:center;font-weight:700;color:#f0a500;padding:5px 10px">${o.neu}</td>
      <td style="text-align:center;color:#94a3b8;padding:5px 10px">${o.alt}</td>
      <td style="text-align:center;font-weight:700;color:${color};padding:5px 10px">${arrow}</td>
      <td style="text-align:right;color:#60a5fa;font-weight:600;padding:5px 10px">${o.s4.toFixed(1)}</td>
      <td style="text-align:right;color:#94a3b8;padding:5px 24px 5px 10px">${o.s3.toFixed(1)}</td>
      <td style="padding:5px 10px 5px 20px"><span onclick="openByNr(${o.nr})" style="color:#60a5fa;font-size:12px;cursor:pointer;text-decoration:underline;text-underline-offset:3px;">${o.name}</span></td>
    </tr>`;
  });
  document.getElementById('vergleich-overlay').style.display = 'block';
  document.body.style.overflow = 'hidden';
}
function closeVergleich() {
  document.getElementById('vergleich-overlay').style.display = 'none';
  document.body.style.overflow = '';
}

// ── KARTEN ──
let kartenInitialized = false;
function openKarten() {
  document.getElementById('karten-overlay').style.display = 'block';
  document.body.style.overflow = 'hidden';
  if (!kartenInitialized) { initKarten(); kartenInitialized = true; }
}
function closeKarten() {
  document.getElementById('karten-overlay').style.display = 'none';
  document.body.style.overflow = '';
}
function minToM(min) { return min * 50 / 60 * 1000; }
function addZonen(map, lat, lng, label, color, z) {
  L.circle([lat,lng],{radius:minToM(z.db),color:'#ef4444',weight:1.5,opacity:0.6,fillColor:'#ef4444',fillOpacity:0.04}).addTo(map).bindTooltip(`${label}<br>Dealbreaker: ${z.db} min`,{sticky:true});
  L.circle([lat,lng],{radius:minToM(z.ok),color:'#eab308',weight:1.5,opacity:0.7,fillColor:'#eab308',fillOpacity:0.07}).addTo(map);
  L.circle([lat,lng],{radius:minToM(z.ideal),color:'#22c55e',weight:2,opacity:0.8,fillColor:'#22c55e',fillOpacity:0.12}).addTo(map);
  L.circleMarker([lat,lng],{radius:8,color:'#fff',weight:2,fillColor:color,fillOpacity:1}).addTo(map).bindTooltip(`<b>${label}</b>`,{permanent:true,direction:'top',offset:[0,-8]});
}
function initKarten() {
  const opts={center:[39.58,2.82],zoom:9};
  const tile='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
  const attr='© OpenStreetMap © CARTO';
  const mA=L.map('kmap-alt',opts); L.tileLayer(tile,{attribution:attr}).addTo(mA);
  addZonen(mA,39.5517,2.7388,'✈ Flughafen PMI','#60a5fa',{ideal:15,ok:25,db:40});
  addZonen(mA,39.7492,2.6487,'🏨 Daia','#a78bfa',{ideal:20,ok:40,db:70});
  addZonen(mA,39.3468,3.0456,'🌊 Ses Salines','#34d399',{ideal:15,ok:30,db:45});
  addZonen(mA,39.5741,2.3876,'⛰ Andratx','#fb923c',{ideal:25,ok:40,db:60});
  const mN=L.map('kmap-neu',opts); L.tileLayer(tile,{attribution:attr}).addTo(mN);
  addZonen(mN,39.5517,2.7388,'✈ Flughafen PMI','#60a5fa',{ideal:15,ok:25,db:60});
  addZonen(mN,39.7492,2.6487,'🏨 Daia','#a78bfa',{ideal:20,ok:40,db:70});
  addZonen(mN,39.3468,3.0456,'🌊 Ses Salines','#34d399',{ideal:15,ok:30,db:60});
  L.circleMarker([39.5741,2.3876],{radius:8,color:'#fff',weight:1,fillColor:'#374151',fillOpacity:0.4}).addTo(mN).bindTooltip('<b>⛰ Andratx</b><br><i>gestrichen</i>',{permanent:true,direction:'top',offset:[0,-8]});
}
</script>
'''

# ─── PATCHEN ─────────────────────────────────────────────────────────────────

# 1. Deckblatt nach <body>
content = content.replace('<body>', '<body>' + DECKBLATT, 1)

# 2. Header Info-Button
content = content.replace(
    '<div>\n    <div id="count">469 Objekte</div>\n    <div class="meta">Stand: 22.03.2026',
    '''<div style="display:flex;align-items:center;gap:12px;">
    <button onclick="document.getElementById('deckblatt').style.display='flex'" style="background:rgba(255,255,255,0.07);border:1px solid #2d3148;color:#94a3b8;padding:5px 12px;border-radius:6px;cursor:pointer;font-size:12px;">ℹ️ Info</button>
    <div>
      <div id="count">469 Objekte</div>
      <div class="meta">Stand: 22.03.2026'''
)
content = content.replace(
    'Stand: 22.03.2026 09:12</div>\n  </div>\n</header>',
    'Stand: 22.03.2026 09:12</div>\n    </div>\n  </div>\n</header>'
)

# 3. Filter Buttons
content = content.replace(
    '<button class="btn" onclick="applyFilters()">Filter</button>\n  <button class="btn sec" onclick="resetFilters()">Reset</button>',
    FILTER_NEW
)

# 4. Ort Normalisierung
content = content.replace(
    "// Populate ort filter",
    "// Ort normalisieren + Populate"
)
content = content.replace(
    "const orte = [...new Set(DATA.map(o => o.ort).filter(Boolean))].sort();\nconst ortSel = document.getElementById('filt-ort');\norte.forEach(o => { const op = document.createElement('option'); op.value = o; op.textContent = o; ortSel.appendChild(op); });",
    ORT_NEW
)

# 5. Filter auf ortNorm umstellen
content = content.replace("!o.ort.toLowerCase().includes(q)", "!(o.ortNorm||'').toLowerCase().includes(q)")
content = content.replace("if (ort && o.ort !== ort)", "if (ort && o.ortNorm !== ort)")
content = content.replace("${o.ort||'–'}", "${o.ortNorm||'–'}")
content = content.replace("(o.ort || '–')", "(o.ortNorm || '–')")

# 6. card-ort kleiner
content = content.replace(
    ".card-ort{font-size:.75rem;color:#888;margin-bottom:8px}",
    ".card-ort{font-size:.65rem;color:#666;margin-bottom:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
)

# 7. Modals + Scripts vor </body>
content = content.replace('</body>', EXTRA + '\n</body>')

with open(HTML, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ HTML vollständig gepatcht")
