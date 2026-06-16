---
name: schwarm-operationen
version: 1.0.0
type: protocol
author: Lukas Geiger
created: 2026-03-12
updated: 2026-03-12
description: >
  5 Schwarm-Muster fuer KI-Agenten: Epstein-Methode, Hierarchie-Schwarm,
  Stigmergy, Konsensus und Spezialist-Schwarm. Koordinationsstrategien
  fuer Multi-Agent-Systeme.

standalone: true
anthropic_compatible: true
bach_compatible: false
bach_origin: true

category: dev
tags: [schwarm, multi-agent, koordination, parallel, architektur]
language: de
status: active

dependencies:
  tools: []
  services: []
  protocols: []
  python: []

provenance:
  origin: "bach"
  origin_path: "system/skills/workflows/schwarm-operationen.md"
  origin_version: "1.0.0"
  origin_repo: "github.com/ellmos-ai/bach"
  last_sync_from_origin: "2026-03-12"
  last_sync_to_origin: null
  local_changes_since_sync: true
---

# Schwarm-Operationen: 5 Muster fuer Multi-Agent-Systeme

Koordinationsstrategien fuer KI-Agenten die parallel oder hierarchisch
zusammenarbeiten. Von einfacher Aufgabenverteilung bis zu emergenten
Schwarm-Mustern.

---

## Uebersicht der 5 Muster

| # | Muster | Agenten | Koordination | Best fuer |
|---|--------|---------|-------------|-----------|
| 1 | Epstein-Methode | 3-5 | Zentral (Orchestrator) | Wissensaufbau, Recherche |
| 2 | Hierarchie-Schwarm | 5-20 | Baum-Struktur | Grosse Projekte, Refactoring |
| 3 | Stigmergy | 3-10 | Dezentral (Umgebung) | Exploration, Daten-Crawling |
| 4 | Konsensus | 3-7 | Peer-to-Peer | Entscheidungen, Review |
| 5 | Spezialist-Schwarm | 3-8 | Hub-and-Spoke | Domain-uebergreifend |

---

## Muster 1: Epstein-Methode

### Prinzip

Ein Orchestrator verteilt Teilaufgaben an spezialisierte Worker.
Ergebnisse werden gesammelt, dedupliziert und zu einem Gesamtbild zusammengefuehrt.

### Ablauf

```
[Orchestrator]
     │
     ├── Worker 1: Teilfrage A → Ergebnis A
     ├── Worker 2: Teilfrage B → Ergebnis B
     └── Worker 3: Teilfrage C → Ergebnis C
              │
              ▼
     [Orchestrator: Synthese]
              │
              ▼
     [Gesamtergebnis]
```

### Rollen

| Rolle | Aufgabe |
|-------|---------|
| **Orchestrator** | Zerteilt Aufgabe, verteilt an Worker, synthetisiert Ergebnisse |
| **Worker** | Bearbeitet Teilaufgabe, liefert strukturiertes Ergebnis |
| **Validator** (optional) | Prueft Ergebnisse auf Qualitaet/Konsistenz |

### Implementierung

1. **Aufgabe analysieren:** Was sind die unabhaengigen Teilfragen?
2. **Worker spawnen:** Pro Teilfrage einen Agenten starten
3. **Ergebnisse sammeln:** Warten bis alle fertig, Timeout setzen
4. **Synthese:** Ergebnisse zusammenfuehren, Widersprueche aufloesen
5. **Qualitaetskontrolle:** Ist das Gesamtergebnis konsistent?

### Wann einsetzen

- Recherche-Aufgaben mit mehreren unabhaengigen Aspekten
- Wissensaufbau ueber groessere Themengebiete
- Datenextraktion aus mehreren Quellen
- Analyse mit verschiedenen Perspektiven

### Grenzen

- Orchestrator ist Single Point of Failure
- Overhead bei weniger als 3 Teilaufgaben
- Abhaengige Teilaufgaben schwer parallelisierbar

---

## Muster 2: Hierarchie-Schwarm

### Prinzip

Baumartige Struktur mit Boss-Knoten die Sub-Teams koordinieren.
Jeder Boss kennt nur seine direkten Untergebenen.

### Ablauf

```
            [Projekt-Boss]
            /            \
    [Team-Lead A]    [Team-Lead B]
    /    |    \        /       \
 [W1]  [W2]  [W3]  [W4]     [W5]
```

### Rollen

| Ebene | Rolle | Aufgabe |
|-------|-------|---------|
| 0 | Projekt-Boss | Gesamtplanung, Endergebnis |
| 1 | Team-Lead | Teilbereich koordinieren |
| 2 | Worker | Einzelaufgabe ausfuehren |

### Implementierung

