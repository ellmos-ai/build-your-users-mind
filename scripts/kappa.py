#!/usr/bin/env python3
"""Dependency-free Cohen's kappa for inter-rater agreement.

Two rating columns (CSV or JSONL) → Cohen's κ plus the confusion matrix,
observed agreement (p_o) and chance agreement (p_e). Pure stdlib, offline.

    python scripts/kappa.py --input ratings.csv --col-a rater_a --col-b rater_b --header
    python scripts/kappa.py --input ratings.jsonl --format jsonl --col-a a --col-b b

Use it for the semantic classifier's inter-rater review (see TODO.md, κ≈0.24).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def cohen_kappa(pairs: list[tuple[str, str]]) -> dict[str, object]:
    """Cohen's kappa over (rater_a, rater_b) label pairs."""
    if not pairs:
        raise ValueError("no rating pairs")
    labels = sorted({label for pair in pairs for label in pair})
    index = {label: i for i, label in enumerate(labels)}
    size = len(labels)
    matrix = [[0] * size for _ in range(size)]
    for a, b in pairs:
        matrix[index[a]][index[b]] += 1

    n = len(pairs)
    agree = sum(matrix[i][i] for i in range(size))
    po = agree / n
    row_tot = [sum(matrix[i]) for i in range(size)]
    col_tot = [sum(matrix[i][j] for i in range(size)) for j in range(size)]
    pe = sum(row_tot[i] * col_tot[i] for i in range(size)) / (n * n)
    if pe == 1:
        kappa = 1.0 if po == 1 else 0.0
    else:
        kappa = (po - pe) / (1 - pe)
    return {"n": n, "po": po, "pe": pe, "kappa": kappa, "labels": labels, "matrix": matrix}


def read_pairs(path: Path, fmt: str, col_a: str, col_b: str, header: bool) -> list[tuple[str, str]]:
    text = path.read_text(encoding="utf-8")
    pairs: list[tuple[str, str]] = []
    if fmt == "jsonl":
        for line in text.splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            pairs.append((str(obj[col_a]).strip(), str(obj[col_b]).strip()))
        return pairs

    rows = [row for row in csv.reader(text.splitlines()) if row and any(cell.strip() for cell in row)]
    if header:
        head = [cell.strip() for cell in rows[0]]
        ia, ib = head.index(col_a), head.index(col_b)
        rows = rows[1:]
    else:
        ia, ib = int(col_a), int(col_b)
    for row in rows:
        pairs.append((row[ia].strip(), row[ib].strip()))
    return pairs


def format_report(result: dict[str, object]) -> str:
    labels = result["labels"]
    matrix = result["matrix"]
    width = max([len(str(x)) for x in labels] + [3])
    header = "a\\b".ljust(width) + " | " + " ".join(str(x).rjust(width) for x in labels)
    lines = [
        "Cohen's kappa (inter-rater agreement)",
        f"  n = {result['n']}   labels = {len(labels)}",
        f"  observed agreement p_o = {float(result['po']):.4f}",
        f"  chance agreement   p_e = {float(result['pe']):.4f}",
        f"  kappa = {float(result['kappa']):.4f}",
        "  confusion matrix (rows = rater A, cols = rater B):",
        "    " + header,
    ]
    for i, label in enumerate(labels):
        lines.append("    " + str(label).ljust(width) + " | "
                     + " ".join(str(matrix[i][j]).rjust(width) for j in range(len(labels))))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dependency-free Cohen's kappa.")
    parser.add_argument("--input", required=True, help="ratings file (CSV or JSONL)")
    parser.add_argument("--format", default="auto", choices=("auto", "csv", "jsonl"))
    parser.add_argument("--col-a", default="", help="column A (CSV index/name, or JSONL key)")
    parser.add_argument("--col-b", default="", help="column B (CSV index/name, or JSONL key)")
    parser.add_argument("--header", action="store_true", help="CSV has a header row (use column names)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a report")
    parser.add_argument("--out", default="", help="write output to this file instead of stdout")
    args = parser.parse_args(argv)

    path = Path(args.input).expanduser()
    if not path.is_file():
        print(f"ERROR: input not found: {path}", file=sys.stderr)
        return 2

    fmt = args.format
    if fmt == "auto":
        fmt = "jsonl" if path.suffix.lower() in (".jsonl", ".ndjson") else "csv"
    col_a = args.col_a or ("a" if fmt == "jsonl" else "0")
    col_b = args.col_b or ("b" if fmt == "jsonl" else "1")

    try:
        pairs = read_pairs(path, fmt, col_a, col_b, args.header)
        result = cohen_kappa(pairs)
    except (ValueError, KeyError, IndexError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    payload = json.dumps(result, ensure_ascii=False, indent=2) if args.json else format_report(result)
    if args.out:
        Path(args.out).expanduser().write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
