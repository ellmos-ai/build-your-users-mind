#!/usr/bin/env python3
"""Offline Stage-2 classification worker for the synthetic demo.

Follows `templates/CLASSIFY-CHUNK.md`: reads each `chunk_*.jsonl` named in the
manifest and emits exactly one schema-valid classification per row into the
manifest's `classification_file`. On real data this stage is an LLM swarm; here
the labels come from the synthetic answer key, so the demo runs fully offline
with no model. The labels are pre-authored fixtures, NOT a measured accuracy claim.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FIELDS = ("type_code", "topic", "is_decision", "decision_kind",
          "formulation_pattern", "method_triggered", "is_turning_point")


def classify(chunks_dir: Path, answer_key: Path) -> int:
    answer = json.loads(answer_key.read_text(encoding="utf-8"))
    manifest = json.loads((chunks_dir / "manifest.json").read_text(encoding="utf-8"))
    total = 0
    for chunk in manifest["chunks"]:
        rows = [json.loads(line) for line
                in (chunks_dir / chunk["file"]).read_text(encoding="utf-8").splitlines()
                if line.strip()]
        out = []
        for row in rows:
            label = answer[row["text"]]
            record = {"id": row["id"]}
            for field in FIELDS:
                record[field] = label[field]
            out.append(record)
        (chunks_dir / chunk["classification_file"]).write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n", encoding="utf-8")
        total += len(out)
        print(f"  wrote {chunk['classification_file']} ({len(out)} rows)")
    print(f"classified {total} prompts across {len(manifest['chunks'])} chunk(s)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline demo classifier (answer-key based, no LLM).")
    parser.add_argument("--chunks", required=True, help="chunk directory containing manifest.json")
    parser.add_argument("--answer-key", required=True, help="answer_key.json from generate_fixtures.py")
    args = parser.parse_args(argv)
    return classify(Path(args.chunks).expanduser(), Path(args.answer_key).expanduser())


if __name__ == "__main__":
    raise SystemExit(main())
