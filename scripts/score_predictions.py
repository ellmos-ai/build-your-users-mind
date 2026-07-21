#!/usr/bin/env python3
"""Score the feedback-precognition loop: how often did predictions match reality?

Reads the machine-readable action log `MY-ACTIONS.txt` (the mirror of
`WHAT-I-DID-…md`) and, optionally, a `WHAT-USER-SAID-ABOUT-…md` feedback file,
and reports the hit rate overall and per confidence tier (🟢/🟡/🔴) plus the
escalation rate at 🔴 ("escalate, don't guess").

`MY-ACTIONS.txt` line format (tab-separated, see templates/MY-ACTIONS.txt):

    <ISO-ts>\\t<confidence>\\t<reversible y|n>\\t<status>\\t<title>\\t<assumed-will>

`status` vocabulary (backward-compatible extension):
    confirmed  -> prediction hit
    corrected  -> prediction miss
    rejected   -> prediction miss
    escalated  -> agent escalated at 🔴 instead of guessing (excluded from hit rate)
    open       -> pending (no feedback yet)

An optional `--feedback` file resolves still-`open` predictions by matching the
title against `## [date] <title> — verdict: 👍 confirmed / ✋ corrected / ⛔ rejected`.
Deterministic, stdlib-only, offline. This scores the loop; it is not an accuracy
guarantee for the semantic classifier (see TODO.md, κ≈0.24).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CONFIDENCE = {
    "🟢": "green", "green": "green", "g": "green", "high": "green",
    "🟡": "yellow", "yellow": "yellow", "y": "yellow", "medium": "yellow", "med": "yellow",
    "🔴": "red", "red": "red", "r": "red", "low": "red", "novel": "red",
}
STATUS = {
    "confirmed": "hit",
    "corrected": "miss", "rejected": "miss",
    "escalated": "escalated",
    "open": "pending", "pending": "pending", "": "pending",
}
TIERS = ("green", "yellow", "red")
_VERDICT_RE = re.compile(r"^##\s*\[[^\]]*\]\s*(?P<title>.+?)\s*[—-]\s*verdict:\s*(?P<verdict>.+?)\s*$")


def norm_confidence(raw: str) -> str | None:
    return CONFIDENCE.get(raw.strip().lower())


def parse_actions(text: str) -> list[dict[str, str]]:
    """Parse MY-ACTIONS.txt content into normalized rows."""
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) < 4:
            continue
        confidence = norm_confidence(fields[1])
        outcome = STATUS.get(fields[3].strip().lower(), "pending")
        title = fields[4].strip() if len(fields) > 4 else ""
        rows.append({"confidence": confidence or "", "outcome": outcome, "title": title})
    return rows


def parse_feedback(text: str) -> dict[str, str]:
    """Parse WHAT-USER-SAID-ABOUT verdict headers into {title -> hit|miss}."""
    verdicts: dict[str, str] = {}
    for line in text.splitlines():
        match = _VERDICT_RE.match(line.strip())
        if not match:
            continue
        title = match.group("title").strip().lower()
        verdict = match.group("verdict").lower()
        if "👍" in verdict or "confirmed" in verdict:
            verdicts[title] = "hit"
        elif "✋" in verdict or "⛔" in verdict or "corrected" in verdict or "rejected" in verdict:
            verdicts[title] = "miss"
    return verdicts


def _bucket(rows: list[dict[str, str]]) -> dict[str, object]:
    hits = sum(1 for r in rows if r["outcome"] == "hit")
    misses = sum(1 for r in rows if r["outcome"] == "miss")
    resolved = hits + misses
    return {"resolved": resolved, "hits": hits,
            "hit_rate": (hits / resolved) if resolved else None}


def score(actions: list[dict[str, str]],
          feedback: dict[str, str] | None = None) -> dict[str, object]:
    feedback = feedback or {}
    matched: set[str] = set()
    rows: list[dict[str, str]] = []
    for action in actions:
        row = dict(action)
        if row["outcome"] == "pending":
            key = row["title"].strip().lower()
            if key in feedback:
                row["outcome"] = feedback[key]
                matched.add(key)
        rows.append(row)

    red = [r for r in rows if r["confidence"] == "red"]
    escalated = sum(1 for r in red if r["outcome"] == "escalated")
    acted_at_red = sum(1 for r in red if r["outcome"] in ("hit", "miss"))
    decided = escalated + acted_at_red
    return {
        "n_actions": len(rows),
        "overall": _bucket(rows),
        "by_tier": {tier: _bucket([r for r in rows if r["confidence"] == tier]) for tier in TIERS},
        "escalation": {
            "escalated": escalated,
            "acted_at_red": acted_at_red,
            "escalation_rate": (escalated / decided) if decided else None,
        },
        "pending": sum(1 for r in rows if r["outcome"] == "pending"),
        "unmatched_feedback": len(set(feedback) - matched),
    }


def _pct(rate: object) -> str:
    return "n/a" if rate is None else f"{float(rate) * 100:.1f}%"


def format_report(result: dict[str, object]) -> str:
    overall = result["overall"]
    lines = [
        "Feedback-precognition score",
        f"  actions logged : {result['n_actions']}   (pending: {result['pending']})",
        f"  overall hit rate: {_pct(overall['hit_rate'])}  "
        f"({overall['hits']}/{overall['resolved']} resolved)",
        "  by confidence tier:",
    ]
    labels = {"green": "🟢 green ", "yellow": "🟡 yellow", "red": "🔴 red   "}
    for tier in TIERS:
        bucket = result["by_tier"][tier]
        lines.append(f"    {labels[tier]} : {_pct(bucket['hit_rate'])}  "
                     f"({bucket['hits']}/{bucket['resolved']})")
    esc = result["escalation"]
    lines.append(f"  🔴 escalation rate: {_pct(esc['escalation_rate'])}  "
                 f"(escalated {esc['escalated']} / acted {esc['acted_at_red']})")
    if result["unmatched_feedback"]:
        lines.append(f"  note: {result['unmatched_feedback']} feedback entr(ies) matched no action")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--actions", default="MY-ACTIONS.txt", help="path to MY-ACTIONS.txt")
    parser.add_argument("--feedback", default="", help="optional WHAT-USER-SAID-ABOUT…md file")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a report")
    parser.add_argument("--out", default="", help="write output to this file instead of stdout")
    args = parser.parse_args(argv)

    actions_path = Path(args.actions).expanduser()
    if not actions_path.is_file():
        print(f"ERROR: actions log not found: {actions_path}", file=sys.stderr)
        return 2
    actions = parse_actions(actions_path.read_text(encoding="utf-8"))

    feedback: dict[str, str] = {}
    if args.feedback:
        feedback_path = Path(args.feedback).expanduser()
        if not feedback_path.is_file():
            print(f"ERROR: feedback file not found: {feedback_path}", file=sys.stderr)
            return 2
        feedback = parse_feedback(feedback_path.read_text(encoding="utf-8"))

    result = score(actions, feedback)
    payload = json.dumps(result, ensure_ascii=False, indent=2) if args.json else format_report(result)
    if args.out:
        Path(args.out).expanduser().write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
