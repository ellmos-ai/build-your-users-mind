from __future__ import annotations

import contextlib
import io
import json
import math
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import aggregate_stats  # noqa: E402
import build_prompt_log  # noqa: E402
import chunk_corpus  # noqa: E402
import corpus_extract  # noqa: E402
import merge_corpora  # noqa: E402
import verify_ids  # noqa: E402
from adapters import codex_adapter, gemini_adapter, kimi_adapter  # noqa: E402
from classification_contract import load_classifications  # noqa: E402
from pipeline_common import (  # noqa: E402
    DEFAULT_REDACTIONS,
    atomic_write_jsonl,
    load_redaction_rules,
    normalize_rows,
    outcome,
    prompt_type,
    redact,
    stable_id,
    validate_since,
    validate_timestamp,
)


def record(record_id: str, text: str = "Use PostgreSQL") -> dict[str, object]:
    return {
        "id": record_id,
        "ts": "2026-01-02T03:04:05Z",
        "source": "test",
        "project": "demo",
        "branch": "main",
        "session": "s1",
        "sender": "human",
        "ptype": "frei",
        "command": "",
        "text": text,
        "text_short": text,
        "word_count": len(text.split()),
        "decision_score": 1,
        "followup_short": "",
        "outcome_signal": "none",
    }


def classification(record_id: str, type_code: str = "NS") -> dict[str, object]:
    return {
        "id": record_id,
        "type_code": type_code,
        "topic": "database",
        "is_decision": True,
        "decision_kind": "rule",
        "formulation_pattern": "use ...",
        "method_triggered": "--",
        "is_turning_point": False,
    }


def varint(value: int) -> bytes:
    output = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        output.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(output)


def field_varint(tag: int, value: int) -> bytes:
    return varint(tag << 3) + varint(value)


def field_bytes(tag: int, value: bytes) -> bytes:
    return varint((tag << 3) | 2) + varint(len(value)) + value


