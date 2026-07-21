# Synthetic demo — the whole pipeline, offline, in one command

Runs the complete build-your-users-mind pipeline on **synthetic** data with **no LLM
and no network**, then shows the hard validation gate rejecting a tampered result.

```bash
python examples/synthetic-demo/run_demo.py
```

Everything is fictional: an invented user "Sam Rivera" and 23 hand-written prompts,
including a **planted fake secret** so you can watch redaction happen. No real or
private interaction logs are read or produced.

## What it does

```
extract -> merge -> chunk -> classify -> validate -> aggregate -> tamper test
```

| Stage | Script | What you see |
|---|---|---|
| generate | `generate_fixtures.py` | writes synthetic Claude-format logs + an answer key |
| extract | `scripts/corpus_extract.py` | 23 human-typed prompts, **4 redactions** (the planted secret) |
| merge | `scripts/merge_corpora.py` | consolidates source corpora into `00_corpus.jsonl` |
| chunk | `scripts/chunk_corpus.py` | dedupe + a manifest bound to the corpus **SHA-256** |
| classify | `classify_worker.py` | **offline** — labels come from the answer key, so no model is needed |
| validate | `scripts/validate_classifications.py` | hard gate: schema, completeness, collisions → **PASS** |
| aggregate | `scripts/aggregate_stats.py` | Stage-4 stats (`N=23`, `B:K`, decisions, …) |
| tamper | (in `run_demo.py`) | corrupts one classification → the gate refuses with **exit 2** |

## Honesty notes

- The classifications are **pre-authored fixtures**, not a measured accuracy claim.
  On real data this stage is an LLM classification swarm; the module's semantic
  quality remains human-reviewed by design (see the κ≈0.24 note in `TODO.md`).
- Redaction runs **before** classification, so the classifier only ever sees the
  redacted text (`[REDACTED_APIKEY]`, `[REDACTED_EMAIL]`).

## Output

Written to `examples/synthetic-demo/_run/` (git-ignored). Inspect after a run:

- `_run/STUDIE/00_corpus.jsonl` — the extracted, redacted corpus
- `_run/STUDIE/_chunks/manifest.json` — SHA-256-bound chunk manifest
- `_run/STUDIE/04_statistik.md` — the Stage-4 aggregate
