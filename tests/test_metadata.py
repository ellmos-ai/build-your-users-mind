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
        self.third_party_licenses_txt = ROOT / "THIRD_PARTY_LICENSES.txt"
        self.dependabot_config = ROOT / ".github" / "dependabot.yml"
        self.labels_config = ROOT / ".github" / "labels.yml"
        self.auto_assign_workflow = ROOT / ".github" / "workflows" / "auto-assign.yml"
        self.label_sync_workflow = ROOT / ".github" / "workflows" / "label-sync.yml"
        self.contributing = ROOT / "CONTRIBUTING.md"

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
            self.third_party_licenses_txt,
            self.dependabot_config,
            self.labels_config,
            self.auto_assign_workflow,
            self.label_sync_workflow,
            self.contributing,
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
        self.assertIn("Last-checked: 2026-10-18", llms_text)

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
        self.assertRegex(ci_text, r"actions/checkout@v\d+")
        self.assertRegex(ci_text, r"actions/setup-python@v\d+")
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

    def test_plain_text_sbom_companion(self):
        """THIRD_PARTY_LICENSES.txt must exist as a plain-text Level 1 SBOM companion with all 10 invariants."""
        self.assertTrue(self.third_party_licenses_txt.is_file(), "THIRD_PARTY_LICENSES.txt must exist")
        text = self.third_party_licenses_txt.read_text(encoding="utf-8")
        self.assertIn("Audited: 2026-10-18", text)
        self.assertIn("Zero-Copyleft Guarantee", text)
        self.assertIn("Unprivileged User-Mode Operation (RunAsInvoker)", text)
        self.assertIn("§ 521 BGB Gefälligkeitsrecht", text)
        self.assertIn("security@ellmos.ai", text)
        self.assertIn("security@open-bricks.org", text)
        self.assertIn("support@lukasgeiger.com", text)
        self.assertIn("lukas@open-bricks.org", text)
        self.assertIn("48-hour response", text)
        for i in range(1, 11):
            expected = f"{i:02d}"
            self.assertTrue(
                any("INV-" in line and expected in line for line in text.splitlines()),
                f"Invariant {i} missing in THIRD_PARTY_LICENSES.txt",
            )

    def test_dependabot_lifecycle_hardening(self):
        """dependabot.yml must configure weekly github-actions and pip updates with Berlin timezone."""
        self.assertTrue(self.dependabot_config.is_file(), ".github/dependabot.yml must exist")
        text = self.dependabot_config.read_text(encoding="utf-8")
        self.assertIn('package-ecosystem: "github-actions"', text)
        self.assertIn('package-ecosystem: "pip"', text)
        self.assertIn('interval: "weekly"', text)
        self.assertIn('day: "monday"', text)
        self.assertIn('time: "06:00"', text)
        self.assertIn('timezone: "Europe/Berlin"', text)
        self.assertIn("open-pull-requests-limit: 3", text)

    def test_labels_yml_includes_dependabot_labels(self):
        """labels.yml must define required dependency, python and workflow labels."""
        self.assertTrue(self.labels_config.is_file(), ".github/labels.yml must exist")
        text = self.labels_config.read_text(encoding="utf-8")
        self.assertIn("name: dependencies", text)
        self.assertIn("name: github-actions", text)
        self.assertIn("name: python", text)
        self.assertIn("name: security", text)

    def test_github_workflows_and_labels_hygiene(self):
        """auto-assign.yml and label-sync.yml must exist with valid concurrency groups."""
        self.assertTrue(self.auto_assign_workflow.is_file(), "auto-assign.yml must exist")
        self.assertTrue(self.label_sync_workflow.is_file(), "label-sync.yml must exist")
        aa_text = self.auto_assign_workflow.read_text(encoding="utf-8")
        ls_text = self.label_sync_workflow.read_text(encoding="utf-8")
        self.assertIn("cancel-in-progress: true", aa_text)
        self.assertIn("cancel-in-progress: true", ls_text)
        self.assertIn("EndBug/label-sync@v2", ls_text)

    def test_extended_lock_and_cloud_defense_in_gitignore(self):
        """gitignore must exclude multi-host conflict files, lock files, and temporary pytest dirs."""
        content = (ROOT / ".gitignore").read_text(encoding="utf-8")
        patterns = [
            "*-IDEAPAD.*",
            "*-IDEAPAD-GEI*",
            "*_WORKSTATION*",
            "*_WORKSTATION-LG*",
            "*conflicted copy*",
            "* (Kopie)*",
            ".pytest_temp/",
            ".pytest_tmp*/",
            "TASKPLAN_*.md",
            "LOCK.dev.*",
            "LOCK.antigravity.*",
            "LOCK.bugsearch.*",
            "thumbs.db",
            "Desktop.ini",
            "ehthumbs.db",
            "ehthumbs_vista.db",
        ]
        for p in patterns:
            self.assertIn(p, content, f"Pattern '{p}' missing in .gitignore")

    def test_contributing_guide_bilingual_parity(self):
        """CONTRIBUTING.md must provide bilingual parity (EN/DE) with quick navigation anchors."""
        self.assertTrue(self.contributing.is_file(), "CONTRIBUTING.md must exist")
        text = self.contributing.read_text(encoding="utf-8")
        self.assertIn('<a id="english"></a>', text)
        self.assertIn('<a id="deutsch"></a>', text)
        self.assertIn("RunAsInvoker", text)
        self.assertIn("T-20260920-167562623", text)
        self.assertIn("§ 521 BGB", text)
        self.assertIn("Plan D", text)

    def test_pyproject_contributing_url_and_norecursedirs(self):
        """pyproject.toml must declare Contributing, plain-text license URLs and norecursedirs."""
        pyproj = self.pyproject.read_text(encoding="utf-8")
        self.assertIn("Contributing = ", pyproj)
        self.assertIn('"Plain-Text License" = ', pyproj)
        self.assertIn('"Third-Party Licenses Text" = ', pyproj)
        self.assertIn("norecursedirs = [", pyproj)
        self.assertIn(".hypothesis", pyproj)
        self.assertIn(".turbo", pyproj)

    def test_version_freeze_discipline(self):
        """version must remain frozen at 1.1.0-dev across pyproject.toml, module manifest, and llms.txt."""
        pyproj = self.pyproject.read_text(encoding="utf-8")
        manifest = json.loads(self.module_manifest.read_text(encoding="utf-8"))
        llms = self.llms_txt.read_text(encoding="utf-8")
        self.assertIn('version = "1.1.0-dev"', pyproj)
        self.assertEqual(manifest.get("version"), "1.1.0-dev")
        self.assertIn("Version: 1.1.0-dev", llms)


if __name__ == "__main__":
    unittest.main()

