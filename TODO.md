# Pre-Release TODO: build-your-users-mind

**Audit Date:** 2026-06-17
**Auditor:** Claude (for Lukas Geiger)
**Target Repo:** `ellmos-ai/build-your-users-mind` (initially private)
**Status:** `development` — Claude path is complete; private reference implementation exists.

---

## BLOCKERS
> Must be resolved before public release.

- [x] **Secrets:** No API keys/tokens/passwords in tracked files.
- [x] **Private Data:** No PII/real paths (leak scan is green).
- [x] **Hardcoded Paths:** Generic/relative paths in all scripts.
- [x] **Database Files:** No `.db` files tracked.
- [x] **.env Files:** No `.env` files tracked.
- [x] **BACH Internals:** No BACH-internal documents.
- [x] **.gitignore:** Minimum entries present.
- [x] **LICENSE:** MIT license present.
- [x] **README.md:** English, complete.

## HIGH PRIORITY
- [ ] Implement source adapters for Codex (rollout) + Gemini (SQLite) (currently sketches).
- [ ] Add classification spot check / inter-rater Kappa as an optional quality step.
- [ ] Add `domains.json` example.

## MEDIUM PRIORITY
- [x] Added `SECURITY.md`.
- [ ] Create `CHANGELOG.md` starting from v1.0.0.
- [ ] Create `CONTRIBUTING.md`.
- [ ] Kimi adapter (log format during first usage).

## LOW PRIORITY
- [ ] Test/smoke suite, GitHub Actions CI, badges.

## Intentionally Excluded
- No private corpus, no filled avatar files (enforced by `.gitignore`).
- No per-prompt hook (batch + logbook chosen intentionally).

---

## STATUS

| Category | Status | Notes |
|----------|--------|-------|
| Secrets | :green_circle: | Leak scan green |
| Private Data (PII) | :green_circle: | No PII/paths |
| .gitignore | :green_circle: | Minimum entries + corpus/avatar exclusion |
| Language (English) | :green_circle: | README in English |
| BACH Internals | :green_circle: | None |
| Database Files | :green_circle: | None tracked |
| README.md | :green_circle: | Complete |
| LICENSE | :green_circle: | MIT |
| **Overall** | **READY** | Private; Codex/Gemini adapters still sketch |

**Audit Date:** 2026-06-17
**Gate Check Exit Code:** `pending`

---

*Basis: MODULES/_templates/TODO_TEMPLATE.md*
