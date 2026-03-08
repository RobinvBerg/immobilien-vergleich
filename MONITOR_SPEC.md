# Mallorca Market Monitor — Spec

## Ziel
Automatisierter Cron-Job der neue Objekte auf Mallorca-Immobilienportalen findet,
gegen unsere Gesamtliste prüft und gefilterte Neuzugänge meldet.

## Dateien
- `Mallorca_Markt_Gesamt.xlsx` — 18.990 Zeilen, Spalten: Titel, Quelle, URL, Preis, Zimmer, Grundstück, Wohnfläche, Ort, Gefunden am, Status
- `mallorca-kandidaten-v2.xlsx` — 333 kuratierte Top-Objekte
- `monitor_state.json` — State-File für Delta-Erkennung (letzte bekannte Objekte pro Quelle)
- `monitor_results.json` — Output: neue Objekte

## Suchparameter (aus mallorca-kandidaten-v2 Einstellungen)
- Min. Zimmer: 5
- Budget: 2.800.000 – 20.000.000 € (weit für Gesamtliste, 2.8-5.2M für Kandidaten)
- Dealbreaker: Flughafen >40min, Daia >70min, Ses Salines >45min, Andratx >60min

## Quellen & Methoden
1. **Balearic Properties** — requests, kein Block, ✅ bewährt
   URL: https://www.balearic-properties.com/property-for-sale/mallorca.html?page={n}
   
2. **Living Blue Mallorca** — requests direkt (manchmal ok)
   URL: https://www.livingblue-mallorca.com/de-de/immobilien?pag={n}
   Fallback: Decodo Site Unblocker

3. **Engel & Völkers** — requests mit Decodo Proxy
   URL: https://www.engelvoelkers.com/de/suche/?facets=rgn%3Amallorca%3B&_boolFilters=buy%3A&startIndex={n}&pageSize=24
   Proxy: http://sp1e6lma32:pxjc5K6_LBg3Is6vzo@gate.decodo.com:10001

4. **Idealista** — Apify Actor: memo23~idealista-scraper
   Token: apify_api_feD2KhARHjtuV9CrSwOReYgoePFSF44nsDL6
   Input: {"locationName":"Illes Balears","country":"es","propertyType":"homes","operation":"sale","minRooms":5,"maxPages":10}

5. **Kyero** — requests
   URL: https://www.kyero.com/en/property-for-sale/mallorca?min_beds=5&page={n}

6. **Luxury Estates Mallorca** — requests
   URL: https://www.luxury-estates-mallorca.com/en/properties?page={n}

## Duplikat-Erkennung
- URL-Vergleich gegen Mallorca_Markt_Gesamt.xlsx (Spalte C)
- Normalisierung: strip, lowercase, trailing slash entfernen
- Fuzzy-Match auf Titel + Preis falls URL nicht matchbar

## Output
- `monitor_results.json`: Liste neuer Objekte mit Titel, URL, Quelle, Preis, Zimmer, Wohnfläche, Grundstück, Ort
- Telegram-Nachricht via: openclaw message send --accountId zweiter-bot --target 803179451 --message "..."
- Excel-Anhang: neue Zeilen ans Gesamt-Excel appenden (optional, mit --update-excel flag)

## Cron-Aufruf
```
cd /Users/robin/.openclaw/workspace/mallorca-projekt && source venv/bin/activate && python3 monitor.py --notify telegram
```

## Anforderungen
1. Idempotent — kann mehrfach laufen, kein Duplikat-Spam
2. State-File trackt "letzte gesehene URLs" pro Quelle (JSON)
3. Fehler pro Quelle crashen nicht das Gesamt-Script (try/except pro Quelle)
4. Am Ende: kurze Zusammenfassung pro Quelle + Telegram-Message
5. --dry-run Flag: nur anzeigen, nicht speichern
6. --update-excel Flag: neue Objekte an Gesamt-Excel anhängen
7. Logging in monitor.log
