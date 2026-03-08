# Mallorca Ranking — Scoring-Erklärung

## Überblick

Das HTML zeigt 333 Mallorca-Immobilien in einer interaktiven Rangliste. Jedes Objekt hat einen **Score von 0–100**, der aus mehreren gewichteten Kriterien berechnet wurde. Die Scores sind **statisch** — sie wurden einmalig aus einer Excel-Datei berechnet und fest ins HTML eingebettet. Das HTML selbst rechnet nichts, es filtert und sortiert nur die vorberechneten Werte.

---

## Die Kriterien und ihre Gewichtung

| Kriterium | Gewicht | Beschreibung |
|---|---|---|
| Zimmer & Platz | 20% | Anzahl Schlafzimmer |
| Preis-Leistung €/m² | 15% | Preis pro m² bebautem Grundstück |
| Gästehaus | 15% | Kein / 1 / 2 Gästehäuser |
| Erreichbarkeit | 15% | Fahrzeit zu 4 Referenzpunkten |
| Grundstück/Garten | 10% | Grundstücksgröße in m² |
| Charme/Ästhetik | 10% | Subjektive Einschätzung 1–5 |
| Vermietlizenz | 5% | Ja/Nein (ETV-Lizenz) |
| Bewirtschaftung | 5% | Pflegeaufwand des Grundstücks 1–5 |
| Renovierung | 5% | Geschätzter Renovierungsbedarf 0–100% |
| Preis/Budget | 0% | Aktuell deaktiviert |

**Summe: 100%**

---

## Die Formeln im Detail

### Zimmer & Platz
```
≥ 10 Zimmer → 100 Punkte
≥  8 Zimmer →  85 Punkte
≥  6 Zimmer →  70 Punkte
≥  5 Zimmer →  55 Punkte
<  5 Zimmer →  30 Punkte
```

### Preis-Leistung €/m² (bebaut)
```
≤  3.000 €/m² → 100 Punkte
≤  5.000 €/m² →  80 Punkte
≤  7.000 €/m² →  60 Punkte
≤ 10.000 €/m² →  40 Punkte
> 10.000 €/m² →  20 Punkte
```

### Gästehaus
```
0 Gästehäuser →   0 Punkte
1 Gästehaus   →  70 Punkte
2 Gästehäuser → 100 Punkte
```

### Grundstück/Garten
```
≥ 100.000 m² → 100 Punkte
≥  50.000 m² →  80 Punkte
≥  20.000 m² →  60 Punkte
≥  10.000 m² →  40 Punkte
<  10.000 m² →  20 Punkte
```

### Charme/Ästhetik (subjektiv, 1–5)
```
Punkte = Charme-Wert × 20
→ Charme 5 = 100 Punkte, Charme 1 = 20 Punkte
```

### Renovierung (0–100%)
```
Punkte = max(0, 100 − Renovierungsbedarf)
→ Kein Renovierungsbedarf = 100 Punkte, 100% Renovierung = 0 Punkte
```

### Bewirtschaftung (1–5, 5 = pflegeleicht)
```
Punkte = max(0, 100 − (Wert × 20))
→ Wert 1 (aufwändig) = 80 Punkte, Wert 5 (pflegeleicht) = 0 Punkte
→ Hinweis: niedrigerer Bewirtschaftungsaufwand = höhere Punktzahl
```

### Vermietlizenz
```
Lizenz vorhanden → 100 Punkte
Keine Lizenz     →   0 Punkte
```

### Erreichbarkeit (zusammengesetzt)

Fahrzeit zu 4 Referenzpunkten, intern gewichtet:

| Referenzpunkt | Interne Gewichtung |
|---|---|
| Daia (Referenzort) | 30% |
| Flughafen Palma | 30% |
| Ses Salines | 30% |
| Andratx | 10% |

Für jeden Referenzpunkt gilt eine Drei-Stufen-Bewertung der Fahrzeit in Minuten:

| Referenzpunkt | Ideal (100 Pkt) | Akzeptabel (60 Pkt) | Deal-Breaker (0 Pkt) |
|---|---|---|---|
| Daia | ≤ 20 min | ≤ 40 min | > 70 min |
| Flughafen | ≤ 15 min | ≤ 25 min | > 40 min |
| Ses Salines | ≤ 15 min | ≤ 30 min | > 45 min |
| Andratx | ≤ 25 min | ≤ 40 min | > 60 min |

Zwischen den Schwellen wird linear interpoliert. Der Gesamtwert `erreich_score` ist die gewichtete Summe der vier Einzelwerte.

---

## Gesamtformel

```
Score = (S_zimmer × 0.20)
      + (S_eur_m2 × 0.15)
      + (S_gaestehaus × 0.15)
      + (S_erreichbarkeit × 0.15)
      + (S_grundstueck × 0.10)
      + (S_charme × 0.10)
      + (S_vermietlizenz × 0.05)
      + (S_bewirtschaftung × 0.05)
      + (S_renovierung × 0.05)
```

Ergebnis: Wert zwischen 0 und 100. Aktueller Spitzenwert: **82.9** (Nr. 208).

---

## Warum statisch?

Die Scores werden in einer Excel-Datei (`mallorca-kandidaten-v2.xlsx`) gepflegt. Das Sheet `Einstellungen` enthält die Gewichte — wer die Gewichte ändert, lässt ein Python-Skript laufen, das alle Scores neu berechnet und das HTML aktualisiert. Das HTML selbst enthält nur die fertigen Zahlen, keine Rechenlogik.

---

## Phase 2: Interaktives Ranking (geplant)

Das aktuelle HTML ist **Phase 1** — ein Grobfilter über alle 333 Objekte, um die Liste auf ca. 50 Top-Kandidaten einzugrenzen.

Sobald diese Shortlist steht, wird ein **neues HTML (Phase 2)** gebaut, das grundlegend anders funktioniert:

- Die **Rohwerte** jedes Objekts sind eingebettet (Zimmer, Grundstück, €/m², Erreichbarkeit etc.)
- Die **Gewichte sind keine festen Zahlen mehr**, sondern live einstellbare Schieberegler direkt im Browser
- Sobald ein Gewicht verschoben wird, **berechnet der Browser das komplette Ranking in Echtzeit neu** und sortiert die Karten sofort um
- Beispiel: Charme-Gewicht von 10% auf 25% erhöhen → Objekte mit Charme 5 springen nach oben, preisgünstige Rohbauten fallen zurück

Das ermöglicht es, dieselben ~50 Objekte aus verschiedenen Perspektiven zu bewerten — z.B. "was wäre das Ranking wenn mir Erreichbarkeit egal wäre?" oder "was wenn ich ausschließlich nach Gästehaus und Grundstück gewichte?" — ohne jedes Mal ein Skript laufen zu lassen.

---

## Das HTML

Das HTML bietet folgende Filter:
- **Ort** (Dropdown)
- **Makler** (Dropdown)  
- **Min. Zimmer** (Standard: 5+)
- **Min. Charme** (1–5)
- **Max. Preis** (Schieberegler)
- **Max. Renovierung** (Schieberegler)
- **Min. Erreichbarkeit** (Schieberegler, Standard: 40)

Sortierung: nach Score (beste zuerst), Rang, Preis auf-/absteigend, Erreichbarkeit.

Jede Karte zeigt: Bild, Anzeigename, Score, Rang, Preis, Grundstück, Zimmer, Erreichbarkeit zu allen 4 Referenzpunkten, Gästehaus-Badge, Vermietlizenz-Badge, Link zum Original-Inserat.
