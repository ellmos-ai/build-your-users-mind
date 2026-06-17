# METHODOLOGY — how this avatar was built & how to read it

## Data basis
- Source(s): <agent logs, e.g. ~/.claude/projects> · time window: <since …> · N unique prompts: <…>

## Pipeline
0/1 deterministic (`scripts/corpus_extract.py`) → chunking (`chunk_corpus.py`) → stage-2 swarm
(classification, 8-type `TAXONOMY.md`) → stage 3/4 (`aggregate_stats.py`) → avatar files.

## Metrics
- Type distribution · B:K · proactive:reactive · turning points · decision_kind — see `STUDIE/04_statistik.md`.

## Bias & limits (always mention)
- **Silent approval is invisible** → corrections overrepresented, the avatar skews "critical".
- **Precognition fragility:** robust on recurring, fragile on novel situations → confidence tiers, 🔴 = escalate.
- **LLM-classifier bias:** without spot-check/Kappa it is coarser; evidence IDs come from synthesis → crosscheck.
- **Redaction:** secrets/emails/IP masked; user-specific health/tax data **must be closed before any sharing**.

## Updating
Rerun the scripts periodically (logs persist anyway) — **no per-prompt hook**. Fold runtime lessons
(file 4) back into `WHAT-<USER>-SAID.md`.