1. **Aufgabe dekomponieren:** In 2-4 grosse Teilbereiche zerlegen
2. **Team-Leads erstellen:** Pro Teilbereich einen koordinierenden Agenten
3. **Worker zuweisen:** Team-Leads erstellen eigene Unteraufgaben
4. **Bottom-up aggregieren:** Ergebnisse fliessen von Worker → Lead → Boss

### Wann einsetzen

- Grosse Projekte (>10 Dateien betroffen)
- Refactoring ueber mehrere Module
- Dokumentation ganzer Systeme
- Aufgaben mit natuerlicher Hierarchie

### Grenzen

- Kommunikations-Overhead zwischen Ebenen
- Gesamtbild kann auf unteren Ebenen verloren gehen
- Mindestens 5 Agenten noetig fuer Vorteil

---

## Muster 3: Stigmergy (Umgebungs-Koordination)

### Prinzip

Agenten kommunizieren NICHT direkt miteinander, sondern ueber die
Umgebung (shared state). Wie Ameisen die Pheromone hinterlassen.

### Ablauf

```
[Agent A] ──schreibt──→ [Shared State] ←──liest── [Agent B]
                              ↑
[Agent C] ──schreibt──────────┘
```

### Shared State Mechanismen

| Mechanismus | Beschreibung | Beispiel |
|-------------|-------------|----------|
| **Dateisystem** | Agenten lesen/schreiben Dateien | Ergebnis-JSONs in shared Ordner |
| **Datenbank** | Gemeinsame DB-Tabelle | Status-Eintraege, Queue |
| **Message Queue** | Pub/Sub Pattern | Redis, RabbitMQ |
| **Marker-Dateien** | Lock/Done Signale | `.done`, `.lock` Dateien |

### Implementierung

1. **Shared Ordner definieren:** Wo legen Agenten Ergebnisse ab?
2. **Namenskonvention:** Wie werden Dateien benannt? (z.B. `agent_A_result_001.json`)
3. **Status-Marker:** Wie signalisiert ein Agent "fertig"? (z.B. `.done` Datei)
4. **Konflikt-Vermeidung:** Jeder Agent schreibt nur eigene Dateien
5. **Aggregator:** Ein Agent sammelt alle Ergebnisse am Ende

### Wann einsetzen

- Exploration (Web-Crawling, Code-Analyse)
- Lose gekoppelte Aufgaben
- Wenn direkte Agent-Kommunikation nicht moeglich
- Robustheit wichtiger als Geschwindigkeit

### Grenzen

- Keine Echtzeit-Koordination
- Konflikte bei gleichzeitigem Schreiben
- Debugging schwieriger (verteilter State)

---

## Muster 4: Konsensus

### Prinzip

Mehrere Agenten bearbeiten die GLEICHE Aufgabe unabhaengig.
Ergebnisse werden verglichen, Konsensus wird gebildet.

### Ablauf

```
[Aufgabe] ──→ [Agent A] ──→ Antwort A ──┐
          ──→ [Agent B] ──→ Antwort B ──├──→ [Konsensus-Bildung]
          ──→ [Agent C] ──→ Antwort C ──┘         │
                                                   ▼
                                          [Beste Antwort]
```

### Konsensus-Strategien

| Strategie | Beschreibung | Wann |
|-----------|-------------|------|
| **Mehrheitsvotum** | Haeufigste Antwort gewinnt | Faktenfragen |
| **Best-of-N** | Qualitaets-Score, beste gewinnt | Kreative Aufgaben |
| **Synthese** | Elemente aller Antworten kombinieren | Komplexe Analysen |
| **Debate** | Agenten kritisieren sich gegenseitig | Entscheidungen |

### Implementierung

1. **Gleiche Aufgabe an N Agenten:** Identischer Prompt, verschiedene Seeds/Temperaturen
2. **Ergebnisse sammeln:** Alle N Antworten speichern
3. **Vergleichen:** Uebereinstimmungen und Abweichungen identifizieren
4. **Konsensus bilden:** Je nach Strategie (Voting, Synthese, Debate)
5. **Konfidenz bestimmen:** Wie stark ist der Konsensus? (3/3 = hoch, 2/3 = mittel)

### Wann einsetzen

- Kritische Entscheidungen (Security Review, Architektur)
- Code Review (mehrere Perspektiven)
- Fakten-Verifikation
- Wenn ein einzelner Agent unzuverlaessig sein koennte

### Grenzen

- N-facher Kosten-/Zeit-Aufwand
- Alle Agenten koennen den gleichen Fehler machen
- Konsensus ≠ Korrektheit

---

## Muster 5: Spezialist-Schwarm

### Prinzip

Jeder Agent ist Experte fuer eine Domain. Ein Koordinator routet
Aufgaben an den passenden Spezialisten.

### Ablauf

