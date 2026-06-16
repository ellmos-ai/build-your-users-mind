#!/usr/bin/env python3
"""
build-user-tom · Stufe 0/1 — deterministische Korpus-Extraktion (kein LLM)
==========================================================================
Liest Agenten-Session-Logs (Default-Adapter: Claude Code JSONL) und extrahiert
NUR vom Menschen getippte Prompts. Mit Followup-Outcome-Verknuepfung, Redaction
und Slash-Command-Parsing. Andere Quellen: siehe ../SOURCE-ADAPTERS.md.

Nutzung:
    PYTHONIOENCODING=utf-8 python corpus_extract.py --root <LOG-WURZEL> [--since YYYY-MM-DD] [--out ./STUDIE]
"""
import json, re, argparse
from pathlib import Path
from collections import Counter

SYNTHETIC_PREFIXES = (
    "<system-reminder>", "<task-notification>", "<local-command-stdout>",
    "<bash-stdout>", "<bash-stderr>", "Caveat:", "[Request interrupted",
    "<post-tool-use-hook", "<user-prompt-submit-hook", "<session-start-hook",
)
SYNTHETIC_CONTAINS = ("Your questions have been answered:", "This session is being continued from a previous")

# Entscheidungs-Lexikon (DE/EN) — bei Bedarf an die eigene Sprache anpassen
DECISION_LEXICON = [
    "nicht so","das stimmt nicht","falsch","korrigier","stattdessen","nein,","doch nicht",
    "lieber","eher","bevorzug"," statt ","anstatt","revidier","rückgängig","mach das nicht","lass das",
    "ab jetzt","immer ","niemals"," nie ","grundsätzlich","als regel","konvention","merk dir",
    "in zukunft","von nun an","standard","default","soll ","sollst",
    "warte","zuerst","erst mal","stopp","halt","abbrechen","ändere","umstellen","anders","von vorne",
    "entscheid","ich will","ich möchte","wir machen","nehmen wir","wir nutzen",
    "use ","instead","rather","prefer","always","never","don't","do not","actually","let's ","we should","change it","redo",
]
PRAISE = ["sehr gut","perfekt","super","top","danke","passt","genau","richtig","weiter so","great","perfect","exactly","nice","thanks"]
CORRECTION = ["nicht so","stimmt nicht","falsch","nein","doch nicht","korrigier","stattdessen","lieber","ändere","anders","no,","wrong","not that","instead","fix that","revert"]
ACK = ["ok","okay","ja","weiter","gut","passt","go","yes","continue","next"]

REDACT = [
    (re.compile(r"\b(sk-[A-Za-z0-9]{20,})"), "[REDACTED_APIKEY]"),
    (re.compile(r"\b(ghp_[A-Za-z0-9]{20,})"), "[REDACTED_GHTOKEN]"),
    (re.compile(r"\b(github_pat_[A-Za-z0-9_]{20,})"), "[REDACTED_GHPAT]"),
    (re.compile(r"\b(AKIA[0-9A-Z]{16})\b"), "[REDACTED_AWS]"),
    (re.compile(r"(_authToken\s*=\s*)\S+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._\-]{20,}"), r"\1 [REDACTED_TOKEN]"),
    (re.compile(r"(?i)(api[_-]?key|token|secret|passwo?rt?|password)\s*[:=]\s*['\"]?[A-Za-z0-9._\-/+]{12,}"), r"\1=[REDACTED]"),
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[REDACTED_IP]"),
    (re.compile(r"\b(?:\d[ ]?){13,19}\b"), "[REDACTED_NUM]"),
]
def redact(t):
    n = 0
    for p, r in REDACT:
        t, c = p.subn(r, t); n += c
    return t, n

CMD_NAME = re.compile(r"<command-name>\s*(/?[^<]+?)\s*</command-name>")
CMD_ARGS = re.compile(r"<command-args>\s*(.*?)\s*</command-args>", re.DOTALL)
def parse_command(t):
    m = CMD_NAME.search(t)
    if not m: return False, "", t
    name = m.group(1).strip()
    am = CMD_ARGS.search(t); args = am.group(1).strip() if am else ""
    return True, name, (name + (" " + args if args else "")).strip()

