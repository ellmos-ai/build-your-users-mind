from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import secure_text_avatar as sta  # noqa: E402


RECORDS = [
    {"id": "H-1", "ts": "2026-08-01T10:00:00Z", "text": "Keep release work local and reversible."},
    {"id": "H-2", "ts": "2026-08-02T10:00:00Z", "text": "Do not push during release judging."},
    {"id": "H-3", "ts": "2026-08-03T10:00:00Z", "text": "Local tests are useful before release."},
]


class RetrievalAndSafety(unittest.TestCase):
    def test_plan_is_evidence_bound_without_raw_prompt(self) -> None:
        result = sta.simulate(
            RECORDS,
            "Should release work stay local before judging?",
            min_evidence=2,
            prediction_id="DP-1",
        )
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["mode"], "secure")
        self.assertFalse(result["private_prompt_included"])
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(result["prediction_id"], "DP-1")
        self.assertTrue(result["text_prediction_id"].startswith("TP_"))
        self.assertIsNone(result["simulated_text"])
        self.assertNotIn("Keep release work", json.dumps(result))

    def test_novel_scenario_escalates_instead_of_guessing(self) -> None:
        result = sta.simulate(RECORDS, "quantum biology vacation", min_evidence=1)
        self.assertEqual(result["status"], "escalate")
        self.assertEqual(result["confidence"], "low")
        self.assertEqual(result["evidence_ids"], [])

    def test_selected_evidence_is_redacted_again_before_generation(self) -> None:
        records = RECORDS + [{
            "id": "H-4",
            "ts": "2026-08-04T10:00:00Z",
            "text": "release token sk-abcdefghijklmnop1234 must stay private",
        }]
        prompt, count = sta._build_private_prompt("release token", sta.retrieve(records, "release token", 5))
        self.assertGreater(count, 0)
        self.assertIn("[REDACTED_APIKEY]", prompt)
        self.assertNotIn("sk-abcdefghijklmnop1234", prompt)

    def test_non_loopback_model_endpoint_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "loopback"):
            sta.call_ollama("https://example.com/api/generate", "model", "prompt", 0.2, 1)


class FakeResponse:
    def __init__(self, payload: dict[str, object]):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class LocalGeneration(unittest.TestCase):
    def test_ollama_result_is_labelled_simulation(self) -> None:
        captured: dict[str, object] = {}

        def opener(request, timeout):
            captured["url"] = request.full_url
            captured["payload"] = json.loads(request.data)
            captured["timeout"] = timeout
            return FakeResponse({"response": "Keep it local and test first."})

        result = sta.simulate(
            RECORDS,
            "Should release work stay local before judging?",
            provider="ollama",
            model="local-test",
            min_evidence=2,
            opener=opener,
        )
        self.assertEqual(result["simulated_text"], "Keep it local and test first.")
        self.assertIn("NOT A USER STATEMENT", result["label"])
        self.assertEqual(captured["url"], "http://127.0.0.1:11434/api/generate")
        self.assertIn("untrusted quotations", captured["payload"]["system"])

    def test_model_can_escalate(self) -> None:
        def opener(request, timeout):
            return FakeResponse({"response": "ESCALATE_TO_OPERATOR"})

        result = sta.simulate(
            RECORDS,
            "Should release work stay local before judging?",
            provider="ollama",
            model="local-test",
            min_evidence=2,
            opener=opener,
        )
        self.assertEqual(result["status"], "escalate")
        self.assertIsNone(result["simulated_text"])


class Cli(unittest.TestCase):
    def test_plan_cli(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            corpus = Path(directory) / "corpus.jsonl"
            corpus.write_text("".join(json.dumps(row) + "\n" for row in RECORDS), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = sta.main([
                    "--corpus", str(corpus),
                    "--scenario", "Should release work stay local before judging?",
                    "--min-evidence", "2",
                ])
            self.assertEqual(rc, 0)
            self.assertEqual(json.loads(output.getvalue())["status"], "ready")


if __name__ == "__main__":
    unittest.main()
