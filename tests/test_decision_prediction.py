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
        "decision_ref": {
            "decision_id": "D-20260820-001",
            "index_key": "D-20260820-001/E01",
            "scope": "test",
            "source_locator": {
                "path": ".TOPICS/_control-center/_DECISIONS/TO-DECIDE-USER_4.txt",
                "block_id": "E01",
            },
            "source_sha256": "a" * 64,
        },
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
    def test_prediction_requires_structured_decision_ref(self) -> None:
        missing = prediction()
        del missing["decision_ref"]
        with self.assertRaisesRegex(ValueError, "decision_ref must be an object"):
            dp.project([missing])

        malformed_hash = prediction()
        malformed_hash["decision_ref"]["source_sha256"] = "not-a-sha256"  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "source_sha256 must be 64 lowercase hexadecimal"):
            dp.project([malformed_hash])

        mismatched_scope = prediction()
        mismatched_scope["decision_ref"]["scope"] = "another-scope"  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "decision_ref.scope must match scope"):
            dp.project([mismatched_scope])

    def test_decision_ref_is_owned_only_by_prediction_created(self) -> None:
        observed = decision("A")
        observed["decision_ref"] = prediction()["decision_ref"]
        with self.assertRaisesRegex(ValueError, "decision_ref is only allowed on prediction.created"):
            dp.project([prediction(), observed])

    def test_private_or_execution_payload_fields_are_rejected(self) -> None:
        for field in (
            "prompt", "raw_prompt", "decision_text", "raw_decision_text", "private_prompt", "secure_text",
            "secure_text_payload", "payload", "action_payload", "execution_payload", "avatar_content", "receipt",
            "action_receipt", "execution_receipt",
        ):
            with self.subTest(field=field):
                event = prediction()
                event[field] = "must not enter the prediction journal"
                with self.assertRaisesRegex(ValueError, "forbidden private or execution field"):
                    dp.project([event])

    def test_followup_events_cannot_claim_execution_authority(self) -> None:
        observed = decision("A")
        observed["execution_authorized"] = False
        with self.assertRaisesRegex(ValueError, "execution_authorized is only allowed on prediction.created"):
            dp.project([prediction(), observed])

    def test_duplicate_prediction_cannot_replace_reference_or_options_snapshot(self) -> None:
        replacement = prediction(recommended="B")
        replacement["event_id"] = "EV-replacement"
        replacement["decision_ref"]["source_sha256"] = "b" * 64  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "duplicate prediction.created"):
            dp.project([prediction(), replacement])

    def test_recovery_event_requires_observation_and_validation_first(self) -> None:
        with self.assertRaisesRegex(ValueError, "recovery events require validation.scored first"):
            dp.project([prediction(), adopted("EV-4", "privacy-gate")])

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
        self.assertEqual(item["final_score"], 10)

    def test_projection_exposes_decision_scoring_and_event_provenance(self) -> None:
        bonus = {
            "schema": dp.SCHEMA,
            "event_id": "EV-5",
            "prediction_id": "DP-1",
            "event_type": "user.bonus",
            "occurred_at": "2026-08-20T10:04:00Z",
            "points": 2,
            "reason": "Explicit operator bonus.",
        }
        events = [
            prediction(), decision("B"), validation(correction=2, harm=1),
            adopted("EV-4", "privacy-gate", "later_correction"), bonus,
        ]
        item = dp.project(events)["predictions"][0]

        self.assertEqual(item["decision_ref"], prediction()["decision_ref"])
        self.assertFalse(item["recommended_match"])
        self.assertTrue(item["chosen_option_was_offered"])
        self.assertFalse(item["no_option_fit"])
        self.assertEqual(item["correction_burden"], 2)
        self.assertEqual(item["correction_deduction"], 2)
        self.assertEqual(item["harm_penalty"], 1)
        self.assertEqual(item["initial_score"], 4)
        self.assertEqual(item["final_score"], 7)
        self.assertEqual(item["current_score"], item["final_score"])
        self.assertFalse(item["execution_authorized"])
        self.assertNotIn("action_receipt", item)
        self.assertEqual(
            item["validation_events"],
            [{
                "event_id": "EV-3",
                "occurred_at": "2026-08-20T10:02:00Z",
                "correction_burden": 2,
                "correction_deduction": 2,
                "harm_penalty": 1,
                "reason": "Explicit operator evaluation.",
            }],
        )
        self.assertEqual(item["recovery_deltas"][0]["event_id"], "EV-4")
        self.assertEqual(item["recovery_deltas"][0]["points"], 1)
        self.assertEqual(item["bonus_events"][0]["event_id"], "EV-5")
        self.assertEqual(item["bonus_events"][0]["points"], 2)

    def test_custom_decision_explicitly_records_that_no_option_fit(self) -> None:
        item = dp.project([prediction(), decision(None, "A different solution"), validation()])["predictions"][0]
        self.assertFalse(item["recommended_match"])
        self.assertFalse(item["chosen_option_was_offered"])
        self.assertTrue(item["no_option_fit"])

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


