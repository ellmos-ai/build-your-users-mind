from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import score_predictions as sp  # noqa: E402

# Synthetic MY-ACTIONS.txt: 3 green (2 hit, 1 miss), 2 yellow (1 hit, 1 miss),
# 3 red (1 escalated, 1 acted+hit, 1 open). Mixes emoji + ascii confidence.
ACTIONS = "\n".join([
    "# MY-ACTIONS.txt — append-only",
    "# comment line is skipped",
    "2026-05-10T10:00:00Z\t🟢\ty\tconfirmed\tuse pnpm\tenforce pnpm",
    "2026-05-10T10:03:00Z\tgreen\ty\tconfirmed\ttailwind\tprefer tailwind",
    "2026-05-10T10:06:00Z\t🟢\ty\tcorrected\tformat on save\tassumed format",
    "2026-05-11T10:00:00Z\t🟡\ty\tconfirmed\tauth refactor\task first",
    "2026-05-11T10:03:00Z\tyellow\ty\tcorrected\trename var\tguessed rename",
    "2026-05-12T10:00:00Z\t🔴\tn\tescalated\tnew framework\tno pattern",
    "2026-05-12T10:03:00Z\tred\ty\tconfirmed\tacted at red\tguessed anyway",
    "2026-05-12T10:06:00Z\t🔴\ty\topen\tpending red\tawaiting feedback",
    "",
]) + "\n"

FEEDBACK = "\n".join([
    "# WHAT USER SAID ABOUT WHAT I DID",
    "## [2026-05-12] pending red — verdict: 👍 confirmed",
    "- Prediction was: keep it | Reality: kept | Hit? yes",
    "## [2026-05-13] never happened — verdict: ✋ corrected",
    "- Prediction was: X | Reality: Y | Hit? no",
]) + "\n"


class ConfidenceNorm(unittest.TestCase):
    def test_emoji_and_aliases(self) -> None:
        for raw in ("🟢", "green", "GREEN", "g", "high"):
            self.assertEqual(sp.norm_confidence(raw), "green")
        for raw in ("🟡", "yellow", "y", "medium"):
            self.assertEqual(sp.norm_confidence(raw), "yellow")
        for raw in ("🔴", "red", "r", "low", "novel"):
            self.assertEqual(sp.norm_confidence(raw), "red")
        self.assertIsNone(sp.norm_confidence("banana"))


class ParseActions(unittest.TestCase):
    def test_parses_and_skips_comments(self) -> None:
        rows = sp.parse_actions(ACTIONS)
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[0]["confidence"], "green")
        self.assertEqual(rows[0]["outcome"], "hit")
        self.assertEqual(rows[2]["outcome"], "miss")   # corrected
        self.assertEqual(rows[5]["outcome"], "escalated")
        self.assertEqual(rows[7]["outcome"], "pending")


class Scoring(unittest.TestCase):
    def test_overall_and_tiers(self) -> None:
        result = sp.score(sp.parse_actions(ACTIONS))
        self.assertEqual(result["overall"]["resolved"], 6)
        self.assertEqual(result["overall"]["hits"], 4)
        self.assertAlmostEqual(result["overall"]["hit_rate"], 4 / 6)
        self.assertAlmostEqual(result["by_tier"]["green"]["hit_rate"], 2 / 3)
        self.assertAlmostEqual(result["by_tier"]["yellow"]["hit_rate"], 0.5)
        self.assertAlmostEqual(result["by_tier"]["red"]["hit_rate"], 1.0)
        self.assertEqual(result["pending"], 1)

    def test_escalation_rate(self) -> None:
        result = sp.score(sp.parse_actions(ACTIONS))
        esc = result["escalation"]
        self.assertEqual(esc["escalated"], 1)
        self.assertEqual(esc["acted_at_red"], 1)
        self.assertAlmostEqual(esc["escalation_rate"], 0.5)

    def test_empty_is_safe(self) -> None:
        result = sp.score([])
        self.assertIsNone(result["overall"]["hit_rate"])
        self.assertEqual(result["overall"]["resolved"], 0)
        self.assertIsNone(result["escalation"]["escalation_rate"])


class Feedback(unittest.TestCase):
    def test_feedback_resolves_open_by_title(self) -> None:
        fb = sp.parse_feedback(FEEDBACK)
        self.assertEqual(fb["pending red"], "hit")
        self.assertEqual(fb["never happened"], "miss")
        result = sp.score(sp.parse_actions(ACTIONS), feedback=fb)
        # the open red prediction now resolves to a hit
        self.assertEqual(result["by_tier"]["red"]["resolved"], 2)
        self.assertEqual(result["by_tier"]["red"]["hits"], 2)
        self.assertEqual(result["pending"], 0)
        self.assertEqual(result["unmatched_feedback"], 1)  # "never happened"


class Cli(unittest.TestCase):
    def test_main_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            actions = Path(tmp) / "MY-ACTIONS.txt"
            actions.write_text(ACTIONS, encoding="utf-8")
            out = Path(tmp) / "out.json"
            rc = sp.main(["--actions", str(actions), "--json", "--out", str(out)])
            self.assertEqual(rc, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["overall"]["hits"], 4)

    def test_main_missing_file_fails_closed(self) -> None:
        rc = sp.main(["--actions", "does-not-exist-42.txt"])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
