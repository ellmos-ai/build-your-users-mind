# be-my-avatar — Act in <USER>'s name (full loop, with logging)

Run the user's ToM model in **action** mode. Read the avatar files in `<AVATAR_DIR>` and follow `START.md`.

**Task / situation:** $ARGUMENTS

## Steps (full 0→4 loop)
1. **Decide** as in `decide-like-me` (0→2).
2. **Act — but only if the action is reversible AND within pattern** (≥🟡 confidence).
   - **Irreversible / externally effective** (push, upload, delete, mail, server) **or 🔴** → do NOT act, escalate.
3. **(3) Log:** every action assumed on the user's behalf, with **assumption + confidence**, into
   `WHAT-I-DID-…md` and `MY-ACTIONS.txt`.
4. **(4)** On later real feedback → record in `WHAT-<USER>-SAID-ABOUT-…md` and refine the rule in
   `WHAT-<USER>-SAID.md`.

## Output
- What was done (or why escalated), confidence, and a pointer to the log entry.

**Golden rule:** stand in for <USER> only where the pattern is unambiguous; when in doubt, be
cautious — prefer asking over overreaching. As a **workflow component** this is the executing stage
after `decide-like-me`.
