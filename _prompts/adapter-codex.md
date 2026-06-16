# Auftrag — Source-Adapter für **Codex** (build-your-users-mind)

**Für:** Codex/GPT (kennt sein eigenes Log-Format am besten)
**Repo-Root:** `C:\Users\User\OneDrive\.TOPICS\.AI\.MODULES\build-your-users-mind`
**Output-Datei:** `scripts/adapters/codex_adapter.py` (neu)
**Referenz:** `scripts/corpus_extract.py` (Claude-Adapter) + `SOURCE-ADAPTERS.md` (Vertrag)

## Aufgabe
Schreibe einen Stufe-0/1-Extraktor für **Codex-CLI-Logs**, der dieselbe normalisierte JSONL-Zeile
erzeugt wie `corpus_extract.py`, sodass `chunk_corpus.py` / `aggregate_stats.py` unverändert darauf laufen.

## Quelle (Codex)
- Pfad: `~/.codex/sessions/<YYYY>/<MM>/<DD>/rollout-*.jsonl` (+ `~/.codex/archived_sessions/`).
- Menschlich getippte Prompts: `type=="response_item"` & `payload.role=="user"` & `payload.content[].type=="input_text"`.
- **Ausschließen:** `<environment_context>`, `<user_instructions>`, Tool-Outputs, reine System-Einschübe.

## Vertrag (PFLICHT — identisch zu corpus_extract)
Pro getipptem Human-Prompt eine JSON-Zeile mit Feldern:
`id, ts, source("codex"), project, branch, session, sender("human"), ptype(slash|ack|frei),
command, text, text_short, word_count, decision_score, followup_short, outcome_signal`.
- **Redaction vor dem Schreiben** (Secrets/Mails/IP/lange Ziffern) — Logik aus `corpus_extract.py` wiederverwenden (importieren oder spiegeln).
- **decision_score** über dasselbe Lexikon; **outcome_signal** aus dem nächsten Human-Turn derselben Session.
- IDs chronologisch `H{n:05d}` global nach (ts, session).
- `--root` (Default `~/.codex/sessions`), `--since`, `--out ./STUDIE`. `PYTHONIOENCODING=utf-8`.

## Akzeptanzkriterien (werden geprüft)
1. Läuft mit `--root <codex-logs> --dry-run`-artig durch, schreibt valides `00_corpus.jsonl`.
2. Jede Zeile hat alle Vertragsfelder; `source=="codex"`.
3. Keine `<environment_context>`/Tool-Outputs im `text`.
4. Redaction greift (kein `sk-…`, keine Klartext-Mail/IP).
5. Keine hardcodierten Privatpfade; argparse-Defaults generisch.

Danach: kurze Meldung (Pfad der Datei + Beispielzeile + Anzahl extrahierter Prompts auf einem Testlauf).
