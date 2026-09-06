# USER.md — Declared preferences & delivery defaults

> **Operator-maintained, declarative layer** of the user model. Unlike `WHAT-<USER>-SAID.md`
> (evidence distilled from logs, cited by prompt ID), every entry here was **directly declared or
> explicitly confirmed by the user**. In the runtime loop this file sits at **(0.5)**: after
> project `DECISIONS.md`, before the evidence layer — a current declared preference outranks an
> older distilled rule.
>
> Agent rule files (`CLAUDE.md`, `GPT.md`/`AGENTS.md`, `GEMINI.md`, …) are **consumers** of this
> file: they may mirror single entries as short pointers where guaranteed loading matters, but
> THIS file is canonical. Fix here first, then refresh the mirrors.

## Delivery defaults

<!-- Where do finished artifacts go? One block per artifact type. -->

### Reports / analyses
- **Read location:** <where the user actually reads, e.g. their desktop folder>
- **Archive copy (mandatory):** <backup location, e.g. `<read-location>/.USER/`>
- **Lifecycle:** <e.g. the user deletes the read copy after reading; the archive copy persists>

### <another artifact type>
- …

## Format & style preferences

<!-- e.g. Markdown vs. PDF, language, naming pattern `<topic>_<YYYY-MM-DD>.md`, length -->

## Maintenance rules

- Every entry carries `[<initials> YYYY-MM-DD]` and, where useful, its source (conversation,
  decision file, ticket).
- Agents append or change entries **only on explicit user instruction**, keeping the user's
  wording.
- Precedence on conflict: project `DECISIONS.md` (0) → **this file (0.5)** → `WHAT-<USER>-SAID.md` (1).
