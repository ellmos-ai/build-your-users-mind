from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import rating_form as rf  # noqa: E402
import score_predictions as sp  # noqa: E402


def sample_input() -> dict[str, object]:
    return {
        "schema": rf.INPUT_SCHEMA,
        "run_id": "synthetic-rating-run-1",
        "title": "Avatar Decisions Review",
        "description": "Synthetic review items for rating form verification.",
        "entries": [
            {
                "nr": 1,
                "id": "DEC-001",
                "kontext": "An operator requested a dry-run before writing files.",
                "entscheidung": "Run dry-run first and preview the output path.",
                "konfidenz": "🟡",
                "ziel": "ACTIONABLE",
            },
            {
                "nr": 2,
                "id": "DEC-002",
                "kontext": "A new external release target has no prior precedent.",
                "entscheidung": "Escalate to the operator instead of guessing.",
                "konfidenz": "🔴",
                "ziel": "USER",
            },
        ],
    }


def sample_response() -> dict[str, object]:
    return {
        "schema": rf.RESPONSE_SCHEMA,
        "run_id": "synthetic-rating-run-1",
        "saved_at": "2026-11-21T20:00:00Z",
        "ratings": [
            {
                "nr": 1,
                "id": "DEC-001",
                "entscheidung": "Run dry-run first and preview the output path.",
                "score": 9,
                "note": "Matches preference.",
                "note_source": "text",
            },
            {
                "nr": 2,
                "id": "DEC-002",
                "entscheidung": "Escalate to the operator instead of guessing.",
                "score": 4,
                "note": "Should clarify scope first.",
                "note_source": "voice",
            },
        ],
    }


class SchemaValidationTests(unittest.TestCase):
    def test_valid_input_and_response_schemas_pass(self) -> None:
        validated_in = rf.validate_input_payload(sample_input())
        self.assertEqual(len(validated_in["entries"]), 2)
        validated_out = rf.validate_response_payload(sample_response())
        self.assertEqual(validated_out["ratings"][0]["score"], 9)

        input_schema = json.loads((ROOT / "schemas" / "avatar-rating-input.schema.json").read_text(encoding="utf-8"))
        response_schema = json.loads(
            (ROOT / "schemas" / "avatar-rating-response.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(input_schema["properties"]["schema"]["const"], rf.INPUT_SCHEMA)
        self.assertEqual(response_schema["properties"]["schema"]["const"], rf.RESPONSE_SCHEMA)
        self.assertEqual(
            set(input_schema["properties"]["entries"]["items"]["required"]),
            {"id", "kontext", "entscheidung", "konfidenz", "ziel"},
        )

    def test_invalid_input_payloads_fail_closed(self) -> None:
        missing_field = sample_input()
        del missing_field["entries"][0]["ziel"]  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "missing required field 'ziel'"):
            rf.validate_input_payload(missing_field)

        duplicate_ids = sample_input()
        duplicate_ids["entries"][1]["id"] = "DEC-001"  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "duplicate entry id"):
            rf.validate_input_payload(duplicate_ids)

    def test_invalid_response_score_fails_closed(self) -> None:
        out_of_range = sample_response()
        out_of_range["ratings"][0]["score"] = 11  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "0..10"):
            rf.validate_response_payload(out_of_range)

        bool_score = sample_response()
        bool_score["ratings"][0]["score"] = True  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "0..10"):
            rf.validate_response_payload(bool_score)


