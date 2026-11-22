from __future__ import annotations

import http.client
import json
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import rating_form as rf  # noqa: E402
import score_predictions as sp  # noqa: E402


def sample_input() -> dict[str, object]:
    return {
        "schema": rf.INPUT_SCHEMA,
        "run_id": "synthetic-rating-run-1",
        "title": "Avatar Decisions Review",
        "description": "Synthetic review items for rating form verification.",
        "entries": [
            {
                "nr": 1,
                "id": "DEC-001",
                "kontext": "An operator requested a dry-run before writing files.",
                "entscheidung": "Run dry-run first and preview the output path.",
                "konfidenz": "🟡",
                "ziel": "ACTIONABLE",
            },
            {
                "nr": 2,
                "id": "DEC-002",
                "kontext": "A new external release target has no prior precedent.",
                "entscheidung": "Escalate to the operator instead of guessing.",
                "konfidenz": "🔴",
                "ziel": "USER",
            },
        ],
    }


def sample_response() -> dict[str, object]:
    return {
        "schema": rf.RESPONSE_SCHEMA,
        "run_id": "synthetic-rating-run-1",
        "saved_at": "2026-11-21T20:00:00Z",
        "ratings": [
            {
                "nr": 1,
                "id": "DEC-001",
                "entscheidung": "Run dry-run first and preview the output path.",
                "score": 9,
                "note": "Matches preference.",
                "note_source": "text",
            },
            {
                "nr": 2,
                "id": "DEC-002",
                "entscheidung": "Escalate to the operator instead of guessing.",
                "score": 4,
                "note": "Should clarify scope first.",
                "note_source": "voice",
            },
        ],
    }


class SchemaValidationTests(unittest.TestCase):
    def test_valid_input_and_response_schemas_pass(self) -> None:
        validated_in = rf.validate_input_payload(sample_input())
        self.assertEqual(len(validated_in["entries"]), 2)
        validated_out = rf.validate_response_payload(sample_response())
        self.assertEqual(validated_out["ratings"][0]["score"], 9)

        input_schema = json.loads((ROOT / "schemas" / "avatar-rating-input.schema.json").read_text(encoding="utf-8"))
        response_schema = json.loads(
            (ROOT / "schemas" / "avatar-rating-response.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(input_schema["properties"]["schema"]["const"], rf.INPUT_SCHEMA)
        self.assertEqual(response_schema["properties"]["schema"]["const"], rf.RESPONSE_SCHEMA)
        self.assertEqual(
            set(input_schema["properties"]["entries"]["items"]["required"]),
            {"id", "kontext", "entscheidung", "konfidenz", "ziel"},
        )

    def test_invalid_input_payloads_fail_closed(self) -> None:
        missing_field = sample_input()
        del missing_field["entries"][0]["ziel"]  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "missing required field 'ziel'"):
            rf.validate_input_payload(missing_field)

        duplicate_ids = sample_input()
        duplicate_ids["entries"][1]["id"] = "DEC-001"  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "duplicate entry id"):
            rf.validate_input_payload(duplicate_ids)

    def test_invalid_response_score_fails_closed(self) -> None:
        out_of_range = sample_response()
        out_of_range["ratings"][0]["score"] = 11  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "0..10"):
            rf.validate_response_payload(out_of_range)

        bool_score = sample_response()
        bool_score["ratings"][0]["score"] = True  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "0..10"):
            rf.validate_response_payload(bool_score)


