import json, re

with open('mallorca-ranking-v4.html', encoding='utf-8') as f:
    html = f.read()

with open('shortlist_data.json', encoding='utf-8') as f:
    data = json.load(f)

SHORTLIST_HTML = '''
<!-- SHORTLIST OVERLAY -->
<div id="shortlist-overlay" style="display:none;position:fixed;inset:0;background:#0d0f1a;z-index:3000;overflow-y:auto;">
  <div style="max-width:1400px;margin:0 auto;padding:20px;">
    <!-- Header -->
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:24px;padding-bottom:16px;border-bottom:1px solid #2a2a3e;">
      <button onclick="closeShortlist()" style="background:#1e2235;border:1px solid #2a2a3e;color:#e0e0e0;padding:8px 16px;border-radius:8px;cursor:pointer;font-size:14px;">← Zurück</button>
      <div>
        <h1 style="font-size:1.4em;color:#fff;margin:0;">🎛 Shortlist — Top 25</h1>
        <div style="font-size:12px;color:#64748b;margin-top:2px;">Passe die Gewichtungen an und sieh dein persönliches Ranking</div>
      </div>
      <div style="margin-left:auto;display:flex;gap:8px;">
        <button onclick="setMode('simple')" id="btn-simple" style="background:#f0a500;border:none;color:#000;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:bold;">Einfach</button>
        <button onclick="setMode('expert')" id="btn-expert" style="background:#1e2235;border:1px solid #2a2a3e;color:#aaa;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:12px;">Experte</button>
      </div>
    </div>

    <div style="display:flex;gap:24px;">
      <!-- Sidebar -->
      <div style="min-width:260px;max-width:280px;flex-shrink:0;">
        <div style="background:#1e2235;border-radius:12px;padding:16px;position:sticky;top:20px;">
          
          <!-- Einfach Mode -->
          <div id="sl-simple">
            <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">Gewichtungen</div>
            <div id="sl-simple-sliders"></div>
          </div>

          <!-- Experte Mode -->
          <div id="sl-expert" style="display:none;">
            <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">Alle Gewichtungen</div>
            <div id="sl-expert-sliders"></div>
            <div style="margin-top:8px;padding:6px 10px;border-radius:6px;font-size:12px;text-align:center;" id="sl-weight-sum"></div>
          </div>

          <hr style="border:0;border-top:1px solid #2a2a3e;margin:16px 0;">
          <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">Budget</div>
          <div style="font-size:12px;color:#e0e0e0;margin-bottom:6px;">Max: <span id="sl-budget-val" style="color:#f0a500;font-weight:bold;">6M €</span></div>
          <input type="range" id="sl-budget" min="1" max="12" value="6" step="0.25" style="width:100%;accent-color:#f0a500;" oninput="document.getElementById('sl-budget-val').textContent=this.value+'M €';slCompute()">

          <button onclick="slReset()" style="margin-top:16px;width:100%;background:#2a2a3e;border:none;color:#aaa;padding:8px;border-radius:6px;cursor:pointer;font-size:12px;">↺ Zurücksetzen</button>
        </div>
      </div>

      <!-- Cards -->
      <div style="flex:1;min-width:0;">
        <div id="sl-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;"></div>
      </div>
    </div>
  </div>
</div>
'''

# Slider CSS
SHORTLIST_CSS = '''
<style id="sl-css">
.sl-slider-row { margin-bottom:10px; }
.sl-slider-row label { display:flex;justify-content:space-between;font-size:12px;color:#ccc;margin-bottom:3px; }
.sl-slider-row label span { color:#f0a500;font-weight:bold; }
.sl-slider-row input[type=range] { width:100%;accent-color:#f0a500; }
.sl-card { background:#16213e;border-radius:10px;overflow:hidden;cursor:pointer;transition:transform .2s,box-shadow .2s;border:1px solid #2a2a3e; }
.sl-card:hover { transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.4); }
.sl-card.excluded { opacity:0.35;border-color:#ef4444; }
.sl-card img { width:100%;height:180px;object-fit:cover;display:block; }
.sl-card-body { padding:12px; }
.sl-rank { position:absolute;top:8px;left:8px;background:rgba(13,15,26,.85);color:#f0a500;font-weight:bold;font-size:1.1em;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2px solid #f0a500; }
.sl-bar-bg { height:6px;background:#2a2a3e;border-radius:3px;overflow:hidden;margin:6px 0; }
.sl-bar-fill { height:100%;border-radius:3px;transition:width .3s; }
</style>
'''