class CommonTests(unittest.TestCase):
    def test_modern_api_keys_are_redacted(self) -> None:
        for secret in ("sk-proj-" + "A" * 32, "sk-ant-" + "B" * 32):
            cleaned, count = redact(secret)
            self.assertEqual(cleaned, "[REDACTED_APIKEY]")
            self.assertEqual(count, 1)

    def test_common_credentials_are_redacted(self) -> None:
        samples = (
            (
                "postgresql://alice:correct-horse-battery-staple@db.example/app",
                "correct-horse-battery-staple",
            ),
            (
                "AWS_SECRET_ACCESS_KEY='AbCdEfGhIjKlMnOpQrStUvWxYz0123456789ABCD'",
                "AbCdEfGhIjKlMnOpQrStUvWxYz0123456789ABCD",
            ),
            (("pass" + 'word="correct horse battery staple"'), "correct horse battery staple"),
            ("AIza" + "A" * 35, "AIza" + "A" * 35),
        )
        for value, secret in samples:
            with self.subTest(value=value):
                cleaned, count = redact(value)
                self.assertNotIn(secret, cleaned)
                self.assertGreaterEqual(count, 1)

    def test_metadata_fields_are_redacted(self) -> None:
        google_key = "AIza" + "B" * 35
        rows = [
            {
                "ts": "2026-01-01T00:00:00Z",
                "session": "opaque-session-id",
                "project": "postgresql://alice:database-password@db.example/app",
                "branch": f"release/{google_key}",
                "raw": '<command-name>/deploy ' + "pass" + 'word="correct horse battery staple"</command-name>',
            }
        ]
        records, count = normalize_rows(rows, "test")
        serialized = json.dumps(records[0])
        for secret in ("database-password", google_key, "correct horse battery staple"):
            self.assertNotIn(secret, serialized)
        self.assertGreaterEqual(count, 4)

    def test_custom_sensitive_rule(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "rules.json"
            path.write_text('[{"pattern":"PATIENT-[0-9]+","replacement":"[PRIVATE]"}]', encoding="utf-8")
            rules = load_redaction_rules(str(path))
            self.assertEqual(redact("PATIENT-123", rules)[0], "[PRIVATE]")

    def test_short_rule_is_not_ack(self) -> None:
        rows = [
            {
                "ts": "2026-01-01T00:00:00Z",
                "session": "s",
                "project": "p",
                "branch": "",
                "raw": "Never use Docker",
            }
        ]
        records, _ = normalize_rows(rows, "test")
        self.assertEqual(records[0]["ptype"], "frei")
        self.assertGreaterEqual(records[0]["decision_score"], 1)
        self.assertEqual(prompt_type("okay"), "ack")

    def test_decision_lexicon_uses_token_boundaries(self) -> None:
        rows = [
            {
                "ts": "2026-01-01T00:00:00Z",
                "session": "s",
                "project": "p",
                "branch": "",
                "raw": "The house is blue because daylight is strong",
            }
        ]
        records, _ = normalize_rows(rows, "test")
        self.assertEqual(records[0]["decision_score"], 0)

    def test_outcome_is_conservative(self) -> None:
        self.assertEqual(outcome("please deploy the build"), "none")
        self.assertEqual(outcome("try again"), "reissue")
        self.assertEqual(outcome("stop deployment"), "none")

    def test_stable_id_does_not_depend_on_sort_order(self) -> None:
        expected = stable_id("codex", "session", "2026-01-02T00:00:00Z", "Rule A")
        rows = [
            {"ts": "2025-01-01T00:00:00Z", "session": "old", "project": "", "branch": "", "raw": "older"},
            {"ts": "2026-01-02T00:00:00Z", "session": "session", "project": "", "branch": "", "raw": "Rule A"},
        ]
        records, _ = normalize_rows(rows, "codex")
        self.assertIn(expected, {item["id"] for item in records})

    def test_validate_since_is_exact(self) -> None:
        self.assertEqual(validate_since("2026-01-02"), "2026-01-02")
        with self.assertRaises(ValueError):
            validate_since("2026-1-2")

    def test_timestamp_requires_real_iso_datetime_and_timezone(self) -> None:
        self.assertEqual(
            validate_timestamp("2026-01-02T03:04:05Z"), "2026-01-02T03:04:05Z"
        )
        for invalid in ("not-a-date", "2026-02-30T00:00:00Z", "2026-01-02T03:04:05"):
            with self.assertRaises(ValueError):
                validate_timestamp(invalid)


class AdapterTests(unittest.TestCase):
    def test_codex_filters_internal_records_and_tracks_turn_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "rollout-fixture.jsonl"
            entries = [
                {"timestamp": "2026-01-01T00:00:00Z", "type": "session_meta", "payload": {"cwd": "old"}},
                {"timestamp": "2026-01-01T00:00:01Z", "type": "response_item", "payload": {"role": "user", "content": [{"type": "input_text", "text": "<codex_internal_context>hidden</codex_internal_context>"}]}},
                {"timestamp": "2026-01-01T00:00:02Z", "type": "turn_context", "payload": {"cwd": "new", "git_branch": "main"}},
                {"timestamp": "2026-01-01T00:00:02Z", "type": "response_item", "payload": {"role": "user", "content": [{"type": "input_text", "text": "# AGENTS.md instructions for C:\\Workspace\\demo\n<INSTRUCTIONS>hidden</INSTRUCTIONS>"}]}},
                {"timestamp": "2026-01-01T00:00:03Z", "type": "response_item", "payload": {"role": "user", "content": [{"type": "input_text", "text": "Never use Docker"}]}},
                {"timestamp": "2026-01-01T00:00:04Z", "type": "response_item", "payload": {"role": "user", "content": {"type": "input_text", "text": "schema drift"}}},
                [],
            ]
            path.write_text("".join(json.dumps(item) + "\n" for item in entries), encoding="utf-8")
            rows, _, with_data, errors = codex_adapter.build_records([path], "", DEFAULT_REDACTIONS)
            self.assertEqual((len(rows), with_data, errors), (1, 1, 2))
            self.assertEqual(rows[0]["project"], "new")
            self.assertEqual(rows[0]["branch"], "main")

    def test_claude_missing_timestamp_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "session.jsonl"
            path.write_text(json.dumps({"type": "user", "message": {"role": "user", "content": "hello"}}), encoding="utf-8")
            rows, _, _, errors = corpus_extract.build_records([path], "2099-01-01", "claude", DEFAULT_REDACTIONS)
            self.assertEqual(rows, [])
            self.assertEqual(errors, 1)

    def test_claude_schema_drift_is_counted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "session.jsonl"
            entries = [
                {"type": "user", "timestamp": "2026-01-01T00:00:00Z", "message": {"role": "user", "content": "valid"}},
                {"type": "user", "timestamp": "2026-01-01T00:00:01Z", "message": {"role": "user", "content": {"text": "drift"}}},
                [],
            ]
            path.write_text("".join(json.dumps(item) + "\n" for item in entries), encoding="utf-8")
            rows, _, _, errors = corpus_extract.build_records([path], "", "claude", DEFAULT_REDACTIONS)
            self.assertEqual((len(rows), errors), (1, 2))

    def test_claude_invalid_timestamp_is_counted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "session.jsonl"
            path.write_text(json.dumps({"type": "user", "timestamp": "not-a-date", "message": {"role": "user", "content": "valid"}}), encoding="utf-8")
            rows, _, _, errors = corpus_extract.build_records([path], "2099-01-01", "claude", DEFAULT_REDACTIONS)
            self.assertEqual((rows, errors), ([], 1))

    def test_kimi_timestamp_rejects_bool_nan_and_nonpositive(self) -> None:
        self.assertEqual(kimi_adapter.ms_to_iso(True), "")
        self.assertEqual(kimi_adapter.ms_to_iso(math.nan), "")
        self.assertEqual(kimi_adapter.ms_to_iso(0), "")

    def test_kimi_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            root = home / "sessions"
            wire = root / "s1" / "agents" / "main" / "wire.jsonl"
            wire.parent.mkdir(parents=True)
            wire.write_text(
                json.dumps({"type": "turn.prompt", "origin": {"kind": "user"}, "input": "Use PostgreSQL", "time": 1_700_000_000_000})
                + "\n"
                + json.dumps({"type": "turn.steer", "origin": {"kind": "user"}, "input": "Actually, use SQLite", "time": 1_700_000_000_500})
                + "\n"
                + json.dumps({"type": "turn.prompt", "origin": {"kind": "user"}, "input": {"text": "drift"}, "time": 1_700_000_001_000})
                + "\n"
                + json.dumps([])
                + "\n",
                encoding="utf-8",
            )
            rows, _, _, errors = kimi_adapter.build_records([wire], root, "", DEFAULT_REDACTIONS)
            self.assertEqual((len(rows), errors), (2, 2))
            self.assertEqual([row["text"] for row in rows], ["Use PostgreSQL", "Actually, use SQLite"])

    def test_kimi_malformed_session_index_is_counted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            root = home / "sessions"
            wire = root / "s1" / "agents" / "main" / "wire.jsonl"
            wire.parent.mkdir(parents=True)
            wire.write_text(
                json.dumps(
                    {
                        "type": "turn.prompt",
                        "origin": {"kind": "user"},
                        "input": "Use PostgreSQL",
                        "time": 1_700_000_000_000,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (home / "session_index.jsonl").write_text("{broken}\n", encoding="utf-8")
            rows, _, _, errors = kimi_adapter.build_records(
                [wire], root, "", DEFAULT_REDACTIONS
            )
            self.assertEqual((len(rows), errors), (1, 1))

    def test_gemini_parser_rejects_truncation(self) -> None:
        with self.assertRaises(ValueError):
            gemini_adapter.parse_varint(b"\x80", 0)
        with self.assertRaises(ValueError):
            gemini_adapter.parse_proto(b"\x0a\x05A")

    def test_gemini_missing_timestamp_seconds_is_rejected(self) -> None:
        # Metadata field 1 contains an empty protobuf timestamp.  Treating the
        # absent seconds field as zero would silently invent 1970-01-01.
        self.assertEqual(gemini_adapter.extract_timestamp(field_bytes(1, b"")), "")

    def test_gemini_read_only_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "fixture.db"
            connection = sqlite3.connect(path)
            connection.execute("CREATE TABLE steps (idx INTEGER, step_type INTEGER, metadata BLOB, step_payload BLOB)")
            metadata = field_bytes(1, field_varint(1, 1_700_000_000))
            payload = field_bytes(19, field_bytes(2, b"Use PostgreSQL"))
            connection.execute("INSERT INTO steps VALUES (1, 14, ?, ?)", (metadata, payload))
            connection.execute("INSERT INTO steps VALUES (2, 14, ?, ?)", (metadata, b""))
            corrupt_metadata = field_bytes(1, field_varint(1, 2**63 - 1))
            connection.execute(
                "INSERT INTO steps VALUES (3, 14, ?, ?)", (corrupt_metadata, payload)
            )
            connection.commit()
            connection.close()
            rows, _, _, errors = gemini_adapter.build_records([path], "", DEFAULT_REDACTIONS)
            self.assertEqual((len(rows), errors), (1, 2))
            read_only = gemini_adapter.open_read_only(path)
            with self.assertRaises(sqlite3.OperationalError):
                read_only.execute("CREATE TABLE forbidden (id INTEGER)")
            read_only.close()

    def test_gemini_missing_steps_table_keeps_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "conversations"
            root.mkdir()
            good = root / "good.db"
            connection = sqlite3.connect(good)
            connection.execute(
                "CREATE TABLE steps (idx INTEGER, step_type INTEGER, metadata BLOB, step_payload BLOB)"
            )
            metadata = field_bytes(1, field_varint(1, 1_700_000_000))
            payload = field_bytes(19, field_bytes(2, b"Use PostgreSQL"))
            connection.execute("INSERT INTO steps VALUES (1, 14, ?, ?)", (metadata, payload))
            connection.commit()
            connection.close()
            sqlite3.connect(root / "missing-steps.db").close()

            output = Path(temp) / "out"
            output.mkdir()
            target = output / "00_corpus.jsonl"
            target.write_text("sentinel", encoding="utf-8")
            with self.assertRaises(SystemExit):
                gemini_adapter.main(["--root", str(root), "--out", str(output)])
            self.assertEqual(target.read_text(encoding="utf-8"), "sentinel")

    def test_gemini_preserves_unix_file_uri_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "metadata.db"
            connection = sqlite3.connect(path)
            connection.execute("CREATE TABLE trajectory_metadata_blob (id TEXT, data BLOB)")
            nested = field_bytes(1, b"file:///home/alice/project")
            connection.execute("INSERT INTO trajectory_metadata_blob VALUES ('main', ?)", (field_bytes(1, nested),))
            connection.commit()
            project, _ = gemini_adapter.extract_project_branch(connection)
            connection.close()
            self.assertEqual(project, "/home/alice/project")


class PipelineTests(unittest.TestCase):
    def test_empty_extractor_keeps_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "logs"
            root.mkdir()
            output = Path(temp) / "out"
            output.mkdir()
            target = output / "00_corpus.jsonl"
            target.write_text("sentinel", encoding="utf-8")
            with self.assertRaises(SystemExit):
                corpus_extract.main(["--root", str(root), "--out", str(output)])
            self.assertEqual(target.read_text(encoding="utf-8"), "sentinel")

    def test_malformed_extractor_input_keeps_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "logs"
            root.mkdir()
            (root / "broken.jsonl").write_text("{not json}\n", encoding="utf-8")
            output = Path(temp) / "out"
            output.mkdir()
            target = output / "00_corpus.jsonl"
            target.write_text("sentinel", encoding="utf-8")
            with self.assertRaises(SystemExit):
                corpus_extract.main(["--root", str(root), "--out", str(output)])
            self.assertEqual(target.read_text(encoding="utf-8"), "sentinel")

    def test_partial_extractor_input_requires_explicit_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "logs"
            root.mkdir()
            valid = {
                "type": "user",
                "timestamp": "2026-01-01T00:00:00Z",
                "message": {"role": "user", "content": "Use PostgreSQL"},
            }
            (root / "mixed.jsonl").write_text(
                "{not json}\n" + json.dumps(valid) + "\n", encoding="utf-8"
            )
            output = Path(temp) / "out"
            output.mkdir()
            target = output / "00_corpus.jsonl"
            target.write_text("sentinel", encoding="utf-8")
            with self.assertRaises(SystemExit):
                corpus_extract.main(["--root", str(root), "--out", str(output)])
            self.assertEqual(target.read_text(encoding="utf-8"), "sentinel")
            self.assertEqual(
                corpus_extract.main(
                    ["--root", str(root), "--out", str(output), "--allow-partial"]
                ),
                0,
            )
            self.assertEqual(len(target.read_text(encoding="utf-8").splitlines()), 1)

    def test_merge_corpora_deduplicates_identical_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            first, second = Path(temp) / "a.jsonl", Path(temp) / "b.jsonl"
            atomic_write_jsonl(first, [record("H_a")])
            atomic_write_jsonl(second, [record("H_a"), record("H_b", "Never delete files")])
            merged = merge_corpora.merge([first, second])
            self.assertEqual([item["id"] for item in merged], ["H_a", "H_b"])

    def test_merge_corpora_rejects_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            first, second = Path(temp) / "a.jsonl", Path(temp) / "b.jsonl"
            atomic_write_jsonl(first, [record("H_a")])
            atomic_write_jsonl(second, [record("H_a", "different")])
            with self.assertRaises(ValueError):
                merge_corpora.merge([first, second])

    def test_empty_merge_keeps_existing_output_without_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            empty = base / "empty.jsonl"
            output = base / "00_corpus.jsonl"
            empty.write_text("", encoding="utf-8")
            output.write_text("sentinel", encoding="utf-8")
            with self.assertRaises(SystemExit):
                merge_corpora.main([str(empty), "--out", str(output)])
            self.assertEqual(output.read_text(encoding="utf-8"), "sentinel")
            self.assertEqual(
                merge_corpora.main(
                    [str(empty), "--out", str(output), "--allow-empty"]
                ),
                0,
            )
            self.assertEqual(output.read_text(encoding="utf-8"), "")

    def test_chunker_cleans_stale_files_and_sanitizes_domain(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            corpus = base / "corpus.jsonl"
            chunks = base / "chunks"
            domains = base / "domains.json"
            atomic_write_jsonl(corpus, [record("H_a")])
            domains.write_text('{"../escape":["demo"]}', encoding="utf-8")
            chunks.mkdir()
            (chunks / "cat_stale.jsonl").write_text("stale", encoding="utf-8")
            result = chunk_corpus.main(["--corpus", str(corpus), "--out", str(chunks), "--domains-json", str(domains)])
            self.assertEqual(result, 0)
            self.assertFalse((chunks / "cat_stale.jsonl").exists())
            self.assertEqual(list(base.glob("escape*")), [])
            self.assertEqual(len(list(chunks.glob("chunk_*.jsonl"))), 1)

    def test_chunker_rejects_nonpositive_size(self) -> None:
        with self.assertRaises(SystemExit):
            chunk_corpus.main(["--chunk-size", "0"])

    def test_chunker_rejects_missing_domains_file(self) -> None:
        with self.assertRaises(SystemExit):
            chunk_corpus.main(["--domains-json", "does-not-exist.json"])

    def _classified_fixture(
        self, base: Path, count: int = 2, type_code: str = "NS", chunk_size: int = 1
    ) -> tuple[Path, Path]:
        corpus = base / "corpus.jsonl"
        chunks = base / "chunks"
        rows = [record(f"H_{index}", f"Use option {index}") for index in range(count)]
        atomic_write_jsonl(corpus, rows)
        chunk_corpus.main(
            [
                "--corpus",
                str(corpus),
                "--out",
                str(chunks),
                "--chunk-size",
                str(chunk_size),
            ]
        )
        manifest = json.loads((chunks / "manifest.json").read_text(encoding="utf-8"))
        for item in manifest["chunks"]:
            input_rows = [
                json.loads(line)
                for line in (chunks / item["file"]).read_text(encoding="utf-8").splitlines()
            ]
            atomic_write_jsonl(
                chunks / item["classification_file"],
                [classification(input_row["id"], type_code) for input_row in input_rows],
            )
        return corpus, chunks

    def test_classification_contract_passes_complete_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, chunks = self._classified_fixture(Path(temp))
            rows, errors = load_classifications(chunks, Path(temp) / "corpus.jsonl")
            self.assertEqual((len(rows), errors), (2, []))

    def test_classification_contract_rejects_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, chunks = self._classified_fixture(Path(temp))
            manifest = json.loads((chunks / "manifest.json").read_text(encoding="utf-8"))
            first = json.loads((chunks / manifest["chunks"][0]["classification_file"]).read_text(encoding="utf-8"))
            second_path = chunks / manifest["chunks"][1]["classification_file"]
            atomic_write_jsonl(second_path, [classification(first["id"])])
            _, errors = load_classifications(chunks, Path(temp) / "corpus.jsonl")
            self.assertTrue(any("collision" in error for error in errors))

    def test_classification_contract_rejects_missing_worker_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, chunks = self._classified_fixture(Path(temp))
            next(chunks.glob("cat_*.jsonl")).unlink()
            _, errors = load_classifications(chunks, Path(temp) / "corpus.jsonl")
            self.assertTrue(any("does not exist" in error for error in errors))

    def test_classification_contract_rejects_unmanaged_stale_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            corpus, chunks = self._classified_fixture(Path(temp))
            (chunks / "chunk_9999_stale.jsonl").write_text("{}\n", encoding="utf-8")
            _, errors = load_classifications(chunks, corpus)
            self.assertTrue(any("stale chunk" in error for error in errors))

    def test_classification_contract_rejects_stale_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            corpus, chunks = self._classified_fixture(base, chunk_size=2)
            with corpus.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record("H_new", "New unique prompt")) + "\n")
            _, errors = load_classifications(chunks, corpus)
            self.assertTrue(any("stale" in error for error in errors))

    def test_classification_contract_rejects_truncated_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            corpus, chunks = self._classified_fixture(base, chunk_size=2)
            chunk = next(chunks.glob("chunk_*.jsonl"))
            first_line = chunk.read_text(encoding="utf-8").splitlines()[0]
            chunk.write_text(first_line + "\n", encoding="utf-8")
            manifest = json.loads((chunks / "manifest.json").read_text(encoding="utf-8"))
            classification_path = chunks / manifest["chunks"][0]["classification_file"]
            first_classification = classification_path.read_text(encoding="utf-8").splitlines()[0]
            classification_path.write_text(first_classification + "\n", encoding="utf-8")
            _, errors = load_classifications(chunks, corpus)
            self.assertTrue(any("SHA-256" in error for error in errors))
            self.assertTrue(any("manifest expects" in error for error in errors))
            self.assertTrue(any("representative" in error for error in errors))

    def test_aggregate_reports_zero_denominator_honestly(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            corpus, chunks = self._classified_fixture(base, count=1, type_code="BE")
            output = base / "stats.md"
            self.assertEqual(aggregate_stats.main(["--corpus", str(corpus), "--chunks", str(chunks), "--out", str(output)]), 0)
            self.assertIn("undefined (denominator 0)", output.read_text(encoding="utf-8"))

    def test_verify_ids_is_strict_and_text_is_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            corpus, chunks = self._classified_fixture(Path(temp), count=1)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = verify_ids.main(["H_0", "--corpus", str(corpus), "--chunks", str(chunks)])
            self.assertEqual(result, 0)
            self.assertNotIn("Use option", output.getvalue())
            self.assertEqual(verify_ids.main(["missing", "--corpus", str(corpus), "--chunks", str(chunks)]), 2)

    def test_prompt_log_enforces_line_cap(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            corpus, output = base / "corpus.jsonl", base / "prompt.txt"
            rows = [record(f"H_{index}", "Always use option " + ("word " * 20)) for index in range(20)]
            for index, item in enumerate(rows):
                item["ts"] = f"2026-01-{index + 1:02d}T00:00:00Z"
            atomic_write_jsonl(corpus, rows)
            self.assertEqual(build_prompt_log.main(["--corpus", str(corpus), "--out", str(output), "--maxlines", "30"]), 0)
            self.assertLessEqual(len(output.read_text(encoding="utf-8").splitlines()), 30)

    def test_prompt_log_tiny_line_cap_never_overflows(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            corpus, output = base / "corpus.jsonl", base / "prompt.txt"
            atomic_write_jsonl(corpus, [record("H_1")])
            self.assertEqual(
                build_prompt_log.main(
                    ["--corpus", str(corpus), "--out", str(output), "--maxlines", "15"]
                ),
                0,
            )
            self.assertLessEqual(len(output.read_text(encoding="utf-8").splitlines()), 15)

    def test_classification_contract_handles_unhashable_enum(self) -> None:
        malformed = classification("H_1")
        malformed["type_code"] = []
        from classification_contract import validate_record

        errors = validate_record(malformed, "fixture:1")
        self.assertTrue(any("invalid type_code" in error for error in errors))

    def test_generated_avatar_files_are_recursively_ignored(self) -> None:
        ignored = subprocess.run(
            ["git", "check-ignore", "--no-index", "profiles/alice/WHAT-ALICE-SAID.md"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(ignored.returncode, 0)
        for generated in ("profiles/alice/METHODIK.md", "profiles/alice/START.md"):
            result = subprocess.run(
                ["git", "check-ignore", "--no-index", generated],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0)
        for template_path in (
            "templates/WHAT-USER-SAID.md",
            "templates/METHODIK.md",
            "templates/START.md",
        ):
            template = subprocess.run(
                ["git", "check-ignore", "--no-index", template_path],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(template.returncode, 1)


if __name__ == "__main__":
    unittest.main()