class VoiceGatingTests(unittest.TestCase):
    def test_voice_disabled_renders_no_microphone_element(self) -> None:
        html_out = rf.render_rating_html(sample_input(), {"voice": {"enabled": False}})
        self.assertNotIn("voice-mic-btn", html_out)
        self.assertNotIn("data-voice-mic", html_out)
        self.assertNotIn("getUserMedia", html_out)
        self.assertNotIn("voice-notice", html_out)

    def test_default_example_config_is_disabled_and_has_no_microphone(self) -> None:
        cfg = json.loads(
            (ROOT / "templates" / "avatar-rating.config.example.json").read_text(encoding="utf-8")
        )
        self.assertFalse(cfg["voice"]["enabled"])
        html_out = rf.render_rating_html(sample_input(), cfg)
        self.assertNotIn("voice-mic-btn", html_out)
        self.assertNotIn("getUserMedia", html_out)

    def test_voice_enabled_without_module_shows_notice_and_no_microphone(self) -> None:
        cfg = {
            "voice": {
                "enabled": True,
                "provider": "ellmos-voice-io",
                "endpoint": "http://127.0.0.1:8765/transcribe",
            }
        }
        html_out = rf.render_rating_html(
            sample_input(),
            cfg,
            voice_probe=lambda _cfg: {
                "installed": False,
                "stt_available": False,
                "stt_engine": "",
                "reason": "Modul 'ellmos-voice-io' fehlt.",
            },
        )
        self.assertIn("voice-notice", html_out)
        self.assertIn("ellmos-voice-io", html_out)
        self.assertNotIn("voice-mic-btn", html_out)
        self.assertNotIn("getUserMedia", html_out)

    def test_voice_enabled_with_installed_module_renders_microphone_and_loopback(self) -> None:
        cfg = {
            "voice": {
                "enabled": True,
                "provider": "ellmos-voice-io",
                "endpoint": "http://127.0.0.1:8765/transcribe",
                "language": "de",
            }
        }
        html_out = rf.render_rating_html(
            sample_input(),
            cfg,
            voice_probe=lambda _cfg: {
                "installed": True,
                "stt_available": True,
                "stt_engine": "vosk",
                "reason": "",
            },
        )
        self.assertIn("voice-mic-btn", html_out)
        self.assertIn("getUserMedia", html_out)
        self.assertNotIn("voice-notice", html_out)

    def test_non_loopback_voice_endpoint_is_rejected(self) -> None:
        cfg = {
            "voice": {
                "enabled": True,
                "provider": "ellmos-voice-io",
                "endpoint": "https://remote.example.com/transcribe",
            }
        }
        with self.assertRaisesRegex(ValueError, "loopback"):
            rf.render_rating_html(sample_input(), cfg)


class FeedbackImportAndCliTests(unittest.TestCase):
    def test_response_converts_to_score_predictions_markdown(self) -> None:
        md = rf.response_to_feedback_markdown(sample_response())
        fb = sp.parse_feedback(md)
        self.assertEqual(fb[("2026-11-21", "dec-001")], "hit")
        self.assertEqual(fb[("2026-11-21", "dec-002")], "miss")

        actions = "\n".join([
            "2026-11-21T10:00:00Z\t🟡\ty\topen\tDEC-001\tRun dry-run",
            "2026-11-21T10:05:00Z\t🔴\ty\topen\tDEC-002\tEscalate",
        ])
        result = sp.score(sp.parse_actions(actions), feedback=fb)
        self.assertEqual(result["overall"]["resolved"], 2)
        self.assertEqual(result["overall"]["hits"], 1)

    def test_cli_build_and_import_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            in_file = base / "input.json"
            out_html = base / "rating.html"
            resp_file = base / "response.json"
            out_md = base / "feedback.md"
            in_file.write_text(json.dumps(sample_input()), encoding="utf-8")
            resp_file.write_text(json.dumps(sample_response()), encoding="utf-8")

            self.assertEqual(rf.main(["build", "--input", str(in_file), "--out", str(out_html)]), 0)
            html_text = out_html.read_text(encoding="utf-8")
            self.assertIn("Avatar Decisions Review", html_text)
            self.assertNotIn("voice-mic-btn", html_text)

            self.assertEqual(
                rf.main(["import-feedback", "--response", str(resp_file), "--out", str(out_md)]),
                0,
            )
            self.assertIn("verdict: 👍 confirmed", out_md.read_text(encoding="utf-8"))


