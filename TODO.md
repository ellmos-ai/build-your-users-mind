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
- [x] Synthetic fixture suite and Ubuntu/Windows/macOS CI matrix for Python 3.10-3.13 with a pinned
  Ruff *rule set* (`[tool.ruff.lint] select` in `pyproject.toml`). The Ruff *version* installed in CI
  is deliberately unpinned; the fixed rule set is what keeps a new release from turning the build red.
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

## Maintenance follow-ups (surface after-care, 2026-09-03)

- [ ] Cut a first real release. The version badge links to `/releases`, which is empty: the only tags
  are `build-week-2026` and `build-week-2026-submitted`, both event markers rather than releases.
  Either tag `v1.1.0-dev` (or the first stable version) or point the badge somewhere that exists.
- [ ] Delete the merged leftover branches `post-competition-quarantine/2026-08-24`,
  `post-competition-quarantine/2026-08-25` and `post-hold/integration-20260826`. Verified merged into
  `master` on 2026-09-03. The two older ones, `post-competition-quarantine/2026-08-01` and `/2026-08-07`,
  are **not** merged, but their content is superseded (badge/`llms.txt` work redone in the 08-24/08-25
  branches; 08-01 is a banner change plus its own revert, net zero) — confirm once, then delete.
- [ ] Refresh the five localized `RELEASE_GATE.md` files or retire them. They are 2026-06-17 snapshots
  claiming "10 PASS → READY FOR PUBLIC RELEASE" and calling the repository "initially private", while
  the authoritative English gate says the opposite: public development state, not a stable release.
  The translation banner marks them historical, but a reader who only reads their own language sees a
  release verdict this project does not make.
- [ ] Decide what `docs/SIMULATION-CHANNEL-KONZEPT.md` should be. It is the only German-only document
  in an English-primary repository, and its filename is German too. Either translate it and rename it
  to `SIMULATION-CHANNEL-CONCEPT.md`, or move it out of `docs/` as an operator note.

## STATUS — current gate

| Category | Status | Evidence |
|---|---|---|
| Repository hygiene | PASS | final gate, recursive private-data ignores |
| Python syntax/lint | PASS | compileall + Ruff |
| Deterministic behavior | PASS | synthetic unit/CLI suite |
| Manifest | PASS | `ellmos.module.v2` schema |
| Cross-platform automation | PASS | CI green on `master` since 2026-08-26 (run `32994278714`, 12 jobs) |
| Semantic classifier quality | OPEN | new representative review not yet run |
| Stable release | NOT READY | development/public is honest; no stable tag |

Private corpora, generated profiles, and filled avatar files are intentionally excluded.
