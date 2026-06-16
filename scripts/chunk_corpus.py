#!/usr/bin/env python3
"""
build-your-users-mind · Chunker — bereitet das Korpus fuer den Stufe-2-Schwarm vor.
===================================================================================
Liest 00_corpus.jsonl, dedupliziert auf eindeutige Texte, ordnet (optional) Domaenen
zu und schreibt N-er-Chunks + Manifest. Jeder Chunk = ein Worker-Auftrag, jede
Domaene = ein Lead.

Domaenen sind OPTIONAL und konfigurierbar: --domains-json zeigt auf eine Datei
{"domain-name": ["keyword", ...], ...}; ohne sie laeuft alles als Domaene "all"
(reines Groessen-Chunking). So bleibt das Tool nutzer-/projektunabhaengig.

Nutzung:
    PYTHONIOENCODING=utf-8 python chunk_corpus.py [--corpus ./STUDIE/00_corpus.jsonl] [--out ./STUDIE/_chunks] [--chunk-size 85] [--domains-json domains.json]
"""
import json, argparse
from pathlib import Path
from collections import defaultdict

def classify(project, rules):
    p = (project or "").lower()
    for dom, kws in rules.items():
        if any(kw.lower() in p for kw in kws):
            return dom
    return "all"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="./STUDIE/00_corpus.jsonl")
    ap.add_argument("--out", default="./STUDIE/_chunks")
    ap.add_argument("--chunk-size", type=int, default=85)
    ap.add_argument("--maxchars", type=int, default=700)
    ap.add_argument("--domains-json", default="", help="optional: {domain:[keywords]} fuer Domaenen-Leads")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rules = {}
    if a.domains_json and Path(a.domains_json).exists():
        rules = json.load(open(a.domains_json, encoding="utf-8"))

    recs = [json.loads(l) for l in open(a.corpus, encoding="utf-8") if l.strip()]
    by_text = {}
    for r in recs:
        t = r["text"]
        if t not in by_text:
            r2 = dict(r); r2["dup_count"] = 1; by_text[t] = r2
        else:
            by_text[t]["dup_count"] += 1
    uniques = list(by_text.values())
    for r in uniques:
        r["domain"] = classify(r.get("project",""), rules) if rules else "all"

    by_dom = defaultdict(list)
    for r in uniques:
        by_dom[r["domain"]].append(r)

    manifest = {"domains": {}, "chunks": []}
    cidx = 0
    for dom in sorted(by_dom):
        rows = sorted(by_dom[dom], key=lambda r:(r.get("project",""), r["ts"]))
        manifest["domains"][dom] = len(rows)
        for i in range(0, len(rows), a.chunk_size):
            cidx += 1
            slim = [{
                "id": r["id"], "ts": r["ts"][:10],
                "project_short": (r.get("project") or "?").replace("\\","/").split("/")[-1],
                "ptype": r.get("ptype"), "command": r.get("command"),
                "decision_score": r.get("decision_score"), "outcome_signal": r.get("outcome_signal"),
                "dup_count": r.get("dup_count",1), "text": r["text"][:a.maxchars],
            } for r in rows[i:i+a.chunk_size]]
            fn = out / f"chunk_{cidx:02d}_{dom}.jsonl"
            with open(fn, "w", encoding="utf-8") as f:
                for s in slim: f.write(json.dumps(s, ensure_ascii=False)+"\n")
            manifest["chunks"].append({"chunk": cidx, "domain": dom, "file": fn.name, "n": len(slim)})
    (out/"manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Eindeutig: {len(uniques)} | Domaenen: {dict(manifest['domains'])} | Chunks: {cidx}")
    print(f"-> {out}")

if __name__ == "__main__":
    main()
