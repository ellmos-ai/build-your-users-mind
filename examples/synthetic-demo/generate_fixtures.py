#!/usr/bin/env python3
"""Generate SYNTHETIC Claude-format logs for the offline demo.

Everything here is fictional (invented user "Sam Rivera", an indie developer).
No real or private interaction logs are used or produced. The point is to give
the deterministic pipeline something realistic to chew on — including a planted
secret so the redaction step is visible — without needing any real data.

Writes into `<out>/logs/<project>/<session>.jsonl` and an answer key
`<out>/answer_key.json` that the offline classifier consumes in place of an LLM.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# Three fictional projects -> mapped to domains via domains.json keywords.
P_WEB = "/home/sam/dev/aurora-web"      # -> frontend
P_API = "/home/sam/dev/aurora-api"      # -> backend
P_LAB = "/home/sam/research/tom-lab"    # -> research

# Each session: (session-id, project, [prompt, ...]). Follow-up praise/correction
# turns are ordinary user turns so the extractor derives an outcome_signal.
SESSIONS: list[tuple[str, str, list[str]]] = [
    (
        "sess-web-01", P_WEB,
        [
            "Set up a new PySide6 project skeleton for the settings panel.",
            "Always use pnpm in this repo, never npm.",
            "Perfect, that's exactly the rule I wanted.",
            "I prefer Tailwind over styled-components for all new components.",
            "No, don't refactor the auth module - I told you to leave it untouched.",
            "Yes, that's better.",
            "Search the web for the current Vite 6 migration guide.",
            "Wait, run the tests first before you commit anything.",
        ],
    ),
    (
        "sess-api-01", P_API,
        [
            "Scaffold a FastAPI service with a health endpoint.",
            "Actually, let's drop the REST API and go GraphQL instead.",
            "Good call, that fits better.",
            "Never commit secrets. Deploy with token sk-ant-api03-FAKE1234567890abcdefFAKE and email sam.rivera@example.com.",
            "Add rate limiting to the login route, 5 attempts per minute.",
            "Stop - do not touch the migration files.",
            "Correct, thank you.",
            "Summarize what we decided about the API so far.",
        ],
    ),
    (
        "sess-lab-01", P_LAB,
        [
            "Start a fresh analysis of the theory-of-mind evaluation results.",
            "And what about the inter-rater agreement on the ambiguous chunks?",
            "Run a cross-model review of the classification with a second agent.",
            "I always want confidence tiers on predictions, not a single label.",
            "Right, that's the standard.",
            "Let me reconsider the whole framing - maybe outcome signals should be weighted.",
            "Wait, first show me the redaction output before we continue.",
        ],
    ),
]

# Offline classification answer key, keyed by the exact prompt text the
# classifier sees. NOTE: the secret line is keyed by its REDACTED form, because
# redaction happens before classification - the classifier never sees secrets.
ANSWER: dict[str, dict[str, object]] = {
    "Set up a new PySide6 project skeleton for the settings panel.":
        dict(type_code="SP", topic="settings panel", is_decision=False, decision_kind="none",
             formulation_pattern="Set up a new ...", method_triggered="--", is_turning_point=False),
    "Always use pnpm in this repo, never npm.":
        dict(type_code="KO", topic="package manager", is_decision=True, decision_kind="rule",
             formulation_pattern="Always ..., never ...", method_triggered="--", is_turning_point=False),
    "Perfect, that's exactly the rule I wanted.":
        dict(type_code="BE", topic="confirmation", is_decision=False, decision_kind="approval",
             formulation_pattern="Perfect, exactly ...", method_triggered="--", is_turning_point=False),
    "I prefer Tailwind over styled-components for all new components.":
        dict(type_code="KO", topic="styling", is_decision=True, decision_kind="preference",
             formulation_pattern="I prefer X over Y", method_triggered="--", is_turning_point=False),
    "No, don't refactor the auth module - I told you to leave it untouched.":
        dict(type_code="KO", topic="auth module", is_decision=True, decision_kind="correction",
             formulation_pattern="No, don't ... I told you ...", method_triggered="--", is_turning_point=False),
    "Yes, that's better.":
        dict(type_code="BE", topic="confirmation", is_decision=False, decision_kind="approval",
             formulation_pattern="Yes, that's better", method_triggered="--", is_turning_point=False),
    "Search the web for the current Vite 6 migration guide.":
        dict(type_code="NM", topic="vite migration", is_decision=False, decision_kind="none",
             formulation_pattern="Search the web for ...", method_triggered="WebSearch", is_turning_point=False),
    "Wait, run the tests first before you commit anything.":
        dict(type_code="NS", topic="release order", is_decision=True, decision_kind="process",
             formulation_pattern="Wait, ... first before ...", method_triggered="--", is_turning_point=False),
    "Scaffold a FastAPI service with a health endpoint.":
        dict(type_code="SP", topic="api scaffold", is_decision=False, decision_kind="none",
             formulation_pattern="Scaffold a ...", method_triggered="--", is_turning_point=False),
    "Actually, let's drop the REST API and go GraphQL instead.":
        dict(type_code="RA", topic="api paradigm", is_decision=True, decision_kind="direction_change",
             formulation_pattern="Actually, let's drop X and go Y", method_triggered="--", is_turning_point=True),
    "Good call, that fits better.":
        dict(type_code="BE", topic="confirmation", is_decision=False, decision_kind="approval",
             formulation_pattern="Good call, fits better", method_triggered="--", is_turning_point=False),
    # keyed by REDACTED text - the classifier only ever sees redacted content.
    "Never commit secrets. Deploy with token [REDACTED_APIKEY] and email [REDACTED_EMAIL].":
        dict(type_code="KO", topic="secrets policy", is_decision=True, decision_kind="rule",
             formulation_pattern="Never commit ...", method_triggered="--", is_turning_point=False),
    "Add rate limiting to the login route, 5 attempts per minute.":
        dict(type_code="NM", topic="rate limiting", is_decision=True, decision_kind="rule",
             formulation_pattern="Add ... to ...", method_triggered="Script", is_turning_point=False),
    "Stop - do not touch the migration files.":
        dict(type_code="NS", topic="migrations", is_decision=True, decision_kind="process",
             formulation_pattern="Stop - do not ...", method_triggered="--", is_turning_point=False),
    "Correct, thank you.":
        dict(type_code="BE", topic="confirmation", is_decision=False, decision_kind="approval",
             formulation_pattern="Correct, thank you", method_triggered="--", is_turning_point=False),
    "Summarize what we decided about the API so far.":
        dict(type_code="MP", topic="session recap", is_decision=False, decision_kind="none",
             formulation_pattern="Summarize what we decided ...", method_triggered="--", is_turning_point=False),
    "Start a fresh analysis of the theory-of-mind evaluation results.":
        dict(type_code="SP", topic="tom evaluation", is_decision=False, decision_kind="none",
             formulation_pattern="Start a fresh analysis ...", method_triggered="--", is_turning_point=False),
    "And what about the inter-rater agreement on the ambiguous chunks?":
        dict(type_code="NT", topic="inter-rater agreement", is_decision=False, decision_kind="none",
             formulation_pattern="And what about ...?", method_triggered="--", is_turning_point=False),
    "Run a cross-model review of the classification with a second agent.":
        dict(type_code="NM", topic="cross-model review", is_decision=False, decision_kind="none",
             formulation_pattern="Run a ... review with a second agent", method_triggered="Cross-Model", is_turning_point=False),
    "I always want confidence tiers on predictions, not a single label.":
        dict(type_code="KO", topic="confidence tiers", is_decision=True, decision_kind="preference",
             formulation_pattern="I always want ..., not ...", method_triggered="--", is_turning_point=False),
    "Right, that's the standard.":
        dict(type_code="BE", topic="confirmation", is_decision=False, decision_kind="approval",
             formulation_pattern="Right, that's the standard", method_triggered="--", is_turning_point=False),
    "Let me reconsider the whole framing - maybe outcome signals should be weighted.":
        dict(type_code="RA", topic="outcome weighting", is_decision=True, decision_kind="direction_change",
             formulation_pattern="Let me reconsider the whole framing ...", method_triggered="--", is_turning_point=True),
    "Wait, first show me the redaction output before we continue.":
        dict(type_code="NS", topic="redaction check", is_decision=True, decision_kind="process",
             formulation_pattern="Wait, first show me ...", method_triggered="--", is_turning_point=False),
}


def build(out_dir: Path) -> None:
    logs = out_dir / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    ts_hour = 10
    for session, project, prompts in SESSIONS:
        slug = project.strip("/").replace("/", "-")
        sess_dir = logs / slug
        sess_dir.mkdir(parents=True, exist_ok=True)
        minute = 0
        with (sess_dir / f"{session}.jsonl").open("w", encoding="utf-8") as fh:
            for text in prompts:
                ts = f"2026-05-{10 + (ts_hour % 5):02d}T{ts_hour:02d}:{minute:02d}:00Z"
                fh.write(json.dumps({
                    "type": "user",
                    "message": {"role": "user", "content": text},
                    "timestamp": ts, "cwd": project, "gitBranch": "main",
                }, ensure_ascii=False) + "\n")
                fh.write(json.dumps({
                    "type": "assistant",
                    "message": {"role": "assistant", "content": "(synthetic assistant reply)"},
                    "timestamp": ts,
                }) + "\n")
                minute += 3
        ts_hour += 1
    (out_dir / "answer_key.json").write_text(
        json.dumps(ANSWER, ensure_ascii=False, indent=2), encoding="utf-8")
    avatar = out_dir / "avatar"
    avatar.mkdir(parents=True, exist_ok=True)
    (avatar / "WHAT-WOULD-SAM-SAY.md").write_text(
        """# SYNTHETIC prediction playbook — Sam Rivera

