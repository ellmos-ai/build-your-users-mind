# Decision Ledger — templates

A numbered, append-only register for an operator's real open decisions, their evidence,
and their outcomes. It complements the feedback-precognition loop (`templates/START.md`):
project-local `DECISIONS.md` still wins at step (0), and recurring rules distilled from
past decisions still belong in `WHAT-<USER>-SAID.md` (step 1). The ledger is what sits
above both — the working register that turns a scattered decision request into a
citable, revisitable record: captured → decided → implemented → archived.

## Files

| File | Role |
|---|---|
| `TO-DECIDE.template.txt` | The open chain: one entry per pending decision, plus the binding rule and the cut-and-clue convention for splitting a long chain. |
| `DECIDED-AND-DONE.template.md` | The archive: entries move here only after verified implementation. |
| `DECISION-BRIEFING.template.md` | For decisions that need several framed options and a recommendation grounded in the operator's own prior choices — not a neutral, open-ended listing. |

## ID convention

`D-YYYYMMDD-NNN` — the date the decision was first captured, plus a per-day sequence
number. IDs are never reused or renumbered, even after an entry moves from the open
chain to the archive; that is what keeps a citation (for example "see D-20260723-019")
stable across files and across time.

## Life-cycle

1. **Captured** — an entry is added to `TO-DECIDE.template.txt` with `STATUS: OPEN`, its
   source, the question, the options, and (if useful) a recommendation. No decision yet.
2. **Decided** — only a filled-in `DECISION:` line counts as authorization. An entry with
   options and a recommendation but an empty `DECISION:` line stays open, however old.
3. **Implemented & verified** — after the chosen option is actually carried out and the
   result is checked (not assumed), the full entry moves to `DECIDED-AND-DONE.template.md`
   with a one-line verification note (what was checked, and how).
4. **Archived** — once the decided-and-done file grows past roughly 200–300 lines, or the
   open chain past roughly 150 active lines, apply cut-and-clue: split sequentially and
   leave bidirectional predecessor/successor pointers so the chain stays walkable end to
   end.

## When to use a briefing vs. a plain chain entry

A plain `TO-DECIDE` entry is enough when the question is binary or the options are
self-evident. Use `DECISION-BRIEFING.template.md` when a decision spans several related
sub-questions, when the options need real explanation to be decidable, or when a
grounded recommendation materially helps the operator decide faster than a neutral
options list would. A briefing gets its own file and is referenced from a chain entry's
`SOURCE` field once it exists; after the operator answers, fill in the briefing's own
result table and move the chain entry through the life-cycle above.

## Host- and project-scoping

Global, cross-project decisions live in one shared chain. An operator running the same
agent across multiple hosts or machines may keep a `TO-DECIDE-<HOST>.txt` file for
host-specific decisions; it does not duplicate the global chain, it supplements it — read
both when host-specific context matters. Project-specific decisions are better kept in
that project's own `DECISIONS.md` and take precedence there (see step (0) of the runtime
loop); escalate to this ledger only for decisions with real cross-project or
operator-wide scope.

## Placeholders

`<USER>` / `<AGENT>` follow the same convention as the rest of this module (see the main
`README.md` and `templates/START.md`) — replace with the operator's and the agent's own
names when instantiating these templates for a real deployment. Do not commit a filled
instance with real decisions to a public repository; see `SECURITY.md` and `.gitignore`.
