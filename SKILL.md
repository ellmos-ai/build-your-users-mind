---
name: build-your-users-mind
description: Instructions for any agent model (Claude, Codex, agy/Gemini, Kimi) to build, maintain, and connect an empirical Theory-of-Mind model of ITS user from its own interaction logs to memory/rule files/system prompt. Activates when "build a ToM/decision avatar for my user", "Theory of Mind system user model", "WHAT-WOULD-USER-SAY", "feedback precognition".
---

# build-your-users-mind — Agnostic ToM Module (Feedback Precognition)

> **What you mind is what you get.** A **recipe**, not a framework. Every agent model uses this to build a
> ToM model of *its* user: evaluate own data → distill decision patterns → maintain
> avatar files → bind to own memory/rules file/system prompt.
>
> **Core = feedback precognition (feedforward):** Predict user feedback BEFORE it comes; use it as a
> control signal in their absence; evaluate the prediction against reality afterwards to improve.
> This is an operator-authorized preference model, not mind-reading or diagnosis. Predictions are
> uncertain hypotheses. Never use them to silently expand authority or make irreversible, external,
> safety-critical, legal, medical, employment, financial, or similarly high-impact decisions.
>
> **Templates:** `templates/` (avatar files), `scripts/` (pipeline), `TAXONOMY.md` (8 types),
> `skills/swarm-operations/` (classification swarm). A **private reference implementation**
> (based on the author's own logs) exists but is not shipped.
>
> **Theoretical Basis:** *Prompt-Archaeology* (method, taxonomy in `TAXONOMY.md`)
> + ToM research (ToM-SWE arXiv 2510.21903; Persistent Memory & User Profiles 2510.07925).

## Core Principle

LLMs never see raw gigabytes. **Deterministic scripts first reduce** data to a clean corpus of human-typed
user prompts; only then does a **classification swarm** work semantically.
The core is not "which prompts", but **"which decision → which outcome → was the user satisfied".**

## The 6 Steps

### 1. Identify the Source (Source Adapter)
With the operator's explicit authorization, find that operator's own interaction logs. Differs per
model → see `SOURCE-ADAPTERS.md`.
Extract **only genuine, human-typed prompts** (no tool results, system reminders, hook injections,
context compacting summaries). Fields: `ts, project, session, text`.

### 2. Reduce (deterministic, no LLM)
- Filter synthetic turns, deduplicate, aggregate boilerplate/micro-acks.
- **Follow-up linking:** derive the next user turn per prompt as a conservative `outcome_signal`
  (praise | reissue | correction | none). An unrecognized follow-up is `none`, not `reissue`.
- **`decision_score`** via a decision lexicon (correction/preference/rule/control).
- **REDACTION (mandatory before any persistence):** built-in rules cover common credentials and
  identifiers. Supply reviewed custom rules for **health/tax/legal/financial or domain-specific
  data**; never claim automatic detection of all sensitive content.
- Evidence IDs are source/session/timestamp/content-bound hashes, stable under chronological backfill.
  Use one source-specific filename per adapter and `merge_corpora.py` for multi-source corpora.

### 3. Classify (swarm, hierarchical + stigmergy)
8-type taxonomy **SP/NT/NM/NS/KO/BE/RA/MP** (definitions in `TAXONOMY.md`) + `decision_kind`
(preference/correction/rule/direction_change/approval/rejection/process/none) + `formulation_pattern`
(user's characteristic phrasing). Each worker follows `templates/CLASSIFY-CHUNK.md`; every row must
match `schemas/classification.schema.json`. Run `validate_classifications.py` before aggregation.

### 4. Generate Avatar Files
Structure 1:1 as in `templates/` (copy templates, replace `<USER>`/`<AGENT>`):
`WHAT-<USER>-SAID.md` (evidenced) · `WHAT-WOULD-<USER>-SAY.md` (prediction + confidence) ·
`WHAT-I-DID-…md` + `MY-ACTIONS.txt` (action log) · `WHAT-<USER>-SAID-ABOUT-…md` (lessons learned) ·
`PROMPT-LOG` (cut-and-clue) · `METHODIK.md` (incl. bias warning) · `START.md` (0→4 loop).

### 5. Bind (crucial!)
The ToM model must **actually be used**, not just exist:
- Short rule/pointer in the agent's **own memory/rules file/system prompt**
  (Claude: `CLAUDE.md`; Codex: `GPT.md`/`AGENTS.md`; agy: `GEMINI.md`; Kimi: `KIMI.md`)
  → points to the `START.md` loop. **Keep it short** (pointer, no full text).
- **Precedence rule:** project-specific `DECISIONS.md` take precedence over the cross-cutting avatar.
- **Optional command entry points (nuances):** expose the loop at three depths plus an orchestrator —
  `read-my-mind` (predict, 0→2, no action), `decide-like-me` (one decision, 0→2, a workflow component),
  `be-my-avatar` (act only when already authorized, full 0→4, reversible-only, logs),
  `avatar-orchestrator` (chain over many decisions,
  bundling 🔴/irreversible items into one question). Templates in `templates/commands/`.
- **Versioned binding:** keep the project copy of the loop/skill canonical; if the agent also ships a
  registered copy, the **higher version wins** and the older routed copy is **replaced** — the project
  leads, the registry follows (no drift).

### 6. Maintain (self-improving)
- **Empirical basis:** rerun scripts periodically (logs persist anyway) — **no per-prompt hook**
  (avoid idempotency/multiple registration trap; batch is more robust).
- **Runtime (guided):** within existing authority, log reversible assumptions made on behalf of the
  user → file (3); anything external, irreversible, novel, or high-impact requires confirmation;
  on feedback → file (4) → update rules in (1), adjust confidence in (2).
- **Score the loop:** `scripts/score_predictions.py` reads `MY-ACTIONS.txt` (+ optionally the
  `WHAT-<USER>-SAID-ABOUT` feedback) and reports hit rate overall and per 🟢/🟡/🔴 tier plus the
  🔴 escalation rate — the empirical measure of whether the precognition actually works.

## Bias & Limits (always mention)
- **Silent approval is invisible** → corrections are overrepresented, making the avatar appear "critical".
- **ToM fragility:** robust on recurring situations, fragile under novel/adversarial variations → confidence tiers,
  at 🔴 **escalate instead of guessing**.
- Evidence IDs are deterministic; the claims and labels attached to them are synthesized. Resolve and
  cross-check load-bearing IDs against raw text during an intentional private review.

## Lean Principle
The only model-specific part is the **source adapter** (Step 1). Recipe, taxonomy,
avatar structure, and binding are universal. Do not over-engineer.
