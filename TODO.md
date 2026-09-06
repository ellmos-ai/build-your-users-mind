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

## Incubation: temporal attention and decision trajectory

**Hold status:** This plan was written during the Build-Week judging hold, when it was local-only.
The hold has since ended (tag `build-week-2026-submitted`; post-hold integration merged through
PR #5). The items below are therefore open planning work under the normal contribution rules —
no publication embargo applies to the plan itself. The privacy constraints in the items stay in
force: they concern generated ledger data, not this document.

### P0 — model and contracts

- [ ] Define three explicit, configurable analytical horizons without presenting defaults as
  psychological facts: **current attention** (provisional default: 14 days), **recent tendency**
  (30 days as a weaker comparison window), and **durable pattern** (requires repeated or stable
  evidence across separated windows, not merely old age). Keep a fourth, distinct artifact: the
  complete **lifetime decision history** containing all accepted decision events without claiming
  that each event is still current or durable. Record exact windows and coverage in every result.
- [ ] Separate signal kinds that the current flat model conflates: explicit priority/importance,
  current attention or repeated inquiry, actively enforced requirement/quality gate, open direct
  request/goal, preference/rule, correction, approval/rejection, and direction change. A question
  may raise engagement only. A correction may raise enforcement only when its content explicitly
  states/restates a requirement or links a violation to an already evidenced requirement; otherwise
  it is correction/engagement only. Neither establishes project importance or a durable preference
  by itself.
- [x] Specify an event-sourced decision-trajectory schema with stable decision/event ID, scope,
  `observed_at`, optional `effective_at`, project/topic, decision kind, evidence IDs, confidence,
  effective status, change state (introduced/reaffirmed/softened/superseded/revoked), optional
  `supersedes` links, and provenance. Preserve older decisions as history; a newer explicit
  conflicting decision may replace their current effect but must not erase the earlier state.
  Contradictory explicit evidence without an unambiguous supersession relation must remain an
  unresolved conflict with a deterministic conservative tie-break, never a silently guessed winner.
- [ ] Specify precedence independently for **focus** and **authority**: project `DECISIONS.md` and
  current explicit decisions govern the project; attention affects prioritization only and never
  grants permission; durable patterns apply only where no newer explicit contradiction exists;
  low-confidence inference must not be converted into a user fact.
- [ ] Add a deterministic temporal aggregation stage over redacted corpus/classification rows. Its
  attention score must expose separate factors for explicit priority, recency, manual-session and
  genuine follow-up density, and open direct work. Weights must be configurable, versioned, and
  reported; automation/scheduler/system/tool/subagent artifacts and automation frequency are not
  attention evidence.
- [ ] Define private generated outputs for a human-readable current-attention view, a durable view,
  and a machine-readable decision trajectory/consumer summary. Store only aggregate factors and
  evidence IDs in summaries; never copy raw prompts, diagnoses, secrets, or sensitive content into
  shared logs. Treat project/topic names and aggregates as potentially sensitive too: use minimal
  pseudonymous local IDs in consumer output, explicit consumer/project allowlists, local access
  controls, bounded retention, and no personal/therapeutic/medical topic export unless the operator
  explicitly maps it to a named project automation. Extend recursive `.gitignore` rules before
  generating any real output.
- [ ] Extend the avatar templates and runtime loop so agents compare current versus durable evidence,
  report current project attention separately from currently enforced workflow/quality demands,
  show a change/continuity explanation, and expose uncertainty, decay, contradictory evidence, and
  last-updated time. Keep the existing feedback-precognition and high-impact confirmation boundary.
- [ ] Define a minimal versioned consumer contract for local schedulers such as
  `token-economy-maintainer`: project identifier, horizon, attention score, protection class,
  aggregate factors, confidence, evidence count, timestamp, and cursor — no raw prompt text. Add a
  separate evidence-backed constraints channel for currently enforced workflow/quality demands
  such as minimum reliable model/effort or mandatory review; it constrains an already authorized
  workflow and never grants new authority. The consumer must fail closed on stale, malformed, or
  low-confidence state.

### P1 — implementation, evaluation, and local adoption

- [ ] Add synthetic fixtures and deterministic tests for recency decay, stable long-term patterns,
  changing interests, explicit reprioritization, superseded decisions, contradictory horizons,
  ambiguous project attribution, duplicate prompts, and missing/stale source windows.
- [ ] Add explicit negative-contract tests: attention never grants authority; many questions or
  corrections alone never establish importance, enforcement, or durable preference; automation/
  system/tool/subagent artifacts remain excluded; unresolved explicit conflicts remain visible;
  and stale, malformed, disallowed, or low-confidence consumer state leaves the user's baseline
  unchanged.
- [ ] Prove backward compatibility: existing static corpora, classifiers, aggregate reports, avatar
  templates, and prediction scoring must continue to work when temporal outputs are not requested.
- [ ] Add an incremental cursor/checkpoint design so frequent local refreshes scan only new sessions
  while periodically recomputing bounded windows; interrupted runs must preserve the last valid
  result atomically.
- [ ] Run a representative, operator-owned private evaluation of project-priority precision and
  false-positive rate. Specifically test the bias that frequent corrections, difficult projects,
  or many questions can look important even when they are merely problematic. Publish no raw data;
  retain only non-sensitive local aggregate gate evidence.
- [ ] Update authoritative English `SKILL.md`, `README.md`, `TAXONOMY.md`, `METHODIK.md`, templates,
  schema documentation, and `llms.txt`; mark translations stale until regenerated after the local
  contract stabilizes.
- [ ] After local gates pass, integrate the summary into the private TOM-lm instance and the local
  `token-economy-maintainer`, then verify that currently important projects remain covered in saving
  modes while cold/redundant work is reduced first. Verify separately that valid minimum-model,
  thinking, and mandatory-review constraints are not violated by saving mode. Keep the integration
  local and committed only.
- [x] Lift the embargo only after an explicit operator decision. Done: the Build-Week judging hold
  ended with the submission tag `build-week-2026-submitted`, the local pre-push guard is gone, and
  remote CI runs again. Re-auditing private-data exclusions before publishing any *generated*
  ledger output remains required and is covered by the P0 privacy item above.

## Open before a stable release

- [ ] Run and publish a new representative semantic inter-rater evaluation. The historical κ≈0.24
  result remains a warning; deterministic artifact/collision fixes do not prove label quality.
- [ ] Refresh localized documents from the authoritative 1.1 English contract. Until then each
  translation is explicitly marked as a historical, potentially stale draft.
- [ ] Perform an operator-owned end-to-end classification run on authorized private data and record
  only non-sensitive aggregate gate evidence.
- [ ] Decide a stable-release version and tag only after those semantic/manual gates pass.
- [ ] Propagate the new USER.md (0.5) declared-preferences layer into `SKILL.md` and the localized
  documents (de/es/ja/ru/zh) once the Build-Week judging hold is lifted (layer added on local
  branch `judging-hold/user-md`, 2026-07-24).

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
  Requested by the user, 2026-07-25, during the Build-Week judging hold; that hold has since
  ended (tag `build-week-2026-submitted`), so this item is open work under the normal rules.
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
  Requested by the user, 2026-07-25; the judging hold that deferred it has ended.
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
  Requested by the user, 2026-07-25; the judging hold that deferred it has ended.

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
