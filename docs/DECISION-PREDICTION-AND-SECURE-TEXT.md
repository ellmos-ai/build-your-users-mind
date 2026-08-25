# Decision prediction and Secure-Mode text simulation

> Status: local judging-hold prototype. The deterministic contracts and tests are implemented;
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
| `prediction.created` | model output before feedback | options, recommendation, independent probability distribution, evidence/model identity |
| `decision.observed` | explicit operator response only | chosen offered option or a custom decision |
| `validation.scored` | explicit evaluation of fit/correction/harm | initial advice-process score |
| `advice.adopted` | explicit immediate or later adoption | one point per unique, previously documented material element |
| `user.bonus` | explicit operator grant | additional points, total still capped at 10 |

The original event is never rewritten. A late correction adds an `advice.adopted` event with
`source=later_correction`; projections expose both the initial and current score.

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
- evidence IDs and policy IDs used before the decision;
- recommendation and option probabilities;
- explicit observed decision;
- validation reason, correction burden and harm penalty;
- each unique recovery/bonus event;
- current projection and calibration metrics;
- a separate execution authorization/action record owned by the permission system.

The registry may project a current view but must retain the event history and must never promote
simulated wording into operator evidence.
