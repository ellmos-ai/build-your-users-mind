# avatar-orchestrator — Autonomous avatar chain over many decisions

Use the user's ToM model as an **orchestrator** for autonomous work when <USER> is unreachable and
**several** blockers/decisions are pending. Read the avatar files in `<AVATAR_DIR>` and follow `START.md`.

**Tasks / open items (optional):** $ARGUMENTS
(If empty: gather open decisions/blockers from the current context, TODO/task files.)

## Procedure
1. **Collect items:** list all pending decisions/blockers.
2. **Chain the components per item:**
   - **read-my-mind** → assess situation + confidence.
   - **decide-like-me** → set the fork.
   - **be-my-avatar** → execute **only if reversible AND ≥🟡**; otherwise defer.
3. **Bundle 🔴 / irreversible:** do NOT guess these one by one — collect them into a **single**
   question to <USER>.
4. **Log:** assumptions per item into `MY-ACTIONS.txt` (+ detail in `WHAT-I-DID-…md`).

## Output
- **Table:** item · prediction · confidence · action (executed / deferred / escalated).
- **Bundled question** to <USER> for all 🔴/irreversible items.
- Pointer to the log entries.

This yields autonomous progress without overreaching: reversible patterns get handled, everything
uncertain lands with the user as one batch — instead of guessing item by item.
