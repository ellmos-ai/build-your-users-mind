#!/usr/bin/env python3
"""
Codex CLI source adapter for build-your-users-mind.

Extracts human-typed prompts from Codex rollout JSONL logs and writes the same
normalized JSONL records as scripts/corpus_extract.py.

Usage:
    PYTHONIOENCODING=utf-8 python scripts/adapters/codex_adapter.py --root ~/.codex/sessions --since YYYY-MM-DD --out ./STUDIE
"""
import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from corpus_extract import DECISION_LEXICON, outcome, parse_command, redact


CODEX_SYNTHETIC_PREFIXES = (
    "<environment_context>",
    "<user_instructions>",
    "<tool",
    "Tool-Outputs",
)
CODEX_BLOCKS = (
    re.compile(r"<environment_context>.*?</environment_context>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<user_instructions>.*?</user_instructions>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<tool_outputs?>.*?</tool_outputs?>", re.DOTALL | re.IGNORECASE),
)


def clean_codex_text(t):
    for pattern in CODEX_BLOCKS:
        t = pattern.sub("", t)
    lines = []
    in_tool_outputs = False
    for line in t.splitlines():
        stripped = line.strip()
        if stripped.startswith("Tool-Outputs"):
            in_tool_outputs = True
            continue
        if in_tool_outputs and not stripped:
            in_tool_outputs = False
            continue
        if not in_tool_outputs:
            lines.append(line)
    return "\n".join(lines).strip()


def synthetic(t):
    s = t.strip()
    return s.startswith(CODEX_SYNTHETIC_PREFIXES)


def extract_human(entry):
    if entry.get("type") != "response_item":
        return None
    payload = entry.get("payload", {})
    if not isinstance(payload, dict) or payload.get("role") != "user":
        return None
    content = payload.get("content", [])
    if not isinstance(content, list):
        return None
    parts = []
    for block in content:
        if not isinstance(block, dict) or block.get("type") != "input_text":
            continue
        text = block.get("text", "")
        if isinstance(text, str) and text.strip():
            parts.append(text)
    text = clean_codex_text("\n".join(parts))
    if not text or synthetic(text):
        return None
    return text


def collect_files(root):
    root = Path(root).expanduser()
    roots = [root]
    archived = root.parent / "archived_sessions"
    if root.name == "sessions" and archived.exists():
        roots.append(archived)
    files = []
    for base in roots:
        if base.exists():
            files.extend(base.rglob("rollout-*.jsonl"))
    return sorted(set(files))


def record_context(entry, path):
    payload = entry.get("payload", {})
    if not isinstance(payload, dict):
        payload = {}
    return {
        "ts": entry.get("timestamp", entry.get("ts", "")),
        "session": path.stem,
        "project": entry.get("cwd", payload.get("cwd", "")),
        "branch": entry.get("gitBranch", entry.get("git_branch", payload.get("gitBranch", payload.get("git_branch", "")))),
    }


def build_records(files, since):
    recs, total, redactions, withdata = [], 0, 0, 0
    for path in files:
        rows = []
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    text = extract_human(entry)
                    if not text:
                        continue
                    ctx = record_context(entry, path)
                    if since and ctx["ts"] and ctx["ts"][:10] < since:
                        continue
                    ctx["raw"] = text
                    rows.append(ctx)
        except (OSError, UnicodeDecodeError):
            continue
        if not rows:
            continue
        withdata += 1
        rows.sort(key=lambda r: r["ts"])
        for i, row in enumerate(rows):
            total += 1
            is_cmd, cname, norm = parse_command(row["raw"])
            text, c = redact(norm if is_cmd else row["raw"])
            redactions += c
            words = text.split()
            followup = ""
            if i + 1 < len(rows):
                _, _, next_norm = parse_command(rows[i + 1]["raw"])
                followup, _ = redact(next_norm)
            recs.append({
                "id": "",
                "ts": row["ts"],
                "source": "codex",
                "project": row["project"],
                "branch": row["branch"],
                "session": row["session"],
                "sender": "human",
                "ptype": "slash" if is_cmd else ("ack" if len(words) <= 3 else "frei"),
                "command": cname if is_cmd else "",
                "text": text,
                "text_short": " ".join(words[:15]) + ("..." if len(words) > 15 else ""),
                "word_count": len(words),
                "decision_score": sum(1 for k in DECISION_LEXICON if k in text.lower()),
                "followup_short": " ".join(followup.split()[:15]),
                "outcome_signal": outcome(followup.lower()),
            })
    recs.sort(key=lambda r: (r["ts"], r["session"]))
    for i, rec in enumerate(recs, 1):
        rec["id"] = f"H{i:05d}"
    return recs, total, redactions, withdata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path.home() / ".codex" / "sessions"))
    parser.add_argument("--since", default="", help="ISO-Datum YYYY-MM-DD (optional)")
    parser.add_argument("--out", default="./STUDIE")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    files = collect_files(args.root)
    recs, total, redactions, withdata = build_records(files, args.since)

    target = out / "00_corpus.jsonl"
    with open(target, "w", encoding="utf-8") as f:
        for rec in recs:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    uniq = len(set(r["text"] for r in recs))
    decisions = sum(1 for r in recs if r["decision_score"] >= 1 and r["ptype"] != "ack")
    print(
        f"Sessions: {len(files)} ({withdata} mit Daten) | Human-Prompts: {total} | "
        f"eindeutig: {uniq} | Entscheidungs-Kandidaten: {decisions} | Redaction: {redactions}"
    )
    print(f"-> {target}")


if __name__ == "__main__":
    main()
