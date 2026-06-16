# Auftrag — Source-Adapter für **Gemini / agy (antigravity)** (build-your-users-mind)

**Für:** agy/Gemini (kennt sein eigenes Log-Format am besten)
**Repo-Root:** `C:\Users\User\OneDrive\.TOPICS\.AI\.MODULES\build-your-users-mind`
**Output-Datei (direkt schreiben, --add-dir):** `scripts/adapters/gemini_adapter.py` (neu)
**Referenz:** `scripts/corpus_extract.py` (Claude-Adapter) + `SOURCE-ADAPTERS.md` (Vertrag)

## Aufgabe
Schreibe einen Stufe-0/1-Extraktor für **antigravity/Gemini-Logs**, der dieselbe normalisierte
JSONL-Zeile erzeugt wie `corpus_extract.py`.

## Quelle (Gemini/antigravity)
- Pfad: `~/.gemini/antigravity/conversations/<uuid>.db` (SQLite; WAL beachten → ggf. `PRAGMA wal_checkpoint`).
- Tabelle `steps` enthält den Verlauf — **Spalten beim Bau inspizieren** (`SELECT name FROM pragma_table_info('steps')`)
  und die User-Turns identifizieren (menschlich getippte Eingaben, keine Modell-/Tool-Schritte).

## Vertrag (PFLICHT — identisch zu corpus_extract)
Pro getipptem Human-Prompt eine JSON-Zeile mit Feldern:
`id, ts, source("gemini"), project, branch(""), session(<uuid>), sender("human"), ptype, command,
text, text_short, word_count, decision_score, followup_short, outcome_signal`.
- **Redaction vor dem Schreiben** (Secrets/Mails/IP/Ziffern) — Logik aus `corpus_extract.py` wiederverwenden.
- decision_score / outcome_signal wie im Referenz-Adapter.
- IDs chronologisch `H{n:05d}`. `--root` (Default conversations-Ordner), `--since`, `--out ./STUDIE`. UTF-8/CJK sauber.

## Akzeptanzkriterien (werden geprüft)
1. Liest die SQLite-DBs, schreibt valides `00_corpus.jsonl`, `source=="gemini"`.
2. Alle Vertragsfelder vorhanden; nur menschliche Turns, keine Modell-/Tool-Schritte.
3. Redaction greift; echte Umlaute/CJK erhalten.
4. Keine hardcodierten Privatpfade; generische argparse-Defaults.

Danach: kurze Meldung (Dateipfad + Tabellen-/Spalten-Mapping das du gefunden hast + Beispielzeile + Anzahl).
