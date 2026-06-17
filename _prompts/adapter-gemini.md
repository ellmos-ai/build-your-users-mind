# Task — Source adapter for **Gemini / agy (antigravity)** (build-your-users-mind)

**For:** agy/Gemini (knows its own log format best)
**Repo root:** `<repo-root>` (write files directly, e.g. via `--add-dir`)
**Output file:** `scripts/adapters/gemini_adapter.py` (new)
**Reference:** `scripts/corpus_extract.py` (Claude adapter) + `SOURCE-ADAPTERS.md` (contract)

## Task
Write a stage-0/1 extractor for **antigravity/Gemini logs** that produces the same normalized JSONL row
as `corpus_extract.py`.

## Source (Gemini/antigravity)
- Path: `~/.gemini/antigravity/conversations/<uuid>.db` (SQLite; mind WAL → optionally `PRAGMA wal_checkpoint`).
- Inspect the schema of a sample DB (table `steps` and others) and find where human-typed user input is stored
  (human turns only, not model/tool steps).

## Contract (MANDATORY — identical to corpus_extract)
One JSON line per human prompt with fields:
`id, ts, source("gemini"), project, branch(""), session(<uuid>), sender("human"), ptype, command,
text, text_short, word_count, decision_score, followup_short, outcome_signal`.
- **Redaction before writing** — reuse the logic from `corpus_extract.py`.
- decision_score / outcome_signal as in the reference adapter.
- IDs chronological `H{n:05d}`. `--root` (default conversations folder), `--since`, `--out ./STUDIE`. UTF-8/CJK clean.

## Acceptance criteria (will be checked)
1. Reads the SQLite DBs, writes valid `00_corpus.jsonl`, `source=="gemini"`.
2. All contract fields present; human turns only, no model/tool steps.
3. Redaction works; genuine umlauts/CJK preserved.
4. No hardcoded personal paths; generic argparse defaults.

Afterwards: short report (file path + the table/column mapping you found + sample line + count).
