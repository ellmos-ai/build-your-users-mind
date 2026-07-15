#!/usr/bin/env python3
"""Validate that every current Stage-2 chunk has one strict classification."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from classification_contract import load_classifications
from pipeline_common import load_jsonl, validate_unique_ids


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunks", default="./STUDIE/_chunks")
    parser.add_argument("--corpus", default="./STUDIE/00_corpus.jsonl")
    args = parser.parse_args(argv)
    try:
        corpus_path = Path(args.corpus).expanduser()
        rows, errors = load_classifications(Path(args.chunks).expanduser(), corpus_path)
        corpus = load_jsonl(corpus_path)
        validate_unique_ids(corpus)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    corpus_ids = {str(row["id"]) for row in corpus}
    unknown = sorted(str(row["id"]) for row in rows if str(row.get("id", "")) not in corpus_ids)
    if unknown:
        errors.append(f"{len(unknown)} classification IDs do not exist in the corpus")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Classification contract failed with {len(errors)} error(s).", file=sys.stderr)
        return 2
    print(f"Classification contract PASS: {len(rows)} rows, no missing IDs or collisions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
