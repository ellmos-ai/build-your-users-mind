# RELEASE GATE — build-your-users-mind

**Date:** 2026-07-21<br>
**Repository:** `https://github.com/ellmos-ai/build-your-users-mind` (public)<br>
**Version/status:** `1.1.0-dev` / development<br>
**Scope:** repository hygiene and deterministic pipeline safety, not semantic model validity.

## Current local gate

| Check | Result |
|---|---|
| Python 3.10+ standard-library runtime | PASS |
| `python -m compileall -q scripts tests` | PASS |
| Synthetic adapter/pipeline regression suite | PASS |
| Ruff 0.15.18 | PASS |
| ELLMOS module manifest schema | PASS |
| Classification JSON contract and collision/completeness gate | PASS on fixtures |
| Missing/empty input preserves existing output | PASS on fixtures |
| Recursive private corpus/avatar Git exclusions | PASS |
| Root repository hygiene final gate | PASS |
| GitHub Windows/Linux CI baseline | PASS for `7a05519` ([run 29868228916](https://github.com/ellmos-ai/build-your-users-mind/actions/runs/29868228916)) |

## Honest release decision

The repository is suitable for a **public development** state. Each new revision still needs green
remote CI before release. It is **not yet a stable semantic release**: the historical low inter-rater
agreement requires a new representative evaluation, localized documents need refresh, and a private
operator-owned end-to-end run must confirm the complete human review workflow.

No corpus, generated profile, or real user content is part of this gate. A green deterministic gate
does not make generated preferences true, does not grant an agent authority, and does not permit
psychological diagnosis or external/irreversible/high-impact action without direct confirmation.
