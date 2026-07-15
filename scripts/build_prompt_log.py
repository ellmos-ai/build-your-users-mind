#!/usr/bin/env python3
"""Build a private, line-capped readable view over the full JSONL corpus."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from pipeline_common import atomic_write_text, load_jsonl, validate_unique_ids

HEADER = """# PROMPT-LOG — {user}

> **Storage:** The complete archive is `STUDIE/00_corpus.jsonl`. This file is a
> private, rolling readable view capped at {maxlines} lines. Older entries remain
> addressable by their stable evidence IDs in the JSONL archive.

---
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="./STUDIE/00_corpus.jsonl")
    parser.add_argument("--out", default="./avatar/PROMPT-LOG.txt")
    parser.add_argument("--user", default="USER")
    parser.add_argument("--window", type=int, default=300)
    parser.add_argument("--maxlines", type=int, default=2000)
    args = parser.parse_args(argv)
    if args.window <= 0:
        parser.error("--window must be positive")
    if args.maxlines <= 0:
        parser.error("--maxlines must be positive")
    try:
        records = load_jsonl(Path(args.corpus).expanduser())
        validate_unique_ids(records)
    except ValueError as exc:
        parser.error(str(exc))
    all_decisions = sorted(
        (
            record
            for record in records
            if int(record.get("decision_score", 0)) >= 1 and record.get("ptype") != "ack"
        ),
        key=lambda record: (str(record.get("ts", "")), str(record["id"])),
        reverse=True,
    )
    decisions = all_decisions[: args.window]
    outcomes = Counter(str(record.get("outcome_signal", "none")) for record in records)
    dates = [str(record.get("ts", ""))[:10] for record in records if record.get("ts")]
    span = (min(dates), max(dates)) if dates else ("?", "?")
    prefix = [
        HEADER.format(user=args.user, maxlines=args.maxlines),
        "## Summary\n\n",
        f"- Period: {span[0]} – {span[1]}\n",
        f"- Human prompts: {len(records)} | decision candidates: {len(all_decisions)}\n",
        "- Outcome: " + ", ".join(f"{key}={value}" for key, value in outcomes.most_common()) + "\n\n",
        "## Rolling decision window\n\n",
    ]
    if len("".join(prefix).splitlines()) > args.maxlines:
        parser.error("--maxlines is too small for the document header")
    included: list[str] = []
    for record in decisions:
        project = str(record.get("project") or "?").replace("\\", "/").split("/")[-1]
        text = str(record["text"]).strip()
        if len(text) > 600:
            text = text[:600] + " […]"
        section = (
            f"### [{record['id']}] {str(record.get('ts', ''))[:16]} · {project} · "
            f"outcome={record.get('outcome_signal')} · score={record.get('decision_score')}\n"
            f"{text}\n\n"
        )
        candidate = "".join(prefix + included + [section])
        if len(candidate.splitlines()) > args.maxlines:
            break
        included.append(section)
    omitted = len(all_decisions) - len(included)
    if omitted:
        note = f"> {omitted} older decision entries omitted from this view; use the JSONL archive.\n"
        while included and len("".join(prefix + [note] + included).splitlines()) > args.maxlines:
            included.pop()
            omitted = len(all_decisions) - len(included)
            note = f"> {omitted} older decision entries omitted from this view; use the JSONL archive.\n"
        if len("".join(prefix + [note] + included).splitlines()) <= args.maxlines:
            prefix.append(note)
    target = Path(args.out).expanduser()
    atomic_write_text(target, "".join(prefix + included))
    print(f"-> {target} ({len(included)} inline, {len(records)} in JSONL archive)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
