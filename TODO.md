# Development status: build-your-users-mind

**Audit date:** 2026-08-26<br>
**Target:** `ellmos-ai/build-your-users-mind` (public)<br>
**Version:** `1.1.0-dev`<br>
**Status:** development — deterministic pipeline hardened; semantic quality remains human-gated.

## Completed safety and reliability work

- [x] Claude, Codex, Gemini/Antigravity, and Kimi source adapters.
- [x] Codex internal-artifact filtering and `session_meta`/`turn_context` propagation.
- [x] Current common credential patterns plus operator-supplied custom redaction rules.
- [x] Stable source/session/timestamp/content-bound evidence IDs and multi-source merge.
- [x] Exact date/root/timestamp validation, atomic private writes, and explicit empty/partial overrides.
- [x] Fresh chunk manifests with managed stale-output cleanup and safe domain filenames.
- [x] Executable Stage-2 worker template, JSON schema, completeness/collision validator, and strict
  aggregation/verification exit codes.
- [x] Recursive Git exclusions for private corpora and filled avatar files.
- [x] Synthetic fixture suite and Ubuntu/Windows/macOS CI matrix for Python 3.10-3.13 with pinned Ruff.
- [x] Authorization, diagnosis, privacy, and irreversible/high-impact action boundaries documented.

## Open before a stable release

- [ ] Run and publish a new representative semantic inter-rater evaluation. The historical κ≈0.24
  result remains a warning; deterministic artifact/collision fixes do not prove label quality.
- [ ] Refresh localized documents from the authoritative 1.1 English contract. Until then each
  translation is explicitly marked as a historical, potentially stale draft.
- [ ] Perform an operator-owned end-to-end classification run on authorized private data and record
  only non-sensitive aggregate gate evidence.
- [ ] Decide a stable-release version and tag only after those semantic/manual gates pass.

## Optional improvements

- [x] Add a dependency-free inter-rater Cohen's-kappa helper. → `scripts/kappa.py` (CSV/JSONL → κ +
  confusion matrix; tested in `tests/test_kappa.py`).
- [x] Score the feedback-precognition loop. → `scripts/score_predictions.py` (hit rate overall + per
  🟢/🟡/🔴 tier + 🔴 escalation rate; tested in `tests/test_score_predictions.py`).
- [x] One-command offline demo of the deterministic build, feedback scoring, and tamper gate.
  → `examples/synthetic-demo/run_demo.py`.
- [x] Add synthetic source-schema fixtures for Claude, Codex, Gemini/agy, and Kimi adapters; extend them as upstream log formats evolve. *(verified 2026-08-13)*
- [x] Add an append-only decision-prediction event contract that separates recommendation, likely
  choice, explicit decision and execution authority; report top-1/Brier/log-loss independently from
  the 0–10 advice-process score, recovery events and explicit user bonuses. The v2 contract adds a
  closed, SHA-256-bound `decision_ref` and lossless validation/recovery/bonus projections.
- [x] Add a Secure-Mode-only text-avatar prototype with deterministic evidence retrieval, repeated
  redaction, privacy-minimized output, fail-closed novelty escalation and optional loopback Ollama.
- [ ] Run a private operator acceptance round against a real local model and authorized corpus;
  evaluate style resemblance separately from decision calibration and advice quality. Do not publish
  prompts, generated text or private evidence.
- [ ] Add a clarification/contradiction queue: competing evidence-backed user preferences remain
  visible until a human confirms, rejects, or scopes them; the classifier must not silently merge
  them into one rule.
- [ ] Add historical replay cases for changed preferences: evaluate which model version would have
  predicted the later response, preserve failures, and avoid training and evaluation on the same
  evidence slice.
- [ ] Emit a bounded decision-support packet with prediction, confidence, evidence anchors,
  counter-evidence, missing information, and escalation reason. It must never be interpreted as
  authorization for an irreversible action.

## STATUS — current gate

| Category | Status | Evidence |
|---|---|---|
| Repository hygiene | PASS | final gate, recursive private-data ignores |
| Python syntax/lint | PASS | compileall + Ruff |
| Deterministic behavior | PASS | synthetic unit/CLI suite |
| Manifest | PASS | `ellmos.module.v2` schema |
| Cross-platform automation | PENDING REMOTE | CI workflow added; GitHub run required after push |
| Semantic classifier quality | OPEN | new representative review not yet run |
| Stable release | NOT READY | development/public is honest; no stable tag |

Private corpora, generated profiles, and filled avatar files are intentionally excluded.
