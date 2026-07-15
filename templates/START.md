# START — Runtime loop (feedback precognition)

> For an operator-authorized model that may use an evidence-backed preference hypothesis inside an
> already granted scope. This is not mind-reading and never expands the model's authority.

```
(0) Project DECISIONS.md present & relevant?  → YES: it wins (precedence). Done.
(1) WHAT-<USER>-SAID.md      → evidenced rule/decision for the situation? YES → act on it.
(2) WHAT-WOULD-<USER>-SAY.md → precognition: predicted feedback + confidence.
        🟢 high   → act only if already authorized and reversible.
        🟡 medium → ask, or act only if already authorized/reversible + log in (3).
        🔴 low/novel → do NOT guess: escalate / ask.
(3) WHAT-I-DID-…md (+ MY-ACTIONS.txt) → every action derived from (2), with assumption + confidence.
(4) On real feedback → WHAT-<USER>-SAID-ABOUT-…md → score prediction vs. reality →
        refine the rule in (1), adjust confidence in (2).  [self-improvement]
```

**Default heuristic under uncertainty:** reversible + within both an established pattern and existing
authority → act (log it) · external/irreversible/high-impact → not without confirmation · no pattern
(🔴) → escalate, don't guess.

> Quality metric: **how often the anticipated reaction matches the user's real later feedback.** When in
> doubt, treat the model as a fallible hypothesis and ask rather than overreach.
