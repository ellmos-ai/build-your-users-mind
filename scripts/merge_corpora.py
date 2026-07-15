#!/usr/bin/env python3
"""Merge source-specific corpora without overwriting or renumbering evidence IDs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipeline_common import atomic_write_jsonl, load_jsonl, validate_unique_ids


def merge(paths: list[Path]) -> list[dict[str, object]]:
    by_id: dict[str, dict[str, object]] = {}
    for path in paths:
        rows = load_jsonl(path)
        validate_unique_ids(rows)
        for row in rows:
            record_id = str(row["id"])
            previous = by_id.get(record_id)
            if previous is not None and previous != row:
                raise ValueError(f"stable-ID collision across inputs: {record_id}")
            by_id[record_id] = row
    return sorted(
        by_id.values(),
        key=lambda row: (str(row.get("ts", "")), str(row.get("session", "")), str(row["id"])),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", help="source-specific corpus JSONL files")
    parser.add_argument("--out", default="./STUDIE/00_corpus.jsonl")
    args = parser.parse_args(argv)
    paths = [Path(value).expanduser() for value in args.inputs]
    try:
        records = merge(paths)
    except ValueError as exc:
        parser.error(str(exc))
    target = Path(args.out).expanduser()
    atomic_write_jsonl(target, records)
    print(f"Merged {len(paths)} corpora -> {target} ({len(records)} records)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
