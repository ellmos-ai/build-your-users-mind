# be-my-avatar — Apply an authorized preference hypothesis (full loop, with logging)

Run the preference model in **action** mode only inside authority the user already granted. Read the
avatar files in `<AVATAR_DIR>` and follow `START.md`. The model is not an authority grant.

**Task / situation:** $ARGUMENTS

## Steps (full 0→4 loop)
1. **Decide** as in `decide-like-me` (0→2).
2. **Act — only if already authorized, reversible, local, and within pattern** (≥🟡 confidence).
   - **Irreversible / external / high-impact** (push, upload, delete, mail, server, legal, medical,
     employment, financial, or safety-critical) **or 🔴** → do NOT act; ask for confirmation.
3. **(3) Log:** every action assumed on the user's behalf, with **assumption + confidence**, into
   `WHAT-I-DID-…md` and `MY-ACTIONS.txt`.
4. **(4)** On later real feedback → record in `WHAT-<USER>-SAID-ABOUT-…md` and refine the rule in
   `WHAT-<USER>-SAID.md`.

## Output
- What was done (or why escalated), confidence, and a pointer to the log entry.

**Golden rule:** a pattern never expands authority. When in doubt, prefer asking over overreaching.
As a **workflow component** this is the executing stage
after `decide-like-me`.
