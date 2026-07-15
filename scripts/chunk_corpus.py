#!/usr/bin/env python3
"""Build a fresh, deterministic set of private Stage-2 classification chunks."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from pipeline_common import (
    atomic_write_jsonl,
    atomic_write_text,
    ensure_private_dir,
    load_jsonl,
    validate_unique_ids,
)


def classify(project: str, rules: dict[str, list[str]]) -> str:
    lowered = project.lower()
    for domain, keywords in rules.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            return domain
    return "all"


def safe_slug(domain: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", domain.lower()).strip("-")[:48] or "domain"
    digest = hashlib.sha256(domain.encode("utf-8")).hexdigest()[:8]
    return f"{base}-{digest}"


def load_domains(path_value: str) -> dict[str, list[str]]:
    if not path_value:
        return {}
    path = Path(path_value).expanduser()
    if not path.is_file():
        raise ValueError(f"domains file does not exist: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read domains file: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("domains file must contain an object")
    rules: dict[str, list[str]] = {}
    for domain, keywords in payload.items():
        if (
            not isinstance(domain, str)
            or not domain.strip()
            or not isinstance(keywords, list)
            or not keywords
            or any(not isinstance(keyword, str) or not keyword for keyword in keywords)
        ):
            raise ValueError("each domain needs a non-empty name and non-empty string list")
        rules[domain] = keywords
    return rules


def clean_managed_outputs(directory: Path) -> None:
    for pattern in ("chunk_*.jsonl", "cat_*.jsonl", "manifest.json"):
        for path in directory.glob(pattern):
            if path.is_file():
                path.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="./STUDIE/00_corpus.jsonl")
    parser.add_argument("--out", default="./STUDIE/_chunks")
    parser.add_argument("--chunk-size", type=int, default=85)
    parser.add_argument("--maxchars", type=int, default=700)
    parser.add_argument("--domains-json", default="")
    args = parser.parse_args(argv)
    if args.chunk_size <= 0:
        parser.error("--chunk-size must be positive")
    if args.maxchars <= 0:
        parser.error("--maxchars must be positive")
    try:
        rules = load_domains(args.domains_json)
        corpus_path = Path(args.corpus).expanduser()
        records = load_jsonl(corpus_path)
        validate_unique_ids(records)
    except ValueError as exc:
        parser.error(str(exc))
    for record in records:
        if not isinstance(record.get("text"), str) or not isinstance(record.get("ts"), str):
            parser.error("every corpus row needs string text and ts fields")

    by_text: dict[str, dict[str, object]] = {}
    for record in records:
        text = str(record["text"])
        if text not in by_text:
            copy = dict(record)
            copy["dup_count"] = 1
            by_text[text] = copy
        else:
            by_text[text]["dup_count"] = int(by_text[text]["dup_count"]) + 1

    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in by_text.values():
        project = str(record.get("project", ""))
        domain = classify(project, rules) if rules else "all"
        record["domain"] = domain
        grouped[domain].append(record)

    output = Path(args.out).expanduser()
    ensure_private_dir(output)
    clean_managed_outputs(output)
    manifest: dict[str, object] = {
        "schema": "build-your-users-mind.chunks.v1",
        "corpus": str(corpus_path),
        "corpus_sha256": hashlib.sha256(corpus_path.read_bytes()).hexdigest(),
        "corpus_records": len(records),
        "unique_records": len(by_text),
        "domains": {},
        "chunks": [],
    }
    chunk_index = 0
    for domain in sorted(grouped):
        domain_rows = sorted(
            grouped[domain],
            key=lambda row: (str(row.get("project", "")), str(row["ts"]), str(row["id"])),
        )
        manifest["domains"][domain] = len(domain_rows)  # type: ignore[index]
        slug = safe_slug(domain)
        for start in range(0, len(domain_rows), args.chunk_size):
            chunk_index += 1
            rows = []
            for record in domain_rows[start : start + args.chunk_size]:
                rows.append(
                    {
                        "id": record["id"],
                        "ts": str(record["ts"])[:10],
                        "project_short": str(record.get("project") or "?")
                        .replace("\\", "/")
                        .split("/")[-1],
                        "ptype": record.get("ptype"),
                        "command": record.get("command"),
                        "decision_score": record.get("decision_score"),
                        "outcome_signal": record.get("outcome_signal"),
                        "dup_count": record.get("dup_count", 1),
                        "text": str(record["text"])[: args.maxchars],
                    }
                )
            chunk_name = f"chunk_{chunk_index:04d}_{slug}.jsonl"
            classification_name = f"cat_{chunk_index:04d}_{slug}.jsonl"
            chunk_path = output / chunk_name
            atomic_write_jsonl(chunk_path, rows)
            manifest["chunks"].append(  # type: ignore[union-attr]
                {
                    "chunk": chunk_index,
                    "domain": domain,
                    "file": chunk_name,
                    "classification_file": classification_name,
                    "n": len(rows),
                    "sha256": hashlib.sha256(chunk_path.read_bytes()).hexdigest(),
                }
            )
    atomic_write_text(
        output / "manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    )
    print(
        f"Unique: {len(by_text)} | Domains: {manifest['domains']} | Chunks: {chunk_index}"
    )
    print(f"-> {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
