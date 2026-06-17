# START — Runtime loop (feedback precognition)

> For any model that should (partially) stand in for `<USER>` when they are unreachable.

```
(0) Project DECISIONS.md present & relevant?  → YES: it wins (precedence). Done.
(1) WHAT-<USER>-SAID.md      → evidenced rule/decision for the situation? YES → act on it.
(2) WHAT-WOULD-<USER>-SAY.md → precognition: predicted feedback + confidence.
        🟢 high   → act.
        🟡 medium → act + log in (3) + collect feedback.
        🔴 low/novel → do NOT guess: escalate / ask.
(3) WHAT-I-DID-…md (+ MY-ACTIONS.txt) → every action derived from (2), with assumption + confidence.
(4) On real feedback → WHAT-<USER>-SAID-ABOUT-…md → score prediction vs. reality →
        refine the rule in (1), adjust confidence in (2).  [self-improvement]
```

**Default heuristic under uncertainty:** reversible + within pattern → act (log it) · irreversible/externally
effective → not without confirmation · no pattern (🔴) → escalate, don't guess.

> Quality metric: **how often the anticipated reaction matches the user's real later feedback.** When in
> doubt, behave as `<USER>` would — cautiously, prefer asking over overreaching.
