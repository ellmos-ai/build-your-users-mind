#!/usr/bin/env python3
"""
build-your-users-mind · Stufe 0/1 — Kimi-Source-Adapter (kein LLM)
=================================================================
Liest Kimi Code CLI Session-Logs und extrahiert NUR vom Menschen getippte Prompts.

Kimi-speicherort/-format (ermittelt über `kimi-code doctor` und Inspektion von
~/.kimi-code/):

- Konfigurations-/Daten-Home:  ~/.kimi-code/
  (auf Windows z. B. C:/Users/<user>/.kimi-code/)
- Session-Index:               ~/.kimi-code/session_index.jsonl
  Jede Zeile ein JSON-Objekt mit den Feldern:
  sessionId, sessionDir (absoluter Pfad), workDir (absoluter Pfad).
- Session-Daten pro Session:   <sessionDir>/agents/main/wire.jsonl
  Das ist eine JSONL-Datei, in der jede Zeile ein Wire-Ereignis darstellt.
- Menschliche Prompts sind Ereignisse vom Typ "turn.prompt" mit
  origin.kind == "user". Der eingegebene Text steht in entry["input"]
  entweder als Liste von Text-Blöcken (dict mit type:"text") oder direkt
  als String.
- Zeitstempel stehen im Feld "time" als Unix-Epoche in Millisekunden.
- Projekt/Working-Directory wird dem Session-Index entnommen (workDir).
  Git-Branch wird optional aus workDir ermittelt.

Nutzung:
    PYTHONIOENCODING=utf-8 python scripts/adapters/kimi_adapter.py \
        --root ~/.kimi-code/sessions [--since YYYY-MM-DD] [--out ./STUDIE]
"""
import sys
from pathlib import Path

# corpus_extract liegt im Elternverzeichnis; dort Vertragsfunktionen importieren.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from corpus_extract import redact, outcome, parse_command, DECISION_LEXICON

import json
import re
import argparse
import subprocess
import datetime

# Dieselben synthetischen Einschübe wie im Referenz-Adapter (lokaler Filter,
# da sie nicht Teil des öffentlichen Imports aus corpus_extract sind).
SYNTHETIC_PREFIXES = (
    "<system-reminder>", "<task-notification>", "<local-command-stdout>",
    "<bash-stdout>", "<bash-stderr>", "Caveat:", "[Request interrupted",
    "<post-tool-use-hook", "<user-prompt-submit-hook", "<session-start-hook",
)
SYNTHETIC_CONTAINS = ("Your questions have been answered:", "This session is being continued from a previous")


def synthetic(t):
    return t.startswith(SYNTHETIC_PREFIXES) or any(s in t for s in SYNTHETIC_CONTAINS)


def extract_human(entry):
    if entry.get("type") != "turn.prompt":
        return None
    origin = entry.get("origin") or {}
    if origin.get("kind") != "user":
        return None
    inp = entry.get("input", "")
    if isinstance(inp, list):
        texts = [b.get("text", "") for b in inp
                 if isinstance(b, dict) and b.get("type") == "text"]
        raw = " ".join(texts)
    elif isinstance(inp, str):
        raw = inp
    else:
        return None
    raw = raw.strip()
    return raw or None


def ms_to_iso(ts_ms):
    if not isinstance(ts_ms, (int, float)):
        return ""
    try:
        dt = datetime.datetime.fromtimestamp(ts_ms / 1000.0, tz=datetime.timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(ts_ms) % 1000:03d}Z"
    except (OverflowError, OSError, ValueError):
        return ""


def git_branch(work_dir):
    try:
        cp = subprocess.run(
            ["git", "-C", str(work_dir), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5, encoding="utf-8", errors="ignore"
        )
        if cp.returncode == 0:
            return cp.stdout.strip()
    except Exception:
        pass
    return ""


def load_session_index(root):
    """Liest ~/.kimi-code/session_index.jsonl und liefert session_name -> workDir."""
    idx = {}
    idx_path = Path(root).parent / "session_index.jsonl"
    if not idx_path.exists():
        return idx
    for line in open(idx_path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
            sd = e.get("sessionDir")
            wd = e.get("workDir")
            if sd and wd:
                idx[Path(sd).name] = wd
        except (json.JSONDecodeError, TypeError):
            continue
    return idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True,
                    help="Wurzel der Kimi-Sessions (z. B. ~/.kimi-code/sessions)")
    ap.add_argument("--since", default="", help="ISO-Datum YYYY-MM-DD (optional)")
    ap.add_argument("--out", default="./STUDIE")
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    root = Path(a.root)
    session_index = load_session_index(root)

    files = sorted(root.rglob("wire.jsonl"))
    recs, total, rh, withdata = [], 0, 0, 0

    for path in files:
        # Erwartete Struktur: .../<sessionDir>/agents/main/wire.jsonl
        session_dir = path.parents[2]
        session_name = session_dir.name
        work_dir = session_index.get(session_name, "")
        project = Path(work_dir).name if work_dir else session_name
        branch = git_branch(work_dir) if work_dir else ""

        rows = []
        try:
            for line in open(path, encoding="utf-8"):
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                raw = extract_human(e)
                if not raw or synthetic(raw):
                    continue
                ts = ms_to_iso(e.get("time"))
                if a.since and ts and ts[:10] < a.since:
                    continue
                rows.append({"ts": ts, "session": session_name, "project": project,
                             "branch": branch, "raw": raw})
        except (OSError, UnicodeDecodeError):
            continue

        if not rows:
            continue
        withdata += 1
        rows.sort(key=lambda r: r["ts"])
        n = len(rows)
        for i, r in enumerate(rows):
            total += 1
            is_cmd, cname, norm = parse_command(r["raw"])
            text, c = redact(norm if is_cmd else r["raw"])
            rh += c
            w = text.split()
            fl = ""
            if i + 1 < n:
                _, _, fn = parse_command(rows[i + 1]["raw"])
                fl, _ = redact(fn)
            recs.append({
                "id": "",
                "ts": r["ts"],
                "source": "kimi",
                "project": r["project"],
                "branch": r["branch"],
                "session": r["session"],
                "sender": "human",
                "ptype": "slash" if is_cmd else ("ack" if len(w) <= 3 else "frei"),
                "command": cname if is_cmd else "",
                "text": text,
                "text_short": " ".join(w[:15]) + ("..." if len(w) > 15 else ""),
                "word_count": len(w),
                "decision_score": sum(1 for k in DECISION_LEXICON if k in text.lower()),
                "followup_short": " ".join(fl.split()[:15]),
                "outcome_signal": outcome(fl.lower()),
            })

    recs.sort(key=lambda r: (r["ts"], r["session"]))
    for i, r in enumerate(recs, 1):
        r["id"] = f"H{i:05d}"

    with open(out / "00_corpus.jsonl", "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    uniq = len(set(r["text"] for r in recs))
    dec = sum(1 for r in recs if r["decision_score"] >= 1 and r["ptype"] != "ack")
    print(f"Sessions: {len(files)} ({withdata} mit Daten) | Human-Prompts: {total} | "
          f"eindeutig: {uniq} | Entscheidungs-Kandidaten: {dec} | Redaction: {rh}")
    print(f"-> {out / '00_corpus.jsonl'}")


if __name__ == "__main__":
    main()