class JsonSchemaContract(unittest.TestCase):
    def test_schema_requires_closed_structured_decision_ref(self) -> None:
        schema = json.loads((ROOT / "schemas" / "decision-prediction-event.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(dp.SCHEMA, "byum.decision-prediction.v2")
        self.assertEqual(schema["properties"]["schema"]["const"], dp.SCHEMA)
        self.assertIn("decision_ref", schema["properties"])
        decision_ref = schema["properties"]["decision_ref"]
        self.assertEqual(
            set(decision_ref["required"]),
            {"decision_id", "index_key", "scope", "source_locator", "source_sha256"},
        )
        self.assertFalse(decision_ref["additionalProperties"])
        self.assertEqual(decision_ref["properties"]["source_sha256"]["pattern"], "^[0-9a-f]{64}$")
        locator = decision_ref["properties"]["source_locator"]
        self.assertEqual(set(locator["required"]), {"path", "block_id"})
        self.assertFalse(locator["additionalProperties"])


class GuardedAppend(unittest.TestCase):
    def journal(self, stack: contextlib.ExitStack) -> Path:
        return Path(stack.enter_context(tempfile.TemporaryDirectory())) / "events.jsonl"

    def test_append_creates_journal_and_returns_receipt(self) -> None:
        with contextlib.ExitStack() as stack:
            path = self.journal(stack)
            receipt = dp.append_event(path, prediction())
            self.assertTrue(receipt["appended"])
            self.assertEqual(receipt["event_id"], "EV-1")
            self.assertEqual(receipt["line_number"], 1)
            self.assertIsNone(receipt["journal_sha256_before"])
            self.assertFalse(receipt["execution_authorized"])
            self.assertEqual(len(dp.load_events(path)), 1)

            second = dp.append_event(path, decision())
            self.assertEqual(second["events_before"], 1)
            self.assertEqual(second["journal_sha256_before"], receipt["journal_sha256_after"])
            self.assertEqual(len(dp.load_events(path)), 2)

    def test_append_rejects_backdated_event(self) -> None:
        with contextlib.ExitStack() as stack:
            path = self.journal(stack)
            dp.append_event(path, prediction())
            backdated = decision()
            backdated["occurred_at"] = "2026-08-20T09:59:00Z"
            with self.assertRaisesRegex(ValueError, "retroactive"):
                dp.append_event(path, backdated)
            self.assertEqual(len(dp.load_events(path)), 1)

    def test_append_rejects_invariant_break_without_touching_the_journal(self) -> None:
        with contextlib.ExitStack() as stack:
            path = self.journal(stack)
            first = dp.append_event(path, prediction())
            orphan = dict(decision())
            orphan["prediction_id"] = "DP-unknown"
            with self.assertRaises(ValueError):
                dp.append_event(path, orphan)
            self.assertEqual(dp._digest(path), first["journal_sha256_after"])

    def test_append_rejects_execution_and_private_payload_fields(self) -> None:
        with contextlib.ExitStack() as stack:
            path = self.journal(stack)
            leaky = prediction()
            leaky["action_receipt"] = "granted"
            with self.assertRaises(ValueError):
                dp.append_event(path, leaky)
            self.assertFalse(path.exists())

    def test_cli_append_prints_receipt_and_reports_errors(self) -> None:
        with contextlib.ExitStack() as stack:
            path = self.journal(stack)
            event_file = path.parent / "event.json"
            event_file.write_text(json.dumps(prediction()), encoding="utf-8")
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                code = dp.main(["--events", str(path), "--append", str(event_file)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(stream.getvalue())["event_id"], "EV-1")

            errors = io.StringIO()
            with contextlib.redirect_stderr(errors):
                code = dp.main(["--events", str(path), "--append", str(event_file)])
            self.assertEqual(code, 2)
            self.assertIn("cannot append", errors.getvalue())
            self.assertEqual(len(dp.load_events(path)), 1)


if __name__ == "__main__":
    unittest.main()
