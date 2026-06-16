#!/usr/bin/env python3
"""
build-your-users-mind · Stufe 0/1 — Gemini / agy (antigravity) Korpus-Extraktion
========================================================================
Liest Gemini-Session-Logs (SQLite-DBs) und extrahiert NUR vom Menschen getippte Prompts.
Unterstuetzt Followup-Outcome-Verknuepfung, Redaction und Slash-Command-Parsing
unter Verwendung der Logik aus corpus_extract.py.

Nutzung:
    PYTHONIOENCODING=utf-8 python gemini_adapter.py [--root <LOG-WURZEL>] [--since YYYY-MM-DD] [--out ./STUDIE]
"""
import sys
import sqlite3
import datetime
import json
import argparse
import urllib.parse
from pathlib import Path

# Add parent directory of scripts/adapters/ to sys.path to import corpus_extract.py
sys.path.append(str(Path(__file__).resolve().parents[1]))
from corpus_extract import redact, outcome, parse_command, DECISION_LEXICON


def parse_varint(data, pos):
    val = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        val |= (b & 0x7f) << shift
        pos += 1
        if not (b & 0x80):
            break
        shift += 7
    return val, pos


def parse_proto(data):
    pos = 0
    fields = {}
    while pos < len(data):
        try:
            key, pos = parse_varint(data, pos)
        except IndexError:
            break
        tag = key >> 3
        wire_type = key & 0x07
        if wire_type == 0:  # Varint
            try:
                val, pos = parse_varint(data, pos)
                fields[tag] = val
            except IndexError:
                break
        elif wire_type == 2:  # Length-delimited
            try:
                length, pos = parse_varint(data, pos)
                val = data[pos:pos+length]
                pos += length
                fields[tag] = val
            except IndexError:
                break
        elif wire_type == 1:  # 64-bit
            val = data[pos:pos+8]
            pos += 8
            fields[tag] = val
        elif wire_type == 5:  # 32-bit
            val = data[pos:pos+4]
            pos += 4
            fields[tag] = val
        else:
            break
    return fields


def extract_timestamp(metadata):
    if not metadata:
        return ""
    try:
        fields = parse_proto(metadata)
        ts_bytes = fields.get(1)
        if not ts_bytes or not isinstance(ts_bytes, bytes):
            return ""
        ts_fields = parse_proto(ts_bytes)
        seconds = ts_fields.get(1, 0)
        nanos = ts_fields.get(2, 0)
        dt = datetime.datetime.fromtimestamp(seconds + nanos / 1e9, tz=datetime.timezone.utc)
        return dt.isoformat().replace('+00:00', 'Z')
    except Exception:
        return ""


def extract_project_branch(db_conn):
    try:
        cursor = db_conn.cursor()
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trajectory_metadata_blob'")
        if not cursor.fetchone():
            return "", ""
        
        cursor.execute('SELECT data FROM trajectory_metadata_blob WHERE id = "main"')
        row = cursor.fetchone()
        if not row:
            return "", ""
        fields = parse_proto(row[0])
        
        project = ""
        branch = ""
        
        k18 = fields.get(18)
        if k18 and isinstance(k18, bytes):
            project = k18.decode('utf-8', errors='ignore').strip()
            
        k1 = fields.get(1)
        if k1 and isinstance(k1, bytes):
            nested1 = parse_proto(k1)
            proj_bytes = nested1.get(1)
            if proj_bytes and isinstance(proj_bytes, bytes):
                proj_str = proj_bytes.decode('utf-8', errors='ignore').strip()
                if proj_str.startswith("file:///"):
                    proj_str = proj_str[8:]
                proj_str = urllib.parse.unquote(proj_str)
                project = proj_str.replace('\\', '/')
            
            branch_bytes = nested1.get(4)
            if branch_bytes and isinstance(branch_bytes, bytes):
                branch = branch_bytes.decode('utf-8', errors='ignore').strip()
                
        return project, branch
    except Exception:
        return "", ""


def extract_user_text(step_payload):
    if not step_payload:
        return ""
    try:
        payload_fields = parse_proto(step_payload)
        k19 = payload_fields.get(19)
        if not k19 or not isinstance(k19, bytes):
            return ""
        nested19 = parse_proto(k19)
        text_bytes = nested19.get(2)
        if not text_bytes or not isinstance(text_bytes, bytes):
            return ""
        return text_bytes.decode('utf-8', errors='ignore').strip()
    except Exception:
        return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path.home() / ".gemini" / "antigravity" / "conversations"), 
                    help="Wurzel der Gemini-Conversations-Logs (SQLite-Datenbankordner)")
    ap.add_argument("--since", default="", help="ISO-Datum YYYY-MM-DD (optional)")
    ap.add_argument("--out", default="./STUDIE")
    a = ap.parse_args()
    
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    
    files = sorted(Path(a.root).glob("*.db"))
    recs, total, rh, withdata = [], 0, 0, 0
    
    for path in files:
        session_rows = []
        try:
            conn = sqlite3.connect(path)
            project, branch = extract_project_branch(conn)
            
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='steps'")
            if not cursor.fetchone():
                conn.close()
                continue
                
            cursor.execute('SELECT idx, metadata, step_payload FROM steps WHERE step_type = 14 ORDER BY idx')
            for idx, md, sp in cursor.fetchall():
                ts = extract_timestamp(md)
                if not ts:
                    continue
                if a.since and ts[:10] < a.since:
                    continue
                raw_text = extract_user_text(sp)
                if not raw_text:
                    continue
                session_rows.append({
                    "ts": ts,
                    "project": project,
                    "branch": branch,
                    "session": path.stem,
                    "raw": raw_text
                })
            conn.close()
        except Exception:
            continue
            
        if not session_rows:
            continue
            
        withdata += 1
        session_rows.sort(key=lambda r: r["ts"])
        n = len(session_rows)
        for i, r in enumerate(session_rows):
            total += 1
            is_cmd, cname, norm = parse_command(r["raw"])
            text, c = redact(norm if is_cmd else r["raw"])
            rh += c
            w = text.split()
            fl = ""
            if i + 1 < n:
                _, _, fn = parse_command(session_rows[i+1]["raw"])
                fl, _ = redact(fn)
                
            recs.append({
                "id": "",
                "ts": r["ts"],
                "source": "gemini",
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
                "outcome_signal": outcome(fl.lower())
            })
            
    recs.sort(key=lambda r: (r["ts"], r["session"]))
    for i, r in enumerate(recs, 1):
        r["id"] = f"H{i:05d}"
        
    out_file = out / "00_corpus.jsonl"
    with open(out_file, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    uniq = len(set(r["text"] for r in recs))
    dec = sum(1 for r in recs if r["decision_score"] >= 1 and r["ptype"] != "ack")
    print(f"Sessions: {len(files)} ({withdata} mit Daten) | Human-Prompts: {total} | eindeutig: {uniq} | Entscheidungs-Kandidaten: {dec} | Redaction: {rh}")
    print(f"-> {out_file}")


if __name__ == "__main__":
    main()
