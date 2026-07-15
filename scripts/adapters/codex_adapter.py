#!/usr/bin/env python3
"""Extract genuine human prompts from Codex rollout JSONL logs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from pipeline_common import (  # noqa: E402
    atomic_write_jsonl,
    is_synthetic,
    load_redaction_rules,
    normalize_rows,
    validate_since,
    validate_timestamp,
    validate_unique_ids,
)


def extract_human(entry: dict[str, object]) -> str | None:
    if entry.get("type") != "response_item":
        return None
    payload = entry.get("payload", {})
    if not isinstance(payload, dict):
        raise ValueError("malformed Codex response_item payload")
    if payload.get("role") != "user":
        return None
    content = payload.get("content", [])
    if not isinstance(content, list):
        raise ValueError("malformed Codex human event: content")
    if not content:
        raise ValueError("malformed Codex human event: empty content list")
    if any(not isinstance(block, dict) for block in content):
        raise ValueError("malformed Codex human event: content block")
    parts = []
    for block in content:
        block_type = block.get("type")
        if block_type != "input_text":
            if block_type != "input_image":
                raise ValueError(f"malformed Codex human event: unknown block {block_type!r}")
            continue
        if not isinstance(block.get("text"), str):
            raise ValueError("malformed Codex human event: input_text")
        parts.append(block["text"])
    if not parts:
        return None
    text = "\n".join(parts).strip()
    if not text:
        raise ValueError("malformed Codex human event: empty text")
    return text if not is_synthetic(text) else None


def collect_files(root: Path) -> list[Path]:
    roots = [root]
    archived = root.parent / "archived_sessions"
    if root.name == "sessions" and archived.is_dir():
        roots.append(archived)
    files: set[Path] = set()
    for base in roots:
        files.update(base.rglob("rollout-*.jsonl"))
    return sorted(files)


def _update_context(entry: dict[str, object], context: dict[str, str]) -> None:
    if entry.get("type") not in {"session_meta", "turn_context"}:
        return
    payload = entry.get("payload", {})
    if not isinstance(payload, dict):
        return
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        context["project"] = cwd
    branch = payload.get("git_branch", payload.get("gitBranch"))
    if isinstance(branch, str) and branch:
        context["branch"] = branch


def build_records(
    files: list[Path], since: str, redaction_rules: object
) -> tuple[list[dict[str, object]], int, int, int]:
    records: list[dict[str, object]] = []
    redactions = 0
    with_data = 0
    read_errors = 0
    for path in files:
        rows: list[dict[str, str]] = []
        context = {"project": "", "branch": ""}
        try:
            with path.open(encoding="utf-8") as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        read_errors += 1
                        continue
                    if not isinstance(entry, dict):
                        read_errors += 1
                        continue
                    _update_context(entry, context)
                    try:
                        text = extract_human(entry)
                    except ValueError:
                        read_errors += 1
                        continue
                    if not text:
                        continue
                    try:
                        timestamp = validate_timestamp(
                            entry.get("timestamp", entry.get("ts", ""))
                        )
                    except ValueError:
                        read_errors += 1
                        continue
                    if since and (not timestamp or timestamp[:10] < since):
                        continue
                    rows.append(
                        {
                            "ts": timestamp,
                            "session": path.stem,
                            "project": context["project"],
                            "branch": context["branch"],
                            "raw": text,
                        }
                    )
        except (OSError, UnicodeDecodeError):
            read_errors += 1
            continue
        if rows:
            with_data += 1
            normalized, count = normalize_rows(rows, "codex", redaction_rules)
            records.extend(normalized)
            redactions += count
    records.sort(key=lambda row: (str(row["ts"]), str(row["session"]), str(row["id"])))
    return records, redactions, with_data, read_errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path.home() / ".codex" / "sessions"))
    parser.add_argument("--since", default="", help="exact ISO date YYYY-MM-DD")
    parser.add_argument("--out", default="./STUDIE")
    parser.add_argument("--output-name", default="00_corpus.jsonl")
    parser.add_argument("--redaction-rules", default="")
    parser.add_argument("--allow-empty", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args(argv)
    try:
        since = validate_since(args.since)
        rules = load_redaction_rules(args.redaction_rules)
    except ValueError as exc:
        parser.error(str(exc))
    root = Path(args.root).expanduser()
    if not root.is_dir():
        parser.error(f"log root is not a directory: {root}")
    if Path(args.output_name).name != args.output_name or not args.output_name.endswith(".jsonl"):
        parser.error("--output-name must be a plain .jsonl filename")
    files = collect_files(root)
    if not files and not args.allow_empty:
        parser.error("no rollout JSONL files found; output was left untouched")
    records, redactions, with_data, read_errors = build_records(files, since, rules)
    if read_errors and not args.allow_partial:
        parser.error(
            f"encountered {read_errors} malformed/unreadable input record(s); output was left "
            "untouched (inspect the source or use --allow-partial explicitly)"
        )
    if not records and not args.allow_empty:
        parser.error(
            "no eligible human prompts found; output was left untouched "
            "(use --allow-empty to confirm an empty replacement)"
        )
    try:
        validate_unique_ids(records)
    except ValueError as exc:
        parser.error(f"extraction produced colliding IDs; output was left untouched: {exc}")
    target = Path(args.out).expanduser() / args.output_name
    atomic_write_jsonl(target, records)
    unique = len({str(record["text"]) for record in records})
    decisions = sum(
        1
        for record in records
        if int(record["decision_score"]) >= 1 and record["ptype"] != "ack"
    )
    print(
        f"Sessions: {len(files)} ({with_data} with data) | Human prompts: {len(records)} | "
        f"unique: {unique} | decision candidates: {decisions} | redactions: {redactions} | "
        f"read warnings: {read_errors}"
    )
    print(f"-> {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
