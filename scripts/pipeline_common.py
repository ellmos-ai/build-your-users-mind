#!/usr/bin/env python3
"""Shared, deterministic safety helpers for the private prompt pipeline."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Iterable


DECISION_LEXICON = (
    "nicht so", "das stimmt nicht", "falsch", "korrigier", "stattdessen",
    "nein,", "doch nicht", "lieber", "eher", "bevorzug", " statt ",
    "anstatt", "revidier", "rückgängig", "mach das nicht", "lass das",
    "ab jetzt", "immer ", "niemals", " nie ", "grundsätzlich", "als regel",
    "konvention", "merk dir", "in zukunft", "von nun an", "standard",
    "default", "soll ", "sollst", "warte", "zuerst", "erst mal", "stopp",
    "halt", "abbrechen", "ändere", "umstellen", "anders", "von vorne",
    "entscheid", "ich will", "ich möchte", "wir machen", "nehmen wir",
    "wir nutzen", "use ", "instead", "rather", "prefer", "always", "never",
    "don't", "do not", "actually", "let's ", "we should", "change it",
    "redo", "stop ",
)

PRAISE = (
    "sehr gut", "perfekt", "super", "top", "danke", "passt", "genau",
    "richtig", "weiter so", "great", "perfect", "exactly", "nice", "thanks",
)
CORRECTION = (
    "nicht so", "stimmt nicht", "falsch", "nein", "doch nicht", "korrigier",
    "stattdessen", "lieber", "ändere", "anders", "no,", "wrong", "not that",
    "instead", "fix that", "revert",
)
ACK_PHRASES = frozenset(
    {
        "ok", "okay", "ja", "yes", "gut", "passt", "go", "weiter",
        "continue", "next", "danke", "thanks", "sounds good", "sieht gut aus",
    }
)
REISSUE = (
    "nochmal", "noch einmal", "wiederhole", "erneut", "versuch es erneut",
    "mach das nochmal", "repeat", "try again", "once more", "redo that",
)

SYNTHETIC_PREFIXES = (
    "<system-reminder>", "<task-notification>", "<local-command-stdout>",
    "<bash-stdout>", "<bash-stderr>", "caveat:", "[request interrupted",
    "<post-tool-use-hook", "<user-prompt-submit-hook", "<session-start-hook",
    "<environment_context>", "<user_instructions>", "<tool", "tool-outputs",
    "<codex_internal_context>", "<recommended_plugins>",
)
SYNTHETIC_CONTAINS = (
    "your questions have been answered:",
    "this session is being continued from a previous",
)

DEFAULT_REDACTIONS = (
    (re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"), "[REDACTED_APIKEY]"),
    (re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"), "[REDACTED_GHTOKEN]"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"), "[REDACTED_GHPAT]"),
    (re.compile(r"\bglpat-[A-Za-z0-9_-]{16,}\b"), "[REDACTED_GITLAB]"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{16,}\b"), "[REDACTED_SLACK]"),
    (re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"), "[REDACTED_HF]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_AWS]"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"), "[REDACTED_JWT]"),
    (
        re.compile(
            r"-----BEGIN [A-Z ]*" + "PRIVATE" + r" KEY-----.*?-----END [A-Z ]*" + "PRIVATE" + r" KEY-----",
            re.DOTALL,
        ),
        "[REDACTED_ASYMMETRIC_CREDENTIAL]",
    ),
    (re.compile(r"(_authToken\s*=\s*)\S+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._\-]{12,}"), r"\1 [REDACTED_TOKEN]"),
    (re.compile(r"(?i)(api[_-]?key|access[_-]?token|token|secret|passwo?rt?|password)\s*[:=]\s*['\"]?[^\s'\"]{8,}"), r"\1=[REDACTED]"),
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[REDACTED_IP]"),
    (re.compile(r"\b(?:\d[ ]?){13,19}\b"), "[REDACTED_NUM]"),
)

CMD_NAME = re.compile(r"<command-name>\s*(/?[^<]+?)\s*</command-name>")
CMD_ARGS = re.compile(r"<command-args>\s*(.*?)\s*</command-args>", re.DOTALL)


def validate_since(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("--since must be an exact ISO date (YYYY-MM-DD)") from exc
    if parsed.isoformat() != value:
        raise ValueError("--since must be an exact ISO date (YYYY-MM-DD)")
    return value


ISO_TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def validate_timestamp(value: object) -> str:
    if not isinstance(value, str) or not ISO_TIMESTAMP.fullmatch(value):
        raise ValueError("timestamp must be a complete ISO-8601 datetime with timezone")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("timestamp is not a valid ISO-8601 datetime") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return value


def is_synthetic(text: str) -> bool:
    lowered = text.lstrip().lower()
    return lowered.startswith(SYNTHETIC_PREFIXES) or any(
        marker in lowered for marker in SYNTHETIC_CONTAINS
    )


def parse_command(text: str) -> tuple[bool, str, str]:
    match = CMD_NAME.search(text)
    if not match:
        return False, "", text
    name = match.group(1).strip()
    args_match = CMD_ARGS.search(text)
    args = args_match.group(1).strip() if args_match else ""
    return True, name, (name + (" " + args if args else "")).strip()


def load_redaction_rules(path: str = "") -> tuple[tuple[re.Pattern[str], str], ...]:
    if not path:
        return DEFAULT_REDACTIONS
    source = Path(path).expanduser()
    if not source.is_file():
        raise ValueError(f"redaction rules file does not exist: {source}")
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read redaction rules: {exc}") from exc
    if not isinstance(payload, list):
        raise ValueError("redaction rules must be a JSON array")
    custom: list[tuple[re.Pattern[str], str]] = []
    for index, item in enumerate(payload, 1):
        if not isinstance(item, dict) or not isinstance(item.get("pattern"), str):
            raise ValueError(f"redaction rule {index} needs a string 'pattern'")
        replacement = item.get("replacement", "[REDACTED_CUSTOM]")
        if not isinstance(replacement, str):
            raise ValueError(f"redaction rule {index} has a non-string replacement")
        flags = re.IGNORECASE if item.get("ignore_case") is True else 0
        try:
            custom.append((re.compile(item["pattern"], flags), replacement))
        except re.error as exc:
            raise ValueError(f"invalid regex in redaction rule {index}: {exc}") from exc
    return DEFAULT_REDACTIONS + tuple(custom)


def redact(
    text: str, rules: Iterable[tuple[re.Pattern[str], str]] = DEFAULT_REDACTIONS
) -> tuple[str, int]:
    count = 0
    for pattern, replacement in rules:
        text, matches = pattern.subn(replacement, text)
        count += matches
    return text, count


def decision_score(text: str) -> int:
    lowered = text.lower()
    return sum(1 for term in DECISION_LEXICON if _contains_term(lowered, term))


def _contains_term(text: str, term: str) -> bool:
    value = term.strip().lower()
    if not value:
        return False
    if value[0].isalnum() and value[-1].isalnum():
        return re.search(rf"(?<!\w){re.escape(value)}(?!\w)", text) is not None
    return value in text


def prompt_type(text: str, is_command: bool = False) -> str:
    if is_command:
        return "slash"
    normalized = " ".join(text.lower().strip(" .!?,;:").split())
    return "ack" if normalized in ACK_PHRASES else "frei"


def outcome(followup_lower: str) -> str:
    normalized = " ".join(followup_lower.strip().split())
    if not normalized:
        return "none"
    if any(_contains_term(normalized, term) for term in CORRECTION):
        return "correction"
    if any(_contains_term(normalized, term) for term in PRAISE) or normalized.strip(" .!?,;:") in ACK_PHRASES:
        return "praise"
    if any(_contains_term(normalized, term) for term in REISSUE):
        return "reissue"
    return "none"


def stable_id(source: str, session: str, timestamp: str, text: str) -> str:
    canonical = json.dumps(
        [source, session, timestamp, text], ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return "H_" + hashlib.sha256(canonical).hexdigest()[:20]


def normalize_rows(
    rows: list[dict[str, str]],
    source: str,
    redaction_rules: Iterable[tuple[re.Pattern[str], str]] = DEFAULT_REDACTIONS,
) -> tuple[list[dict[str, object]], int]:
    records: list[dict[str, object]] = []
    redactions = 0
    rows.sort(key=lambda row: (row.get("ts", ""), row.get("session", "")))
    for index, row in enumerate(rows):
        is_command, command_name, normalized = parse_command(row["raw"])
        text, count = redact(normalized if is_command else row["raw"], redaction_rules)
        redactions += count
        followup = ""
        if index + 1 < len(rows):
            _, _, next_text = parse_command(rows[index + 1]["raw"])
            followup, followup_count = redact(next_text, redaction_rules)
            redactions += followup_count
        words = text.split()
        ptype = prompt_type(text, is_command)
        score = decision_score(text)
        record: dict[str, object] = {
            "id": stable_id(source, row["session"], row["ts"], normalized if is_command else row["raw"]),
            "ts": row["ts"],
            "source": source,
            "project": row.get("project", ""),
            "branch": row.get("branch", ""),
            "session": row["session"],
            "sender": "human",
            "ptype": ptype,
            "command": command_name if is_command else "",
            "text": text,
            "text_short": " ".join(words[:15]) + ("..." if len(words) > 15 else ""),
            "word_count": len(words),
            "decision_score": score,
            "followup_short": " ".join(followup.split()[:15]),
            "outcome_signal": outcome(followup.lower()),
        }
        records.append(record)
    return records, redactions


def ensure_private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path, 0o700)
    except OSError:
        pass


def atomic_write_text(path: Path, content: str) -> None:
    ensure_private_dir(path.parent)
    handle, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.chmod(temp, 0o600)
        except OSError:
            pass
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def atomic_write_jsonl(path: Path, records: Iterable[dict[str, object]]) -> None:
    atomic_write_text(
        path,
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
    )


def load_jsonl(path: Path, *, require_object: bool = True) -> list[dict[str, object]]:
    if not path.is_file():
        raise ValueError(f"file does not exist: {path}")
    rows: list[dict[str, object]] = []
    try:
        with path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
                if require_object and not isinstance(value, dict):
                    raise ValueError(f"{path}:{line_number}: expected a JSON object")
                rows.append(value)
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    return rows


def validate_unique_ids(records: Iterable[dict[str, object]]) -> None:
    seen: dict[str, dict[str, object]] = {}
    for record in records:
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id:
            raise ValueError("every corpus row needs a non-empty string id")
        if record_id in seen:
            raise ValueError(f"duplicate or colliding corpus id: {record_id}")
        seen[record_id] = record
