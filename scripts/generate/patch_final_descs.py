#!/usr/bin/env python3
"""Patch final approved titles + descriptions into mallorca-ranking-v5.html"""
import re

# Old name → new name, old desc → new desc
# From RTF approved table
patches = [
    # Establiments (big one) - title + desc changed
    ("Establiments — Raum ohne Ende; 762m² pures Volumen",
     "Establiments — Das Volumen; 762m² zum Umdenken",
     "Die Große — wer Wände verschieben kann, hat hier ein Monster.",
     "Riesig, tolle Lage — aber nur 4 Zimmer. Umbau nötig, dann ein Monster."),
    # Binissalem - desc changed
    ("Binissalem — Platz für alle; 8 Zimmer, endlose Gärten",
     None,  # title unchanged
     "Der Allrounder — genug Platz für große Abende unter freiem Himmel.",
     "Sommer im Garten, Großmutter zum Abendessen — alles nah, alles einfach."),
    # Establiments Charme - desc changed
    ("Establiments — Charme-Refugium; wo Stein und Seele verschmelzen",
     None,
     "Wo Stein und Seele verschmelzen — ein Ort, der Geschichten erzählt.",
     "Alte Mauern, warmes Licht — ein Haus das die Kinder nie vergessen werden."),
    # Palmanyola - desc changed
    ("Palmanyola — Klein aber Wow; Designvilla, null Kompromisse",
     "Palmanyola — Klein aber Wow; Designvilla vor den Toren Palmas",
     "Klein im Grundstück, groß im Auftritt — null Kompromisse.",
     "Modern, sofort bezugsfertig, nah dran — aber Grundstück zu klein für drei Kinder."),
    # Santa Maria - desc changed
    ("Santa Maria — Potenzial pur; Rohling in Traumlage",
     None,
     "Die Lage schreit nach Zukunft — wer's sieht, gewinnt.",
     "Traumlage, nah am Flughafen — aber unfertig. Mit kleinen Kindern erstmal stressig."),
    # Campos Zum Selbermachen - title + desc changed
    ("Campos — Zum Selbermachen; ehrliche Finca, ehrlicher Preis",
     "Campos — Deine Leinwand; ehrliche Finca, ehrlicher Preis",
     "Ehrlich, bodenständig, deins — für alle, die lieber selbst gestalten.",
     "Solide Basis, fairer Preis — aber hier muss noch Hand angelegt werden."),
    # Sa Ràpita Strandgold - desc changed
    ("Sa Ràpita — Strandgold; aufwachen, Es Trenc, fertig",
     None,
     "Aufwachen, Salz auf der Haut, Sand unter den Füßen.",
     "Strand vor der Tür, perfekt für Sommer — aber über eine Stunde zum Familienhaus."),
    # Sa Ràpita Vision - desc changed
    ("Sa Ràpita — Vision 1800; 5 Hektar warten auf deine Handschrift",
     None,
     "Wer hier baut, baut Legende — für Visionäre mit Geduld.",
     "Für Visionäre — aber nichts für 6 Wochen im Jahr. Ehrlich gesagt: zu viel Projekt."),
    # Sencelles - desc changed
    ("Sencelles — 13 Hektar Paradies; dein eigenes Landgut",
     None,
     "Dein eigenes Königreich — Herrenhaus mit Geschichte, Platz ohne Ende.",
     "So viel Platz, dass sich drei kleine Entdecker darin verlaufen können."),
    # Ses Salines - desc changed
    ("Ses Salines — Neubau Deluxe; einziehen und leben",
     None,
     "Koffer abstellen, ankommen, leben — nichts mehr tun müssen.",
     "Koffer abstellen, fertig. Aber weit vom Familienhaus und über Budget."),
    # Moscari - desc changed
    ("Moscari — Architekten-Traum; Design trifft Serra de Tramuntana",
     None,
     "Wohnen wie im Designmagazin — mitten in den Bergen.",
     "Aufwachen mit Bergblick, einschlafen mit Stille — aber weit weg vom Familienhaus."),
    # Campos Finca mit Lizenz - desc changed
    ("Campos — Finca mit Lizenz; 14 Hektar mallorquinischer Traum",
     None,
     "Landleben, das sich selbst trägt — hier arbeitet die Finca für dich.",
     "Vermieten wenn ihr nicht da seid, ankommen wenn ihr wollt — die Finca rechnet sich."),
    # Bunyola - desc changed
    ("Bunyola — Berglage mit Lizenz; Tramuntana vor der Tür",
     None,
     "Panorama, Ruhe, Ankommen — 20 Minuten zu allem, was zählt.",
     "20 Minuten zum Familienhaus, Berge vor der Tür, Gäste im Haus — alles gleichzeitig."),
]

with open('/Users/robin/.openclaw/workspace/mallorca-projekt/html/mallorca-ranking-v5.html', 'r', encoding='utf-8') as f:
    html = f.read()

count = 0
for old_title, new_title, old_desc, new_desc in patches:
    # Patch description
    if old_desc in html:
        html = html.replace(old_desc, new_desc)
        count += 1
        print(f"✅ desc: {old_desc[:50]}...")
    else:
        print(f"⚠️  desc not found: {old_desc[:50]}...")
    
    # Patch title if changed
    if new_title and old_title in html:
        html = html.replace(old_title, new_title)
        count += 1
        print(f"✅ title: {old_title[:50]}...")
    elif new_title:
        print(f"⚠️  title not found: {old_title[:50]}...")

with open('/Users/robin/.openclaw/workspace/mallorca-projekt/html/mallorca-ranking-v5.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n{'='*40}")
print(f"Patched {count} items total")
