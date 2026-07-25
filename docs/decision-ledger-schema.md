# Decision Ledger — Event-Sourced Schema

> **Status:** specification (P0). No implementation is claimed by this document.
> **Scope:** operator-neutral. This file describes the *shape* of the ledger, never the content of
> any particular operator's decisions.
> **Embargo:** local-only until the operator lifts it. Commit locally; do not push, tag, or publish.

This specification closes P0 item 3 ("event-sourced decision-trajectory schema") and unifies it with
the two object types agreed for the ledger: `decision` and `policy` share one store and one
lifecycle, because a policy is a decision that has been made durable.

---

## 1. Why event-sourced

A decision store that overwrites its rows loses the one thing that makes it trustworthy: the ability
to say *what was true when, and what changed it*. Three requirements follow directly:

1. **History is never erased.** A newer conflicting decision may replace the *current effect* of an
   older one, but the older record remains readable with its original timestamps.
2. **The current view is derived, not stored.** "What holds right now" is a projection over events,
   computed deterministically — never a hand-maintained field that can silently drift.
3. **Unresolved conflicts stay visible.** Contradictory explicit evidence without an unambiguous
   supersession relation must surface as a conflict with a conservative tie-break, never as a
   silently chosen winner.

---

## 2. Object types

Both types live in one ledger and share the event envelope. They differ in what they bind.

| | `decision` | `policy` |
|---|---|---|
| Answers | "What was decided in this case?" | "What rule now holds generally?" |
| Created by | an operator decision event | promotion from one or more decisions |
| Binds | the case it was made for | every case inside its `scope` |
| Extra fields | — | `scope`, `version`, `supersedes`, `source_decision_id` |

**Lifecycle:** `decision` → (repeated, reaffirmed, generalized) → `policy` → (superseded / revoked).
Promotion is itself an event and carries its own evidence.

---

## 3. Event envelope

Every row in the ledger is an immutable event.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `event_id` | string | yes | Stable, unique, never reused. |
| `object_id` | string | yes | Identity of the decision/policy this event belongs to. Multiple events share it. |
| `object_type` | `decision` \| `policy` | yes | See §2. |
| `change_state` | enum | yes | `introduced` \| `reaffirmed` \| `softened` \| `superseded` \| `revoked`. |
| `observed_at` | ISO-8601 | yes | When the evidence was observed. Always known. |
| `effective_at` | ISO-8601 | no | When it starts to hold, if different from `observed_at`. |
| `scope` | string | yes | Where it binds: project, topic, or `global`. |
| `project` | string | no | Pseudonymous local project/topic ID. Never a raw path. |
| `decision_kind` | enum | yes | See §4. |
| `statement` | string | yes | What was decided, in one sentence. |
| `evidence_ids` | string[] | yes | References into the corpus. **Never inline raw prompt text.** |
| `confidence` | 0.0–1.0 | yes | Of the extraction, not of the operator. |
| `provenance` | enum | yes | See §5. **Determines admissibility.** |
| `supersedes` | string[] | no | `object_id`s whose current effect this event replaces. |
| `effective_status` | enum | derived | `active` \| `superseded` \| `revoked` \| `conflicted`. Computed, never authored. |

`effective_status` is listed for readers of the projection; it must not be writable on an event.

---

## 4. Decision kinds — kept separate on purpose

A flat model conflates signals that mean different things. These stay distinct:

| Kind | Meaning | What it does **not** establish |
|---|---|---|
| `priority` | explicit importance statement | — |
| `engagement` | current attention, repeated inquiry | importance, requirement, durability |
| `requirement` | actively enforced gate or demand | project importance |
| `request` | open direct goal or task | a rule |
| `preference` | a rule for how things should be done | authority to act |
| `correction` | a wrong turn was named | a requirement, unless it restates one explicitly or links a violation to already-evidenced requirement |
| `approval` / `rejection` | explicit assent or refusal | a general rule from a single case |
| `direction_change` | a previous course is abandoned | that older records may be deleted |

**Two negative rules that the schema must enforce, not merely document:**

- Many questions or corrections **never** add up to importance, enforcement, or a durable preference.
- Attention (`engagement`) affects prioritization only and **never grants permission**. Focus and
  authority are separate axes and are resolved independently (§6).

---

## 5. Provenance — what may count as evidence

Admissibility is decided here, not at read time.

| Provenance | Admissible as | Ceiling |
|---|---|---|
| `operator_statement` | full evidence | — |
| `operator_correction` | full evidence (highest value: it corrects a wrong model) | — |
| `operator_approval` | full evidence | — |
| `agent_working_doc` | weak context only (HANDOFF, LOG, TODO, registries) | low confidence |
| `agent_inference` | **never evidence** | rejected |
| `automation_artifact` | **never evidence** (schedulers, tools, subagents, system events) | rejected |

Two consequences worth stating explicitly, because both have been violated in practice:

- **A ledger's own earlier output is not evidence for its later output.** Otherwise the model
  confirms itself.
- **Silence is not assent.** An absent objection establishes nothing; an explicit approval is strong
  evidence precisely because corpora over-represent corrections.

---

## 6. Precedence — focus and authority resolved separately

Two independent questions, two independent resolutions:

**Authority** ("may this be done?"), highest first:
1. explicit current `requirement` / `preference` in the narrowest matching `scope`
2. project-level decisions
3. `global` policies
4. durable patterns — only where no newer explicit contradiction exists

**Focus** ("what should be worked on?"): `engagement` and recency contribute here and nowhere else.

Low-confidence inference is never promoted into a stated fact. Where two `active` objects conflict
within the same scope and neither supersedes the other, both remain visible and
`effective_status = conflicted`; the conservative branch wins the tie-break — the one that grants
less authority or preserves the prior state.

---

## 7. Privacy constraints on the store

- Summaries carry **aggregate factors and evidence IDs only** — never raw prompts, diagnoses,
  secrets, or sensitive content.
- Project and topic names are themselves potentially sensitive: consumer output uses **minimal
  pseudonymous local IDs** with an explicit allowlist.
- No personal, therapeutic, or medical topic is exported unless the operator explicitly maps it to a
  named project automation.
- Recursive `.gitignore` rules must be in place **before** any real ledger file is generated.

---

## 8. Open questions

These are deliberately unresolved and must be answered before implementation:

1. **Storage backend** — SQLite table vs. append-only JSONL. JSONL is simpler to audit and diff;
   SQLite composes with the existing memory column. Not yet decided.
2. **Promotion trigger** — how many reaffirmations across how many separated windows justify
   `decision` → `policy`? Must be configurable and reported, never a hidden constant.
3. **Ingest adapter** — the planned `to-decide-ingest` reads the operator's decision chain. Its
   mapping from free-text entries to `decision_kind` needs its own specification and fixtures.
4. **Interaction with the permission system** — the ledger may *reference* rights but is never the
   source of truth for them. The boundary needs a written contract.
