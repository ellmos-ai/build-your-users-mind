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

## Local-only incubation: temporal attention and decision trajectory

**Operator embargo:** This work is local-only until the operator explicitly lifts the competition
embargo. Commit finished local units, but do not push, open a pull request, trigger remote CI,
publish a release, or create a public issue/tag. Local deterministic tests and local integration are
allowed and required.

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
- [ ] Specify an event-sourced decision-trajectory schema with stable decision/event ID, scope,
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
- [ ] Lift the embargo only after an explicit operator decision. At that point re-audit private-data
  exclusions, decide what portion is safe to publish, remove the local `.git/hooks/pre-push` embargo
  guard, run remote CI, and only then consider push, pull request, release notes, or a public
  version/tag.

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
