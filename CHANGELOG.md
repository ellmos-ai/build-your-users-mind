# Changelog

All notable changes to `build-your-users-mind` are documented here.

## [1.1.0-dev] - 2026-08-26

- **Guarded journal write seam**: `decision_prediction.py --append` adds one event after
  revalidating the whole stream, rejects backdated `occurred_at`, writes atomically and returns an
  audit receipt with line and journal hashes. A rejected append leaves the journal unchanged; the
  journal plus receipt remain the only audit trail (ticket T-20260820-942457158).
- **Decision Prediction v2**: Added a closed, source-hashed `decision_ref`; explicit match, offered-
  option and no-fit outcomes; complete validation/recovery/bonus projections; and `final_score` with
  a tested `current_score` compatibility alias. Raw/private payload and action-receipt fields now fail
  closed, while execution authority remains outside the journal.
- **Post-Hold Integration**: Integrated the decision-prediction and Secure-Mode text-avatar work, the simulation-channel concept, and both post-competition quarantine branches after the Build Week judging hold ended.
- **Multi-OS CI Matrix**: Added concurrency cancellation, Ubuntu/Windows/macOS coverage, Python 3.10-3.13, compilation, Ruff, and test gates.
- **Repository Hygiene**: Expanded `.gitignore` for build artifacts, sync-conflict copies, generated data, and lock files.
- **Security Contract**: Added supported-version and 48-hour response commitments plus the ellmos-ai/open-bricks security contacts while retaining the prediction and Secure-Mode authorization boundary in both languages.
- **PEP 621 Metadata**: Added the complete project URL set, security and utility classifiers, and development dependencies.
- **Contract Tests**: Added checks for CI-matrix integrity, manifest boundaries, zero-egress imports, feature schemas, public-contract visibility, and bilingual documentation.

- **Marketing & Discoverability**: Synchronized Shields.io badges across `README.md` and `README_de.md` (CI status, 86 passed tests, Python 3.10-3.13, Platform support, 100% Offline / Zero-Egress Privacy, Local-First / Redaction-Bound Security, Ecosystem & Umbrella badges).
- **Quick Navigation**: Integrated bilingual quick navigation headers in `README.md` and `README_de.md`.
- **Ecosystem Matrix**: Expanded sibling tools and ecosystem matrix across `ellmos-ai`, `dev-bricks`, `doc-bricks`, `research-line`, and `open-bricks`.
- **Bilingual Security Policy**: Upgraded `SECURITY.md` to comprehensive English and German documentation, covering local-first & zero-egress invariants, fail-closed redaction bounds, non-elevation (user-mode), direct security contacts (`security@ellmos.ai` and `support@lukasgeiger.com`), and GitHub Private Vulnerability Reporting.
- **PEP 621 Classifiers & URLs**: Extended `pyproject.toml` with PEP 621 classifiers (Python 3.13, OS Independent, Windows, Linux, MacOS) and project URLs (Documentation, Changelog).
- **Automated Metadata Parity Tests**: Extended `tests/test_metadata.py` to 9 contract tests (86 total passed tests in suite), verifying bilingual security policy, PEP 621 classifiers, CI workflow integrity, and sibling ecosystem table parity.
- **LLM Context**: Synchronized `llms.txt` with Last-checked date `2026-08-21`, 86 passed tests, and complete sibling ecosystem list.

## 2026-08-16

- Added an append-only decision-prediction event architecture that keeps recommendation, likely
  choice, explicit user feedback, recovery scoring and execution authority separate.
- Added top-1 accuracy, multiclass Brier score and log loss alongside the operator-defined 0–10
  advice-process score with later adoption credits and explicit bonus events.
- Added a Secure-Mode-only text-avatar prototype with deterministic evidence retrieval, repeated
  redaction, privacy-minimized outputs, novelty escalation and optional loopback-only Ollama use.
- Added executable JSON schemas, synthetic examples and regression tests for both new contracts.

- Synchronized discovery metadata, Shields.io badges, and test status across `README.md`, `README_de.md`, and `llms.txt`.
- Added interactive bilingual Mermaid diagrams for system architecture and feedback-precognition runtime loop.
- Added comprehensive German documentation in `README_de.md` with complete parity.
- Added sibling tools matrix linking related repositories in `ellmos-ai`, `dev-bricks`, `research-line`, and `open-bricks`.
- Configured PEP 621 `pyproject.toml` with project metadata, pytest options, and `[tool.ruff]` lint settings.
- Added automated metadata, schema, and manifest parity testsuite in `tests/test_metadata.py` (5 assertions, 82 total passed).
- Added a declared-preferences layer: `templates/USER.md` at runtime-loop step (0.5) —
  operator-declared preferences and delivery defaults that outrank older distilled evidence;
  agent rule files (`CLAUDE.md`, `GPT.md`, `GEMINI.md`, …) act as consumers of it.
- Hardened all adapters to fail closed, validate timestamps/dates, and write atomically.
- Filtered Codex internal-context/plugin artifacts and carried turn-level project context.
- Expanded secret redaction, added operator-defined sensitive-data rules, and private file modes.
- Replaced chronological evidence counters with stable source-bound IDs and added corpus merging.
- Added fresh chunk manifests, safe domain filenames, a Stage-2 schema/worker contract, and strict
  completeness, unknown-ID, stale-file, and collision gates.
- Added fixture-based tests, pinned Ruff, and Windows/Linux GitHub Actions CI.
- Corrected public/repository metadata and documented explicit authorization, non-diagnosis, and
  irreversible/high-impact action boundaries.
- Marked translations as needing refresh from the authoritative English 1.1 contract.
- Refused empty corpus merges unless explicitly confirmed with `--allow-empty`.
- Rejected Gemini records whose protobuf timestamps omit the required seconds field.
- Made prediction scoring fail closed on malformed action-log rows and unknown values.
- Matched prediction feedback by date plus title and rejected ambiguous duplicate keys.
- Filtered Codex `AGENTS.md` injections and retained Kimi `turn.steer` corrections.
- Treated Gemini databases without the required `steps` table as partial-input failures.
- Expanded redaction for URI credentials, AWS secrets, Google API keys, quoted passwords, and
  corpus metadata fields.
- Extended the offline demo with an explicitly synthetic prediction/feedback scoring loop.
- Corrected the Codex attribution to avoid an unsupported per-session model-version claim.
- Documented the verified GPT-5.6/Codex final hardening session separately from the earlier,
  model-unspecified Codex adapter implementation.
- Synchronized the adapter implementation briefs with stable IDs, read-only sources, current CLI
  flags, and fail-closed output semantics.
- Added reviewable synthetic source-schema fixtures for all four adapters, including multi-block
  JSONL events and hex-encoded Gemini protobuf fields.

## 2026-06-17

- Added source adapters for Claude, Codex, Gemini/Antigravity, and Kimi.
- Added multilingual documentation with English as the authoritative source.
- Added MIT licensing and initial repository hygiene checks.