def extract_human(entry):
    if entry.get("type") != "user": return None
    msg = entry.get("message", {})
    if not isinstance(msg, dict) or msg.get("role") != "user": return None
    c = msg.get("content", "")
    if isinstance(c, list):
        t = " ".join(b.get("text","") for b in c if isinstance(b, dict) and b.get("type")=="text")
    elif isinstance(c, str): t = c
    else: t = ""
    return t.strip() or None

def synthetic(t):
    return t.startswith(SYNTHETIC_PREFIXES) or any(s in t for s in SYNTHETIC_CONTAINS)

def outcome(fl):
    if not fl: return "none"
    if any(x in fl for x in CORRECTION): return "correction"
    if any(x in fl for x in PRAISE): return "praise"
    if len(fl.split()) <= 3 and any(x in fl for x in ACK): return "praise"
    return "reissue"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Wurzel der Session-Logs (z.B. ~/.claude/projects)")
    ap.add_argument("--since", default="", help="ISO-Datum YYYY-MM-DD (optional)")
    ap.add_argument("--out", default="./STUDIE")
    ap.add_argument("--source", default="claude")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    files = sorted(Path(a.root).rglob("*.jsonl"))
    recs, total, rh, withdata = [], 0, 0, 0
    for path in files:
        rows = []
        try:
            for line in open(path, encoding="utf-8"):
                line = line.strip()
                if not line: continue
                try: e = json.loads(line)
                except: continue
                t = extract_human(e)
                if not t or synthetic(t): continue
                ts = e.get("timestamp", "")
                if a.since and ts and ts[:10] < a.since: continue
                rows.append({"ts": ts, "session": path.stem, "project": e.get("cwd",""),
                             "branch": e.get("gitBranch",""), "raw": t})
        except (OSError, UnicodeDecodeError): continue
        if not rows: continue
        withdata += 1
        rows.sort(key=lambda r: r["ts"]); n = len(rows)
        for i, r in enumerate(rows):
            total += 1
            is_cmd, cname, norm = parse_command(r["raw"])
            text, c = redact(norm if is_cmd else r["raw"]); rh += c
            w = text.split()
            fl = ""
            if i+1 < n:
                _, _, fn = parse_command(rows[i+1]["raw"]); fl, _ = redact(fn)
            recs.append({"id":"", "ts":r["ts"], "source":a.source, "project":r["project"],
                         "branch":r["branch"], "session":r["session"], "sender":"human",
                         "ptype":"slash" if is_cmd else ("ack" if len(w)<=3 else "frei"),
                         "command":cname if is_cmd else "", "text":text,
                         "text_short":" ".join(w[:15])+("..." if len(w)>15 else ""),
                         "word_count":len(w), "decision_score":sum(1 for k in DECISION_LEXICON if k in text.lower()),
                         "followup_short":" ".join(fl.split()[:15]), "outcome_signal":outcome(fl.lower())})
    recs.sort(key=lambda r:(r["ts"], r["session"]))
    for i, r in enumerate(recs, 1): r["id"] = f"H{i:05d}"
    with open(out/"00_corpus.jsonl","w",encoding="utf-8") as f:
        for r in recs: f.write(json.dumps(r, ensure_ascii=False)+"\n")
    uniq = len(set(r["text"] for r in recs))
    dec = sum(1 for r in recs if r["decision_score"]>=1 and r["ptype"]!="ack")
    print(f"Sessions: {len(files)} ({withdata} mit Daten) | Human-Prompts: {total} | eindeutig: {uniq} | Entscheidungs-Kandidaten: {dec} | Redaction: {rh}")
    print(f"-> {out/'00_corpus.jsonl'}")

if __name__ == "__main__":
    main()
