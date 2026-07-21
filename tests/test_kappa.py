from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import kappa  # noqa: E402


def pairs_from_counts(counts: dict[tuple[str, str], int]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for (a, b), n in counts.items():
        out.extend([(a, b)] * n)
    return out


class CohenKappa(unittest.TestCase):
    def test_known_value(self) -> None:
        # Classic 2x2: po=0.7, pe=0.5 -> kappa=0.4
        pairs = pairs_from_counts({
            ("yes", "yes"): 20, ("yes", "no"): 5,
            ("no", "yes"): 10, ("no", "no"): 15,
        })
        result = kappa.cohen_kappa(pairs)
        self.assertEqual(result["n"], 50)
        self.assertAlmostEqual(result["po"], 0.7)
        self.assertAlmostEqual(result["pe"], 0.5)
        self.assertAlmostEqual(result["kappa"], 0.4)

    def test_perfect_agreement(self) -> None:
        pairs = pairs_from_counts({("a", "a"): 3, ("b", "b"): 7})
        self.assertAlmostEqual(kappa.cohen_kappa(pairs)["kappa"], 1.0)

    def test_total_disagreement_is_zero(self) -> None:
        pairs = pairs_from_counts({("yes", "no"): 10})
        self.assertAlmostEqual(kappa.cohen_kappa(pairs)["kappa"], 0.0)

    def test_single_label_everywhere_is_one(self) -> None:
        # pe == 1 edge: both raters always agree on the only label
        result = kappa.cohen_kappa([("yes", "yes")] * 5)
        self.assertAlmostEqual(result["kappa"], 1.0)

    def test_confusion_matrix_shape(self) -> None:
        result = kappa.cohen_kappa(pairs_from_counts({
            ("yes", "yes"): 2, ("yes", "no"): 1, ("no", "no"): 1,
        }))
        self.assertEqual(result["labels"], ["no", "yes"])
        # matrix[i][j] = count(A=labels[i], B=labels[j])
        i_yes = result["labels"].index("yes")
        j_no = result["labels"].index("no")
        self.assertEqual(result["matrix"][i_yes][j_no], 1)

    def test_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            kappa.cohen_kappa([])


class ReadPairs(unittest.TestCase):
    def test_csv_no_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.csv"
            p.write_text("yes,yes\nyes,no\nno,no\n", encoding="utf-8")
            pairs = kappa.read_pairs(p, "csv", "0", "1", header=False)
            self.assertEqual(pairs, [("yes", "yes"), ("yes", "no"), ("no", "no")])

    def test_csv_with_header_by_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.csv"
            p.write_text("ra,rb\nSP,SP\nKO,NT\n", encoding="utf-8")
            pairs = kappa.read_pairs(p, "csv", "ra", "rb", header=True)
            self.assertEqual(pairs, [("SP", "SP"), ("KO", "NT")])

    def test_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.jsonl"
            p.write_text('{"a": "SP", "b": "SP"}\n{"a": "KO", "b": "RA"}\n', encoding="utf-8")
            pairs = kappa.read_pairs(p, "jsonl", "a", "b", header=False)
            self.assertEqual(pairs, [("SP", "SP"), ("KO", "RA")])


class Cli(unittest.TestCase):
    def test_main_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.csv"
            rows = ["yes,yes"] * 20 + ["yes,no"] * 5 + ["no,yes"] * 10 + ["no,no"] * 15
            p.write_text("\n".join(rows) + "\n", encoding="utf-8")
            out = Path(tmp) / "k.json"
            rc = kappa.main(["--input", str(p), "--format", "csv", "--json", "--out", str(out)])
            self.assertEqual(rc, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertAlmostEqual(data["kappa"], 0.4)

    def test_main_missing_file(self) -> None:
        self.assertEqual(kappa.main(["--input", "nope-404.csv"]), 2)


if __name__ == "__main__":
    unittest.main()
