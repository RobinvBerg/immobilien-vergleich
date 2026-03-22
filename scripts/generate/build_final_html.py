#!/usr/bin/env python3

# Script to build the final HTML with embedded images and complete functionality

from images_data import IMAGES_DATA

# Property data from original HTML (mapping to our image names)
PROPERTY_DATA = [
    {"name": "Casa o chalet Establiments", "image_key": "casa-establiments", "zimmer": 4, "grundstueck": 20262, "garten": 19500, "location": "Establiments", "fl_min": 20, "daia_min": 39, "and_min": 35, "preis": 3600000, "bebaut": 762, "charme": 4, "reno": 4, "bewirt": 3, "vermiet": 0},
    {"name": "EV Exposé Binissalem", "image_key": "ev-binissalem", "zimmer": 8, "grundstueck": 8261, "garten": 7861, "location": "Binissalem", "fl_min": 24, "daia_min": 42, "and_min": 42, "preis": 3400000, "bebaut": 400, "charme": 4, "reno": 4, "bewirt": 3, "vermiet": 0},
    {"name": "Gästehaus Establiments", "image_key": "gaestehaus-establiments", "zimmer": 7, "grundstueck": 14393, "garten": 13792, "location": "Establiments", "fl_min": 20, "daia_min": 39, "and_min": 35, "preis": 4500000, "bebaut": 601, "charme": 5, "reno": 4, "bewirt": 2, "vermiet": 0},
    {"name": "Modern Palmanyola", "image_key": "modern-palmanyola", "zimmer": 5, "grundstueck": 2500, "garten": 1830, "location": "Palmanyola", "fl_min": 16, "daia_min": 23, "and_min": 32, "preis": 5600000, "bebaut": 670, "charme": 4, "reno": 3, "bewirt": 4, "vermiet": 0},
    {"name": "Santa Maria unfertig", "image_key": "santa-maria-unfertig", "zimmer": 5, "grundstueck": 29307, "garten": 28807, "location": "Sta Maria", "fl_min": 16, "daia_min": 32, "and_min": 34, "preis": 4100000, "bebaut": 500, "charme": 4, "reno": 3, "bewirt": 3, "vermiet": 0},
    {"name": "Gute Substanz Campos", "image_key": "gute-substanz-campos", "zimmer": 6, "grundstueck": 11700, "garten": 11344, "location": "Campos", "fl_min": 21, "daia_min": 57, "and_min": 50, "preis": 2850000, "bebaut": 356, "charme": 4, "reno": 4, "bewirt": 3, "vermiet": 0},
    {"name": "Nähe Es Trenc", "image_key": "naehe-es-trenc", "zimmer": 5, "grundstueck": 30000, "garten": 29467, "location": "Sa Ràpita", "fl_min": 28, "daia_min": 64, "and_min": 58, "preis": 3950000, "bebaut": 533, "charme": 4, "reno": 3, "bewirt": 2, "vermiet": 0},
    {"name": "Kreativprojekt Sa Ràpita", "image_key": "kreativ-sa-rapita", "zimmer": 6, "grundstueck": 51000, "garten": 50320, "location": "Sa Ràpita", "fl_min": 28, "daia_min": 64, "and_min": 58, "preis": 2950000, "bebaut": 680, "charme": 3, "reno": 3, "bewirt": 4, "vermiet": 0},
    {"name": "Estate Sencelles", "image_key": "estate-sencelles", "zimmer": 6, "grundstueck": 132500, "garten": 131818, "location": "Sencelles", "fl_min": 26, "daia_min": 44, "and_min": 45, "preis": 3900000, "bebaut": 682, "charme": 5, "reno": 5, "bewirt": 2, "vermiet": 50},
    {"name": "Designer House Ses Salines", "image_key": "designer-ses-salines", "zimmer": 5, "grundstueck": 23800, "garten": 23401, "location": "Ses Salines", "fl_min": 34, "daia_min": 70, "and_min": 63, "preis": 5450000, "bebaut": 399, "charme": 5, "reno": 5, "bewirt": 4, "vermiet": 0},
    {"name": "Contemporary Moscari", "image_key": "contemporary-moscari", "zimmer": 5, "grundstueck": 19811, "garten": 18979, "location": "Moscari", "fl_min": 34, "daia_min": 52, "and_min": 52, "preis": 3950000, "bebaut": 832, "charme": 5, "reno": 5, "bewirt": 4, "vermiet": 0},
    {"name": "Finca Campos (Lizenz)", "image_key": "finca-campos-lizenz", "zimmer": 6, "grundstueck": 14200, "garten": 13764, "location": "Campos", "fl_min": 23, "daia_min": 57, "and_min": 50, "preis": 3490000, "bebaut": 436, "charme": 4, "reno": 4, "bewirt": 2, "vermiet": 100},
    {"name": "Villa Bunyola (Lizenz)", "image_key": "villa-bunyola-lizenz", "zimmer": 6, "grundstueck": 14785, "garten": 0, "location": "Bunyola", "fl_min": 20, "daia_min": 20, "and_min": 38, "preis": 3500000, "bebaut": 355, "charme": 5, "reno": 4, "bewirt": 3, "vermiet": 100}
]

