#!/usr/bin/env python3
"""Extract genuine human prompts from Gemini/Antigravity SQLite logs."""

from __future__ import annotations

import argparse
from contextlib import closing
import datetime as dt
import sqlite3
import sys
import urllib.parse
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


def parse_varint(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    for offset in range(10):
        if pos >= len(data):
            raise ValueError("truncated protobuf varint")
        byte = data[pos]
        pos += 1
        value |= (byte & 0x7F) << (7 * offset)
        if not byte & 0x80:
            return value, pos
    raise ValueError("protobuf varint exceeds 10 bytes")


def parse_proto(data: bytes) -> dict[int, object]:
    if not isinstance(data, bytes):
        raise ValueError("protobuf value must be bytes")
    pos = 0
    fields: dict[int, object] = {}
    while pos < len(data):
        key, pos = parse_varint(data, pos)
        tag, wire_type = key >> 3, key & 0x07
        if tag == 0:
            raise ValueError("invalid protobuf field tag 0")
        if wire_type == 0:
            value, pos = parse_varint(data, pos)
        elif wire_type == 1:
            if pos + 8 > len(data):
                raise ValueError("truncated protobuf fixed64 field")
            value, pos = data[pos : pos + 8], pos + 8
        elif wire_type == 2:
            length, pos = parse_varint(data, pos)
            if pos + length > len(data):
                raise ValueError("truncated protobuf length-delimited field")
            value, pos = data[pos : pos + length], pos + length
        elif wire_type == 5:
            if pos + 4 > len(data):
                raise ValueError("truncated protobuf fixed32 field")
            value, pos = data[pos : pos + 4], pos + 4
        else:
            raise ValueError(f"unsupported protobuf wire type: {wire_type}")
        fields[tag] = value
    return fields


def extract_timestamp(metadata: bytes | None) -> str:
    if not metadata:
        return ""
    fields = parse_proto(metadata)
    timestamp_bytes = fields.get(1)
    if not isinstance(timestamp_bytes, bytes):
        return ""
    timestamp = parse_proto(timestamp_bytes)
    seconds = timestamp.get(1)
    nanos = timestamp.get(2, 0)
    if (
        isinstance(seconds, bool)
        or not isinstance(seconds, int)
        or seconds <= 0
        or isinstance(nanos, bool)
        or not isinstance(nanos, int)
    ):
        return ""
    if nanos < 0 or nanos >= 1_000_000_000:
        raise ValueError("invalid protobuf timestamp nanos")
    value = dt.datetime.fromtimestamp(seconds + nanos / 1e9, tz=dt.timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def _decode(value: object) -> str:
    if not isinstance(value, bytes):
        return ""
    return value.decode("utf-8").strip()


def extract_project_branch(connection: sqlite3.Connection) -> tuple[str, str]:
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='trajectory_metadata_blob'"
    ).fetchone()
    if not exists:
        return "", ""
    row = connection.execute(
        'SELECT data FROM trajectory_metadata_blob WHERE id = "main"'
    ).fetchone()
    if not row or not isinstance(row[0], bytes):
        return "", ""
    fields = parse_proto(row[0])
    project = _decode(fields.get(18))
    branch = ""
    nested_bytes = fields.get(1)
    if isinstance(nested_bytes, bytes):
        nested = parse_proto(nested_bytes)
        project_uri = _decode(nested.get(1))
        if project_uri:
            parsed = urllib.parse.urlparse(project_uri)
            if parsed.scheme == "file":
                project = urllib.parse.unquote(parsed.path)
                if parsed.netloc:
                    project = f"//{parsed.netloc}{project}"
                if len(project) >= 3 and project[0] == "/" and project[2] == ":":
                    project = project[1:]
            else:
                project = urllib.parse.unquote(project_uri)
            project = project.replace("\\", "/")
        branch = _decode(nested.get(4))
    return project, branch


def extract_user_text(step_payload: bytes | None) -> str:
    if not step_payload:
        return ""
    payload = parse_proto(step_payload)
    nested_bytes = payload.get(19)
    if not isinstance(nested_bytes, bytes):
        return ""
    nested = parse_proto(nested_bytes)
    return _decode(nested.get(2))


def open_read_only(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)


def build_records(
    files: list[Path], since: str, redaction_rules: object
) -> tuple[list[dict[str, object]], int, int, int]:
    records: list[dict[str, object]] = []
    redactions = 0
    with_data = 0
    read_errors = 0
    for path in files:
        rows: list[dict[str, str]] = []
        try:
            with closing(open_read_only(path)) as connection:
                project, branch = extract_project_branch(connection)
                exists = connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='steps'"
                ).fetchone()
                if not exists:
                    read_errors += 1
                    print(
                        f"warning: skipped {path}: missing required steps table",
                        file=sys.stderr,
                    )
                    continue
                cursor = connection.execute(
                    "SELECT metadata, step_payload FROM steps WHERE step_type = 14 ORDER BY idx"
                )
                for metadata, step_payload in cursor:
                    try:
                        timestamp = extract_timestamp(metadata)
                        if not timestamp:
                            read_errors += 1
                            continue
                        timestamp = validate_timestamp(timestamp)
                        if since and timestamp[:10] < since:
                            continue
                        text = extract_user_text(step_payload)
                    except (OverflowError, OSError, UnicodeDecodeError, ValueError):
                        read_errors += 1
                        continue
                    if not text:
                        read_errors += 1
                        continue
                    if is_synthetic(text):
                        continue
                    rows.append(
                        {
                            "ts": timestamp,
                            "project": project,
                            "branch": branch,
                            "session": path.stem,
                            "raw": text,
                        }
                    )
        except (OSError, UnicodeDecodeError, sqlite3.Error, ValueError) as exc:
            read_errors += 1
            print(f"warning: skipped {path}: {exc}", file=sys.stderr)
            continue
        if rows:
            with_data += 1
            normalized, count = normalize_rows(rows, "gemini", redaction_rules)
            records.extend(normalized)
            redactions += count
    records.sort(key=lambda row: (str(row["ts"]), str(row["session"]), str(row["id"])))
    return records, redactions, with_data, read_errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default=str(Path.home() / ".gemini" / "antigravity" / "conversations"),
    )
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
    files = sorted(root.glob("*.db"))
    if not files and not args.allow_empty:
        parser.error("no Gemini .db files found; output was left untouched")
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
    print(
        f"Sessions: {len(files)} ({with_data} with data) | Human prompts: {len(records)} | "
        f"redactions: {redactions} | read warnings: {read_errors}"
    )
    print(f"-> {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
