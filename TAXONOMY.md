# TAXONOMY — 8 Prompt Types + Classification Fields

> Standalone version (module is self-contained). **Methodological basis:** *Prompt-Archaeology*
> (L. Geiger) — the method of classifying a complete human-AI interaction protocol.

## The 8 Prompt Types

| Type | Code | Definition | Indicator |
|---|---|---|---|
| Start Prompt | **SP** | Initiates a new analysis or phase | No reference to prior context |
| Follow-up Topic | **NT** | Deepens existing topic | "And what about...?" |
| Follow-up Method | **NM** | Triggers method/tool/review/search/agent | Action verb |
| Follow-up Control | **NS** | Manages sequence or priority | "Wait", "first", "stop" |
| Correction | **KO** | Corrects an error or assumption | Negation, counterexample |
| Confirmation | **BE** | Validates intermediate status | Short agreement/acknowledgment |
| Course Change | **RA** | Fundamental change of direction | Questions the entire framework |
| Meta-Prompt | **MP** | About the process or dialogue itself | Process terminology |

**Borderline Cases:** SP vs. NT (new vs. connected) · NM vs. NS (trigger method vs. re-order only) ·
BE vs. KO ("yes, but..." is usually KO) · RA is rarer than KO, concerns the entire framework.

## Classification Fields (per Prompt)

| Field | Values |
|---|---|
| `type_code` | SP/NT/NM/NS/KO/BE/RA/MP |
| `topic` | Short topic (project-related) |
| `is_decision` | true if decision, preference, rule, correction, or course change |
| `decision_kind` | preference / correction / rule / direction_change / approval / rejection / process / none |
| `formulation_pattern` | Characterizing phrasing of the user (original phrasing, short) |
| `method_triggered` | WebSearch / WebFetch / Multi-Agent / Review / Cross-Model / Script / LaTeX / -- |
| `is_turning_point` | true/false |
| `outcome_signal` *(deterministic, Stage 0/1)* | praise / correction / reissue / none (derived from the next user turn) |

## Bias Indicators (Stage 4)
- **Confirmation:Correction (B:K)** — Disparity suggests approval bias; **silent approval is
  invisible** (not typed) → corrections are overrepresented.
- **Correction Rate per Topic** — Error-prone topics.
- **Proactive:Reactive** — Does the user lead or are they AI-driven?
- **Course Change Rate** — Epistemic flexibility.
