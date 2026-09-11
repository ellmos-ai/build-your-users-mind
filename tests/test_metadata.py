"""Tests for repository metadata, schema parity, and discovery consistency."""

import json
from pathlib import Path
import subprocess
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
        self.third_party_licenses = ROOT / "THIRD_PARTY_LICENSES.md"
        self.skill = ROOT / "SKILL.md"
        self.source_adapters = ROOT / "SOURCE-ADAPTERS.md"
        self.taxonomy = ROOT / "TAXONOMY.md"
        self.classification_schema = ROOT / "schemas" / "classification.schema.json"
        self.prediction_schema = ROOT / "schemas" / "decision-prediction-event.schema.json"
        self.secure_avatar_schema = ROOT / "schemas" / "secure-text-avatar-output.schema.json"
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
            self.third_party_licenses,
            self.skill,
            self.source_adapters,
            self.taxonomy,
            self.classification_schema,
            self.prediction_schema,
            self.secure_avatar_schema,
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
        self.assertIn("Last-checked: 2026-09-11", llms_text)

    def test_schema_validity(self):
        with open(self.classification_schema, "r", encoding="utf-8") as f:
            schema = json.load(f)
        self.assertEqual(schema.get("type"), "object")
        self.assertIn("properties", schema)
        self.assertIn("id", schema["properties"])
        self.assertIn("type_code", schema["properties"])
        prediction = json.loads(self.prediction_schema.read_text(encoding="utf-8"))
        secure_avatar = json.loads(self.secure_avatar_schema.read_text(encoding="utf-8"))
        self.assertEqual(prediction["properties"]["schema"]["const"], "byum.decision-prediction.v2")
        self.assertEqual(secure_avatar["properties"]["mode"]["const"], "secure")
        self.assertFalse(secure_avatar["properties"]["execution_authorized"]["const"])

    def test_manifest_boundaries(self):
        manifest = json.loads(self.module_manifest.read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("category"), "memory")
        self.assertEqual(manifest.get("kind"), "workflow")
        self.assertEqual(manifest.get("boundaries", {}).get("network"), "transport-defined")
        self.assertEqual(manifest.get("boundaries", {}).get("data"), "sensitive")

    def test_adapters_and_scripts_exist(self):
        with open(self.module_manifest, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        entrypoints = manifest.get("entrypoints", {})
        for name, rel_path in entrypoints.items():
            full_path = ROOT / rel_path
            self.assertTrue(full_path.is_file(), f"Entrypoint '{name}' -> '{rel_path}' does not exist")

    def test_public_contracts_are_not_gitignored(self):
        if not (ROOT / ".git").exists():
            self.skipTest("Git metadata is unavailable in this source projection")
        for path in (self.prediction_schema, self.secure_avatar_schema):
            result = subprocess.run(
                ["git", "check-ignore", "--quiet", "--", str(path.relative_to(ROOT))],
                cwd=ROOT,
                check=False,
            )
            self.assertEqual(result.returncode, 1, f"Public contract is gitignored: {path.name}")

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
        self.assertIn("## Deutsch", sec_text)
        self.assertIn("security@ellmos.ai", sec_text)
        self.assertIn("support@lukasgeiger.com", sec_text)
        self.assertIn("security@open-bricks.org", sec_text)
        self.assertIn("lukas@open-bricks.org", sec_text)
        self.assertIn("48 hours", sec_text)
        self.assertIn("GitHub Security Advisories", sec_text)
        self.assertIn("100% local-first", sec_text.lower())
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
        self.assertIn("macos-latest", ci_text)
        self.assertIn("cancel-in-progress: true", ci_text)
        for version in ('"3.10"', '"3.11"', '"3.12"', '"3.13"'):
            self.assertIn(version, ci_text)
        self.assertIn("ruff check .", ci_text)

    def test_zero_egress_import_contract(self):
        forbidden = {"urllib.request", "requests", "httpx", "aiohttp", "socket"}
        for path in (ROOT / "scripts").rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if path.name == "secure_text_avatar.py":
                self.assertIn("_loopback_endpoint", text)
                self.assertIn('parsed.hostname not in {"127.0.0.1", "localhost", "::1"}', text)
                self.assertIn('parsed.scheme != "http"', text)
                continue
            for module in forbidden:
                self.assertNotIn(f"import {module}", text, f"Forbidden network import {module} in {path}")
                self.assertNotIn(f"from {module}", text, f"Forbidden network import {module} in {path}")

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

    def test_third_party_licenses_inventory_and_zero_dependencies(self):
        """THIRD_PARTY_LICENSES.md must exist and certify zero runtime dependencies."""
        self.assertTrue(self.third_party_licenses.is_file(), "THIRD_PARTY_LICENSES.md must exist")
        content = self.third_party_licenses.read_text(encoding="utf-8")
        self.assertIn("Zero-Runtime-Dependency Guarantee", content)
        self.assertIn("MIT License", content)
        self.assertIn("Python Software Foundation License", content)
        for tool in ("pytest", "ruff", "setuptools", "build"):
            self.assertIn(tool, content)

        pyproj = self.pyproject.read_text(encoding="utf-8")
        self.assertIn("dependencies = []", pyproj)

    def test_pep639_license_files_metadata(self):
        """pyproject.toml must declare PEP 639 license-files."""
        pyproj = self.pyproject.read_text(encoding="utf-8")
        self.assertIn('license-files = ["LICENSE", "THIRD_PARTY_LICENSES.md"]', pyproj)

    def test_gitignore_secret_and_credential_patterns(self):
        """gitignore must exclude secrets, tokens, private keys, and sync artifacts."""
        gi_file = ROOT / ".gitignore"
        self.assertTrue(gi_file.is_file(), ".gitignore must exist")
        content = gi_file.read_text(encoding="utf-8")
        required_patterns = [
            "*.pem",
            "*.key",
            "*.token",
            "*.secret",
            ".npmrc",
            ".pypirc",
            "credentials.json",
            "secrets.json",
            "id_rsa*",
            "id_ed25519*",
            "*.orig",
            "*.rej",
            "*-WORKSTATION-LG.*",
            "*-ASUS-GEI.*",
        ]
        for pattern in required_patterns:
            self.assertIn(pattern, content, f"Pattern '{pattern}' missing in .gitignore")


if __name__ == "__main__":
    unittest.main()

