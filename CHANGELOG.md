# Changelog

All notable changes to `build-your-users-mind` are documented here.

## Unreleased — 1.1.0-dev

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

## 2026-06-17

- Added source adapters for Claude, Codex, Gemini/Antigravity, and Kimi.
- Added multilingual documentation with English as the authoritative source.
- Added MIT licensing and initial repository hygiene checks.
