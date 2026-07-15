# decide-like-me — Decide this one thing the way <USER> would (a fork, no side effect)

Run the preference model in **decision-support** mode. Read the avatar files in `<AVATAR_DIR>` and
follow `START.md`. The result is a fallible hypothesis, not a fact about the user or an authority grant.

**Decision to make:** $ARGUMENTS

## Steps (0→2, then return a decision)
1. **(0)** Project `DECISIONS.md` relevant? → if so, it wins.
2. **(1)** Evidenced rule in `WHAT-<USER>-SAID.md`? → decide accordingly.
3. **(2)** Otherwise prediction + confidence from `WHAT-WOULD-<USER>-SAY.md`.

## Output
- **Decision:** the concrete choice <USER> would make.
- **Rationale:** what it rests on (evidence/pattern).
- **Confidence:** 🟢/🟡/🔴.
- On **🔴**: do NOT decide — escalate (ask the user) and say so.

This command performs **no** side effect (no push/write/delete) — it only returns the fork, which makes
it usable as a **workflow component**: the caller (e.g. `be-my-avatar` or `avatar-orchestrator`)
executes the decision.
