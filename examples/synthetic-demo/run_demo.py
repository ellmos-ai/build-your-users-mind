#!/usr/bin/env python3
"""One-command offline demo of the deterministic build and feedback pipeline.

Runs the whole deterministic pipeline on SYNTHETIC fixtures (invented user
"Sam Rivera") with NO LLM and NO network:

    extract -> merge -> chunk -> classify (answer-key) -> validate -> aggregate
    -> score a pre-authored synthetic prediction/feedback loop

then shows the hard validation gate rejecting a tampered classification (exit 2).

    python examples/synthetic-demo/run_demo.py

Outputs land in `examples/synthetic-demo/_run/` (git-ignored). No real data is
read or written. The pre-filled classifications are fixtures, not an accuracy claim.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SCRIPTS = REPO / "scripts"

ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def _rmtree_robust(path: Path, attempts: int = 3, delay: float = 0.5) -> bool:
    """Best-effort recursive delete; survives read-only files and transient
    Windows/cloud-sync (OneDrive) locks. Returns True when the tree is gone."""

    def _on_rm_error(func: object, p: str, exc_info: object) -> None:
        try:
            os.chmod(p, stat.S_IWRITE)
            os.unlink(p) if os.path.isfile(p) else os.rmdir(p)
        except OSError:
            pass  # judged by the final exists() check, not by single ops

    for attempt in range(attempts):
        if not path.exists():
            return True
        try:
            shutil.rmtree(path, onerror=_on_rm_error)
        except OSError:
            pass
        if not path.exists():
            return True
        if attempt < attempts - 1:
            time.sleep(delay)
    return not path.exists()


def prepare_work_dir(base: Path, max_fallbacks: int = 9) -> Path:
    """Return a fresh, empty work dir. If `base` cannot be cleared (e.g. a
    cloud-sync lock holds a handle), fall back to `<base>-2`, `<base>-3`, ...
    instead of crashing — the demo must never fail on cleanup."""
    for n in range(max_fallbacks + 1):
        candidate = base if n == 0 else base.with_name(f"{base.name}-{n + 1}")
        if _rmtree_robust(candidate):
            candidate.mkdir(parents=True)
            if n:
                print(
                    f"note: {base.name}/ is locked (cloud sync?) - "
                    f"using {candidate.name}/ for this run"
                )
            return candidate
    raise SystemExit(f"! could not prepare a work directory next to {base}")


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
    # The scorer intentionally prints confidence emoji. Child processes already
    # receive PYTHONIOENCODING via ENV; configure this parent as well so the
    # one-command demo works in Windows shells whose legacy default is cp1252.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
    work = prepare_work_dir(HERE / "_run")
    studie = work / "STUDIE"
    avatar = work / "avatar"
    chunks = studie / "_chunks"
    corpus = studie / "00_corpus.jsonl"
    print("build-your-users-mind - offline synthetic demo (no LLM, no network)")
    print(f"work dir: {work}")

    step("0", "generate synthetic fixtures (fictional user 'Sam Rivera')")
    run(HERE / "generate_fixtures.py", "--out", str(work))

    step("1", "extract  - deterministic; human-typed prompts only + secret redaction")
    run(SCRIPTS / "corpus_extract.py", "--root", str(work / "logs"),
        "--out", str(studie), "--output-name", "corpus_claude.jsonl", "--source", "claude")

    step("2", "merge    - consolidate source corpora into the canonical corpus")
    run(SCRIPTS / "merge_corpora.py", str(studie / "corpus_claude.jsonl"), "--out", str(corpus))

    step("3", "chunk    - dedupe + SHA-256 manifest bound to the corpus")
    run(SCRIPTS / "chunk_corpus.py", "--corpus", str(corpus),
        "--out", str(chunks), "--domains-json", str(HERE / "domains.json"))

    step("4", "classify - offline answer-key worker (an LLM swarm on real data)")
    run(HERE / "classify_worker.py", "--chunks", str(chunks),
        "--answer-key", str(work / "answer_key.json"))

    step("5", "validate - hard gate: schema, completeness, collisions, SHA-256")
    run(SCRIPTS / "validate_classifications.py", "--chunks", str(chunks), "--corpus", str(corpus))

    step("6", "aggregate - Stage-4 statistics")
    run(SCRIPTS / "aggregate_stats.py", "--chunks", str(chunks),
        "--corpus", str(corpus), "--out", str(studie / "04_statistik.md"))

    _show_redaction(corpus)

    step("7", "feedback loop - score synthetic predictions against synthetic feedback")
    run(
        SCRIPTS / "score_predictions.py",
        "--actions",
        str(avatar / "MY-ACTIONS.txt"),
        "--feedback",
        str(avatar / "WHAT-SAM-SAID-ABOUT-DEMO.md"),
    )

    step("8", "tamper test - the gate must REJECT a corrupted classification")
    _tamper_test(chunks, corpus)

    print("\nOK - deterministic build, feedback scoring, and tamper rejection are green.")
    print(f"Inspect the run: {studie}  (04_statistik.md, 00_corpus.jsonl, _chunks/manifest.json)")
    print(f"Inspect the synthetic feedback loop: {avatar}")
    return 0


def _show_redaction(corpus: Path) -> None:
    print("\n--- redaction proof (the stored corpus line for the planted secret) ---")
    for line in corpus.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if "Never commit" in row["text"]:
            print("  " + row["text"])
            break


def _tamper_test(chunks: Path, corpus: Path) -> None:
    cat = next(sorted(chunks.glob("cat_*.jsonl")).__iter__())
    original = cat.read_text(encoding="utf-8")
    rows = [json.loads(line) for line in original.splitlines() if line.strip()]
    rows[0]["type_code"] = "ZZ"   # invalid enum
    rows = rows[:-1]              # drop a row -> completeness failure
    cat.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    print(f"  tampered {cat.name}: set an invalid type_code and dropped one row")
    run(SCRIPTS / "validate_classifications.py",
        "--chunks", str(chunks), "--corpus", str(corpus), expect=2)
    print("  -> validation refused (exit 2), as it should. restoring clean classifications.")
    cat.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
