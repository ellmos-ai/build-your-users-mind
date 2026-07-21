#!/usr/bin/env python3
"""Extract genuine human prompts from Kimi Code wire JSONL logs."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import subprocess
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
    entry_type = entry.get("type")
    if entry_type not in {"turn.prompt", "turn.steer"}:
        return None
    origin = entry.get("origin") or {}
    if not isinstance(origin, dict):
        raise ValueError(f"malformed Kimi {entry_type} origin")
    if origin.get("kind") != "user":
        return None
    value = entry.get("input", "")
    if isinstance(value, list):
        if not value:
            raise ValueError("malformed Kimi human event: empty input list")
        if any(not isinstance(block, dict) for block in value):
            raise ValueError("malformed Kimi human event: input block")
        parts = []
        for block in value:
            if block.get("type") != "text":
                raise ValueError(
                    f"malformed Kimi human event: unknown block {block.get('type')!r}"
                )
            if not isinstance(block.get("text"), str):
                raise ValueError("malformed Kimi human event: text value")
            parts.append(block["text"])
        if not parts:
            return None
        text = " ".join(parts)
    elif isinstance(value, str):
        text = value
    else:
        raise ValueError("malformed Kimi human event: input")
    text = text.strip()
    if not text:
        raise ValueError("malformed Kimi human event: empty input")
    return text if not is_synthetic(text) else None


def ms_to_iso(timestamp_ms: object) -> str:
    if (
        isinstance(timestamp_ms, bool)
        or not isinstance(timestamp_ms, (int, float))
        or not math.isfinite(timestamp_ms)
        or timestamp_ms <= 0
    ):
        return ""
    try:
        value = dt.datetime.fromtimestamp(timestamp_ms / 1000.0, tz=dt.timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ""
    return value.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(timestamp_ms) % 1000:03d}Z"


def git_branch(work_dir: str) -> str:
    path = Path(work_dir).expanduser()
    if not path.is_dir():
        return ""
    try:
        completed = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            encoding="utf-8",
            errors="strict",
            check=False,
        )
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return ""
    return completed.stdout.strip() if completed.returncode == 0 else ""


def load_session_index(root: Path) -> tuple[dict[str, str], int]:
    index: dict[str, str] = {}
    errors = 0
    index_path = root.parent / "session_index.jsonl"
    if not index_path.is_file():
        return index, errors
    with index_path.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                errors += 1
                continue
            if not isinstance(entry, dict):
                errors += 1
                continue
            session_dir, work_dir = entry.get("sessionDir"), entry.get("workDir")
            if isinstance(session_dir, str) and isinstance(work_dir, str):
                index[Path(session_dir).name] = work_dir
            else:
                errors += 1
    return index, errors


def build_records(
    files: list[Path], root: Path, since: str, redaction_rules: object
) -> tuple[list[dict[str, object]], int, int, int]:
    session_index, index_errors = load_session_index(root)
    records: list[dict[str, object]] = []
    redactions = 0
    with_data = 0
    read_errors = index_errors
    for path in files:
        if len(path.parents) < 3:
            read_errors += 1
            continue
        session_name = path.parents[2].name
        work_dir = session_index.get(session_name, "")
        project = str(Path(work_dir).expanduser()) if work_dir else session_name
        branch = git_branch(work_dir) if work_dir else ""
        rows: list[dict[str, str]] = []
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
                    try:
                        text = extract_human(entry)
                    except ValueError:
                        read_errors += 1
                        continue
                    if not text:
                        continue
                    timestamp = ms_to_iso(entry.get("time"))
                    if not timestamp:
                        read_errors += 1
                        continue
                    try:
                        timestamp = validate_timestamp(timestamp)
                    except ValueError:
                        read_errors += 1
                        continue
                    if since and (not timestamp or timestamp[:10] < since):
                        continue
                    rows.append(
                        {
                            "ts": timestamp,
                            "session": session_name,
                            "project": project,
                            "branch": branch,
                            "raw": text,
                        }
                    )
        except (OSError, UnicodeDecodeError):
            read_errors += 1
            continue
        if rows:
            with_data += 1
            normalized, count = normalize_rows(rows, "kimi", redaction_rules)
            records.extend(normalized)
            redactions += count
    records.sort(key=lambda row: (str(row["ts"]), str(row["session"]), str(row["id"])))
    return records, redactions, with_data, read_errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="Kimi sessions root")
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
    files = sorted(root.rglob("wire.jsonl"))
    if not files and not args.allow_empty:
        parser.error("no Kimi wire.jsonl files found; output was left untouched")
    try:
        records, redactions, with_data, read_errors = build_records(
            files, root, since, rules
        )
    except (OSError, UnicodeDecodeError) as exc:
        parser.error(f"cannot read Kimi session index: {exc}")
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
    print(
        f"Sessions: {len(files)} ({with_data} with data) | Human prompts: {len(records)} | "
        f"redactions: {redactions} | read warnings: {read_errors}"
    )
    print(f"-> {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
