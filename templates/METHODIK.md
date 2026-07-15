# METHODOLOGY — how this avatar was built & how to read it

## Data basis
- Source(s): <agent logs, e.g. ~/.claude/projects> · time window: <since …> · N unique prompts: <…>

## Pipeline
0/1 deterministic extraction/redaction → optional `merge_corpora.py` → fresh chunk manifest →
contracted Stage-2 classification (`CLASSIFY-CHUNK.md` + JSON schema) → strict validator →
stage 3/4 (`aggregate_stats.py`) → avatar files.

## Metrics
- Type distribution · B:K · proactive:reactive · turning points · decision_kind — see `STUDIE/04_statistik.md`.

## Bias & limits (always mention)
- **Silent approval is invisible** → corrections overrepresented, the avatar skews "critical".
- **Precognition fragility:** robust on recurring, fragile on novel situations → confidence tiers, 🔴 = escalate.
- **LLM-classifier bias:** IDs are deterministic, but claims/labels are synthesized; resolve and
  cross-check load-bearing evidence during an intentional private review.
- **Redaction:** common secrets/emails/IP-like values are masked; custom reviewed rules are required for
  user-specific health/tax/legal/financial data before persistence or sharing.
- **Scope:** preference hypotheses are not diagnoses or authority grants; external, irreversible,
  novel, or high-impact actions require direct confirmation.

## Updating
Rerun the scripts periodically (logs persist anyway) — **no per-prompt hook**. Fold runtime lessons
(file 4) back into `WHAT-<USER>-SAID.md`.
