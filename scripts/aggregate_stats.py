#!/usr/bin/env python3
"""
build-your-users-mind · Stufe-3/4-Aggregation: Statistik aus den Schwarm-Klassifikaten
(cat_*.jsonl) joined mit 00_corpus.jsonl (outcome_signal). Schreibt 04_statistik.md.

Nutzung:
    PYTHONIOENCODING=utf-8 python aggregate_stats.py [--chunks ./STUDIE/_chunks] [--corpus ./STUDIE/00_corpus.jsonl] [--out ./STUDIE/04_statistik.md]
"""
import json, glob, argparse
from pathlib import Path
from collections import Counter, defaultdict

TYPES = {"SP":"Startprompt","NT":"Nachfrage-Thema","NM":"Nachfrage-Methode","NS":"Nachfrage-Steuerung",
         "KO":"Korrektur","BE":"Bestätigung","RA":"Richtungsänderung","MP":"Meta-Prompt"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", default="./STUDIE/_chunks")
    ap.add_argument("--corpus", default="./STUDIE/00_corpus.jsonl")
    ap.add_argument("--out", default="./STUDIE/04_statistik.md")
    a = ap.parse_args()

    corpus = {}
    for l in open(a.corpus, encoding="utf-8"):
        if l.strip():
            r = json.loads(l); corpus[r["id"]] = r
    cats = []
    for fn in glob.glob(a.chunks + "/cat_*.jsonl"):
        dom = Path(fn).stem.split("_")[-1]
        for l in open(fn, encoding="utf-8"):
            l = l.strip()
            if not l: continue
            try: c = json.loads(l); c["_domain"] = dom; cats.append(c)
            except: pass
    if not cats:
        print("Keine cat_*.jsonl gefunden — erst Stufe-2-Klassifikation (Schwarm) laufen lassen."); return

    n = len(cats)
    td = Counter(c.get("type_code","??") for c in cats)
    kind = Counter((c.get("decision_kind") or "none") for c in cats)
    method = Counter((c.get("method_triggered") or "--") for c in cats)
    tp = [c for c in cats if c.get("is_turning_point")]
    dec = [c for c in cats if c.get("is_decision")]
    by_dom = Counter(c["_domain"] for c in cats)
    be, ko = td.get("BE",0), td.get("KO",0)
    bk = round(be/max(ko,1),2)
    pro = td.get("SP",0)+td.get("NM",0)+td.get("RA",0)
    rea = be+ko+td.get("NT",0)
    pr = round(pro/max(rea,1),2)
    o_dom = defaultdict(Counter)
    for c in cats:
        r = corpus.get(c["id"])
        if r: o_dom[c["_domain"]][r.get("outcome_signal","none")] += 1

    L = ["# Statistische Prompt-Aggregation (Stufe 4)\n\n", f"Basis: **{n}** klassifizierte eindeutige Human-Prompts.\n\n",
         "## Prompt-Typ-Verteilung\n\n| Typ | Name | Anzahl | % |\n|---|---|---|---|\n"]
    for code,c in td.most_common():
        L.append(f"| {code} | {TYPES.get(code,code)} | {c} | {round(c/n*100,1)}% |\n")
    L += [f"\n## Mensch-Maschine-Dynamik\n\n- **B:K (Bestätigung:Korrektur):** {bk}:1\n",
          f"- **Proaktiv:Reaktiv:** {pr}:1\n- **Wendepunkte:** {len(tp)} ({round(len(tp)/n*100,1)}%)\n",
          f"- **Entscheidungs-Prompts:** {len(dec)} ({round(len(dec)/n*100,1)}%)\n\n## decision_kind\n\n| Art | Anzahl |\n|---|---|\n"]
    for k,v in kind.most_common(): L.append(f"| {k} | {v} |\n")
    L.append("\n## Methodenauslösung\n\n| Methode | Anzahl |\n|---|---|\n")
    for k,v in method.most_common(12): L.append(f"| {k} | {v} |\n")
    L.append("\n## Je Domäne (outcome praise/correction/reissue/none)\n\n| Domäne | Prompts | Outcome |\n|---|---|---|\n")
    for d,c in by_dom.most_common():
        o = o_dom[d]; L.append(f"| {d} | {c} | {o.get('praise',0)}/{o.get('correction',0)}/{o.get('reissue',0)}/{o.get('none',0)} |\n")
    L.append("\n> **Bias:** Stille Zustimmung wird nicht getippt → Korrekturen überrepräsentiert; B:K unterschätzt die Zufriedenheit. Avatar skemmt 'kritisch'.\n")
    Path(a.out).write_text("".join(L), encoding="utf-8")
    print(f"-> {a.out}  | N={n} B:K={bk} P:R={pr} TP={len(tp)} decisions={len(dec)}")

if __name__ == "__main__":
    main()
