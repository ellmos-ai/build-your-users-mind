#!/usr/bin/env python3
"""Aggregate statistics only from a complete, collision-free Stage-2 result."""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

from classification_contract import load_classifications
from pipeline_common import atomic_write_text, load_jsonl, validate_unique_ids

TYPES = {
    "SP": "Start prompt",
    "NT": "Follow-up topic",
    "NM": "Follow-up method",
    "NS": "Follow-up control",
    "KO": "Correction",
    "BE": "Confirmation",
    "RA": "Course change",
    "MP": "Meta-prompt",
}


def ratio(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "undefined (denominator 0)"
    return f"{round(numerator / denominator, 2)}:1"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunks", default="./STUDIE/_chunks")
    parser.add_argument("--corpus", default="./STUDIE/00_corpus.jsonl")
    parser.add_argument("--out", default="./STUDIE/04_statistik.md")
    args = parser.parse_args(argv)
    try:
        corpus_path = Path(args.corpus).expanduser()
        corpus_rows = load_jsonl(corpus_path)
        validate_unique_ids(corpus_rows)
        classifications, errors = load_classifications(
            Path(args.chunks).expanduser(), corpus_path
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    corpus = {str(row["id"]): row for row in corpus_rows}
    unknown = sorted(
        str(row["id"]) for row in classifications if str(row.get("id", "")) not in corpus
    )
    if unknown:
        errors.append(f"{len(unknown)} classification IDs do not exist in the corpus")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print("Aggregation refused: Stage-2 contract is not complete.", file=sys.stderr)
        return 2
    if not classifications:
        print("ERROR: no classifications found", file=sys.stderr)
        return 2

    count = len(classifications)
    type_counts = Counter(str(row["type_code"]) for row in classifications)
    decision_kinds = Counter(str(row["decision_kind"]) for row in classifications)
    methods = Counter(str(row["method_triggered"]) for row in classifications)
    turning_points = [row for row in classifications if row["is_turning_point"] is True]
    decisions = [row for row in classifications if row["is_decision"] is True]
    by_domain = Counter(str(row["_domain"]) for row in classifications)
    confirmations, corrections = type_counts["BE"], type_counts["KO"]
    proactive = type_counts["SP"] + type_counts["NM"] + type_counts["RA"]
    reactive = confirmations + corrections + type_counts["NT"]
    outcomes: dict[str, Counter[str]] = defaultdict(Counter)
    for classification in classifications:
        corpus_record = corpus[str(classification["id"])]
        outcomes[str(classification["_domain"])][
            str(corpus_record.get("outcome_signal", "none"))
        ] += 1

    lines = [
        "# Statistical prompt aggregation (Stage 4)\n\n",
        f"Basis: **{count}** classified unique human prompts.\n\n",
        "## Prompt-type distribution\n\n| Type | Name | Count | % |\n|---|---|---:|---:|\n",
    ]
    for code, value in type_counts.most_common():
        lines.append(
            f"| {code} | {TYPES[code]} | {value} | {round(value / count * 100, 1)}% |\n"
        )
    lines.extend(
        [
            "\n## Human-machine dynamics\n\n",
            f"- **Confirmation:correction:** {ratio(confirmations, corrections)}\n",
            f"- **Proactive:reactive:** {ratio(proactive, reactive)}\n",
            f"- **Turning points:** {len(turning_points)} ({round(len(turning_points) / count * 100, 1)}%)\n",
            f"- **Decision prompts:** {len(decisions)} ({round(len(decisions) / count * 100, 1)}%)\n",
            "\n## decision_kind\n\n| Kind | Count |\n|---|---:|\n",
        ]
    )
    for key, value in decision_kinds.most_common():
        lines.append(f"| {key} | {value} |\n")
    lines.append("\n## Method trigger\n\n| Method | Count |\n|---|---:|\n")
    for key, value in methods.most_common():
        lines.append(f"| {key} | {value} |\n")
    lines.append(
        "\n## By domain (outcome praise/correction/reissue/none)\n\n"
        "| Domain | Prompts | Outcome |\n|---|---:|---|\n"
    )
    for domain, value in by_domain.most_common():
        domain_outcomes = outcomes[domain]
        lines.append(
            f"| {domain} | {value} | {domain_outcomes['praise']}/{domain_outcomes['correction']}/"
            f"{domain_outcomes['reissue']}/{domain_outcomes['none']} |\n"
        )
    lines.append(
        "\n> **Bias:** Silent approval is not typed, so corrections are overrepresented. "
        "Ratios are descriptive signals, not psychological measurements.\n"
    )
    target = Path(args.out).expanduser()
    atomic_write_text(target, "".join(lines))
    print(
        f"-> {target} | N={count} B:K={ratio(confirmations, corrections)} "
        f"P:R={ratio(proactive, reactive)} TP={len(turning_points)} decisions={len(decisions)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
