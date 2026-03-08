import openpyxl
import re

def kuerze_ort(ort):
    if not ort:
        return "Mallorca"
    ort = str(ort).strip()
    # Clean up suffixes like ",Villa", ",Finca" etc.
    ort = re.sub(r'\s*,.*$', '', ort)
    ort = ort.strip()
    
    # Normalize variants
    mapping = {
        "Palma de Mallorca": "Palma",
        "Santa Maria del Cami": "Santa Maria",
        "Santa María del Camí": "Santa Maria",
        "Santa Maria del Camí": "Santa Maria",
        "Santa María del Cami": "Santa Maria",
        "Santa María": "Santa Maria",
        "Sta. Maria": "Santa Maria",
        "Santa Margalida": "Santa Margalida",
        "Son Macià": "Son Macià",
        "S´Arraco": "S'Arraco",
        "Llucmajor interior": "Llucmajor",
        "Biniaraix": "Biniaraix",
        "Puerto Andratx": "Puerto Andratx",
        "Alqueria Blanca": "Alqueria Blanca",
        "Lloret de Vistalegre": "Lloret",
        "Maria de la Salut": "Maria de la Salut",
        "Camp De Mar": "Camp de Mar",
        "Cala Murada": "Cala Murada",
        "Cas Concos": "Cas Concos",
        "Son Vida": "Son Vida",
    }
    if ort in mapping:
        return mapping[ort]
    return ort

def hat_keyword(text, keywords):
    if not text:
        return False
    text_lower = str(text).lower()
    return any(k.lower() in text_lower for k in keywords)

def grundstueck_str(qm):
    if not qm:
        return None
    qm = int(qm)
    if qm >= 1000000:
        ha = qm // 10000
        return f"{ha} Hektar"
    elif qm >= 100000:
        ha = qm // 10000
        return f"{ha} Hektar"
    elif qm >= 10000:
        ha_f = qm / 10000
        if ha_f == int(ha_f):
            return f"{int(ha_f)} Hektar"
        return f"{ha_f:.1f} Hektar"
    else:
        return f"{qm:,}m²".replace(",", ".")