# JavaScript
SHORTLIST_JS = r'''
<script id="sl-js">
const SL_DATA = ''' + json.dumps(data, ensure_ascii=False) + r''';

const SL_SIMPLE = [
  {id:'zimmer',    label:'🛏 Zimmer & Platz',    val:25, desc:'Anzahl Schlafzimmer + Grundstück'},
  {id:'preis',     label:'💰 Preis',              val:20, desc:'Gesamtpreis (günstigere bevorzugt)'},
  {id:'charme',    label:'✨ Charme & Zustand',   val:20, desc:'Optik, Stil, Renovierungsstand'},
  {id:'gaestehaus',label:'🏡 Gästehaus',          val:15, desc:'Separate Gästehäuser'},
  {id:'lage',      label:'📍 Lage & Erreichbarkeit', val:10, desc:'PMI, Daia, Ses Salines'},
  {id:'vermiet',   label:'📄 Vermietlizenz',      val:10, desc:'Lizenz zur Ferienvermietung'},
];

const SL_EXPERT = [
  {id:'zimmer',     label:'Zimmer',           val:20},
  {id:'grundstueck',label:'Grundstück',       val:10},
  {id:'charme',     label:'Charme',           val:10},
  {id:'renovierung',label:'Renovierung',      val:15},
  {id:'bewirtschaft',label:'Bewirtschaftung', val:10},
  {id:'gaestehaus', label:'Gästehaus',        val:15},
  {id:'vermiet',    label:'Vermietlizenz',    val:5},
  {id:'erreichbar', label:'Erreichbarkeit',   val:5},
  {id:'preis',      label:'Preis-Leistung',   val:10},
];

let slMode = 'simple';

function setMode(m) {
  slMode = m;
  document.getElementById('sl-simple').style.display = m === 'simple' ? 'block' : 'none';
  document.getElementById('sl-expert').style.display = m === 'expert' ? 'block' : 'none';
  document.getElementById('btn-simple').style.background = m === 'simple' ? '#f0a500' : '#1e2235';
  document.getElementById('btn-simple').style.color = m === 'simple' ? '#000' : '#aaa';
  document.getElementById('btn-expert').style.background = m === 'expert' ? '#f0a500' : '#1e2235';
  document.getElementById('btn-expert').style.color = m === 'expert' ? '#000' : '#aaa';
  slCompute();
}

function makeSlRow(s, containerId) {
  const el = document.getElementById(containerId);
  const d = document.createElement('div');
  d.className = 'sl-slider-row';
  d.innerHTML = `<label>${s.label} <span id="slv_${s.id}${containerId}">${s.val}</span></label><input type="range" id="sli_${s.id}${containerId}" min="0" max="40" value="${s.val}" oninput="document.getElementById('slv_${s.id}${containerId}').textContent=this.value;s_${s.id}_${containerId}=+this.value;slCompute()">`;
  el.appendChild(d);
  window[`s_${s.id}_${containerId}`] = s.val;
}

function getW(id, arr, containerId) {
  const el = document.getElementById(`sli_${id}${containerId}`);
  return el ? +el.value : (arr.find(s=>s.id===id)?.val || 0);
}

function slScore(o) {
  const budget = +document.getElementById('sl-budget').value * 1e6;
  const excluded = o.preis > budget;

  if (slMode === 'simple') {
    const cid = 'sl-simple-sliders';
    const wZi = getW('zimmer', SL_SIMPLE, cid);
    const wPr = getW('preis', SL_SIMPLE, cid);
    const wCh = getW('charme', SL_SIMPLE, cid);
    const wGh = getW('gaestehaus', SL_SIMPLE, cid);
    const wLa = getW('lage', SL_SIMPLE, cid);
    const wVm = getW('vermiet', SL_SIMPLE, cid);
    const total = wZi+wPr+wCh+wGh+wLa+wVm || 1;

    const sZi = Math.min(100, ((o.zimmer||0)/10)*100);
    const sGrund = Math.min(100, ((o.grundstueck||0)/15000)*100);
    const sPlatz = sZi*0.6 + sGrund*0.4;
    const sPr = o.preis <= budget ? Math.max(0, 100 - ((o.preis/budget)*50)) : 0;
    const sCh = ((o.charme||0)/5)*100;
    const sRe = o.renovierung||0;
    const sChTotal = sCh*0.5 + sRe*0.5;
    const sGh = Math.min(100, ((o.gaestehaus||0)/2)*100);
    const sLa = o.erreichbarkeit||0;
    const sVm = o.vermietlizenz||0;

    const score = (sPlatz*wZi + sPr*wPr + sChTotal*wCh + sGh*wGh + sLa*wLa + sVm*wVm) / total;
    return {score, excluded};
  } else {
    const cid = 'sl-expert-sliders';
    const ws = SL_EXPERT.map(s => ({id:s.id, w: getW(s.id, SL_EXPERT, cid)}));
    const total = ws.reduce((a,b)=>a+b.w, 0) || 1;

    const scores = {
      zimmer:      Math.min(100, ((o.zimmer||0)/10)*100),
      grundstueck: Math.min(100, ((o.grundstueck||0)/15000)*100),
      charme:      ((o.charme||0)/5)*100,
      renovierung: o.renovierung||0,
      bewirtschaft:((o.bewirtschaftung||0)/5)*100,
      gaestehaus:  Math.min(100,((o.gaestehaus||0)/2)*100),
      vermiet:     o.vermietlizenz||0,
      erreichbar:  o.erreichbarkeit||0,
      preis:       o.preis <= budget ? Math.max(0,100-((o.preis/budget)*50)) : 0,
    };
    const score = ws.reduce((a,s) => a + (scores[s.id]||0)*s.w, 0) / total;
    return {score, excluded};
  }
}

function slCompute() {
  // Experte: Gewicht-Summe anzeigen
  if (slMode === 'expert') {
    const cid = 'sl-expert-sliders';
    const sum = SL_EXPERT.reduce((a,s) => a + getW(s.id, SL_EXPERT, cid), 0);
    const el = document.getElementById('sl-weight-sum');
    el.textContent = 'Gesamt: ' + sum + '%';
    el.style.background = sum === 100 ? 'rgba(34,197,94,.12)' : 'rgba(239,83,80,.12)';
    el.style.color = sum === 100 ? '#22c55e' : '#ef4444';
  }

  const scored = SL_DATA.map(o => {
    const {score, excluded} = slScore(o);
    return {...o, slScore: score, slExcluded: excluded};
  });
  scored.sort((a,b) => b.slScore - a.slScore);
  slRender(scored);
}

function slRender(data) {
  const grid = document.getElementById('sl-grid');
  grid.innerHTML = '';
  data.forEach((o, i) => {
    const rank = i + 1;
    const hue = Math.round((o.slScore/100)*120);
    const color = `hsl(${hue},70%,50%)`;
    const medal = rank===1?'🥇':rank===2?'🥈':rank===3?'🥉':rank;
    const preisStr = o.preis ? (o.preis/1e6).toFixed(2)+' Mio €' : '–';
    const div = document.createElement('div');
    div.className = 'sl-card' + (o.slExcluded ? ' excluded' : '');
    div.style.position = 'relative';
    div.innerHTML = `
      <img src="${o.img}" alt="${o.name}" loading="lazy" onerror="this.style.display='none'">
      <div class="sl-rank">${medal}</div>
      <div class="sl-card-body">
        <div style="font-size:13px;font-weight:bold;color:#fff;margin-bottom:2px;">${o.name.substring(0,55)}</div>
        <div style="font-size:11px;color:#64748b;margin-bottom:6px;">📍 ${o.ort} · ${preisStr}</div>
        <div class="sl-bar-bg"><div class="sl-bar-fill" style="width:${o.slScore.toFixed(0)}%;background:${color}"></div></div>
        <div style="display:flex;justify-content:space-between;font-size:11px;margin-top:2px;">
          <span style="color:${color};font-weight:bold;">${o.slScore.toFixed(1)} Punkte</span>
          <span style="color:#64748b;">V4 Rang #${o.rang}</span>
        </div>
        <div style="display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;">
          <span style="font-size:10px;background:#1a2840;color:#4fc3f7;padding:2px 7px;border-radius:4px;">${o.zimmer} Zi</span>
          <span style="font-size:10px;background:#1a2840;color:#4fc3f7;padding:2px 7px;border-radius:4px;">${o.grundstueck?.toLocaleString('de')} m²</span>
          ${o.gaestehaus ? `<span style="font-size:10px;background:#1a3020;color:#22c55e;padding:2px 7px;border-radius:4px;">🏡 Gästehaus</span>` : ''}
          ${o.vermietlizenz >= 100 ? `<span style="font-size:10px;background:#1a3020;color:#22c55e;padding:2px 7px;border-radius:4px;">✓ Lizenz</span>` : ''}
        </div>
      </div>`;
    if (o.url) div.onclick = () => window.open(o.url, '_blank');
    grid.appendChild(div);
  });
}

function slReset() {
  SL_SIMPLE.forEach(s => { const el = document.getElementById('sli_'+s.id+'sl-simple-sliders'); if(el){el.value=s.val;document.getElementById('slv_'+s.id+'sl-simple-sliders').textContent=s.val;} });
  SL_EXPERT.forEach(s => { const el = document.getElementById('sli_'+s.id+'sl-expert-sliders'); if(el){el.value=s.val;document.getElementById('slv_'+s.id+'sl-expert-sliders').textContent=s.val;} });
  document.getElementById('sl-budget').value = 6;
  document.getElementById('sl-budget-val').textContent = '6M €';
  slCompute();
}

function openShortlist() {
  document.getElementById('shortlist-overlay').style.display = 'block';
  document.body.style.overflow = 'hidden';
  if (!document.getElementById('sli_zimmersl-simple-sliders')) {
    SL_SIMPLE.forEach(s => makeSlRow(s, 'sl-simple-sliders'));
    SL_EXPERT.forEach(s => makeSlRow(s, 'sl-expert-sliders'));
  }
  slCompute();
}

function closeShortlist() {
  document.getElementById('shortlist-overlay').style.display = 'none';
  document.body.style.overflow = '';
}
</script>
'''

# Button in Navbar einfügen
html = html.replace(
    '<button onclick="openVergleich()"',
    '<button onclick="openShortlist()" style="background:linear-gradient(135deg,#7c3aed,#5b21b6);">🎛 Shortlist</button>\n  <button onclick="openVergleich()"'
)

# HTML + CSS + JS einfügen
html = html.replace('</body>', SHORTLIST_CSS + SHORTLIST_HTML + SHORTLIST_JS + '\n</body>')

with open('mallorca-ranking-v4.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('✅ Shortlist eingebaut')
