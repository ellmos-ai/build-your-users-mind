#!/usr/bin/env python3
"""Strict Stage-2 classification contract used by validation and aggregation."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path

from pipeline_common import load_jsonl, validate_unique_ids


TYPE_CODES = frozenset({"SP", "NT", "NM", "NS", "KO", "BE", "RA", "MP"})
DECISION_KINDS = frozenset(
    {
        "preference",
        "correction",
        "rule",
        "direction_change",
        "approval",
        "rejection",
        "process",
        "none",
    }
)
METHODS = frozenset(
    {"WebSearch", "WebFetch", "Multi-Agent", "Review", "Cross-Model", "Script", "LaTeX", "--"}
)
REQUIRED_FIELDS = frozenset(
    {
        "id",
        "type_code",
        "topic",
        "is_decision",
        "decision_kind",
        "formulation_pattern",
        "method_triggered",
        "is_turning_point",
    }
)
ALLOWED_FIELDS = REQUIRED_FIELDS


def validate_record(record: dict[str, object], location: str) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_FIELDS - record.keys())
    extra = sorted(record.keys() - ALLOWED_FIELDS)
    if extra:
        errors.append(f"{location}: unexpected fields: {', '.join(extra)}")
    if missing:
        errors.append(f"{location}: missing fields: {', '.join(missing)}")
        return errors
    if not isinstance(record["id"], str) or not record["id"]:
        errors.append(f"{location}: id must be a non-empty string")
    if not isinstance(record["type_code"], str) or record["type_code"] not in TYPE_CODES:
        errors.append(f"{location}: invalid type_code: {record['type_code']!r}")
    if not isinstance(record["decision_kind"], str) or record["decision_kind"] not in DECISION_KINDS:
        errors.append(f"{location}: invalid decision_kind: {record['decision_kind']!r}")
    if not isinstance(record["method_triggered"], str) or record["method_triggered"] not in METHODS:
        errors.append(f"{location}: invalid method_triggered: {record['method_triggered']!r}")
    for field in ("topic", "formulation_pattern"):
        if not isinstance(record[field], str):
            errors.append(f"{location}: {field} must be a string")
    for field in ("is_decision", "is_turning_point"):
        if not isinstance(record[field], bool):
            errors.append(f"{location}: {field} must be boolean")
    return errors


def load_manifest(directory: Path) -> dict[str, object]:
    path = directory / "manifest.json"
    if not path.is_file():
        raise ValueError(f"classification manifest does not exist: {path}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read classification manifest: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema") != "build-your-users-mind.chunks.v1":
        raise ValueError("unsupported or missing chunk manifest schema")
    if not isinstance(manifest.get("chunks"), list):
        raise ValueError("chunk manifest needs a chunks array")
    return manifest


def load_classifications(
    directory: Path,
    corpus_path: Path,
) -> tuple[list[dict[str, object]], list[str]]:
    manifest = load_manifest(directory)
    errors: list[str] = []
    if not corpus_path.is_file():
        raise ValueError(f"corpus does not exist: {corpus_path}")
    try:
        current_digest = hashlib.sha256(corpus_path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ValueError(f"cannot read corpus for manifest verification: {exc}") from exc
    if manifest.get("corpus_sha256") != current_digest:
        errors.append("chunk manifest is stale: corpus SHA-256 does not match")
    corpus_rows = load_jsonl(corpus_path)
    validate_unique_ids(corpus_rows)
    if manifest.get("corpus_records") != len(corpus_rows):
        errors.append("chunk manifest corpus_records does not match the bound corpus")
    representatives: dict[str, str] = {}
    for line_number, record in enumerate(corpus_rows, 1):
        text = record.get("text")
        record_id = record.get("id")
        if not isinstance(text, str) or not isinstance(record_id, str):
            errors.append(f"corpus:{line_number}: text and id must be strings")
            continue
        representatives.setdefault(text, record_id)
    expected_representative_ids = set(representatives.values())
    if manifest.get("unique_records") != len(expected_representative_ids):
        errors.append("chunk manifest unique_records does not match corpus deduplication")
    classifications: list[dict[str, object]] = []
    seen_ids: dict[str, str] = {}
    chunk_ids_seen: set[str] = set()
    chunk_files_seen: set[str] = set()
    expected_files: set[str] = set()
    for chunk in manifest["chunks"]:
        if not isinstance(chunk, dict):
            errors.append("manifest: every chunk entry must be an object")
            continue
        chunk_name = chunk.get("file")
        classification_name = chunk.get("classification_file")
        domain = chunk.get("domain")
        chunk_digest = chunk.get("sha256")
        chunk_count = chunk.get("n")
        if not all(
            isinstance(value, str) and value
            for value in (chunk_name, classification_name, domain, chunk_digest)
        ):
            errors.append("manifest: chunk/classification files, domain and sha256 must be strings")
            continue
        if not isinstance(chunk_count, int) or isinstance(chunk_count, bool) or chunk_count < 0:
            errors.append(f"manifest: invalid row count for {chunk_name}")
            continue
        if Path(chunk_name).name != chunk_name or Path(classification_name).name != classification_name:
            errors.append("manifest: chunk filenames must not contain path components")
            continue
        if chunk_name in chunk_files_seen or classification_name in expected_files:
            errors.append(f"manifest: duplicate managed filename for {chunk_name}")
            continue
        chunk_files_seen.add(chunk_name)
        expected_files.add(classification_name)
        chunk_path = directory / chunk_name
        try:
            actual_chunk_digest = hashlib.sha256(chunk_path.read_bytes()).hexdigest()
        except OSError as exc:
            errors.append(f"cannot hash {chunk_name}: {exc}")
            continue
        if chunk_digest != actual_chunk_digest:
            errors.append(f"{chunk_name}: SHA-256 does not match manifest")
        try:
            expected_rows = load_jsonl(chunk_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if len(expected_rows) != chunk_count:
            errors.append(
                f"{chunk_name}: manifest expects {chunk_count} rows, found {len(expected_rows)}"
            )
        expected_ids = [row.get("id") for row in expected_rows]
        if any(not isinstance(value, str) or not value for value in expected_ids):
            errors.append(f"{chunk_name}: every row needs a non-empty string id")
            continue
        expected_set = set(expected_ids)
        if len(expected_set) != len(expected_ids):
            errors.append(f"{chunk_name}: duplicate IDs inside chunk")
        overlap = chunk_ids_seen & expected_set
        if overlap:
            errors.append(f"{chunk_name}: {len(overlap)} IDs also occur in another chunk")
        chunk_ids_seen.update(expected_set)
        classification_path = directory / classification_name
        try:
            rows = load_jsonl(classification_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        actual_ids: list[str] = []
        for line_number, record in enumerate(rows, 1):
            location = f"{classification_name}:{line_number}"
            errors.extend(validate_record(record, location))
            record_id = record.get("id")
            if not isinstance(record_id, str) or not record_id:
                continue
            actual_ids.append(record_id)
            if record_id in seen_ids:
                errors.append(
                    f"{location}: classification ID collision with {seen_ids[record_id]}: {record_id}"
                )
            else:
                seen_ids[record_id] = location
            copy = dict(record)
            copy["_domain"] = domain
            classifications.append(copy)
        actual_set = set(actual_ids)
        missing = sorted(expected_set - actual_set)
        extra = sorted(actual_set - expected_set)
        if missing:
            errors.append(f"{classification_name}: missing {len(missing)} expected IDs")
        if extra:
            errors.append(f"{classification_name}: contains {len(extra)} IDs not in its chunk")
        if len(actual_set) != len(actual_ids):
            errors.append(f"{classification_name}: duplicate IDs inside classification file")
    extra_files = sorted(path.name for path in directory.glob("cat_*.jsonl") if path.name not in expected_files)
    if extra_files:
        errors.append(f"unexpected stale classification files: {', '.join(extra_files)}")
    extra_chunks = sorted(
        path.name for path in directory.glob("chunk_*.jsonl") if path.name not in chunk_files_seen
    )
    if extra_chunks:
        errors.append(f"unexpected stale chunk files: {', '.join(extra_chunks)}")
    missing_representatives = expected_representative_ids - chunk_ids_seen
    extra_representatives = chunk_ids_seen - expected_representative_ids
    if missing_representatives:
        errors.append(
            f"chunk set misses {len(missing_representatives)} deduplicated corpus representative IDs"
        )
    if extra_representatives:
        errors.append(
            f"chunk set contains {len(extra_representatives)} IDs outside corpus representatives"
        )
    return classifications, errors
