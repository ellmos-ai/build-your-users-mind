# Auftrag — Source-Adapter für **Kimi** (build-your-users-mind)

**Für:** Kimi Code CLI (kennt sein eigenes Log-Format am besten)
**Repo-Root:** `C:\Users\User\OneDrive\.TOPICS\.AI\.MODULES\build-your-users-mind`
**Output-Datei:** `scripts/adapters/kimi_adapter.py` (neu)
**Referenz:** `scripts/corpus_extract.py` (Claude-Adapter) + `SOURCE-ADAPTERS.md` (Vertrag)

## Aufgabe
Schreibe einen Stufe-0/1-Extraktor für **Kimi-CLI-Logs**, der dieselbe normalisierte JSONL-Zeile
erzeugt wie `corpus_extract.py`.

## Quelle (Kimi) — zuerst bestimmen
- Log-/Session-Speicherort von Kimi Code ermitteln (Home-Konfig/Sessions-Ordner) und das Format
  inspizieren (JSONL? SQLite? JSON?). Im Adapter-Docstring dokumentieren.
- Nur **menschlich getippte** Prompts extrahieren; System-/Tool-/Kontext-Einschübe ausschließen.

## Vertrag (PFLICHT — identisch zu corpus_extract)
Pro getipptem Human-Prompt eine JSON-Zeile mit Feldern:
`id, ts, source("kimi"), project, branch, session, sender("human"), ptype, command,
text, text_short, word_count, decision_score, followup_short, outcome_signal`.
- **Redaction vor dem Schreiben** — Logik aus `corpus_extract.py` wiederverwenden.
- decision_score / outcome_signal wie im Referenz-Adapter; IDs `H{n:05d}`. `--root`, `--since`, `--out`. UTF-8.

## Akzeptanzkriterien (werden geprüft)
1. Schreibt valides `00_corpus.jsonl`, `source=="kimi"`, alle Vertragsfelder.
2. Nur menschliche Turns; Redaction greift; keine Privatpfade hardcodiert.
3. Quellformat im Docstring dokumentiert.

Danach: kurze Meldung (Dateipfad + ermitteltes Kimi-Logformat + Beispielzeile + Anzahl).
