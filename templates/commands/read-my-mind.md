# read-my-mind — What does <USER> probably want here? (prediction, no action)

Run the user's ToM model in **prediction** mode (feedback precognition). Read the avatar files in
`<AVATAR_DIR>` and follow `START.md`.

**Context / question:** $ARGUMENTS

## Steps (0→2 only, then STOP)
1. **(0)** Is a project `DECISIONS.md` relevant? → if so, state its line (it wins).
2. **(1)** `WHAT-<USER>-SAID.md` — an evidenced rule/decision for this situation?
3. **(2)** `WHAT-WOULD-<USER>-SAY.md` — most likely user position + **confidence**.

## Output (compact)
- **Prediction:** what <USER> most likely wants/says here.
- **Confidence:** 🟢 high / 🟡 medium / 🔴 low-novel.
- **Evidence:** prompt IDs from `WHAT-<USER>-SAID` or clusters from `WHAT-WOULD-<USER>-SAY`.
- On 🔴: say so explicitly — "no robust pattern, escalate instead of guessing".

**No** action, **no** entry in `MY-ACTIONS.txt` — this is pure assessment before anything is done.
