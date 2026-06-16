#!/usr/bin/env python3
"""
build-your-users-mind · PROMPT-LOG-Builder
===========================================
Baut aus 00_corpus.jsonl eine lesbare PROMPT-LOG.txt: Kopf + Cut-and-Clue-
Archivierungsregeln + rollendes Fenster der juengsten Entscheidungs-Prompts.
Vollarchiv bleibt 00_corpus.jsonl.

Nutzung:
    PYTHONIOENCODING=utf-8 python build_prompt_log.py [--corpus ./STUDIE/00_corpus.jsonl] [--out ./avatar/PROMPT-LOG.txt] [--window 300]
"""
import json, argparse
from pathlib import Path
from collections import Counter

HEADER = """# PROMPT-LOG — {user}

> **Datenhaltung:** Vollstaendiges Korpus = `STUDIE/00_corpus.jsonl`. Diese .txt ist die
> lesbare Sicht mit rollendem Fenster der juengsten Entscheidungs-Prompts.

## Archivierungsanweisung (Cut-and-Clue)
1. Nur das **rollende Fenster** ({window} juengste Entscheidungs-Prompts) inline halten.
2. Bei > {maxlines} Zeilen: aelteste Inline-Eintraege nach `PROMPT-LOG_archiv_<YYYY-MM-DD>.txt`
   auslagern, im Kopf einen **Clue/Pointer** (Vorlaeufer/Nachfolger) lassen.
3. Das JSONL-Archiv wird NIE gekuerzt — nur die lesbare .txt rolliert.
---
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="./STUDIE/00_corpus.jsonl")
    ap.add_argument("--out", default="./avatar/PROMPT-LOG.txt")
    ap.add_argument("--user", default="USER")
    ap.add_argument("--window", type=int, default=300)
    ap.add_argument("--maxlines", type=int, default=2000)
    a = ap.parse_args()
    recs = [json.loads(l) for l in open(a.corpus, encoding="utf-8") if l.strip()]
    dec = sorted([r for r in recs if r.get("decision_score",0)>=1 and r.get("ptype")!="ack"],
                 key=lambda r: r["ts"], reverse=True)
    win = dec[:a.window]
    by_o = Counter(r["outcome_signal"] for r in recs)
    span = (min(r["ts"][:10] for r in recs), max(r["ts"][:10] for r in recs)) if recs else ("?","?")
    L = [HEADER.format(user=a.user, window=a.window, maxlines=a.maxlines),
         f"## Kurzstatistik\n\n- Zeitraum: {span[0]} – {span[1]}\n",
         f"- Human-Prompts: {len(recs)} | Entscheidungs-Kandidaten: {len(dec)}\n",
         f"- Outcome: " + ", ".join(f"{k}={v}" for k,v in by_o.most_common()) + "\n\n",
         f"## Rollendes Fenster — juengste {len(win)} Entscheidungs-Prompts\n\n"]
    for r in win:
        proj = (r.get("project") or "?").replace("\\","/").split("/")[-1]
        L.append(f"### [{r['id']}] {r['ts'][:16]} · {proj} · outcome={r['outcome_signal']} · score={r['decision_score']}\n")
        t = r["text"].strip()
        L.append((t[:600] + " […]" if len(t) > 600 else t) + "\n\n")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("".join(L), encoding="utf-8")
    print(f"-> {a.out} ({len(win)} inline, {len(recs)} im JSONL-Archiv)")

if __name__ == "__main__":
    main()
