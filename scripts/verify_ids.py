#!/usr/bin/env python3
"""Resolve evidence IDs against a strict, collision-free classified corpus."""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from classification_contract import load_classifications
from pipeline_common import load_jsonl, validate_unique_ids


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ids", nargs="*", help="evidence IDs to check")
    parser.add_argument("--corpus", default="./STUDIE/00_corpus.jsonl")
    parser.add_argument("--chunks", default="./STUDIE/_chunks")
    parser.add_argument("--sample", type=int, default=10)
    parser.add_argument(
        "--show-text",
        action="store_true",
        help="opt in to printing private prompt text to the terminal/log",
    )
    args = parser.parse_args(argv)
    if args.sample <= 0:
        parser.error("--sample must be positive")
    try:
        corpus_path = Path(args.corpus).expanduser()
        corpus_rows = load_jsonl(corpus_path)
        validate_unique_ids(corpus_rows)
        classifications, contract_errors = load_classifications(
            Path(args.chunks).expanduser(), corpus_path
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if contract_errors:
        for error in contract_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if not classifications:
        print("ERROR: no classifications found", file=sys.stderr)
        return 2
    corpus = {str(row["id"]): row for row in corpus_rows}
    cats = {str(row["id"]): row for row in classifications}
    unknown_classifications = sorted(set(cats) - set(corpus))
    if unknown_classifications:
        print(
            f"ERROR: {len(unknown_classifications)} classifications do not resolve in the corpus",
            file=sys.stderr,
        )
        return 2
    ids = list(args.ids)
    if not ids:
        ids = random.SystemRandom().sample(list(cats), min(args.sample, len(cats)))
    missing = 0
    unclassified = 0
    for record_id in ids:
        record = corpus.get(record_id)
        classification = cats.get(record_id)
        print(f"=== {record_id} ===")
        if record is None:
            print("  ERROR: ID does not exist in corpus")
            missing += 1
            continue
        if classification is None:
            print("  ERROR: ID has no classification (it may be a deduplicated corpus row)")
            unclassified += 1
            continue
        project = str(record.get("project") or "?").replace("\\", "/").split("/")[-1]
        print(
            f"  project={project} score={record.get('decision_score')} "
            f"outcome={record.get('outcome_signal')} type={classification['type_code']} "
            f"kind={classification['decision_kind']}"
        )
        if args.show_text:
            print("  TEXT: " + " ".join(str(record["text"])[:260].split()))
    print(f"\n-> checked {len(ids)} IDs: {missing} missing, {unclassified} unclassified")
    return 2 if missing or unclassified else 0


if __name__ == "__main__":
    sys.exit(main())
