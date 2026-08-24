# Changelog

All notable changes to `build-your-users-mind` are documented here.

## [1.1.0-dev] — 2026-08-24

- **Multi-OS GitHub Actions CI Matrix**: Hardened `.github/workflows/ci.yml` with concurrency control (`cancel-in-progress: true`), full multi-OS matrix (`ubuntu-latest`, `windows-latest`, `macos-latest`), Python 3.10-3.13 matrix, bytecode compilation checks, Ruff linter gate, and Pytest test execution.
- **PEP 621 Metadata Standards**: Added standard `pyproject.toml` with PEP 621 metadata, standard PyPI classifiers (`Topic :: Security`, `Topic :: Scientific/Engineering :: Artificial Intelligence`), full `[project.urls]` (`Homepage`, `Documentation`, `Repository`, `Bug Tracker`, `Changelog`, `Security`, `Parent Organization`, `Umbrella Ecosystem`), and pytest configuration.
- **Bilingual Security Policy (`SECURITY.md`)**: Expanded security policy with Supported Versions matrix (`1.1.x`), 48-hour response SLA, GitHub Security Advisories link, official security contact channels (`security@ellmos.ai`, `security@open-bricks.org`, `support@lukasgeiger.com`, `lukas@open-bricks.org`), and formal guarantees for Local-First processing, Zero-Egress, Non-Elevation (unprivileged user space), and fail-closed secret redaction.
- **Automated Contract & Hygiene Test Suite**: Implemented `tests/test_metadata.py` containing 9 contract tests for version parity, PEP 621 compliance, CI matrix validation, security SLA & advisories verification, manifest boundaries, llms.txt synchronization, and zero-egress invariants (82/82 tests passing).
- **Documentation & Badges Parity**: Synchronized Shields.io badges in `README.md` (CI status, 82 passed tests, Python 3.10-3.13, Linux/Windows/macOS, Local-First, Security Policy, LLM-Ready).
- **Repository Hygiene**: Hardened `.gitignore` to exclude build artifacts, sync conflict patterns (`*.sync-conflict-*`, `*.conflict`), and lock files.

## 1.1.0-dev (Pre-Release)

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

## 2026-06-17

- Added source adapters for Claude, Codex, Gemini/Antigravity, and Kimi.
- Added multilingual documentation with English as the authoritative source.
- Added MIT licensing and initial repository hygiene checks.
