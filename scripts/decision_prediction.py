#!/usr/bin/env python3
"""Validate and score event-sourced decision predictions.

Recommendation quality, likely user choice, simulated wording, observed user
decision, and execution authority are deliberately separate.  Events are
append-only JSONL and contain references to evidence, never authority grants.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from pipeline_common import atomic_write_text, load_jsonl, validate_timestamp

SCHEMA = "byum.decision-prediction.v1"
EVENT_TYPES = {
    "prediction.created",
    "decision.observed",
    "validation.scored",
    "advice.adopted",
    "user.bonus",
}
CONFIDENCE = {"high", "medium", "low"}


def _string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _integer(value: object, field: str, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f"{field} must be an integer from {low} to {high}")
    return value


def _event_base(event: dict[str, Any], line_number: int) -> tuple[str, str]:
    prefix = f"line {line_number}"
    if event.get("schema") != SCHEMA:
        raise ValueError(f"{prefix}: schema must be {SCHEMA!r}")
    event_id = _string(event.get("event_id"), f"{prefix}: event_id")
    prediction_id = _string(event.get("prediction_id"), f"{prefix}: prediction_id")
    event_type = _string(event.get("event_type"), f"{prefix}: event_type")
    if event_type not in EVENT_TYPES:
        raise ValueError(f"{prefix}: unknown event_type {event_type!r}")
    try:
        validate_timestamp(event.get("occurred_at"))
    except ValueError as exc:
        raise ValueError(f"{prefix}: invalid occurred_at: {exc}") from exc
    return event_id, prediction_id


def _validate_prediction(event: dict[str, Any], prefix: str) -> None:
    _string(event.get("decision_type"), f"{prefix}: decision_type")
    _string(event.get("scope"), f"{prefix}: scope")
    if event.get("execution_authorized") is not False:
        raise ValueError(f"{prefix}: a prediction must set execution_authorized=false")

    evidence_ids = event.get("evidence_ids")
    if not isinstance(evidence_ids, list) or not evidence_ids:
        raise ValueError(f"{prefix}: evidence_ids must be a non-empty list")
    if any(not isinstance(item, str) or not item.strip() for item in evidence_ids):
        raise ValueError(f"{prefix}: evidence_ids must contain non-empty strings")
    if len(set(evidence_ids)) != len(evidence_ids):
        raise ValueError(f"{prefix}: evidence_ids contain duplicates")

    options = event.get("options")
    if not isinstance(options, list) or len(options) < 2:
        raise ValueError(f"{prefix}: options must contain at least two entries")
    option_ids: list[str] = []
    for index, option in enumerate(options):
        if not isinstance(option, dict):
            raise ValueError(f"{prefix}: option {index} must be an object")
        option_ids.append(_string(option.get("id"), f"{prefix}: option {index} id"))
        _string(option.get("label"), f"{prefix}: option {index} label")
    if len(set(option_ids)) != len(option_ids):
        raise ValueError(f"{prefix}: option IDs must be unique")

    recommendation = event.get("recommendation")
    prediction = event.get("prediction")
    if not isinstance(recommendation, dict) or not isinstance(prediction, dict):
        raise ValueError(f"{prefix}: recommendation and prediction must be objects")
    recommended = _string(recommendation.get("option_id"), f"{prefix}: recommendation.option_id")
    likely = _string(prediction.get("likely_option"), f"{prefix}: prediction.likely_option")
    _string(recommendation.get("rationale"), f"{prefix}: recommendation.rationale")
    if recommended not in option_ids or likely not in option_ids:
        raise ValueError(f"{prefix}: recommended and likely options must be offered")
    if prediction.get("confidence") not in CONFIDENCE:
        raise ValueError(f"{prefix}: prediction.confidence must be high, medium, or low")

    probabilities = prediction.get("probabilities")
    if not isinstance(probabilities, dict) or set(probabilities) != set(option_ids):
        raise ValueError(f"{prefix}: probabilities must cover exactly the offered option IDs")
    total = 0.0
    for option_id, probability in probabilities.items():
        if isinstance(probability, bool) or not isinstance(probability, (int, float)):
            raise ValueError(f"{prefix}: probability for {option_id!r} must be numeric")
        probability = float(probability)
        if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
            raise ValueError(f"{prefix}: probability for {option_id!r} must be finite and in [0,1]")
        total += probability
    if not math.isclose(total, 1.0, abs_tol=1e-6):
        raise ValueError(f"{prefix}: probabilities must sum to 1.0, got {total}")
    max_probability = max(float(value) for value in probabilities.values())
    if not math.isclose(float(probabilities[likely]), max_probability, abs_tol=1e-12):
        raise ValueError(f"{prefix}: likely_option must have maximum probability")

    model = event.get("model")
    if not isinstance(model, dict):
        raise ValueError(f"{prefix}: model must be an object")
    _string(model.get("name"), f"{prefix}: model.name")
    _string(model.get("version"), f"{prefix}: model.version")


def _validate_event_payload(event: dict[str, Any], line_number: int) -> None:
    prefix = f"line {line_number}"
    event_type = event["event_type"]
    if event_type == "prediction.created":
        _validate_prediction(event, prefix)
    elif event_type == "decision.observed":
        if event.get("explicit_user_feedback") is not True:
            raise ValueError(f"{prefix}: decision.observed requires explicit_user_feedback=true")
        selected = event.get("selected_option")
        if selected is not None:
            _string(selected, f"{prefix}: selected_option")
        if selected is None:
            _string(event.get("custom_decision"), f"{prefix}: custom_decision")
    elif event_type == "validation.scored":
        _integer(event.get("correction_deduction"), f"{prefix}: correction_deduction", 0, 5)
        _integer(event.get("harm_penalty"), f"{prefix}: harm_penalty", 0, 3)
        _string(event.get("reason"), f"{prefix}: reason")
    elif event_type == "advice.adopted":
        _string(event.get("element_id"), f"{prefix}: element_id")
        if event.get("source") not in {"immediate", "later_correction"}:
            raise ValueError(f"{prefix}: advice source must be immediate or later_correction")
        _integer(event.get("points"), f"{prefix}: points", 1, 1)
        _string(event.get("reason"), f"{prefix}: reason")
    elif event_type == "user.bonus":
        _integer(event.get("points"), f"{prefix}: points", 1, 10)
        _string(event.get("reason"), f"{prefix}: reason")


def validate_events(events: list[dict[str, Any]]) -> None:
    seen_event_ids: set[str] = set()
    predictions: dict[str, dict[str, Any]] = {}
    phase: dict[str, set[str]] = defaultdict(set)
    adopted: dict[str, set[str]] = defaultdict(set)
    for line_number, event in enumerate(events, 1):
        event_id, prediction_id = _event_base(event, line_number)
        if event_id in seen_event_ids:
            raise ValueError(f"line {line_number}: duplicate event_id {event_id!r}")
        seen_event_ids.add(event_id)
        _validate_event_payload(event, line_number)
        event_type = event["event_type"]
        if event_type == "prediction.created":
            if prediction_id in predictions:
                raise ValueError(f"line {line_number}: duplicate prediction.created for {prediction_id!r}")
            predictions[prediction_id] = event
            phase[prediction_id].add(event_type)
            continue
        if prediction_id not in predictions:
            raise ValueError(f"line {line_number}: event precedes prediction.created for {prediction_id!r}")
        prediction = predictions[prediction_id]
        if event_type == "decision.observed":
            if event_type in phase[prediction_id]:
                raise ValueError(f"line {line_number}: duplicate decision.observed for {prediction_id!r}")
            selected = event.get("selected_option")
            option_ids = {option["id"] for option in prediction["options"]}
            if selected is not None and selected not in option_ids:
                raise ValueError(f"line {line_number}: selected_option is not offered; use custom_decision")
        elif event_type == "validation.scored":
            if "decision.observed" not in phase[prediction_id]:
                raise ValueError(f"line {line_number}: validation requires decision.observed first")
            if event_type in phase[prediction_id]:
                raise ValueError(f"line {line_number}: duplicate validation.scored for {prediction_id!r}")
        elif event_type in {"advice.adopted", "user.bonus"}:
            if "validation.scored" not in phase[prediction_id]:
                raise ValueError(f"line {line_number}: recovery events require validation.scored first")
            if event_type == "advice.adopted":
                element_id = event["element_id"]
                if element_id in adopted[prediction_id]:
                    raise ValueError(f"line {line_number}: advice element {element_id!r} was already credited")
                adopted[prediction_id].add(element_id)
        phase[prediction_id].add(event_type)


def _initial_advice_score(prediction: dict[str, Any], decision: dict[str, Any],
                          validation: dict[str, Any]) -> tuple[int, int]:
    selected = decision.get("selected_option")
    recommended = prediction["recommendation"]["option_id"]
    offered = {option["id"] for option in prediction["options"]}
    if selected == recommended:
        base = 10
        max_deduction = 5
    elif selected in offered:
        base = 7
        max_deduction = 2
    else:
        base = 3
        max_deduction = 0
    correction = validation["correction_deduction"]
    if correction > max_deduction:
        raise ValueError(
            f"prediction {prediction['prediction_id']!r}: correction_deduction {correction} "
            f"exceeds {max_deduction} for base score {base}"
        )
    return base, max(0, base - correction - validation["harm_penalty"])


def project(events: list[dict[str, Any]]) -> dict[str, Any]:
    validate_events(events)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        grouped[event["prediction_id"]].append(event)

    projections: list[dict[str, Any]] = []
    probability_rows: list[tuple[dict[str, float], str, str]] = []
    for prediction_id, rows in grouped.items():
        by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            by_type[row["event_type"]].append(row)
        prediction = by_type["prediction.created"][0]
        decision = by_type["decision.observed"][0] if by_type["decision.observed"] else None
        validation = by_type["validation.scored"][0] if by_type["validation.scored"] else None
        item: dict[str, Any] = {
            "prediction_id": prediction_id,
            "recommended_option": prediction["recommendation"]["option_id"],
            "likely_option": prediction["prediction"]["likely_option"],
            "confidence": prediction["prediction"]["confidence"],
            "status": "pending",
            "selected_option": decision.get("selected_option") if decision else None,
            "initial_score": None,
            "recovery_points": 0,
            "bonus_points": 0,
            "current_score": None,
        }
        if decision and decision.get("selected_option") is not None:
            probability_rows.append(
                (prediction["prediction"]["probabilities"], decision["selected_option"],
                 prediction["prediction"]["likely_option"])
            )
        if decision and validation:
            base, initial = _initial_advice_score(prediction, decision, validation)
            recovery = len(by_type["advice.adopted"])
            bonus = sum(row["points"] for row in by_type["user.bonus"])
            item.update({
                "status": "validated",
                "base_score": base,
                "initial_score": initial,
                "recovery_points": recovery,
                "bonus_points": bonus,
                "current_score": min(10, initial + recovery + bonus),
            })
        elif decision:
            item["status"] = "decision-observed"
        projections.append(item)

    accuracy = None
    brier = None
    log_loss = None
    if probability_rows:
        accuracy = sum(1 for _, actual, likely in probability_rows if actual == likely) / len(probability_rows)
        brier = sum(
            sum((probability - (1.0 if option == actual else 0.0)) ** 2
                for option, probability in probabilities.items())
            for probabilities, actual, _ in probability_rows
        ) / len(probability_rows)
        log_loss = sum(-math.log(max(probabilities[actual], 1e-15))
                       for probabilities, actual, _ in probability_rows) / len(probability_rows)
    scores = [item["current_score"] for item in projections if item["current_score"] is not None]
    return {
        "schema": "byum.decision-prediction-report.v1",
        "predictions": projections,
        "summary": {
            "count": len(projections),
            "validated": len(scores),
            "custom_decisions": sum(
                1 for item in projections
                if item["status"] != "pending" and item["selected_option"] is None
            ),
            "top1_accuracy": accuracy,
            "multiclass_brier": brier,
            "log_loss": log_loss,
            "mean_advice_score": (sum(scores) / len(scores)) if scores else None,
        },
    }


def format_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "Decision-prediction report",
        f"  predictions: {summary['count']}  validated: {summary['validated']}",
        f"  top-1 accuracy: {summary['top1_accuracy'] if summary['top1_accuracy'] is not None else 'n/a'}",
        f"  multiclass Brier: {summary['multiclass_brier'] if summary['multiclass_brier'] is not None else 'n/a'}",
        f"  log loss: {summary['log_loss'] if summary['log_loss'] is not None else 'n/a'}",
        f"  mean advice score: {summary['mean_advice_score'] if summary['mean_advice_score'] is not None else 'n/a'}",
    ]
    for item in report["predictions"]:
        lines.append(
            f"  - {item['prediction_id']}: likely={item['likely_option']} "
            f"recommended={item['recommended_option']} selected={item['selected_option']} "
            f"score={item['current_score']} status={item['status']}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--events", required=True, help="append-only decision event JSONL")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--out", default="", help="write report to a file")
    args = parser.parse_args(argv)
    try:
        events = load_events(Path(args.events).expanduser())
        report = project(events)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"ERROR: invalid decision events: {exc}", file=sys.stderr)
        return 2
    payload = json.dumps(report, ensure_ascii=False, indent=2) if args.json else format_report(report)
    if args.out:
        atomic_write_text(Path(args.out).expanduser(), payload + "\n")
    else:
        print(payload)
    return 0


def load_events(path: Path) -> list[dict[str, Any]]:
    return [dict(row) for row in load_jsonl(path)]


if __name__ == "__main__":
    raise SystemExit(main())
