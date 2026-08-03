# Changelog

All notable changes to `build-your-users-mind` are documented here.

## Unreleased — 1.1.0-dev

- Updated discoverability metadata, added GFM callout box for `llms.txt`, synchronized `llms.txt` index timestamp (2026-08-03), and added Shields.io organization/umbrella badges (`ellmos-ai`, `open-bricks`, `Pytest 73 passed`).
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
- Revalidated the local deterministic gate on 2026-08-01: 73 tests plus 8 subtests, Ruff,
  compileall, manifest JSON validation, and the offline synthetic demo passed.

## 2026-06-17

- Added source adapters for Claude, Codex, Gemini/Antigravity, and Kimi.
- Added multilingual documentation with English as the authoritative source.
- Added MIT licensing and initial repository hygiene checks.
