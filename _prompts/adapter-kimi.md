# Task — Source adapter for **Kimi** (build-your-users-mind)

**For:** Kimi Code CLI (knows its own log format best)
**Repo root:** `<repo-root>` (this repository)
**Output file:** `scripts/adapters/kimi_adapter.py` (new)
**Reference:** `scripts/corpus_extract.py` (Claude adapter) + `SOURCE-ADAPTERS.md` (contract)

## Task
Write a stage-0/1 extractor for **Kimi CLI logs** that produces the same normalized JSONL row as
`corpus_extract.py`.

## Source (Kimi) — determine first
- Find where Kimi Code stores its own session/chat logs (its config/sessions folder; use `doctor` or config)
  and inspect the format (JSONL? SQLite? JSON?). Document it in the adapter docstring.
- Extract **human-typed** prompts only; exclude system/tool/context inserts.

## Contract (MANDATORY — identical to corpus_extract)
One JSON line per human prompt with fields:
`id, ts, source("kimi"), project, branch, session, sender("human"), ptype, command,
text, text_short, word_count, decision_score, followup_short, outcome_signal`.
- **Redaction before writing** — reuse the logic from `corpus_extract.py`.
- decision_score / outcome_signal as in the reference adapter; IDs `H{n:05d}`. `--root`, `--since`, `--out`. UTF-8.

## Acceptance criteria (will be checked)
1. Writes valid `00_corpus.jsonl`, `source=="kimi"`, all contract fields.
2. Human turns only; redaction works; no hardcoded personal paths.
3. Source format documented in the docstring.

Afterwards: short report (file path + detected Kimi log format + sample line + count).
