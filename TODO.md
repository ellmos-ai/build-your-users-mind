# Development status: build-your-users-mind

**Audit date:** 2026-07-15<br>
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
- [x] Synthetic fixture suite and Windows/Linux CI with pinned Ruff.
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
- [ ] Add more synthetic source-schema fixtures as upstream log formats evolve.
- [ ] **Training wizard: build evidence by asking, not only by mining logs.** The pipeline derives
  its model from a user's *past* interaction logs, so a new operator starts with nothing — and an
  existing one has thin coverage wherever no comparable situation ever came up. A wizard would
  close that gap directly: present simulated decision cases (in the shape of a decision briefing —
  situation, options, trade-offs), let the user decide, and record the answer as first-class
  evidence with its own provenance. Design questions to settle first: where the case catalogue
  comes from (hand-written seed set, generated from the taxonomy, or mined from anonymized real
  situations), how wizard-derived evidence is weighted against log-derived evidence, and whether
  the wizard can be pointed at the avatar's current 🟡 areas to train exactly where confidence is
  weak instead of asking at random.
  *Motivation from live use (2026-07-25):* the avatar decided a release question at 🟡 solely
  because no directly comparable case existed in the corpus; the user's confirmation afterwards
  turned it into a rule. That feedback loop already works — it is just slow, because it waits for
  situations to occur by chance. The wizard would drive the same loop on purpose.
  Requested by the user; to be picked up once the Build-Week judging hold is lifted
  (noted on local branch `judging-hold/training-wizard`, 2026-07-25).

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
