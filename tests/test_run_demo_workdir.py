"""Regression tests for the synthetic demo's work-dir preparation.

The demo must never crash on cleanup: read-only leftovers and transient
Windows/cloud-sync (OneDrive) locks on `_run/` caused a PermissionError
traceback on every re-run. `prepare_work_dir` now retries and, if the base
dir stays locked, falls back to `_run-2/`, `_run-3/`, ...
"""
from __future__ import annotations

import importlib.util
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "run_demo", ROOT / "examples" / "synthetic-demo" / "run_demo.py")
run_demo = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(run_demo)


class RmtreeRobustTests(unittest.TestCase):
    def test_removes_tree_with_readonly_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "work"
            (tree / "sub").mkdir(parents=True)
            victim = tree / "sub" / "readonly.txt"
            victim.write_text("locked", encoding="utf-8")
            os.chmod(victim, stat.S_IREAD)
            try:
                self.assertTrue(run_demo._rmtree_robust(tree, attempts=2, delay=0))
                self.assertFalse(tree.exists())
            finally:
                if victim.exists():  # restore writability so tempdir cleanup works
                    os.chmod(victim, stat.S_IWRITE)

    def test_reports_failure_instead_of_raising(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "work"
            tree.mkdir()
            with mock.patch.object(
                    run_demo.shutil, "rmtree", side_effect=PermissionError):
                self.assertFalse(run_demo._rmtree_robust(tree, attempts=2, delay=0))
            self.assertTrue(tree.exists())


class PrepareWorkDirTests(unittest.TestCase):
    def test_reuses_base_when_removable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "_run"
            (base / "old").mkdir(parents=True)
            chosen = run_demo.prepare_work_dir(base)
            self.assertEqual(chosen, base)
            self.assertTrue(base.is_dir())
            self.assertEqual(list(base.iterdir()), [])

    def test_falls_back_when_base_is_locked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "_run"
            base.mkdir()
            (base / "held.txt").write_text("x", encoding="utf-8")
            with mock.patch.object(
                    run_demo.shutil, "rmtree", side_effect=PermissionError):
                chosen = run_demo.prepare_work_dir(base)
            self.assertEqual(chosen.name, "_run-2")
            self.assertTrue(chosen.is_dir())
            self.assertTrue(base.exists())  # locked base is left alone

    def test_gives_up_after_max_fallbacks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "_run"
            for name in ("_run", "_run-2", "_run-3"):
                d = Path(tmp) / name
                d.mkdir()
                (d / "held.txt").write_text("x", encoding="utf-8")
            with mock.patch.object(
                    run_demo.shutil, "rmtree", side_effect=PermissionError):
                with self.assertRaises(SystemExit):
                    run_demo.prepare_work_dir(base, max_fallbacks=2)


if __name__ == "__main__":
    unittest.main()
