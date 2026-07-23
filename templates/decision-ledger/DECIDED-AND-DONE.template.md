# DECIDED-AND-DONE — archived decisions

State: <YYYY-MM-DD>
Purpose: verified, implemented, or otherwise closed decisions moved out of the open chain.

---
Active open chain: <path>/TO-DECIDE.template.txt
Archived full states: <path>/_archive/ (optional, for large historical cuts)
---

## Archive rule

Only move an entry here after its implementation is verified — not merely decided. When
this file exceeds roughly 200–300 lines, apply cut-and-clue: split into a dated archive
file and leave a pointer, exactly as in the open chain. Entries are historical
documentation; technical claims are not re-validated during a later structural migration
unless explicitly noted inline.

## D-<YYYYMMDD>-<NNN> — <short title>

STATUS: DONE <YYYY-MM-DD> — <one-line verification note, e.g. link, commit, or record ID>
SOURCE: `<where this decision originated>`
QUESTION: <the concrete question that needed a decision>
OPTIONS:
- A — <option A>
- B — <option B>
RECOMMENDATION: <the agent's recommendation and why>
DECISION: [<the option actually chosen, with any operator qualifier or condition>]

---