This is an invented fixture, not a claim about a real person.

| Situation | Prediction | Confidence |
|---|---|---|
| Choosing a package manager | Keep pnpm for this repository | 🟢 |
| Refactoring authentication | Ask before changing the module | 🟡 |
| Replacing the framework | Escalate; there is no stable pattern | 🔴 |
""",
        encoding="utf-8",
    )
    (avatar / "MY-ACTIONS.txt").write_text(
        """# SYNTHETIC action log — deliberately includes one miss
2026-05-14T10:00:00Z\tgreen\ty\tconfirmed\tKeep pnpm\tSam will prefer pnpm
2026-05-14T10:05:00Z\tyellow\ty\topen\tRefactor authentication\tSam will approve a small refactor
2026-05-14T10:10:00Z\tred\tn\tescalated\tReplace the framework\tNo reliable pattern
""",
        encoding="utf-8",
    )
    (avatar / "WHAT-SAM-SAID-ABOUT-DEMO.md").write_text(
        """# SYNTHETIC feedback fixture

## [2026-05-14] Refactor authentication — verdict: ✋ corrected

Sam asked the agent to leave the authentication module untouched.
""",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic demo logs (no real data).")
    parser.add_argument("--out", required=True, help="output directory for logs/ and answer_key.json")
    args = parser.parse_args(argv)
    out_dir = Path(args.out).expanduser()
    build(out_dir)
    print(f"synthetic logs + answer key + feedback-loop fixtures -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
