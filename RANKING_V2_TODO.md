# Mallorca Ranking — TODO für neue Version

## Scoring & Logik

- [ ] **Dealbreaker als harte Grenze** — Objekte die einen Dealbreaker überschreiten (z.B. Ses Salines > 45 Min) sollen komplett aus dem Ranking fallen, nicht nur schlechte Punkte bekommen
- [ ] Preiskorridor als aktiven Faktor einbauen (aktuell Gewicht 0 im Excel)

## Datenbereinigung
- [ ] **Makler-Namen vereinheitlichen** — E&V existiert als "Engel & Völkers", "EV Mallorca", "Minkner / EV", "Minkner", "EV / Lucas Fox", "Engel & Völkers (Exposé W-009Y23)" → alles auf "Engel & Völkers"

## Weitere Punkte
_(werden ergänzt)_

## Nr. 337 — Erreichbarkeit falsch (0 statt korrekt berechnet)
- Daia: 80 Min, Andratx: 75 Min → beide Dealbreaker
- Erreichbarkeit = 0 statt korrektem Negativwert
- Fix: Dealbreaker-Logik korrekt anwenden

## Nr. 346 — Son Reus de Randa genauer prüfen
- Außergewöhnliches Objekt, Wurzeln 16. Jh., Portal 1776
- Weinkeller, Olivenmühle, Qanat-System — historisch einzigartig
- Reno-Score 40% und Gästehäuser=0 nochmal prüfen
- Eventuell Charme höher ansetzen

## Post-Milestone: Living Blue URL-Problem
- Nr.147 (Santa Maria, 4.1M) + Nr.203 (Moscari, 3.95M) haben kaputte UUID-URLs
- Echte `/immobilie/ID` URLs fehlen — LB war während Session nicht erreichbar
- **Ursache:** Kein Dokument über funktionierenden LB-Scrape-Prozess existiert
- **Fix:** lb_full_scan.py nochmal laufen lassen wenn LB erreichbar → URLs nachtragen
- **KIRA-Learning:** Jede funktionierende Scraping-Methode sofort in SCRAPING_METHODS.md dokumentieren
