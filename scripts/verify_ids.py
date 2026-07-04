#!/usr/bin/env python3
"""
build-your-users-mind - Evidence-ID spot check
================================================
Verifies that the evidence prompt-IDs cited in avatar files (e.g. WHAT-<USER>-SAID.md)
actually exist in the raw corpus, and shows the swarm's classification for each ID
(type_code / decision_kind) side by side with the source text.

Use this BEFORE trusting a "belegt"/"evidenced" claim in a generated avatar file, and
periodically as a quality gate (see TODO.md: "classification spot check / inter-rater
Kappa"). It only checks IDs you pass in -- pick a random or load-bearing sample.

Usage:
    PYTHONIOENCODING=utf-8 python verify_ids.py ID1 ID2 ID3 ...
    PYTHONIOENCODING=utf-8 python verify_ids.py --corpus ./STUDIE/00_corpus.jsonl \\
        --chunks ./STUDIE/_chunks --sample 10

If no IDs are given, draws a random sample (--sample, default 10) from the corpus so you
always have something to eyeball.
"""
import json
import glob
import argparse
import random
from pathlib import Path


def load_corpus(path):
    corpus = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        corpus[rec["id"]] = rec
    return corpus


def load_classifications(chunks_dir):
    cats = {}
    for fn in glob.glob(str(Path(chunks_dir) / "cat_*.jsonl")):
        for line in open(fn, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                c = json.loads(line)
                cid = c.get("id")
                if cid in cats:
                    # duplicate/collided classification across chunks -- flag it
                    c["_collision"] = True
                cats[cid] = c
            except json.JSONDecodeError:
                pass
    return cats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*", help="Prompt IDs to check (default: random sample)")
    ap.add_argument("--corpus", default="./STUDIE/00_corpus.jsonl")
    ap.add_argument("--chunks", default="./STUDIE/_chunks")
    ap.add_argument("--sample", type=int, default=10, help="Random sample size if no IDs given")
    args = ap.parse_args()

    corpus = load_corpus(args.corpus)
    cats = load_classifications(args.chunks)

    ids = args.ids
    if not ids:
        pool = list(corpus.keys())
        ids = random.sample(pool, min(args.sample, len(pool)))

    n_missing, n_collision = 0, 0
    for i in ids:
        rec = corpus.get(i)
        cat = cats.get(i, {})
        print(f"=== {i} ===")
        if not rec:
            print("  !! NOT IN CORPUS (evidence ID does not resolve)")
            n_missing += 1
            continue
        if cat.get("_collision"):
            n_collision += 1
        proj = (rec.get("project") or "?").replace("\\", "/").split("/")[-1]
        print(
            f"  project={proj} score={rec.get('decision_score')} "
            f"outcome={rec.get('outcome_signal')} type={cat.get('type_code', '?')} "
            f"kind={cat.get('decision_kind', '?')}"
            + ("  [COLLISION: classified in >1 chunk]" if cat.get("_collision") else "")
        )
        print("  TEXT: " + " ".join(rec["text"][:260].split()))

    print(f"\n-> checked {len(ids)} IDs: {n_missing} missing, {n_collision} chunk-collisions.")
    if n_missing or n_collision:
        print("   Missing IDs or collisions undermine 'evidenced' claims -- see TAXONOMY.md bias notes.")


if __name__ == "__main__":
    main()
