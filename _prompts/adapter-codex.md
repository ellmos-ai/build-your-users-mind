# Task — Source adapter for **Codex** (build-your-users-mind)

**For:** Codex/GPT (knows its own log format best)
**Repo root:** `<repo-root>` (this repository)
**Output file:** `scripts/adapters/codex_adapter.py` (new)
**Reference:** `scripts/corpus_extract.py` (Claude adapter) + `SOURCE-ADAPTERS.md` (contract)

## Task
Write a stage-0/1 extractor for **Codex CLI logs** that produces the same normalized JSONL row as
`corpus_extract.py`, so `chunk_corpus.py` / `aggregate_stats.py` run on it unchanged.

## Source (Codex)
- Path: `~/.codex/sessions/<YYYY>/<MM>/<DD>/rollout-*.jsonl` (+ `~/.codex/archived_sessions/`).
- Human-typed prompts: `type=="response_item"` & `payload.role=="user"` & `payload.content[].type=="input_text"`.
- **Exclude:** `<environment_context>`, `<user_instructions>`, injected `# AGENTS.md instructions`,
  tool outputs, pure system inserts.

## Contract (MANDATORY — identical to corpus_extract)
One JSON line per human prompt with fields:
`id, ts, source("codex"), project, branch, session, sender("human"), ptype(slash|ack|frei),
command, text, text_short, word_count, decision_score, followup_short, outcome_signal`.
- **Redaction before writing** (secrets/emails/IP/long digit runs) — reuse the logic from `corpus_extract.py` (import or mirror).
- **decision_score** via the same lexicon; **outcome_signal** from the next human turn in the same session.
- IDs are stable source/session/timestamp/content-bound hashes from the shared pipeline helpers; never
  renumber them by corpus order.
- CLI: `--root` (default `~/.codex/sessions`), `--since`, `--out`, `--output-name`,
  `--redaction-rules`, `--allow-empty`, and `--allow-partial`. Default behavior is fail-closed and
  must leave an existing output untouched on missing, empty, unreadable, or malformed input.
- Use `PYTHONIOENCODING=utf-8` for the console; persist UTF-8 atomically with private permissions.

## Acceptance criteria (will be checked)
1. Runs against `--root <codex-logs>`, writes valid `00_corpus.jsonl`.
2. Every line has all contract fields; `source=="codex"`.
3. No `<environment_context>`/`AGENTS.md` injections/tool outputs in `text`.
4. Redaction works (no `sk-…`, no plaintext email/IP).
5. Missing timestamps/schema drift fail closed unless the operator explicitly accepts partial input.
6. No hardcoded personal paths; generic argparse defaults.

Afterwards: short report (file path + sample line + number of prompts extracted on a test run).
