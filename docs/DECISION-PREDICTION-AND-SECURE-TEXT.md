# Decision prediction and Secure-Mode text simulation

> Status: development contract v2 after the judging hold. The deterministic contracts and tests are implemented;
> operator acceptance against a real private corpus/model remains open. Nothing in this document
> authorizes an action or publication.

## Separation of concerns

```text
evidence + policies + current context
                  |
                  +--> recommendation: best advised option
                  +--> prediction: likely operator option + probabilities
                  +--> text simulation: likely wording, labelled as synthetic

explicit operator response --> observed decision --> validation --> calibration
                                                        |
later adopted advice -----------------------------------+--> recovery score
```

The three model outputs are not interchangeable. A good advisor may recommend B while predicting
that the operator will choose A. A text candidate may sound plausible while the option prediction
is poorly calibrated. Execution authority is outside all three outputs.

## Append-only event stream

`schemas/decision-prediction-event.schema.json` describes the portable shape;
`scripts/decision_prediction.py` enforces the cross-event invariants that JSON Schema alone cannot.

| Event | Created from | Role |
|---|---|---|
| `prediction.created` | model output before feedback | immutable decision reference, options snapshot, recommendation, independent probability distribution, evidence/model identity |
| `decision.observed` | explicit operator response only | chosen offered option or a custom decision |
| `validation.scored` | explicit evaluation of fit/correction/harm | initial advice-process score |
| `advice.adopted` | explicit immediate or later adoption | one point per unique, previously documented material element |
| `user.bonus` | explicit operator grant | additional points, total still capped at 10 |

The original event is never rewritten. A late correction adds an `advice.adopted` event with
`source=later_correction`; projections expose both the initial and current score.

### Guarded write seam

Events enter the journal through one seam, so a federating surface such as ControlRoom never writes
the file itself:

```bash
python scripts/decision_prediction.py --events JOURNAL.jsonl --append event.json   # '-' reads stdin
```

The append revalidates the entire stream with the new event included, rejects an `occurred_at` that
predates the last entry, writes atomically, and prints a receipt with the event identity, the line
number, the line hash and the journal hash before and after. Within one file the cross-event
invariants are checked in line order, which alone would let a later write claim an earlier moment;
the timestamp guard closes that gap. A rejected append leaves the journal byte-identical. The
append-only journal and this receipt are the audit trail — there is no second audit store, and
`execution_authorized` stays false.

## Decision reference, projection and privacy contract

Contract v2 requires every `prediction.created` event to carry one closed `decision_ref`:

```json
{
  "decision_id": "D-20260820-001",
  "index_key": "D-20260820-001/E01",
  "scope": "controlroom",
  "source_locator": {
    "path": "decisions/open-decisions-4.txt",
    "block_id": "E01"
  },
  "source_sha256": "64 lowercase hexadecimal characters"
}
```

The nested object accepts no additional fields. Its scope must match the prediction scope, and the
source hash binds the reference to the exact source state without copying decision text. Later events
may reference only the `prediction_id`; they cannot redefine `decision_ref` or the option snapshot.

Each projection explicitly exposes `recommended_match`, `chosen_option_was_offered`,
`no_option_fit`, correction burden/deduction, harm penalty, `initial_score`, every validation event,
every recovery delta, every bonus event and `final_score`. `current_score` remains a tested
compatibility alias for `final_score`. The journal rejects raw prompts, raw decision text, private
prompts, Secure-Mode payloads, private avatar content, generic payload fields and action receipts.
`execution_authorized` is always false; action and receipt records remain owned by the separate
permission/execution system.

## Scoring

The initial base is 10 for the unmodified recommendation, 7 for another unmodified offered option,
or 3 when no option fits. A documented correction deduction can lower an offered choice to 5. A
0–3 harm penalty may lower the result to zero. Unique adopted advice elements and explicit bonus
events then add points, capped at 10.

This advice score is not a probability metric. The report separately computes top-1 accuracy,
multiclass Brier score and log loss for observed offered choices. Custom decisions count toward
advice-quality evaluation but are excluded from option-probability calibration.

## Secure-Mode text prototype

`scripts/secure_text_avatar.py` retrieves relevant records using a deterministic lexical overlap
score. The score is a transparent retrieval heuristic, not a calibrated claim about the operator.
Insufficient or novel evidence returns exit code 3 and `status=escalate`.

The default `plan` provider returns evidence IDs, scores and prompt hash without raw evidence or a
private prompt. The optional `ollama` provider sends the private prompt only to an explicit HTTP
loopback URL. Non-loopback URLs and embedded credentials are rejected. The tool does not launch or
configure Ollama and does not retain its private prompt.

Every result contains:

```json
{
  "mode": "secure",
  "label": "SIMULATED USER TEXT — NOT A USER STATEMENT",
  "private_prompt_included": false,
  "execution_authorized": false
}
```

Each result also has a content-derived `text_prediction_id` and may carry the originating
`prediction_id`, so registries can link wording simulation to a decision prediction without
merging their provenance.

Role-mode impersonation, external delivery and autonomous execution are intentionally absent.

## Registry integration contract

A future policy/decision registry can ingest this event stream without treating predictions as user
facts. Keep these identities distinct:

- `prediction_id` and immutable model/version;
- the stable, source-hashed `decision_ref` without copied source text;
- evidence IDs and policy IDs used before the decision;
- recommendation and option probabilities;
- explicit observed decision;
- validation reason, correction burden and harm penalty;
- each unique recovery/bonus event;
- current projection and calibration metrics;
- a separate execution authorization/action record owned by the permission system.

The registry may project a current view but must retain the event history and must never promote
simulated wording into operator evidence.

---

## Deutsch: Entscheidungsreferenz, Projektion und Datenschutzvertrag

Vertragsversion v2 verlangt für jedes Ereignis `prediction.created` genau einen geschlossenen
`decision_ref`. Er enthält die stabile Entscheidungs-ID, den Indexschlüssel, den Scope, einen
Quell-Locator aus Pfad und Block-ID sowie den SHA-256-Hash der Quelle. Zusätzliche Felder sind nicht
zulässig, der Scope muss mit dem Prognose-Scope übereinstimmen, und spätere Ereignisse dürfen die
Referenz oder den Optionen-Snapshot nicht neu definieren. Der Hash verankert den exakten Quellstand,
ohne den rohen Entscheidungstext in das Journal zu kopieren.

Die Projektion weist ausdrücklich aus, ob die Empfehlung getroffen wurde, ob die gewählte Option
angeboten war oder keine Option passte. Sie bewahrt Korrekturbelastung und -abzug, Schadensabzug,
`initial_score`, jedes Validierungsereignis, jedes Recovery-Delta, jedes Bonusereignis und
`final_score`. `current_score` ist ausschließlich ein getesteter Kompatibilitätsalias für
`final_score`.

Rohprompts, rohe Entscheidungstexte, private Prompts, Secure-Mode-Payloads, private Avatarinhalte,
generische Payload-Felder und Action-Receipts werden fail-closed abgewiesen. Eine Prognose behält
immer `execution_authorized=false`. Aktion, Ausführungsbefugnis und Receipt bleiben getrennte
Datensätze des zuständigen Rechte-/Ausführungssystems; BYUM übernimmt diese Autorität nicht.
