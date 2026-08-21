"""Tests for repository metadata, schema parity, and discovery consistency."""

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent


class TestMetadataParity(unittest.TestCase):
    def setUp(self):
        self.module_manifest = ROOT / "ellmos-module.v2.json"
        self.pyproject = ROOT / "pyproject.toml"
        self.llms_txt = ROOT / "llms.txt"
        self.readme_en = ROOT / "README.md"
        self.readme_de = ROOT / "README_de.md"
        self.locales_de_readme = ROOT / "locales" / "de" / "README.md"
        self.changelog = ROOT / "CHANGELOG.md"
        self.security = ROOT / "SECURITY.md"
        self.license = ROOT / "LICENSE"
        self.skill = ROOT / "SKILL.md"
        self.source_adapters = ROOT / "SOURCE-ADAPTERS.md"
        self.taxonomy = ROOT / "TAXONOMY.md"
        self.classification_schema = ROOT / "schemas" / "classification.schema.json"
        self.ci_workflow = ROOT / ".github" / "workflows" / "ci.yml"

    def test_required_files_exist(self):
        required = [
            self.module_manifest,
            self.pyproject,
            self.llms_txt,
            self.readme_en,
            self.changelog,
            self.security,
            self.license,
            self.skill,
            self.source_adapters,
            self.taxonomy,
            self.classification_schema,
            self.ci_workflow,
        ]
        for f in required:
            self.assertTrue(f.is_file(), f"Missing required file: {f.name}")

    def test_manifest_version_and_metadata_parity(self):
        with open(self.module_manifest, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        self.assertEqual(manifest.get("schema"), "ellmos.module.v2")
        self.assertEqual(manifest.get("id"), "build-your-users-mind")
        version = manifest.get("version")
        self.assertTrue(version, "Version must be defined in ellmos-module.v2.json")

        pyproject_text = self.pyproject.read_text(encoding="utf-8")
        self.assertIn(f'version = "{version}"', pyproject_text)

        llms_text = self.llms_txt.read_text(encoding="utf-8")
        self.assertIn(f"Version: {version}", llms_text)
        self.assertIn("Last-checked: 2026-08-21", llms_text)

    def test_schema_validity(self):
        with open(self.classification_schema, "r", encoding="utf-8") as f:
            schema = json.load(f)
        self.assertEqual(schema.get("type"), "object")
        self.assertIn("properties", schema)
        self.assertIn("id", schema["properties"])
        self.assertIn("type_code", schema["properties"])

    def test_adapters_and_scripts_exist(self):
        with open(self.module_manifest, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        entrypoints = manifest.get("entrypoints", {})
        for name, rel_path in entrypoints.items():
            full_path = ROOT / rel_path
            self.assertTrue(full_path.is_file(), f"Entrypoint '{name}' -> '{rel_path}' does not exist")

    def test_readme_badges_and_ecosystem_links(self):
        readme_text = self.readme_en.read_text(encoding="utf-8")
        self.assertIn("ellmos-ai", readme_text)
        self.assertIn("open-bricks", readme_text)
        self.assertIn("llms.txt", readme_text)
        self.assertIn("SECURITY.md", readme_text)

        if self.readme_de.is_file():
            de_text = self.readme_de.read_text(encoding="utf-8")
            self.assertIn("ellmos-ai", de_text)
            self.assertIn("open-bricks", de_text)
            self.assertIn("llms.txt", de_text)

    def test_security_policy_bilingual_and_contacts(self):
        sec_text = self.security.read_text(encoding="utf-8")
        self.assertIn("# Security Policy", sec_text)
        self.assertIn("# Sicherheitsrichtlinie (German)", sec_text)
        self.assertIn("security@ellmos.ai", sec_text)
        self.assertIn("support@lukasgeiger.com", sec_text)
        self.assertIn("GitHub Private Vulnerability Reporting", sec_text)
        self.assertIn("100% offline", sec_text.lower())
        self.assertIn("zero-egress", sec_text.lower())

    def test_pyproject_pep621_classifiers_and_urls(self):
        pyproj_text = self.pyproject.read_text(encoding="utf-8")
        self.assertIn("Programming Language :: Python :: 3.13", pyproj_text)
        self.assertIn("Operating System :: OS Independent", pyproj_text)
        self.assertIn("Operating System :: Microsoft :: Windows", pyproj_text)
        self.assertIn("Operating System :: POSIX :: Linux", pyproj_text)
        self.assertIn("Documentation = ", pyproj_text)
        self.assertIn("Changelog = ", pyproj_text)

    def test_ci_workflow_integrity(self):
        ci_text = self.ci_workflow.read_text(encoding="utf-8")
        self.assertIn("actions/checkout@v4", ci_text)
        self.assertIn("actions/setup-python@v5", ci_text)
        self.assertIn("ubuntu-latest", ci_text)
        self.assertIn("windows-latest", ci_text)
        self.assertIn("ruff check .", ci_text)

    def test_sibling_tools_matrix_parity(self):
        readme_en_text = self.readme_en.read_text(encoding="utf-8")
        self.assertIn("coma", readme_en_text)
        self.assertIn("swarm-ai", readme_en_text)
        self.assertIn("memoryhooker", readme_en_text)
        self.assertIn("workflowhooker", readme_en_text)
        self.assertIn("system-explorer", readme_en_text)
        self.assertIn("policy-registry", readme_en_text)
        self.assertIn("sqlite-transit-sync", readme_en_text)
        self.assertIn("ellmos-delegation-authority", readme_en_text)
        self.assertIn("open-bricks", readme_en_text)


if __name__ == "__main__":
    unittest.main()
