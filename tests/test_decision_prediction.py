from __future__ import annotations

import contextlib
import io
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import decision_prediction as dp  # noqa: E402


def prediction(*, probabilities: dict[str, float] | None = None,
               likely: str = "A", recommended: str = "A") -> dict[str, object]:
    return {
        "schema": dp.SCHEMA,
        "event_id": "EV-1",
        "prediction_id": "DP-1",
        "event_type": "prediction.created",
        "occurred_at": "2026-08-20T10:00:00Z",
        "decision_type": "test.choice",
        "scope": "test",
        "evidence_ids": ["H-1"],
        "options": [{"id": "A", "label": "Alpha"}, {"id": "B", "label": "Beta"}],
        "recommendation": {"option_id": recommended, "rationale": "Best supported option."},
        "prediction": {
            "likely_option": likely,
            "probabilities": probabilities or {"A": 0.75, "B": 0.25},
            "confidence": "medium",
        },
        "model": {"name": "test-model", "version": "1"},
        "execution_authorized": False,
    }


def decision(selected: str | None = "A", custom: str = "") -> dict[str, object]:
    event: dict[str, object] = {
        "schema": dp.SCHEMA,
        "event_id": "EV-2",
        "prediction_id": "DP-1",
        "event_type": "decision.observed",
        "occurred_at": "2026-08-20T10:01:00Z",
        "explicit_user_feedback": True,
        "selected_option": selected,
    }
    if custom:
        event["custom_decision"] = custom
    return event


def validation(correction: int = 0, harm: int = 0) -> dict[str, object]:
    return {
        "schema": dp.SCHEMA,
        "event_id": "EV-3",
        "prediction_id": "DP-1",
        "event_type": "validation.scored",
        "occurred_at": "2026-08-20T10:02:00Z",
        "correction_deduction": correction,
        "harm_penalty": harm,
        "reason": "Explicit operator evaluation.",
    }


def adopted(event_id: str, element_id: str, source: str = "immediate") -> dict[str, object]:
    return {
        "schema": dp.SCHEMA,
        "event_id": event_id,
        "prediction_id": "DP-1",
        "event_type": "advice.adopted",
        "occurred_at": "2026-08-20T10:03:00Z",
        "element_id": element_id,
        "source": source,
        "points": 1,
        "reason": "Operator adopted this previously recorded element.",
    }


class ValidationAndScoring(unittest.TestCase):
    def test_recommended_option_without_correction_scores_ten(self) -> None:
        report = dp.project([prediction(), decision("A"), validation()])
        self.assertEqual(report["predictions"][0]["current_score"], 10)

    def test_offered_alternative_without_text_scores_seven(self) -> None:
        report = dp.project([prediction(), decision("B"), validation()])
        self.assertEqual(report["predictions"][0]["base_score"], 7)
        self.assertEqual(report["predictions"][0]["current_score"], 7)

    def test_text_correction_can_reduce_recommendation_to_five(self) -> None:
        report = dp.project([prediction(), decision("A"), validation(correction=5)])
        self.assertEqual(report["predictions"][0]["current_score"], 5)

    def test_unoffered_decision_starts_at_three_and_accepts_harm_penalty(self) -> None:
        report = dp.project([prediction(), decision(None, "A different solution"), validation(harm=2)])
        item = report["predictions"][0]
        self.assertEqual(item["base_score"], 3)
        self.assertEqual(item["current_score"], 1)

    def test_recovery_and_user_bonus_are_append_only_and_capped(self) -> None:
        bonus = {
            "schema": dp.SCHEMA,
            "event_id": "EV-6",
            "prediction_id": "DP-1",
            "event_type": "user.bonus",
            "occurred_at": "2026-08-21T10:00:00Z",
            "points": 6,
            "reason": "Explicit operator bonus.",
        }
        events = [
            prediction(), decision(None, "Custom"), validation(),
            adopted("EV-4", "privacy-gate"),
            adopted("EV-5", "local-only", "later_correction"),
            bonus,
        ]
        item = dp.project(events)["predictions"][0]
        self.assertEqual(item["initial_score"], 3)
        self.assertEqual(item["recovery_points"], 2)
        self.assertEqual(item["bonus_points"], 6)
        self.assertEqual(item["current_score"], 10)

    def test_duplicate_advice_element_cannot_be_double_counted(self) -> None:
        events = [
            prediction(), decision(None, "Custom"), validation(),
            adopted("EV-4", "same"), adopted("EV-5", "same"),
        ]
        with self.assertRaisesRegex(ValueError, "already credited"):
            dp.project(events)

    def test_prediction_never_authorizes_execution(self) -> None:
        event = prediction()
        event["execution_authorized"] = True
        with self.assertRaisesRegex(ValueError, "execution_authorized=false"):
            dp.project([event])

    def test_probabilities_are_strict_and_likely_is_argmax(self) -> None:
        with self.assertRaisesRegex(ValueError, "sum to 1.0"):
            dp.project([prediction(probabilities={"A": 0.8, "B": 0.8})])
        with self.assertRaisesRegex(ValueError, "maximum probability"):
            dp.project([prediction(likely="B")])

    def test_probability_metrics_are_separate_from_advice_score(self) -> None:
        report = dp.project([prediction(), decision("B"), validation()])
        summary = report["summary"]
        self.assertEqual(summary["top1_accuracy"], 0.0)
        self.assertTrue(math.isclose(summary["multiclass_brier"], 1.125))
        self.assertTrue(math.isclose(summary["log_loss"], -math.log(0.25)))
        self.assertEqual(summary["mean_advice_score"], 7.0)

    def test_feedback_must_be_explicit(self) -> None:
        event = decision("A")
        event["explicit_user_feedback"] = False
        with self.assertRaisesRegex(ValueError, "explicit_user_feedback=true"):
            dp.project([prediction(), event])


class Cli(unittest.TestCase):
    def test_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            rows = [prediction(), decision("A"), validation()]
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = dp.main(["--events", str(path), "--json"])
            self.assertEqual(rc, 0)
            self.assertEqual(json.loads(output.getvalue())["summary"]["mean_advice_score"], 10.0)


if __name__ == "__main__":
    unittest.main()
