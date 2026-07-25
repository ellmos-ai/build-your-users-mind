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
- [ ] **Close the learning loop automatically: scan, classify, file — triggered by the avatar.**
  Today the empirical basis is rebuilt by running the scripts *periodically and by hand*
  (`SKILL.md`: „rerun scripts periodically"). Nothing observes a conversation while it happens, so
  a rule the user states today may sit unrecorded until someone remembers to rerun the pipeline —
  and a rule that is never recorded is a rule the avatar cannot apply. Three parts:
  - **Trigger.** The avatar runs the scan when it starts working and, when it gets to it, again
    when it finishes. `corpus_extract.py --since` already supports incremental runs, so the state
    to keep is just „last processed timestamp". Deliberately *not* a per-prompt hook — that was
    rejected earlier for good reason; note the house rule on hooks (guard against repeated
    registration, make the action idempotent or rate-limited: an unguarded `atexit` hook once
    produced 240 backups in a single session).
  - **Classification without the swarm.** Stage 2 currently means ~52 agents and millions of
    tokens — far too heavy to fire per session. The user's proposal: a **small local model** that
    classifies incrementally, or later **Ollama on the Mac Studio**, which runs 24/7 and could
    process continuously in the background. That removes both the cost ceiling and the batch
    rhythm — no swarm needed, and the corpus stays close to current instead of lagging behind.
  - **What may be written back automatically, and what may not.** Extracted rules are
    **candidates**, not evidence, until the user confirms them; otherwise the model fills itself
    with its own misreadings and they harden with every round. Keep the existing provenance
    discipline: `pipeline_common.py` already strips hook and tool artifacts, and only genuine
    human-typed turns count. Watch one new trap the avatar workflow introduces — when an agent
    quotes the user inside its own message, that quote must not be counted a second time as an
    independent statement.
  *Motivation:* in the 2026-07-25 session the user stated three substantive rules in the space of
  an hour. All three had to be carried into the avatar files by hand, and one of them corrected a
  wrong assumption the avatar had been acting on minutes earlier.
  Requested by the user; same judging-hold conditions as above.
- [ ] **Session-end rating round as the standard close-out (0–10), and scoring that can represent
  it.** New user rule: whenever the avatar was used in a session, that session **ends** with a
  numbered list of every decision the avatar made (question · decision · stated confidence ·
  outcome); the user rates each one **0–10** (0 = worst possible decision, 10 = „exactly how I
  would have decided"), and the ratings feed back into the model. The workflow side is already
  written up in the avatar skill (`tom-lm` v1.2.0) — what is missing here is the tooling:
  - `MY-ACTIONS.txt` currently carries `<ts> <confidence> <reversible> <status> <title>
    <assumed-will>` with a categorical status (`confirmed`/`corrected`/`rejected`/`escalated`/
    `open`). A **score column** has to join it, in a way that keeps old lines parseable.
  - `scripts/score_predictions.py` reports hit rate per confidence tier. Extend it to report the
    **mean score per tier** — that is the calibration question that matters: does 🟢 actually
    score higher than 🟡? A tier that claims high confidence and scores like the middle tier is
    miscalibrated, and today nothing would reveal it.
  - **Why a scale rather than hit/miss:** the categorical vocabulary loses degree. A decision that
    was right in direction and only corrected in scope counts as `corrected` — indistinguishable
    from one that was simply wrong. Real case from 2026-07-25: the avatar's split of a release-gate
    document was accepted in principle and corrected only in its target location.
  Requested by the user; same judging-hold conditions as above.

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
