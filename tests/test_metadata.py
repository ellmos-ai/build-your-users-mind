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
        self.skill = ROOT / "SKILL.md"
        self.source_adapters = ROOT / "SOURCE-ADAPTERS.md"
        self.taxonomy = ROOT / "TAXONOMY.md"
        self.classification_schema = ROOT / "schemas" / "classification.schema.json"
        self.prediction_schema = ROOT / "schemas" / "decision-prediction-event.schema.json"
        self.secure_avatar_schema = ROOT / "schemas" / "secure-text-avatar-output.schema.json"

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
            self.prediction_schema,
            self.secure_avatar_schema,
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
        self.assertIn("Last-checked: 2026-08-20", llms_text)

    def test_schema_validity(self):
        with open(self.classification_schema, "r", encoding="utf-8") as f:
            schema = json.load(f)
        self.assertEqual(schema.get("type"), "object")
        self.assertIn("properties", schema)
        self.assertIn("id", schema["properties"])
        self.assertIn("type_code", schema["properties"])
        prediction = json.loads(self.prediction_schema.read_text(encoding="utf-8"))
        secure_avatar = json.loads(self.secure_avatar_schema.read_text(encoding="utf-8"))
        self.assertEqual(prediction["properties"]["schema"]["const"], "byum.decision-prediction.v1")
        self.assertEqual(secure_avatar["properties"]["mode"]["const"], "secure")
        self.assertFalse(secure_avatar["properties"]["execution_authorized"]["const"])

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

        if self.readme_de.is_file():
            de_text = self.readme_de.read_text(encoding="utf-8")
            self.assertIn("ellmos-ai", de_text)
            self.assertIn("open-bricks", de_text)


if __name__ == "__main__":
    unittest.main()
