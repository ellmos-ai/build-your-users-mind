#!/usr/bin/env python3
"""One-command offline demo of the build-your-users-mind pipeline.

Runs the whole deterministic pipeline on SYNTHETIC fixtures (invented user
"Sam Rivera") with NO LLM and NO network:

    extract -> merge -> chunk -> classify (answer-key) -> validate -> aggregate

then shows the hard validation gate rejecting a tampered classification (exit 2).

    python examples/synthetic-demo/run_demo.py

Outputs land in `examples/synthetic-demo/_run/` (git-ignored). No real data is
read or written. The pre-filled classifications are fixtures, not an accuracy claim.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SCRIPTS = REPO / "scripts"
WORK = HERE / "_run"
STUDIE = WORK / "STUDIE"
CHUNKS = STUDIE / "_chunks"
CORPUS = STUDIE / "00_corpus.jsonl"

ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def run(script: Path, *args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        env=ENV, cwd=str(REPO), capture_output=True, text=True, encoding="utf-8")
    out = (proc.stdout or "").rstrip()
    if out:
        print(out)
    if proc.returncode != expect:
        print((proc.stderr or "").rstrip())
        raise SystemExit(f"! step {script.name} exited {proc.returncode}, expected {expect}")
    return proc


def step(number: str, title: str) -> None:
    print(f"\n=== {number}  {title} ===")


def main() -> int:
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    print("build-your-users-mind - offline synthetic demo (no LLM, no network)")
    print(f"work dir: {WORK}")

    step("0", "generate synthetic fixtures (fictional user 'Sam Rivera')")
    run(HERE / "generate_fixtures.py", "--out", str(WORK))

    step("1", "extract  - deterministic; human-typed prompts only + secret redaction")
    run(SCRIPTS / "corpus_extract.py", "--root", str(WORK / "logs"),
        "--out", str(STUDIE), "--output-name", "corpus_claude.jsonl", "--source", "claude")

    step("2", "merge    - consolidate source corpora into the canonical corpus")
    run(SCRIPTS / "merge_corpora.py", str(STUDIE / "corpus_claude.jsonl"), "--out", str(CORPUS))

    step("3", "chunk    - dedupe + SHA-256 manifest bound to the corpus")
    run(SCRIPTS / "chunk_corpus.py", "--corpus", str(CORPUS),
        "--out", str(CHUNKS), "--domains-json", str(HERE / "domains.json"))

    step("4", "classify - offline answer-key worker (an LLM swarm on real data)")
    run(HERE / "classify_worker.py", "--chunks", str(CHUNKS),
        "--answer-key", str(WORK / "answer_key.json"))

    step("5", "validate - hard gate: schema, completeness, collisions, SHA-256")
    run(SCRIPTS / "validate_classifications.py", "--chunks", str(CHUNKS), "--corpus", str(CORPUS))

    step("6", "aggregate - Stage-4 statistics")
    run(SCRIPTS / "aggregate_stats.py", "--chunks", str(CHUNKS),
        "--corpus", str(CORPUS), "--out", str(STUDIE / "04_statistik.md"))

    _show_redaction()

    step("7", "tamper test - the gate must REJECT a corrupted classification")
    _tamper_test()

    print("\nOK - full pipeline is green and the tamper case was correctly rejected.")
    print(f"Inspect the run: {STUDIE}  (04_statistik.md, 00_corpus.jsonl, _chunks/manifest.json)")
    return 0


def _show_redaction() -> None:
    print("\n--- redaction proof (the stored corpus line for the planted secret) ---")
    for line in CORPUS.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if "Never commit" in row["text"]:
            print("  " + row["text"])
            break


def _tamper_test() -> None:
    cat = next(sorted(CHUNKS.glob("cat_*.jsonl")).__iter__())
    original = cat.read_text(encoding="utf-8")
    rows = [json.loads(line) for line in original.splitlines() if line.strip()]
    rows[0]["type_code"] = "ZZ"   # invalid enum
    rows = rows[:-1]              # drop a row -> completeness failure
    cat.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    print(f"  tampered {cat.name}: set an invalid type_code and dropped one row")
    run(SCRIPTS / "validate_classifications.py",
        "--chunks", str(CHUNKS), "--corpus", str(CORPUS), expect=2)
    print("  -> validation refused (exit 2), as it should. restoring clean classifications.")
    cat.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
