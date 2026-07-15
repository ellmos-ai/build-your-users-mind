# TAXONOMY — 8 Prompt Types + Classification Fields

> Standalone version (module is self-contained). **Methodological basis:** *Prompt-Archaeology*
> (L. Geiger) — the method of classifying a complete human-AI interaction protocol.

## The 8 Prompt Types

| Type | Code | Definition | Indicator |
|---|---|---|---|
| Start Prompt | **SP** | Initiates a new analysis or phase | No reference to prior context |
| Follow-up Topic | **NT** | Deepens existing topic | "And what about...?" |
| Follow-up Method | **NM** | Triggers method/tool/review/search/agent | Action verb |
| Follow-up Control | **NS** | Manages sequence or priority | "Wait", "first", "stop" |
| Correction | **KO** | Corrects an error or assumption | Negation, counterexample |
| Confirmation | **BE** | Validates intermediate status | Short agreement/acknowledgment |
| Course Change | **RA** | Fundamental change of direction | Questions the entire framework |
| Meta-Prompt | **MP** | About the process or dialogue itself | Process terminology |

**Borderline Cases:** SP vs. NT (new vs. connected) · NM vs. NS (trigger method vs. re-order only) ·
BE vs. KO ("yes, but..." is usually KO) · RA is rarer than KO, concerns the entire framework.

## Classification Fields (per Prompt)

| Field | Values |
|---|---|
| `type_code` | SP/NT/NM/NS/KO/BE/RA/MP |
| `topic` | Short topic (project-related) |
| `is_decision` | true if decision, preference, rule, correction, or course change |
| `decision_kind` | preference / correction / rule / direction_change / approval / rejection / process / none |
| `formulation_pattern` | Characterizing phrasing of the user (original phrasing, short) |
| `method_triggered` | WebSearch / WebFetch / Multi-Agent / Review / Cross-Model / Script / LaTeX / -- |
| `is_turning_point` | true/false |
| `outcome_signal` *(deterministic, Stage 0/1)* | praise / correction / reissue / none (derived from the next user turn) |

`outcome_signal` is deliberately conservative: an ordinary or unrecognized next prompt is `none`.
It is a weak interaction signal, not a direct measure of satisfaction or intent.

## Executable Stage-2 contract

- `scripts/chunk_corpus.py` writes a fresh `manifest.json`; managed stale chunk/classification files
  are removed on rerun. The manifest binds the set to the exact corpus SHA-256 and every chunk to
  its own SHA-256 plus expected row count.
- Each worker follows `templates/CLASSIFY-CHUNK.md` and writes the manifest-named `cat_*.jsonl` file.
- Every object must match `schemas/classification.schema.json` and preserve its stable evidence ID.
- `scripts/validate_classifications.py` is mandatory before aggregation. It rejects missing/malformed
  rows, extra or stale files, unknown IDs, and collisions with a non-zero exit code.

## Bias Indicators (Stage 4)
- **Confirmation:Correction (B:K)** — Disparity suggests approval bias; **silent approval is
  invisible** (not typed) → corrections are overrepresented.
- **Correction Rate per Topic** — Error-prone topics.
- **Proactive:Reactive** — Does the user lead or are they AI-driven?
- **Course Change Rate** — Epistemic flexibility.

## Historical Failure Mode: Artifact Contamination + Chunk Collisions

Empirically observed on a real run: an inter-rater spot check (blind second LLM rater, Cohen's
Kappa) on `type_code` came back **poor (κ ≈ 0.24, n=120)**. Root cause: despite the "human-typed
only" filter (Step 2), the corpus still contained a meaningful share of **structural non-human
artifacts** — context-compacting continuation summaries ("This session is being continued…"),
stop-hook feedback, hook activations, loaded skill/tool text, and command caveats. The original
swarm and the second rater typed these artifacts inconsistently (mostly MP↔NT confusion). A second,
independent issue: chunk files can **collide** — the same prompt ID gets classified in more than one
`cat_*.jsonl` chunk, silently duplicating/overwriting its label.

The deterministic pipeline now filters the documented artifact classes, carries Codex turn context,
builds fresh chunks, and enforces the strict collision/completeness gate above. This prevents the
known mechanical cause; it does **not** prove semantic classifier quality.

**Consequences:**
- Treat type-based statistics (`04_statistik.md`) as provisional unless the current corpus has passed
  the strict validator and a representative human/inter-rater semantic spot check.
- The underlying **text** of a prompt is usually still trustworthy for `WHAT-<USER>-SAID` evidence
  citations even when its **type label** is not — don't discard a corpus over this, just don't lean on
  the type distribution for high-stakes claims without a spot check first.
- Run `scripts/verify_ids.py` on a random or load-bearing ID sample. Prompt text is hidden by default;
  add `--show-text` only during an intentional private review.
