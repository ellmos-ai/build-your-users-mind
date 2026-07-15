# avatar-orchestrator — Triage an authorized reversible work queue

Use the preference model to triage **several** blockers/decisions when <USER> is unreachable. It may
execute only work that is already authorized, reversible, local, and low-impact. Read the avatar
files in `<AVATAR_DIR>` and follow `START.md`.

**Tasks / open items (optional):** $ARGUMENTS
(If empty: gather open decisions/blockers from the current context, TODO/task files.)

## Procedure
1. **Collect items:** list all pending decisions/blockers.
2. **Chain the components per item:**
   - **read-my-mind** → assess situation + confidence.
   - **decide-like-me** → set the fork.
   - **be-my-avatar** → execute **only if already authorized, reversible, local, low-impact, and ≥🟡**;
     otherwise defer.
3. **Bundle 🔴 / external / irreversible / high-impact:** do NOT guess these one by one — collect them into a **single**
   question to <USER>.
4. **Log:** assumptions per item into `MY-ACTIONS.txt` (+ detail in `WHAT-I-DID-…md`).

## Output
- **Table:** item · prediction · confidence · action (executed / deferred / escalated).
- **Bundled question** to <USER> for all 🔴/irreversible items.
- Pointer to the log entries.

This may advance an already-authorized reversible queue without broadening scope. Everything
uncertain or consequential lands with the user as one batch instead of being guessed item by item.
