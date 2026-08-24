# -*- coding: utf-8 -*-
"""Repository metadata, CI matrix, documentation, manifest, and safety contract tests for build-your-users-mind."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

try:
    import tomllib
except ModuleNotFoundError:  # Python <3.11 fallback
    import tomli as tomllib  # type: ignore

ROOT = Path(__file__).resolve().parents[1]


class RepositoryMetadataContractTests(unittest.TestCase):
    """Contract tests verifying repository hygiene, PEP 621 compliance, CI matrix, and safety invariant parity."""

    def test_version_and_metadata_consistency(self) -> None:
        """Verify version consistency across pyproject.toml, ellmos-module.v2.json, and llms.txt."""
        pyproject_path = ROOT / "pyproject.toml"
        self.assertTrue(pyproject_path.is_file(), "pyproject.toml must exist")
        with pyproject_path.open("rb") as f:
            pyproject = tomllib.load(f)
        version = pyproject.get("project", {}).get("version")
        self.assertIsNotNone(version)

        manifest_path = ROOT / "ellmos-module.v2.json"
        self.assertTrue(manifest_path.is_file(), "ellmos-module.v2.json must exist")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("version"), version)

        llms_path = ROOT / "llms.txt"
        self.assertTrue(llms_path.is_file(), "llms.txt must exist")
        llms_content = llms_path.read_text(encoding="utf-8")
        self.assertIn(f"Version: {version}", llms_content)

    def test_pyproject_pep621_compliance(self) -> None:
        """Verify PEP 621 project configuration, standard classifiers, keywords, and project URLs."""
        with (ROOT / "pyproject.toml").open("rb") as f:
            data = tomllib.load(f)

        project = data.get("project", {})
        self.assertEqual(project.get("name"), "build-your-users-mind")
        self.assertIn("Local-first", project.get("description", ""))
        self.assertEqual(project.get("requires-python"), ">=3.10")
        self.assertEqual(project.get("license", {}).get("text"), "MIT")

        # Classifiers
        classifiers = set(project.get("classifiers", []))
        expected_classifiers = {
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Intended Audience :: Science/Research",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Operating System :: Microsoft :: Windows",
            "Operating System :: POSIX :: Linux",
            "Operating System :: MacOS",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Programming Language :: Python :: 3.13",
            "Topic :: Scientific/Engineering :: Artificial Intelligence",
            "Topic :: Security",
        }
        for clf in expected_classifiers:
            self.assertIn(clf, classifiers, f"Missing classifier: {clf}")

        # URLs
        urls = project.get("urls", {})
        expected_urls = [
            "Homepage",
            "Documentation",
            "Repository",
            "Bug Tracker",
            "Changelog",
            "Security",
            "Parent Organization",
            "Umbrella Ecosystem",
        ]
        for key in expected_urls:
            self.assertIn(key, urls, f"Missing URL key: {key}")
            self.assertTrue(urls[key].startswith("https://"), f"URL for {key} must start with https://")

    def test_ci_workflow_integrity(self) -> None:
        """Verify GitHub Actions CI workflow for multi-OS, multi-Python matrix, concurrency, and lint/test steps."""
        ci_path = ROOT / ".github" / "workflows" / "ci.yml"
        self.assertTrue(ci_path.is_file(), ".github/workflows/ci.yml must exist")
        content = ci_path.read_text(encoding="utf-8")

        self.assertIn("actions/checkout@v4", content)
        self.assertIn("actions/setup-python@v5", content)
        self.assertIn("cancel-in-progress: true", content)
        self.assertIn("ubuntu-latest", content)
        self.assertIn("windows-latest", content)
        self.assertIn("macos-latest", content)
        self.assertIn('"3.10"', content)
        self.assertIn('"3.11"', content)
        self.assertIn('"3.12"', content)
        self.assertIn('"3.13"', content)
        self.assertIn("ruff check .", content)
        self.assertIn("pytest", content)

    def test_security_policy_contract(self) -> None:
        """Verify SECURITY.md policy: SLA, official contacts, advisories link, and zero-egress invariants."""
        sec_path = ROOT / "SECURITY.md"
        self.assertTrue(sec_path.is_file(), "SECURITY.md must exist")
        content = sec_path.read_text(encoding="utf-8")

        self.assertIn("48 hour", content.lower())
        self.assertIn("security@ellmos.ai", content)
        self.assertIn("security@open-bricks.org", content)
        self.assertIn("support@lukasgeiger.com", content)
        self.assertIn("lukas@open-bricks.org", content)
        self.assertIn("https://github.com/ellmos-ai/build-your-users-mind/security/advisories", content)
        self.assertIn("100% Local-First", content)
        self.assertIn("Zero-Egress", content)
        self.assertIn("Non-Elevation", content)

    def test_manifest_schema_and_boundaries(self) -> None:
        """Verify ellmos-module.v2.json schema validity and offline boundary declarations."""
        manifest_path = ROOT / "ellmos-module.v2.json"
        self.assertTrue(manifest_path.is_file())
        data = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(data.get("schema"), "ellmos.module.v2")
        self.assertEqual(data.get("id"), "build-your-users-mind")
        self.assertEqual(data.get("category"), "memory")
        self.assertEqual(data.get("kind"), "workflow")
        self.assertEqual(data.get("boundaries", {}).get("network"), "none")
        self.assertEqual(data.get("boundaries", {}).get("data"), "sensitive")
        self.assertEqual(data.get("source_of_truth", {}).get("repository"), "https://github.com/ellmos-ai/build-your-users-mind")

    def test_llms_txt_integrity(self) -> None:
        """Verify llms.txt metadata, canonical repository, and Last-checked timestamp."""
        llms_path = ROOT / "llms.txt"
        self.assertTrue(llms_path.is_file())
        content = llms_path.read_text(encoding="utf-8")

        self.assertIn("Last-checked: 2026-08-24", content)
        self.assertIn("https://github.com/ellmos-ai/build-your-users-mind", content)
        self.assertIn("MIT", content)
        self.assertIn("ellmos-ai", content)

    def test_documentation_links_and_no_file_uris(self) -> None:
        """Verify that documentation files exist and do not contain local file:/// URIs."""
        docs = [
            "README.md",
            "SECURITY.md",
            "llms.txt",
            "CHANGELOG.md",
            "SKILL.md",
            "TAXONOMY.md",
            "SOURCE-ADAPTERS.md",
        ]
        for doc in docs:
            doc_path = ROOT / doc
            self.assertTrue(doc_path.is_file(), f"Document {doc} must exist")
            text = doc_path.read_text(encoding="utf-8")
            self.assertNotIn("file:///", text, f"Found local file:/// URI in {doc}")

    def test_readme_badges_and_structure(self) -> None:
        """Verify shields.io badges and language switcher in README.md."""
        readme_path = ROOT / "README.md"
        self.assertTrue(readme_path.is_file())
        content = readme_path.read_text(encoding="utf-8")

        self.assertIn("img.shields.io", content)
        self.assertIn(".github/workflows/ci.yml", content)
        self.assertIn("SECURITY.md", content)
        self.assertIn("llms.txt", content)
        self.assertIn("locales/de/README.md", content)

    def test_zero_egress_and_privacy_invariants(self) -> None:
        """Verify that scripts do not import socket/urllib/requests for outbound networking."""
        scripts_dir = ROOT / "scripts"
        self.assertTrue(scripts_dir.is_dir())
        forbidden_imports = {"urllib.request", "requests", "httpx", "aiohttp", "socket"}

        for py_file in scripts_dir.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            for forbidden in forbidden_imports:
                self.assertNotIn(f"import {forbidden}", text, f"Forbidden network import {forbidden} in {py_file}")
                self.assertNotIn(f"from {forbidden}", text, f"Forbidden network import {forbidden} in {py_file}")


if __name__ == "__main__":
    unittest.main()