```
[Koordinator]
     │
     ├── [Domain-Expert A]  — z.B. Frontend/UI
     ├── [Domain-Expert B]  — z.B. Backend/API
     ├── [Domain-Expert C]  — z.B. Datenbank/Persistence
     └── [Domain-Expert D]  — z.B. Security/Auth
```

### Rollen

| Rolle | System-Prompt | Wissen |
|-------|--------------|--------|
| **Koordinator** | Routing-Logik, kennt alle Domains | Ueberblick ueber alle Bereiche |
| **Domain-Expert A** | Spezialisiert auf Domain A | Tiefes Wissen, eigene Tools/Prompts |
| **Domain-Expert B** | Spezialisiert auf Domain B | Tiefes Wissen, eigene Tools/Prompts |
| **Domain-Expert C** | Spezialisiert auf Domain C | Tiefes Wissen, eigene Tools/Prompts |

### Implementierung

1. **Domains definieren:** Welche Spezialisierungen braucht das Projekt?
2. **Experten erstellen:** Pro Domain einen Agenten mit spezialisiertem System-Prompt
3. **Routing-Logik:** Koordinator entscheidet anhand der Aufgabe welcher Experte zustaendig ist
4. **Handoffs:** Wenn eine Aufgabe mehrere Domains betrifft, sequentielles Routing
5. **Integration:** Koordinator fuegt Teilergebnisse zusammen

### Wann einsetzen

- Domain-uebergreifende Projekte
- Wenn verschiedene Expertise-Bereiche noetig sind
- Support-Systeme mit verschiedenen Themenbereichen
- Komplexe Systeme mit klar abgrenzbaren Modulen

### Grenzen

- Routing-Fehler (falsche Domain zugewiesen)
- Querschnitts-Aufgaben schwer zuzuordnen
- Overhead bei wenigen Domains

---

## Vergleichstabelle

| Kriterium | Epstein | Hierarchie | Stigmergy | Konsensus | Spezialist |
|-----------|---------|-----------|-----------|-----------|------------|
| **Komplexitaet** | Niedrig | Hoch | Mittel | Niedrig | Mittel |
| **Min. Agenten** | 3 | 5 | 3 | 3 | 3 |
| **Koordination** | Zentral | Baum | Dezentral | Peer | Hub-Spoke |
| **Fehlertoleranz** | Niedrig | Mittel | Hoch | Hoch | Mittel |
| **Skalierbarkeit** | Mittel | Hoch | Hoch | Niedrig | Mittel |
| **Overhead** | Niedrig | Hoch | Niedrig | Hoch (N×) | Mittel |
| **Best fuer** | Recherche | Grossprojekte | Exploration | Review | Multi-Domain |

---

## Allgemeine Prinzipien

### 1. Aufgaben-Zerlegung

- Aufgaben muessen **unabhaengig** sein fuer Parallelisierung
- Abhaengige Aufgaben **sequentiell** oder mit expliziten Waits
- Granularitaet: Nicht zu fein (Overhead) und nicht zu grob (kein Vorteil)

### 2. Ergebnis-Aggregation

- **Format festlegen:** JSON, Markdown, strukturierte Dicts
- **Deduplizierung:** Gleiche Informationen aus verschiedenen Quellen zusammenfuehren
- **Konflikt-Aufloesung:** Was tun bei widersprüchlichen Ergebnissen?

### 3. Fehlerbehandlung

- **Timeout:** Jeder Agent braucht ein Timeout (empfohlen: 5-10 min)
- **Retry:** Bei transientem Fehler einmal wiederholen
- **Fallback:** Wenn ein Agent ausfaellt, kann der Orchestrator uebernehmen?
- **Partial Results:** Teilergebnisse sind besser als keine Ergebnisse

### 4. Kommunikation

- **Klar definierte Schnittstellen:** Input/Output Format pro Agent
- **Minimale Kopplung:** Agenten sollen moeglichst wenig voneinander wissen
- **Idempotenz:** Gleiche Eingabe → Gleiche Ausgabe (fuer Retry-Safety)

### 5. Monitoring

- **Status-Tracking:** Welcher Agent ist wo? (started, running, done, failed)
- **Fortschritts-Messung:** Wie viel ist schon erledigt?
- **Logging:** Jeder Agent loggt seine Aktionen fuer Debugging

---

## Entscheidungshilfe

```
Welches Muster brauche ich?

1. Aufgabe zerlegbar in unabhaengige Teile?
   JA → Wie viele Teile?
        3-5  → Epstein-Methode
        5-20 → Hierarchie-Schwarm
   NEIN ↓

2. Gleiche Aufgabe, mehrere Perspektiven?
   JA → Konsensus
   NEIN ↓

3. Verschiedene Expertise-Bereiche noetig?
   JA → Spezialist-Schwarm
   NEIN ↓

4. Lose gekoppelte Exploration?
   JA → Stigmergy
   NEIN ↓

5. Einzelner Agent reicht vermutlich.
```