def generiere_name(nr, ort_raw, charme, grund, preis, gebaeude):
    ort = kuerze_ort(ort_raw)
    g = str(gebaeude) if gebaeude else ""
    g_low = g.lower()
    
    qm = int(grund) if grund else 0
    preis_int = int(preis) if preis else 0
    charme_int = int(charme) if charme else 3
    
    gs = grundstueck_str(qm)
    
    # --- Classify building type ---
    ist_herrenhaus = hat_keyword(g, ["herrenhaus", "Herrensitz", "Gutshof", "Possessió", "possessio"])
    ist_weingut = hat_keyword(g, ["weingut", "weinanlage", "weinberg", "Weinbau"])
    ist_reitanlage = hat_keyword(g, ["reitanlage", "reit"])
    ist_dorfhaus = hat_keyword(g, ["dorfhaus", "dorfkern"])
    ist_neuebau = hat_keyword(g, ["neubau", "Neubau 2025", "Neubau 2022", "2022", "2025", "2024", "modern", "moderne", "minimalist"])
    ist_historisch = hat_keyword(g, ["14. jahrhundert", "15. jahrhundert", "16. jahrhundert", "17. jahrhundert", "13. jahrhundert", "jesuitenkonvent", "1880", "kapelle"])
    ist_stone = hat_keyword(g, ["naturstein", "steinhaus", "steinvilla", "steinmansion", "steinfinca"])
    ist_design = hat_keyword(g, ["design", "architect", "minimalist", "luxus-villa", "infinity-pool"])
    hat_gaestehaus = hat_keyword(g, ["gästehaus", "gästeeinheit", "gästebereich", "gästetrakt", "nebengebäude"])
    hat_pool = hat_keyword(g, ["pool", "infinity"])
    ist_turm = hat_keyword(g, ["turm"])
    ist_komplex = hat_keyword(g, ["komplex", "mehrere wohneinheiten", "mehrere gebäude"])
    ist_panorama = hat_keyword(g, ["panorama", "meerblick", "weitblick", "aussicht"])
    ist_finca = hat_keyword(g, ["finca"])
    ist_villa = hat_keyword(g, ["villa"])
    ist_apartment = hat_keyword(g, ["apartment"])
    
    # Special location-based overrides
    ort_tramuntana = ort in ["Deià", "Valldemossa", "Banyalbufar", "Escorca", "Fornalutx", "Biniaraix", "Estellencs"]
    ort_strand = ort in ["Sa Ràpita", "Ses Covetes", "Cala Santanyí", "Cala Murada", "Camp de Mar", "Puerto Andratx", "Sant Elm"]
    ort_palma_nah = ort in ["Palma", "Palmanyola", "Establiments", "Puigpunyent", "Bunyola", "Marratxí", "Portol", "Son Vida", "Gènova", "Puntiró"]
    ort_zentral = ort in ["Sineu", "Algaida", "Porreres", "Sencelles", "Montuïri", "Llubí", "Lloret", "Campanet"]
    
    # --- Generate title and einordnung ---
    
    # Special cases by location / features (BEFORE size checks)
    if ort == "Deià" or ort == "Banyalbufar":
        if charme_int >= 5:
            return f"{ort} — Steinidyll; Tramuntana trifft Meer"
        return f"{ort} — Tramuntana-Finca; Fels, Olivenland, Ruhe"
    
    if ort == "Escorca":
        return f"{ort} — Gebirgsrückzug; Tramuntana pur, {gs}"
    
    if ort == "Estellencs":
        return f"{ort} — Westküsten-Gut; Klippen, Meer, {gs}"

    # Very large estates (>100ha)
    if qm >= 1000000:
        ha = qm // 10000
        if ist_herrenhaus or ist_historisch:
            return f"{ort} — Feudalerbe; {ha} Hektar historisches Landgut"
        elif ist_reitanlage:
            return f"{ort} — Pferdereich; {ha} Hektar Reitanlage"
        elif ist_stone and charme_int >= 4:
            return f"{ort} — Steinmassiv; {ha} Hektar mallorquinisches Land"
        else:
            return f"{ort} — Landreserve; {ha} Hektar, ungeschriebene Geschichte"
    
    # 10-100ha
    if qm >= 100000:
        ha = qm // 10000
        if ist_weingut:
            return f"{ort} — Weinseele; {ha} Hektar Weinbau und Geschichte"
        elif ist_herrenhaus or ist_historisch:
            return f"{ort} — Alte Größe; {ha} Hektar historisches Herrenhaus"
        elif ist_reitanlage:
            return f"{ort} — Reitland; {ha} Hektar für Pferd und Mensch"
        elif charme_int >= 4:
            return f"{ort} — Großes Erbe; {ha} Hektar Inselmitte"
        else:
            return f"{ort} — Viel Land; {ha} Hektar, viel Potenzial"
    
    if ort == "Puigpunyent":
        if preis_int >= 20000000:
            return f"{ort} — Herrenhaus-Erbe; historisch, {gs}"
        return f"{ort} — Grünes Refugium; Natur, Ruhe, {gs}"
    
    if ort == "Sóller":
        return f"{ort} — Orangental; Tramuntana-Idyll, {gs}"
    
    if ort == "Gènova":
        return f"{ort} — Palma-Panorama; weiße Villa über der Bucht"
    
    if ort == "Son Vida":
        return f"{ort} — Stadtrand-Prestige; Golfblick, Palma-Nähe"
    
    if ort == "Puerto Andratx":
        return f"{ort} — Hafen & Hügel; Yachtblick inklusive"
    
    if ort == "Biniaraix":
        return f"{ort} — Dorfjuwel; Tramuntana-Kulisse, fast vergessen"
    
    if ist_weingut and charme_int >= 4:
        if qm >= 30000:
            return f"{ort} — Weinkultur; {gs} Weinbau mit Geschichte"
        return f"{ort} — Winzer-Traum; Trauben, Stein, Ruhe"
    
    if ist_reitanlage:
        return f"{ort} — Reitdomizil; Anlage mit Wohn- und Wirtschaftsbau"
    
    if ist_herrenhaus and charme_int >= 4:
        if ist_historisch:
            return f"{ort} — Herrensitz; Jahrhunderte in Stein gegossen"
        return f"{ort} — Gutshaus; Charakter, Größe, Grundstück"
    
    # Jesuitenkloster
    if "jesuitenkonvent" in g_low:
        return f"{ort} — Klostererbe; ehemalige Jesuitenanlage, {gs}"
    
    # Strand-Lage
    if ort_strand:
        if charme_int >= 4 and ist_stone:
            return f"{ort} — Sandsteintraum; Strand, Stille, Steinmauern"
        elif charme_int >= 4:
            return f"{ort} — Meeresnähe; {gs}, Strand fast vor der Tür"
        return f"{ort} — Küstennah; {gs}, Meer in Reichweite"
    
    # Design/Neubau
    if ist_neuebau and ist_design and charme_int >= 4:
        if ort_palma_nah:
            return f"{ort} — Stadtrand-Neubau; Design, Pool, Palma-Nähe"
        elif qm >= 30000:
            return f"{ort} — Neubau-Statement; {gs}, klar, modern, fertig"
        return f"{ort} — Saubere Linien; Neubau, einziehen, fertig"
    
    if ist_neuebau and charme_int >= 4:
        if qm >= 20000:
            return f"{ort} — Frischer Start; Neubau auf {gs}"
        return f"{ort} — Moderne Finca; Neubau mit Charakter"
    
    if ist_neuebau and charme_int <= 3:
        return f"{ort} — Neubau; solide, {gs}, kein Schnickschnack"
    
    # Luxury high price
    if preis_int >= 10000000 and charme_int >= 4:
        if ist_stone and ist_historisch:
            return f"{ort} — Landmark; historisches Anwesen, {gs}"
        elif ist_design:
            return f"{ort} — Spitzenklasse; Design-Anwesen, {gs}"
        elif qm >= 20000:
            return f"{ort} — Großes Kino; {gs}, Preis mit Begründung"
        return f"{ort} — Top-Liga; Raum, Lage, Ausstattung"
    
    # Historical charm
    if ist_historisch and charme_int >= 4:
        if "14. jahrhundert" in g_low or "15. jahrhundert" in g_low or "13. jahrhundert" in g_low:
            return f"{ort} — Jahrhunderterbe; alte Seele, neue Möglichkeiten"
        if "kapelle" in g_low:
            return f"{ort} — Mit Kapelle; Weingut aus dem 13. Jahrhundert"
        return f"{ort} — Altes Stein; 1880er-Charme, {gs}"
    
    # Stone / rustic character
    if ist_stone and charme_int >= 5 and hat_gaestehaus:
        return f"{ort} — Steinperle; Haupthaus + Gästehaus, {gs}"
    
    if ist_stone and charme_int >= 5:
        if ort_tramuntana:
            return f"{ort} — Bergidyll; Naturstein, Charme, Weite"
        return f"{ort} — Steinseele; Charme pur, {gs}"
    
    if ist_stone and charme_int >= 4 and hat_gaestehaus:
        return f"{ort} — Steinensemble; Haupt + Gast, {gs}"
    
    if ist_stone and charme_int >= 4:
        if ort_tramuntana:
            return f"{ort} — Tramuntana-Stein; Natur direkt vor der Tür"
        if qm >= 30000:
            return f"{ort} — Steinlandhaus; {gs} mallorquinischer Boden"
        return f"{ort} — Rustikaler Kern; Stein, Patina, Potenzial"
    
    # Innenhof / Dorfhaus
    if ist_dorfhaus and charme_int >= 4:
        return f"{ort} — Dorfkern; Innenhof, Pool, Steinmauern"
    
    if ist_dorfhaus:
        return f"{ort} — Dorfhaus; authentisch, {gs}"
    
    # Panorama / Meerblick
    if ist_panorama and charme_int >= 4:
        if "meerblick" in g_low or "panorama" in g_low:
            return f"{ort} — Panoramalage; {gs}, Aussicht als Bonus"
        return f"{ort} — Aussichtsreich; {gs}, Weitblick inklusive"
    
    # Gästehaus / Komplex
    if hat_gaestehaus and charme_int >= 4 and qm >= 20000:
        return f"{ort} — Haupthaus + Gast; {gs}, Raum für alle"
    
    if hat_gaestehaus and charme_int >= 5:
        return f"{ort} — Gut aufgestellt; Gästehaus dabei, {gs}"
    
    # Design villa
    if ist_design and charme_int >= 5:
        if ort_palma_nah:
            return f"{ort} — Design & Distanz; Palma-nah, Architektur-klar"
        return f"{ort} — Designhaltung; klare Formen, großer Pool"
    
    if ist_design and charme_int >= 4:
        return f"{ort} — Modernes Statement; Design, Pool, {gs}"
    
    # Villa / modern
    if ist_villa and charme_int >= 4:
        if qm >= 15000:
            return f"{ort} — Villenweite; {gs}, moderner Standard"
        return f"{ort} — Villenleben; Komfort, Pool, {gs}"
    
    # Finca categories
    if ist_finca and charme_int >= 5:
        if ist_historisch:
            return f"{ort} — Finca mit Seele; alt, gepflegt, bereit"
        return f"{ort} — Finca-Charme; {gs}, Olivenland inklusive"
    
    if ist_finca and charme_int >= 4:
        if qm >= 30000:
            return f"{ort} — Finca-Weite; {gs} mallorquinische Landschaft"
        elif qm >= 15000:
            return f"{ort} — Arbeitsfinca; solide Basis, {gs}"
        return f"{ort} — Inselfinca; {gs}, mallorquinisches Feeling"
    
    if ist_finca and charme_int <= 3:
        return f"{ort} — Finca-Basics; {gs}, Preis stimmt"
    
    # Palma-nahe Objekte
    if ort_palma_nah and charme_int >= 4:
        if ist_neuebau:
            return f"{ort} — Palma-nah; Neubau mit Blick auf die Stadt"
        return f"{ort} — Stadtflucht; 20 Minuten, anderes Leben"
    
    # Zentral gelegen
    if ort_zentral and charme_int >= 4:
        return f"{ort} — Inselherz; ruhig, zentral, {gs}"
    
    # Charm 5, generic
    if charme_int >= 5:
        return f"{ort} — Charakterstück; {gs}, Charme auf Stufe 5"
    
    # Charm 4, generic
    if charme_int >= 4:
        if qm >= 30000:
            return f"{ort} — Solide Größe; {gs}, guter Ausgangspunkt"
        return f"{ort} — Gute Substanz; {gs}, vernünftiger Preis"
    
    # Low charm
    if charme_int <= 2:
        return f"{ort} — Rohling; {gs}, Preis macht's möglich"
    
    # Fallback
    return f"{ort} — Ruhige Lage; {gs}, mallorquinisch"


# Load workbook
wb = openpyxl.load_workbook('mallorca-kandidaten-v2.xlsx')
ws = wb.active

count = 0
examples = []

for row in ws.iter_rows(min_row=15, max_row=333):
    nr = row[0].value
    ort = row[9].value
    charme = row[3].value
    grund = row[6].value
    preis = row[18].value
    gebaeude = row[28].value
    
    name = generiere_name(nr, ort, charme, grund, preis, gebaeude)
    row[38].value = name  # Column 39 = index 38
    count += 1
    
    if count <= 10 or count % 60 == 0:
        examples.append(f"  Nr {nr} | {name}")

wb.save('mallorca-kandidaten-v2.xlsx')
print(f"✅ Fertig! {count} Anzeigenamen generiert und gespeichert.")
print("\n📋 Beispiele:")
for e in examples[:15]:
    print(e)
