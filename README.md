<p align="center"><img src="assets/banner.svg" alt="build-your-users-mind — what you mind is what you get" width="100%"></p>

# build-your-users-mind

> **What you mind is what you get.**

**🌐 [EN](README.md) · [DE](locales/de/README.md) · [ES](locales/es/README.md) · [JA](locales/ja/README.md) · [RU](locales/ru/README.md) · [ZH](locales/zh/README.md)** — English is authoritative; translations may lag.

A recipe for any AI agent (Claude, Codex, Gemini/agy, Kimi, …) to build an empirical,
self-improving **theory-of-mind model of its own user** from its own interaction logs —
and to act in the user's spirit when the user is away.

It works by **feedforward**: instead of waiting for feedback that won't arrive while the user
is absent, the agent *predicts the user's feedback before it comes* and uses that prediction as a
guidance/reward signal — then evaluates the prediction against reality afterwards to get better.

## "I know what you want."

That sentence is the whole point. The agent reads the user's past prompts, distils **what the user
decides, how they phrase it, and whether they were satisfied**, and turns it into a small set of
living documents it can consult the moment a decision comes up and the user isn't reachable.

It is **not** a chatbot persona and **not** a heavy framework — it is a method + a handful of scripts
+ document templates. The only agent-specific part is the *source adapter* (where each agent reads its
own logs). Everything else is universal.

## Start here

| If you are... | Open first | Why |
|---|---|---|
| An AI agent adding user-memory discipline | `SKILL.md` | End-to-end implementation recipe |
| A maintainer wiring log sources | `SOURCE-ADAPTERS.md` | Claude, Codex, Gemini/agy and Kimi log locations |
| A reviewer checking safety boundaries | `SECURITY.md` and `.gitignore` | Redaction, private-corpus and generated-avatar exclusions |
| A researcher comparing concepts | `TAXONOMY.md` | Prompt-Archaeology categories and decision patterns |

## Find this repository

Canonical search phrase: **`ellmos-ai/build-your-users-mind`**.

Useful discovery phrases:
- `AI agent theory of mind user model`
- `LLM user modeling from interaction logs`
- `Codex Claude Gemini Kimi source adapters`
- `prompt archaeology feedback precognition`
- `local-first AI personalization templates`
- `agent memory decision support from prompt logs`

Disambiguation: this is not a SaaS personalization product, HR platform, chatbot persona pack,
general prompt library or psychological diagnosis tool. It is a local-first documentation and script
kit for building an evidence-backed user model from private agent interaction logs.

## How it works — feedback precognition

A 0→4 runtime loop (see `templates/START.md`):

| Step | File | Role |
|---|---|---|
| 0 | project `DECISIONS.md` | project-specific decisions win (more specific) |
| 1 | `WHAT-<USER>-SAID` | **evidence-based** rules/decisions (with prompt-ID citations) |
| 2 | `WHAT-WOULD-<USER>-SAY` | **precognition** — predicted feedback + confidence (🟢/🟡/🔴) |
| 3 | `WHAT-I-DID…` + `MY-ACTIONS.txt` | log of actions taken on the prediction |
| 4 | `WHAT-<USER>-SAID-ABOUT…` | **evaluation** — prediction vs. reality → improves (1) and (2) |

Quality metric = **how often the anticipated reaction matches the user's real later feedback.**
At 🔴 (novel/no pattern) the rule is **escalate, don't guess.**

### Pipeline (build the model)
1. **Extract** (`scripts/corpus_extract.py`) — deterministic: pull only human-typed prompts from your
   logs, filter synthetic turns, **redact secrets**, link each prompt to the next turn's `outcome_signal`
   (praise/correction/reissue/none).
2. **Chunk** (`scripts/chunk_corpus.py`) — dedupe, optional domains, size-chunks for the swarm.
3. **Classify** (swarm) — 8-type taxonomy (`TAXONOMY.md`) + decision_kind + formulation pattern.
   Hierarchical swarm (domain leads × chunk workers); see bundled `skills/swarm-operations/`.
4. **Aggregate** (`scripts/aggregate_stats.py`) — type distribution, B:K ratio, turning points.
5. **Author** the avatar files from `templates/` and **bind** a short pointer into the agent's own
   memory/rules file (Claude `CLAUDE.md`, Codex `GPT.md`/`AGENTS.md`, Gemini `GEMINI.md`, …).

See `SKILL.md` for the full recipe and `SOURCE-ADAPTERS.md` for per-agent log locations.

## Theory of us — theoretical background

The system models the **dyad** (agent ↔ user), not just the user in isolation — a *theory of us*.
It is grounded in:
- **Theory of Mind** research for LLM agents — predicting and conditioning on an interlocutor's mental
  state improves outcomes (e.g. *ToM-SWE*, arXiv 2510.21903; *Infusing Theory of Mind into Socially
  Intelligent LLM Agents*, 2509.22887; *Persistent Memory & User Profiles*, 2510.07925).
- **Prompt-Archaeology** (L. Geiger) — the method of classifying full human-AI interaction protocols,
  whose 8-type taxonomy this module reuses (`TAXONOMY.md`).
- A known limit: LLM ToM is **robust on recurring cases, fragile under novel/adversarial variation** —
  hence the confidence tiers and the "escalate, don't guess" rule.

## Bias & limits (read before trusting it)
- **Silent approval is invisible** — users type corrections, not praise → the model over-represents
  corrections and skews "critical". Calibrate accordingly.
- **Evidence IDs come from LLM synthesis** — verify load-bearing ones against the raw corpus.
- **Classifier bias** — spot-check a sample; report inter-rater agreement for serious use.

## Privacy & redaction
The extractor redacts API keys, tokens, emails, IP-like and long digit runs **before writing**.
**Health/tax or other sensitive user content is the agent's responsibility to redact** for its own
user before the corpus or any avatar file leaves a private space. Never commit a real corpus —
see `.gitignore`.

## Suggested GitHub topics
`theory-of-mind` · `llm` · `user-modeling` · `personalization` · `ai-agents` · `prompt-analysis`
· `feedback` · `decision-support`

## Credits & License
Method: *Prompt-Archaeology* by Lukas Geiger. Module & concept: Lukas Geiger (+ Claude).
Bundled dependency: `swarm-operations` skill. **MIT** — see `LICENSE`.
Reference implementation (private, not shipped): a personal instance built on the author's own logs.
