> **Translation status (2026-07-15): historical pre-1.1 draft. The root English documents are authoritative; do not use this translation as the current operational or security contract.**

# TAXONOMY — 8 Prompt-Typen + Klassifikationsfelder

> Eigenständige Fassung (Modul ist self-contained). **Methodische Basis:** *Prompt-Archaeology*
> (L. Geiger) — die Methode, ein vollständiges Mensch-KI-Interaktionsprotokoll zu klassifizieren.

## Die 8 Prompt-Typen

| Typ | Code | Definition | Indikator |
|---|---|---|---|
| Startprompt | **SP** | Initiiert neue Analyse/Phase | kein Bezug auf Vorkontext |
| Nachfrage-Thema | **NT** | Vertieft Bestehendes | „und was ist mit …?" |
| Nachfrage-Methode | **NM** | Löst Methode/Tool/Review/Suche/Agent aus | Aufforderungsverb |
| Nachfrage-Steuerung | **NS** | Lenkt Reihenfolge/Priorität | „warte", „zuerst", „stopp" |
| Korrektur | **KO** | Berichtigt Fehler/Annahme | Negation, Gegenbeispiel |
| Bestätigung | **BE** | Validiert Zwischenstand | kurze Zustimmung |
| Richtungsänderung | **RA** | Fundamentaler Kurswechsel | stellt den Rahmen infrage |
| Meta-Prompt | **MP** | Über den Prozess/Dialog selbst | Prozessbegriff |

**Grenzfälle:** SP vs. NT (neu vs. anknüpfend) · NM vs. NS (Methode auslösen vs. nur umsortieren) ·
BE vs. KO („ja, aber …" ist meist KO) · RA seltener als KO, betrifft den ganzen Rahmen.

## Klassifikationsfelder (pro Prompt)

| Feld | Werte |
|---|---|
| `type_code` | SP/NT/NM/NS/KO/BE/RA/MP |
| `topic` | kurzes Thema (projektbezogen) |
| `is_decision` | true, wenn Entscheidung/Präferenz/Regel/Korrektur/Richtungswechsel |
| `decision_kind` | preference / correction / rule / direction_change / approval / rejection / process / none |
| `formulation_pattern` | charakteristische Formulierung des Users (Originalwendung, kurz) |
| `method_triggered` | WebSearch / WebFetch / Multi-Agent / Review / Cross-Model / Script / LaTeX / -- |
| `is_turning_point` | true/false |
| `outcome_signal` *(deterministisch, Stufe 0/1)* | praise / correction / reissue / none (aus dem nächsten User-Turn) |

## Bias-Indikatoren (Stufe 4)
- **Bestätigung:Korrektur (B:K)** — Disparität deutet Zustimmungs-Bias an; **stille Zustimmung ist
  unsichtbar** (wird nicht getippt) → Korrekturen überrepräsentiert.
- **Korrekturrate je Thema** — fehleranfällige Gegenstände.
- **Proaktiv:Reaktiv** — führt der User oder ist er KI-getrieben?
- **Richtungsänderungs-Rate** — epistemische Flexibilität.