# Build the complete JavaScript
js_code = f'''
// Property Images (Base64 embedded)
const PROPERTY_IMAGES = {{
'''

for key, value in IMAGES_DATA.items():
    js_code += f'  "{key}": "{value}",\n'

js_code += '''};

// Property Data
const PROPERTY_DATA = [
'''

for prop in PROPERTY_DATA:
    js_code += f'  {prop},\n'

js_code += '''
];

// Configuration Arrays
const weights = [
  {id:'zimmer', label:'Zimmer', val:20},
  {id:'erreich', label:'Erreichbarkeit', val:15},
  {id:'grund', label:'Grundstück/Garten', val:15},
  {id:'charme', label:'Charme/Ästhetik', val:15},
  {id:'vermiet', label:'Vermietlizenz', val:10},
  {id:'value', label:'Preis-Leistung', val:10},
  {id:'reno', label:'Renovierung', val:10},
  {id:'bewirt', label:'Bewirtschaftung', val:5},
];

const thresholds = [
  {id:'daia_ideal', label:'Daia Ideal (min)', val:20, min:5, max:60},
  {id:'daia_akz', label:'Daia Akzeptabel', val:40, min:10, max:80},
  {id:'daia_deal', label:'Daia Dealbreaker', val:70, min:20, max:120},
  {id:'fl_ideal', label:'Flughafen Ideal', val:15, min:5, max:40},
  {id:'fl_akz', label:'Flughafen Akzeptabel', val:25, min:10, max:50},
  {id:'fl_deal', label:'Flughafen Dealbreaker', val:40, min:15, max:60},
  {id:'and_ideal', label:'Andratx Ideal', val:25, min:5, max:50},
  {id:'and_akz', label:'Andratx Akzeptabel', val:40, min:10, max:70},
  {id:'and_deal', label:'Andratx Dealbreaker', val:60, min:20, max:90},
  {id:'daia_w', label:'Gewicht Daia %', val:50, min:0, max:100},
  {id:'fl_w', label:'Gewicht Flughafen %', val:30, min:0, max:100},
  {id:'and_w', label:'Gewicht Andratx %', val:20, min:0, max:100},
];

const zimmerTh = [
  {id:'zi_min', label:'Minimum Zimmer', val:5, min:3, max:10},
  {id:'zi_ideal', label:'Ideal Zimmer', val:8, min:5, max:15},
];

const grundTh = [
  {id:'gr_min', label:'Grundstück Min (m²)', val:3000, min:0, max:20000, step:500},
  {id:'gr_ideal', label:'Grundstück Ideal (m²)', val:15000, min:5000, max:50000, step:1000},
  {id:'ga_min', label:'Garten Min (m²)', val:1000, min:0, max:10000, step:500},
  {id:'ga_ideal', label:'Garten Ideal (m²)', val:5000, min:1000, max:30000, step:500},
];

// UI Functions
function toggleSection(sectionId) {
  const content = document.getElementById(sectionId + '-content');
  const icon = document.getElementById(sectionId + '-icon');
  
  content.classList.toggle('collapsed');
  icon.textContent = content.classList.contains('collapsed') ? '+' : '−';
}

function createSliders(containerId, items, onChange) {
  const container = document.getElementById(containerId);
  container.innerHTML = '';
  
  items.forEach(item => {
    const group = document.createElement('div');
    group.className = 'slider-group';
    
    const min = item.min ?? 0;
    const max = item.max ?? 40;
    const step = item.step ?? 1;
    
    group.innerHTML = `
      <div class="slider-label">
        <span>${item.label}</span>
        <span class="slider-value" id="val-${item.id}">${item.val}</span>
      </div>
      <input 
        type="range" 
        id="slider-${item.id}" 
        min="${min}" 
        max="${max}" 
        step="${step}" 
        value="${item.val}">
    `;
    
    container.appendChild(group);
    
    const slider = group.querySelector('input');
    const valueSpan = group.querySelector('.slider-value');
    
    slider.addEventListener('input', (e) => {
      item.val = Number(e.target.value);
      valueSpan.textContent = item.val;
      onChange();
    });
  });
}

// Helper Functions
function getWeight(id) {
  return weights.find(w => w.id === id)?.val ?? 0;
}

function getThreshold(id) {
  return thresholds.find(t => t.id === id)?.val ?? 0;
}

function getZimmerTh(id) {
  return zimmerTh.find(t => t.id === id)?.val ?? 0;
}

function getGrundTh(id) {
  return grundTh.find(t => t.id === id)?.val ?? 0;
}

function calculateDestinationScore(minutes, ideal, acceptable, dealbreaker) {
  if (minutes <= ideal) return 100;
  if (minutes >= dealbreaker) return 0;
  if (minutes <= acceptable) {
    return 100 - ((minutes - ideal) / (acceptable - ideal)) * 50;
  }
  return 50 - ((minutes - acceptable) / (dealbreaker - acceptable)) * 50;
}

// Main Scoring Logic
function calculateScores() {
  const totalWeight = weights.reduce((sum, w) => sum + w.val, 0);
  
  // Update total weight display
  const totalEl = document.getElementById('total-weight');
  totalEl.textContent = totalWeight + '%';
  totalEl.className = totalWeight === 100 ? 'total-ok' : 'total-warn';
  
  // Score each property
  const scoredData = PROPERTY_DATA.map(property => {
    const scored = { ...property };
    
    // Zimmer Score
    const ziMin = getZimmerTh('zi_min');
    const ziIdeal = getZimmerTh('zi_ideal');
    scored.zimmerScore = property.zimmer < ziMin ? 0 : 
      property.zimmer >= ziIdeal ? 100 : 
      ((property.zimmer - ziMin) / (ziIdeal - ziMin)) * 100;
    
    // Erreichbarkeit Score
    const daiaWeight = getThreshold('daia_w');
    const flWeight = getThreshold('fl_w');
    const andWeight = getThreshold('and_w');
    const totalReachWeight = daiaWeight + flWeight + andWeight || 1;
    
    const daiaScore = calculateDestinationScore(
      property.daia_min,
      getThreshold('daia_ideal'),
      getThreshold('daia_akz'),
      getThreshold('daia_deal')
    );
    
    const flScore = calculateDestinationScore(
      property.fl_min,
      getThreshold('fl_ideal'),
      getThreshold('fl_akz'),
      getThreshold('fl_deal')
    );
    
    const andScore = calculateDestinationScore(
      property.and_min,
      getThreshold('and_ideal'),
      getThreshold('and_akz'),
      getThreshold('and_deal')
    );
    
    scored.erreichScore = (daiaScore * (daiaWeight / totalReachWeight) + 
                          flScore * (flWeight / totalReachWeight) + 
                          andScore * (andWeight / totalReachWeight));
    
    // Grundstück Score
    const grMin = getGrundTh('gr_min');
    const grIdeal = getGrundTh('gr_ideal');
    const gaMin = getGrundTh('ga_min');
    const gaIdeal = getGrundTh('ga_ideal');
    
    const grundScore = property.grundstueck < grMin ? 0 :
      property.grundstueck >= grIdeal ? 100 :
      ((property.grundstueck - grMin) / (grIdeal - grMin)) * 100;
      
    const gartenScore = property.garten < gaMin ? 0 :
      property.garten >= gaIdeal ? 100 :
      ((property.garten - gaMin) / (gaIdeal - gaMin)) * 100;
    
    scored.grundScore = (grundScore * 0.5 + gartenScore * 0.5);
    
    // Other scores
    scored.charmeScore = (property.charme / 5) * 100;
    scored.vermietScore = property.vermiet;
    scored.renoScore = (property.reno / 5) * 100;
    scored.bewirtScore = (property.bewirt / 5) * 100;
    
    return scored;
  });
  
  // Calculate value scores (needs all properties for normalization)
  const eurPerM2 = scoredData.filter(p => p.bebaut > 0 && p.preis > 0)
    .map(p => p.preis / p.bebaut);
  const roomsPerMillion = scoredData.filter(p => p.preis > 0)
    .map(p => p.zimmer / (p.preis / 1e6));
    
  const minEur = Math.min(...eurPerM2);
  const maxEur = Math.max(...eurPerM2);
  const minRpm = Math.min(...roomsPerMillion);
  const maxRpm = Math.max(...roomsPerMillion);
  
  scoredData.forEach(property => {
    let eurScore = 50;
    let rpmScore = 50;
    
    if (property.bebaut > 0 && property.preis > 0 && maxEur > minEur) {
      eurScore = (1 - (property.preis / property.bebaut - minEur) / (maxEur - minEur)) * 100;
    }
    
    if (property.preis > 0 && maxRpm > minRpm) {
      rpmScore = ((property.zimmer / (property.preis / 1e6) - minRpm) / (maxRpm - minRpm)) * 100;
    }
    
    property.valueScore = eurScore * 0.5 + rpmScore * 0.5;
  });
  
  // Calculate final scores
  scoredData.forEach(property => {
    property.finalScore = (
      property.zimmerScore * getWeight('zimmer') +
      property.erreichScore * getWeight('erreich') +
      property.grundScore * getWeight('grund') +
      property.charmeScore * getWeight('charme') +
      property.vermietScore * getWeight('vermiet') +
      property.valueScore * getWeight('value') +
      property.renoScore * getWeight('reno') +
      property.bewirtScore * getWeight('bewirt')
    ) / (totalWeight || 1);
  });
  
  // Sort by score
  scoredData.sort((a, b) => b.finalScore - a.finalScore);
  
  return scoredData;
}

// Rendering Functions
function formatNumber(num) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(2) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(0) + 'k';
  }
  return num.toLocaleString('de-DE');
}

function getLicenseBadge(vermiet) {
  if (vermiet >= 100) return '<span class="badge badge-yes">Ja</span>';
  if (vermiet >= 50) return '<span class="badge badge-maybe">~</span>';
  return '<span class="badge badge-no">–</span>';
}

function renderProperties(scoredData) {
  const container = document.getElementById('properties-container');
  container.innerHTML = '';
  
  const maxScore = Math.max(...scoredData.map(p => p.finalScore));
  
  scoredData.forEach((property, index) => {
    const rank = index + 1;
    const scorePercent = maxScore > 0 ? (property.finalScore / maxScore) * 100 : 0;
    const scoreHue = Math.round((property.finalScore / 100) * 120);
    
    const card = document.createElement('div');
    card.className = 'property-card';
    
    // Get image
    const imageData = PROPERTY_IMAGES[property.image_key];
    const imageElement = imageData ? 
      `<img src="${imageData}" alt="${property.name}">` :
      '<div class="property-image">📷 Bild nicht verfügbar</div>';
    
    card.innerHTML = `
      <div class="property-rank${rank <= 3 ? ' top3' : ''}">${rank}</div>
      <div class="property-image">
        ${imageElement}
      </div>
      <div class="property-content">
        <div class="property-header">
          <h3 class="property-name">${property.name}</h3>
          <div class="property-location">${property.location}</div>
        </div>
        
        <div class="score-display">
          <div class="score-bar">
            <div class="score-fill" style="width: ${scorePercent}%; background: hsl(${scoreHue}, 70%, 50%);"></div>
          </div>
          <div class="score-text">
            <span>Gesamtscore</span>
            <span class="score-value" style="color: hsl(${scoreHue}, 70%, 50%);">${property.finalScore.toFixed(1)}</span>
          </div>
        </div>
        
        <div class="property-stats">
          <div class="stat-item">
            <span class="stat-label">Zimmer</span>
            <span class="stat-value">${property.zimmer}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Grundstück</span>
            <span class="stat-value">${formatNumber(property.grundstueck)}m²</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Garten</span>
            <span class="stat-value">${formatNumber(property.garten)}m²</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Preis</span>
            <span class="stat-value">${formatNumber(property.preis)}€</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Charme</span>
            <span class="stat-value">${property.charme}/5</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Lizenz</span>
            <span class="stat-value">${getLicenseBadge(property.vermiet)}</span>
          </div>
        </div>
      </div>
    `;
    
    container.appendChild(card);
  });
}

// Initialize Application
function init() {
  // Create sliders
  createSliders('weight-sliders', weights, updateScores);
  createSliders('reach-sliders', thresholds, updateScores);
  createSliders('rooms-sliders', zimmerTh, updateScores);
  createSliders('land-sliders', grundTh, updateScores);
  
  // Initial calculation
  updateScores();
}

function updateScores() {
  const scoredData = calculateScores();
  renderProperties(scoredData);
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', init);
'''

# Read the current HTML file
with open('/Users/robin/.openclaw/workspace/mallorca-projekt/mallorca-ranking-v2.html', 'r') as f:
    html_content = f.read()

# Find the closing </script> tag and insert the JavaScript before it
script_pos = html_content.rfind('</script>')
if script_pos == -1:
    # Add script tag before closing body
    body_pos = html_content.rfind('</body>')
    if body_pos != -1:
        html_content = html_content[:body_pos] + f'<script>{js_code}</script>\n' + html_content[body_pos:]
else:
    html_content = html_content[:script_pos] + js_code + html_content[script_pos:]

# Write the final HTML file
with open('/Users/robin/.openclaw/workspace/mallorca-projekt/mallorca-ranking-v2.html', 'w') as f:
    f.write(html_content)

print("✅ Final HTML file with embedded JavaScript and images created successfully!")
print("📄 File: /Users/robin/.openclaw/workspace/mallorca-projekt/mallorca-ranking-v2.html")
print(f"📦 File size: {len(html_content) / 1024:.1f} KB")