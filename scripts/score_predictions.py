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

An optional `--feedback` file resolves still-`open` predictions from
`## [feedback-date] <title> — verdict: 👍 confirmed / ✋ corrected / ⛔ rejected`.
Exact date/title matches take precedence; later feedback may match one uniquely
identifiable earlier open action with the same title. Ambiguity fails closed.
Deterministic, stdlib-only, offline. This scores the loop; it is not an accuracy
guarantee for the semantic classifier (see TODO.md, κ≈0.24).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from pipeline_common import validate_since, validate_timestamp

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
_VERDICT_RE = re.compile(
    r"^##\s*\[(?P<date>\d{4}-\d{2}-\d{2})\]\s*(?P<title>.+?)\s*"
    r"[—-]\s*verdict:\s*(?P<verdict>.+?)\s*$"
)
FeedbackKey = tuple[str, str]


def norm_confidence(raw: str) -> str | None:
    return CONFIDENCE.get(raw.strip().lower())


def parse_actions(text: str) -> list[dict[str, str]]:
    """Parse MY-ACTIONS.txt content into normalized rows."""
    rows: list[dict[str, str]] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 6:
            raise ValueError(
                f"line {line_number}: expected 6 tab-separated fields, found {len(fields)}"
            )
        timestamp = fields[0].strip()
        try:
            validate_timestamp(timestamp)
        except ValueError as exc:
            raise ValueError(f"line {line_number}: invalid timestamp: {exc}") from exc
        confidence = norm_confidence(fields[1])
        if confidence is None:
            raise ValueError(f"line {line_number}: unknown confidence {fields[1]!r}")
        reversible = fields[2].strip().lower()
        if reversible not in {"y", "n"}:
            raise ValueError(f"line {line_number}: reversible must be 'y' or 'n'")
        status = fields[3].strip().lower()
        if status not in STATUS or not status:
            raise ValueError(f"line {line_number}: unknown status {fields[3]!r}")
        title = fields[4].strip()
        if not title:
            raise ValueError(f"line {line_number}: title must not be empty")
        rows.append(
            {
                "date": timestamp[:10],
                "confidence": confidence,
                "outcome": STATUS[status],
                "title": title,
            }
        )
    return rows


def parse_feedback(text: str) -> dict[FeedbackKey, str]:
    """Parse verdict headers into {(date, normalized title) -> hit|miss}."""
    verdicts: dict[FeedbackKey, str] = {}
    for line in text.splitlines():
        match = _VERDICT_RE.match(line.strip())
        if not match:
            continue
        feedback_date = validate_since(match.group("date"))
        title = match.group("title").strip().lower()
        key = (feedback_date, title)
        if key in verdicts:
            raise ValueError(
                f"duplicate feedback verdict for {feedback_date} and title {title!r}"
            )
        verdict = match.group("verdict").lower()
        if "👍" in verdict or "confirmed" in verdict:
            verdicts[key] = "hit"
        elif "✋" in verdict or "⛔" in verdict or "corrected" in verdict or "rejected" in verdict:
            verdicts[key] = "miss"
    return verdicts


def _bucket(rows: list[dict[str, str]]) -> dict[str, object]:
    hits = sum(1 for r in rows if r["outcome"] == "hit")
    misses = sum(1 for r in rows if r["outcome"] == "miss")
    resolved = hits + misses
    return {"resolved": resolved, "hits": hits,
            "hit_rate": (hits / resolved) if resolved else None}


def score(actions: list[dict[str, str]],
          feedback: dict[FeedbackKey, str] | None = None) -> dict[str, object]:
    feedback = feedback or {}
    matched: set[FeedbackKey] = set()
    rows: list[dict[str, str]] = []
    for action in actions:
        rows.append(dict(action))

    pending_by_key: dict[FeedbackKey, int] = {}
    pending_by_title: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        if row["outcome"] != "pending":
            continue
        title = row["title"].strip().lower()
        key = (row["date"], title)
        if key in pending_by_key:
            raise ValueError(f"ambiguous open actions share date/title key {key!r}")
        pending_by_key[key] = index
        pending_by_title.setdefault(title, []).append(index)

    resolved_actions: set[int] = set()
    # First bind every exact action-date/title reference. This makes matching
    # independent of feedback-file order when a title is reused.
    for key, outcome in feedback.items():
        index = pending_by_key.get(key)
        if index is None:
            continue
        rows[index]["outcome"] = outcome
        resolved_actions.add(index)
        matched.add(key)

    # A feedback header normally carries the day the feedback was received,
    # which can be later than the action. Resolve only a single remaining
    # earlier action with the same title; never guess among repeated titles.
    for key, outcome in feedback.items():
        if key in matched:
            continue
        feedback_date, title = key
        candidates = [
            index
            for index in pending_by_title.get(title, [])
            if index not in resolved_actions and rows[index]["date"] <= feedback_date
        ]
        if len(candidates) > 1:
            dates = ", ".join(rows[index]["date"] for index in candidates)
            raise ValueError(
                f"feedback for {feedback_date} and title {title!r} could match "
                f"multiple earlier open actions ({dates})"
            )
        if candidates:
            index = candidates[0]
            rows[index]["outcome"] = outcome
            resolved_actions.add(index)
            matched.add(key)

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
    try:
        actions = parse_actions(actions_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"ERROR: cannot read valid actions log: {exc}", file=sys.stderr)
        return 2

    feedback: dict[FeedbackKey, str] = {}
    if args.feedback:
        feedback_path = Path(args.feedback).expanduser()
        if not feedback_path.is_file():
            print(f"ERROR: feedback file not found: {feedback_path}", file=sys.stderr)
            return 2
        try:
            feedback = parse_feedback(feedback_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            print(f"ERROR: cannot read feedback file: {exc}", file=sys.stderr)
            return 2

    try:
        result = score(actions, feedback)
    except ValueError as exc:
        print(f"ERROR: cannot score ambiguous action log: {exc}", file=sys.stderr)
        return 2
    payload = json.dumps(result, ensure_ascii=False, indent=2) if args.json else format_report(result)
    if args.out:
        Path(args.out).expanduser().write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
