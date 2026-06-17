# WHAT WOULD <USER> SAY — Prediction playbook (feedback precognition)

> **Inferential** (model prediction from patterns). The *anticipated feedback* of `<USER>` that steers the
> agent in their absence. Evaluated in `WHAT-<USER>-SAID-ABOUT-…` against real feedback.

## Confidence legend
- 🟢 **high** — consistent pattern → act.
- 🟡 **medium** — context-dependent → act + log + collect feedback.
- 🔴 **low/novel** — no pattern → **escalate, don't guess**.

## Situation playbook
| Situation | Prediction: what <USER> wants | Confidence |
|---|---|---|
| <situation 1> | <predicted behavior/decision> | 🟢/🟡/🔴 |

*(Fill from the domain clusters: per cluster → situation + typical decision + confidence from cluster consistency.)*

## Default heuristic under uncertainty
1. Reversible + within pattern → act (log it). 2. Irreversible/external → not without confirmation.
3. Conflicts with core values → the more cautious option. 4. No pattern (🔴) → escalate.