class BridgeRequestFilterTests(unittest.TestCase):
    """Issue #15: the loopback bridge rejects foreign Origin and non-loopback Host."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        html = Path(cls._tmp.name) / "page.html"
        html.write_text("<html>rating</html>", encoding="utf-8")
        handler = rf.make_bridge_handler({"voice": {"enabled": False}}, html)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls._tmp.cleanup()

    def _request(self, method: str, path: str, headers: dict[str, str], body: bytes | None = None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            conn.putrequest(method, path, skip_host=True)
            for key, value in headers.items():
                conn.putheader(key, value)
            if body is not None:
                conn.putheader("Content-Length", str(len(body)))
            conn.endheaders(body)
            resp = conn.getresponse()
            return resp.status, dict(resp.getheaders()), resp.read()
        finally:
            conn.close()

    def _host(self) -> str:
        return f"127.0.0.1:{self.port}"

    def test_loopback_host_and_no_origin_serves_page(self) -> None:
        status, _, body = self._request("GET", "/", {"Host": self._host()})
        self.assertEqual(status, 200)
        self.assertIn(b"rating", body)

    def test_rebinding_host_is_rejected(self) -> None:
        status, _, body = self._request("GET", "/", {"Host": f"attacker.example:{self.port}"})
        self.assertEqual(status, 403)
        self.assertNotIn(b"rating", body)

    def test_missing_host_is_rejected(self) -> None:
        status, _, _ = self._request("GET", "/health", {})
        self.assertEqual(status, 403)

    def test_foreign_origin_post_is_rejected_before_transcription(self) -> None:
        status, headers, body = self._request(
            "POST",
            "/transcribe",
            {"Host": self._host(), "Origin": "https://evil.example", "Content-Type": "text/plain"},
            b"RIFF0000",
        )
        self.assertEqual(status, 403)
        self.assertIn("forbidden origin", body.decode("utf-8"))
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_null_and_own_loopback_origins_are_allowed(self) -> None:
        for origin in ("null", f"http://localhost:{self.port}", f"http://127.0.0.1:{self.port}"):
            with self.subTest(origin=origin):
                status, headers, _ = self._request("OPTIONS", "/transcribe", {"Host": self._host(), "Origin": origin})
                self.assertEqual(status, 204)
                self.assertEqual(headers.get("Access-Control-Allow-Origin"), origin)

    def test_loopback_origin_on_other_port_is_rejected(self) -> None:
        # Another local web app (e.g. a dashboard on :8000) must not drive the transcriber.
        status, headers, _ = self._request(
            "OPTIONS", "/transcribe", {"Host": self._host(), "Origin": "http://127.0.0.1:8000"}
        )
        self.assertEqual(status, 403)
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_page_is_reread_per_request(self) -> None:
        page = Path(self._tmp.name) / "page.html"
        page.write_text("<html>rating v2</html>", encoding="utf-8")
        try:
            _, _, body = self._request("GET", "/", {"Host": self._host()})
            self.assertIn(b"rating v2", body)
        finally:
            page.write_text("<html>rating</html>", encoding="utf-8")

    def test_host_and_origin_helpers(self) -> None:
        for good in ("127.0.0.1", "127.0.0.1:8765", "localhost:1", "[::1]:8765"):
            self.assertTrue(rf.is_loopback_host_header(good), good)
        for bad in (None, "", "evil.example", "127.0.0.1.evil.example", "user@127.0.0.1", "127.0.0.1:x", "127.0.0.1/x"):
            self.assertFalse(rf.is_loopback_host_header(bad), bad)
        self.assertFalse(rf.is_allowed_bridge_origin("file://localhost"))
        self.assertFalse(rf.is_allowed_bridge_origin("http://localhost.evil.example"))
        self.assertFalse(rf.is_allowed_bridge_origin(""))
        self.assertFalse(rf.is_allowed_bridge_origin("http://localhost/path"))
        self.assertFalse(rf.is_allowed_bridge_origin("http://LOCALHOST:80"))
        self.assertFalse(rf.is_allowed_bridge_origin("http://localhost:80\r\nX-Evil: 1"))
        self.assertEqual(rf.canonical_bridge_origin("http://[::1]:8000"), "http://[::1]:8000")
        self.assertEqual(rf.canonical_bridge_origin("https://127.0.0.1"), "https://127.0.0.1")


class MicStreamReuseTests(unittest.TestCase):
    def test_voice_script_reuses_one_stream_and_never_stops_it(self) -> None:
        html_out = rf.render_rating_html(
            sample_input(),
            {"voice": {"enabled": True}},
            voice_probe=lambda _cfg: {"installed": True, "stt_available": True, "stt_engine": "vosk", "reason": ""},
        )
        # Stopping the tracks after each note forced a fresh getUserMedia (and prompt) per click.
        self.assertNotIn("t.stop()", html_out)
        self.assertEqual(html_out.count("getUserMedia({audio:true})"), 1)
        self.assertIn("sharedStream", html_out)


class RatingStoreTests(unittest.TestCase):
    """Every page change is mirrored to a durable file so a browser reset cannot lose ratings."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), rf.make_bridge_handler({"voice": {"enabled": False}}, None, self.dir))
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self._tmp.cleanup()

    def _req(self, method: str, path: str, body: object | None = None, origin: str | None = None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        headers = {"Host": f"127.0.0.1:{self.port}", "Content-Type": "application/json"}
        if origin:
            headers["Origin"] = origin
        raw = json.dumps(body).encode("utf-8") if body is not None else None
        conn.request(method, path, body=raw, headers=headers)
        resp = conn.getresponse()
        data = json.loads(resp.read() or b"{}")
        conn.close()
        return resp.status, data

    def test_post_writes_file_and_get_returns_latest_with_history(self) -> None:
        self.assertEqual(self._req("POST", "/ratings/run-1", {"state": {"A": {"s": 3}}})[0], 200)
        status, data = self._req("POST", "/ratings/run-1", {"state": {"A": {"s": 9, "note": "grün", "note_source": "voice"}}}, origin=f"http://127.0.0.1:{self.port}")
        self.assertEqual(status, 200)
        saved = json.loads((self.dir / "run-1.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["state"], {"A": {"s": 9, "note": "grün", "note_source": "voice"}})
        self.assertEqual(saved["history"][0]["state"], {"A": {"s": 3}})
        status, got = self._req("GET", "/ratings/run-1")
        self.assertEqual((status, got["state"]["A"]["s"], got["saved_at"]), (200, 9, data["saved_at"]))

    def test_unknown_run_returns_empty_state(self) -> None:
        self.assertEqual(self._req("GET", "/ratings/never-saved"), (200, {"ok": True, "saved_at": None, "state": None}))

    def test_history_is_capped(self) -> None:
        for i in range(rf.STORE_HISTORY + 5):
            rf.store_rating_state(self.dir, "run-2", {"A": {"s": i % 11}})
        self.assertEqual(len(rf.load_rating_state(self.dir, "run-2")["history"]), rf.STORE_HISTORY)

    def test_invalid_input_and_foreign_origin_are_rejected(self) -> None:
        self.assertEqual(self._req("POST", "/ratings/..%2Fevil", {"state": {}})[0], 400)
        self.assertEqual(self._req("POST", "/ratings/run-3", {"state": {"A": {"s": 11}}})[0], 400)
        self.assertEqual(self._req("POST", "/ratings/run-3", {"state": {"A": {"x": 1}}})[0], 400)
        self.assertEqual(self._req("POST", "/ratings/run-3", {"state": {"A": {"s": 1}}}, origin="https://evil.example")[0], 403)
        self.assertFalse((self.dir / "run-3.json").exists())
        self.assertEqual(list(self.dir.parent.glob("evil*")), [])

    def test_null_origin_cannot_read_or_overwrite_the_store(self) -> None:
        # B3: any local HTML file or sandboxed iframe sends Origin: null; notes are private.
        rf.store_rating_state(self.dir, "run-4", {"A": {"s": 2, "note": "privat"}})
        status, data = self._req("GET", "/ratings/run-4", origin="null")
        self.assertEqual(status, 403)
        self.assertNotIn("privat", json.dumps(data))
        self.assertEqual(self._req("POST", "/ratings/run-4", {"state": {}}, origin="null")[0], 403)
        self.assertEqual(rf.load_rating_state(self.dir, "run-4")["state"], {"A": {"s": 2, "note": "privat"}})
        self.assertEqual(self._req("GET", "/ratings/run-4", origin=f"http://localhost:{self.port}")[0], 200)

    def test_page_has_import_and_saved_indicator_and_store_only_when_served(self) -> None:
        html_out = rf.render_rating_html(sample_input(), {"voice": {"enabled": False}})
        self.assertIn('id="import-file"', html_out)
        self.assertIn("gespeichert um", html_out)
        self.assertIn('const STORE=location.protocol.startsWith("http")?"/ratings":"";', html_out)
        self.assertNotIn("store_endpoint", html_out)


class RemoteSttTests(unittest.TestCase):
    def test_remote_url_must_stay_on_loopback(self) -> None:
        for bad in ("http://100.119.69.90:8766/transcribe", "http://192.168.1.5:8766/transcribe"):
            cfg = rf._merge_voice_config({"voice": {"enabled": True, "engine": "remote", "remote_url": bad}})
            with self.subTest(url=bad):
                with self.assertRaisesRegex(ValueError, "loopback"):
                    rf.probe_voice_module(cfg)
                with self.assertRaisesRegex(ValueError, "loopback"):
                    rf._transcribe_wav_bytes(b"RIFF", cfg, "de")

    def test_bridge_forwards_audio_to_remote_worker(self) -> None:
        import stt_server

        seen: list[tuple[bytes, str]] = []

        def fake(path: Path, lang: str) -> str:
            seen.append((path.read_bytes(), lang))
            return "hallo welt"

        worker = ThreadingHTTPServer(("127.0.0.1", 0), stt_server.make_handler(fake, "fake-model"))
        threading.Thread(target=worker.serve_forever, daemon=True).start()
        try:
            cfg = {"voice": {"enabled": True, "engine": "remote",
                             "remote_url": f"http://127.0.0.1:{worker.server_address[1]}/transcribe"}}
            self.assertTrue(rf.probe_voice_module(rf._merge_voice_config(cfg))["stt_available"])
            text = rf._transcribe_wav_bytes(b"RIFFfake", rf._merge_voice_config(cfg), "de")
        finally:
            worker.shutdown()
            worker.server_close()
        self.assertEqual(text, "hallo welt")
        self.assertEqual(seen, [(b"RIFFfake", "de")])

    def _serve(self, handler) -> ThreadingHTTPServer:
        srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        return srv

    def test_remote_call_ignores_http_proxy_env(self) -> None:
        # B1: urlopen honours http_proxy, which would ship audio to the proxy.
        import stt_server
        from http.server import BaseHTTPRequestHandler

        proxy_hits: list[str] = []

        class Proxy(BaseHTTPRequestHandler):
            def log_message(self, *a: object) -> None:
                return

            def _any(self) -> None:
                proxy_hits.append(self.path)
                raw = json.dumps({"ok": True, "text": "vom proxy"}).encode()
                self.send_response(200); self.send_header("Content-Length", str(len(raw))); self.end_headers()
                self.wfile.write(raw)

            do_GET = do_POST = _any

        proxy = self._serve(Proxy)
        worker = self._serve(stt_server.make_handler(lambda p, l: "vom worker", "m"))
        cfg = rf._merge_voice_config({"voice": {"enabled": True, "engine": "remote",
                                                "remote_url": f"http://127.0.0.1:{worker.server_address[1]}/transcribe"}})
        # Fresh process: urllib caches its default opener (and the proxy env it read) per process.
        import os
        import subprocess

        env = {**os.environ, "http_proxy": f"http://127.0.0.1:{proxy.server_address[1]}", "no_proxy": "", "NO_PROXY": "",
               "PYTHONIOENCODING": "utf-8"}
        env["HTTP_PROXY"] = env["http_proxy"]
        code = ("import json,sys; sys.path.insert(0, sys.argv[1]); import rating_form as rf; "
                "cfg = json.loads(sys.argv[2]); "
                "print(rf._transcribe_wav_bytes(b'RIFF', cfg, 'de'), rf.probe_voice_module(cfg)['stt_available'])")
        out = subprocess.run([sys.executable, "-c", code, str(SCRIPTS), json.dumps(cfg)], env=env,
                             capture_output=True, text=True, encoding="utf-8", timeout=30, check=True).stdout.strip()
        self.assertEqual(out, "vom worker True")
        self.assertEqual(proxy_hits, [])

    def test_remote_redirect_is_not_followed(self) -> None:
        from http.server import BaseHTTPRequestHandler

        class Redirect(BaseHTTPRequestHandler):
            def log_message(self, *a: object) -> None:
                return

            def do_POST(self) -> None:  # noqa: N802
                self.send_response(302); self.send_header("Location", "/elsewhere"); self.send_header("Content-Length", "0"); self.end_headers()

            def do_GET(self) -> None:  # noqa: N802
                raw = json.dumps({"ok": True, "text": "umgeleitet"}).encode()
                self.send_response(200); self.send_header("Content-Length", str(len(raw))); self.end_headers()
                self.wfile.write(raw)

        srv = self._serve(Redirect)
        cfg = rf._merge_voice_config({"voice": {"enabled": True, "engine": "remote",
                                                "remote_url": f"http://127.0.0.1:{srv.server_address[1]}/transcribe"}})
        with self.assertRaises(OSError):
            rf._transcribe_wav_bytes(b"RIFF", cfg, "de")

    def test_worker_rejects_foreign_host_and_any_origin(self) -> None:
        # B2: DNS rebinding / browser pages must not reach the STT worker.
        import stt_server

        worker = self._serve(stt_server.make_handler(lambda p, l: "x", "m"))
        port = worker.server_address[1]

        def req(method: str, path: str, headers: dict[str, str]) -> int:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            conn.putrequest(method, path, skip_host=True)
            for k, v in headers.items():
                conn.putheader(k, v)
            body = b"RIFF" if method == "POST" else None
            if body:
                conn.putheader("Content-Length", str(len(body)))
            conn.endheaders(body)
            status = conn.getresponse().status
            conn.close()
            return status

        self.assertEqual(req("GET", "/health", {"Host": f"attacker.example:{port}"}), 403)
        self.assertEqual(req("POST", "/transcribe", {"Host": f"127.0.0.1:{port}", "Origin": "http://attacker.example",
                                                      "Content-Type": "text/plain"}), 403)
        self.assertEqual(req("POST", "/transcribe", {"Host": f"127.0.0.1:{port}", "Origin": "null"}), 403)
        self.assertEqual(req("GET", "/health", {}), 403)
        self.assertEqual(req("GET", "/health", {"Host": f"127.0.0.1:{port}"}), 200)

    def test_worker_rejects_public_clients(self) -> None:
        import stt_server

        self.assertTrue(stt_server.is_loopback_client("127.0.0.1"))
        self.assertTrue(stt_server.is_loopback_client("::1"))
        for addr in ("100.64.0.7", "192.168.1.5", "8.8.8.8", "0.0.0.0", "nonsense"):
            self.assertFalse(stt_server.is_loopback_client(addr), addr)


if __name__ == "__main__":
    unittest.main()