class VoiceGatingTests(unittest.TestCase):
    def test_voice_disabled_renders_no_microphone_element(self) -> None:
        html_out = rf.render_rating_html(sample_input(), {"voice": {"enabled": False}})
        self.assertNotIn("voice-mic-btn", html_out)
        self.assertNotIn("data-voice-mic", html_out)
        self.assertNotIn("getUserMedia", html_out)
        self.assertNotIn("voice-notice", html_out)

    def test_default_example_config_is_disabled_and_has_no_microphone(self) -> None:
        cfg = json.loads(
            (ROOT / "templates" / "avatar-rating.config.example.json").read_text(encoding="utf-8")
        )
        self.assertFalse(cfg["voice"]["enabled"])
        html_out = rf.render_rating_html(sample_input(), cfg)
        self.assertNotIn("voice-mic-btn", html_out)
        self.assertNotIn("getUserMedia", html_out)

    def test_voice_enabled_without_module_shows_notice_and_no_microphone(self) -> None:
        cfg = {
            "voice": {
                "enabled": True,
                "provider": "ellmos-voice-io",
                "endpoint": "http://127.0.0.1:8765/transcribe",
            }
        }
        html_out = rf.render_rating_html(
            sample_input(),
            cfg,
            voice_probe=lambda _cfg: {
                "installed": False,
                "stt_available": False,
                "stt_engine": "",
                "reason": "Modul 'ellmos-voice-io' fehlt.",
            },
        )
        self.assertIn("voice-notice", html_out)
        self.assertIn("ellmos-voice-io", html_out)
        self.assertNotIn("voice-mic-btn", html_out)
        self.assertNotIn("getUserMedia", html_out)

    def test_voice_enabled_with_installed_module_renders_microphone_and_loopback(self) -> None:
        cfg = {
            "voice": {
                "enabled": True,
                "provider": "ellmos-voice-io",
                "endpoint": "http://127.0.0.1:8765/transcribe",
                "language": "de",
            }
        }
        html_out = rf.render_rating_html(
            sample_input(),
            cfg,
            voice_probe=lambda _cfg: {
                "installed": True,
                "stt_available": True,
                "stt_engine": "vosk",
                "reason": "",
            },
        )
        self.assertIn("voice-mic-btn", html_out)
        self.assertIn("getUserMedia", html_out)
        self.assertNotIn("voice-notice", html_out)

    def test_non_loopback_voice_endpoint_is_rejected(self) -> None:
        cfg = {
            "voice": {
                "enabled": True,
                "provider": "ellmos-voice-io",
                "endpoint": "https://remote.example.com/transcribe",
            }
        }
        with self.assertRaisesRegex(ValueError, "loopback"):
            rf.render_rating_html(sample_input(), cfg)


class FeedbackImportAndCliTests(unittest.TestCase):
    def test_response_converts_to_score_predictions_markdown(self) -> None:
        md = rf.response_to_feedback_markdown(sample_response())
        fb = sp.parse_feedback(md)
        self.assertEqual(fb[("2026-11-21", "dec-001")], "hit")
        self.assertEqual(fb[("2026-11-21", "dec-002")], "miss")

        actions = "\n".join([
            "2026-11-21T10:00:00Z\t🟡\ty\topen\tDEC-001\tRun dry-run",
            "2026-11-21T10:05:00Z\t🔴\ty\topen\tDEC-002\tEscalate",
        ])
        result = sp.score(sp.parse_actions(actions), feedback=fb)
        self.assertEqual(result["overall"]["resolved"], 2)
        self.assertEqual(result["overall"]["hits"], 1)

    def test_cli_build_and_import_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            in_file = base / "input.json"
            out_html = base / "rating.html"
            resp_file = base / "response.json"
            out_md = base / "feedback.md"
            in_file.write_text(json.dumps(sample_input()), encoding="utf-8")
            resp_file.write_text(json.dumps(sample_response()), encoding="utf-8")

            self.assertEqual(rf.main(["build", "--input", str(in_file), "--out", str(out_html)]), 0)
            html_text = out_html.read_text(encoding="utf-8")
            self.assertIn("Avatar Decisions Review", html_text)
            self.assertNotIn("voice-mic-btn", html_text)

            self.assertEqual(
                rf.main(["import-feedback", "--response", str(resp_file), "--out", str(out_md)]),
                0,
            )
            self.assertIn("verdict: 👍 confirmed", out_md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
