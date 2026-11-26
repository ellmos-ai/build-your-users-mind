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
        self.assertIn("if(!STORE_URL)savedEl.textContent=", html_out)  # file:// says so up front


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
                self.send_response(200)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            do_GET = do_POST = _any

        proxy = self._serve(Proxy)
        worker = self._serve(stt_server.make_handler(lambda path, lang: "vom worker", "m"))
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
                self.send_response(302)
                self.send_header("Location", "/elsewhere")
                self.send_header("Content-Length", "0")
                self.end_headers()

            def do_GET(self) -> None:  # noqa: N802
                raw = json.dumps({"ok": True, "text": "umgeleitet"}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        srv = self._serve(Redirect)
        cfg = rf._merge_voice_config({"voice": {"enabled": True, "engine": "remote",
                                                "remote_url": f"http://127.0.0.1:{srv.server_address[1]}/transcribe"}})
        with self.assertRaises(OSError):
            rf._transcribe_wav_bytes(b"RIFF", cfg, "de")

    def test_worker_rejects_foreign_host_and_any_origin(self) -> None:
        # B2: DNS rebinding / browser pages must not reach the STT worker.
        import stt_server

        worker = self._serve(stt_server.make_handler(lambda path, lang: "x", "m"))
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


class _DomInspector:
    """Lightweight stdlib HTMLParser collector for structural DOM assertions."""

    def __init__(self, raw_html: str) -> None:
        from html.parser import HTMLParser

        outer = self
        outer.elements: list[dict[str, object]] = []
        outer.scripts: list[str] = []

        class _P(HTMLParser):
            def __init__(self) -> None:
                super().__init__()
                self._stack: list[dict[str, object]] = []
                self._in_script = False
                self._script_buf: list[str] = []

            def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
                attr_map = {k: ("" if v is None else v) for k, v in attrs}
                node: dict[str, object] = {
                    "tag": tag,
                    "attrs": attr_map,
                    "text": [],
                    "parent_ids": [
                        str(p["attrs"].get("id"))  # type: ignore[index]
                        for p in self._stack
                        if p["attrs"].get("id")  # type: ignore[index]
                    ],
                }
                outer.elements.append(node)
                self._stack.append(node)
                if tag == "script":
                    self._in_script = True
                    self._script_buf = []

            def handle_endtag(self, tag: str) -> None:
                if tag == "script" and self._in_script:
                    outer.scripts.append("".join(self._script_buf))
                    self._in_script = False
                for idx in range(len(self._stack) - 1, -1, -1):
                    if self._stack[idx]["tag"] == tag:
                        self._stack.pop(idx)
                        break

            def handle_data(self, data: str) -> None:
                if self._in_script:
                    self._script_buf.append(data)
                for ancestor in self._stack:
                    ancestor["text"].append(data)  # type: ignore[index]

        parser = _P()
        parser.feed(raw_html)

    def by_id(self, elem_id: str) -> dict[str, object]:
        for el in self.elements:
            if el["attrs"].get("id") == elem_id:  # type: ignore[index]
                return el
        raise AssertionError(f"Missing element with id={elem_id!r}")


class DictationModeDomAndAccessibilityTests(unittest.TestCase):
    def test_dictation_mode_is_default_with_split_screen_dom_and_zero_external_egress(self) -> None:
        html_out = rf.render_rating_html(sample_input(), {"voice": {"enabled": False}})
        dom = _DomInspector(html_out)

        bodies = [el for el in dom.elements if el["tag"] == "body"]
        self.assertEqual(len(bodies), 1)
        self.assertEqual(bodies[0]["attrs"].get("data-mode"), "dictation")  # type: ignore[index]

        mode_dict = dom.by_id("mode-dictation")
        mode_cards = dom.by_id("mode-cards")
        self.assertEqual(mode_dict["attrs"].get("aria-pressed"), "true")  # type: ignore[index]
        self.assertEqual(mode_cards["attrs"].get("aria-pressed"), "false")  # type: ignore[index]

        dict_view = dom.by_id("dictation-view")
        cards_view = dom.by_id("list")
        self.assertNotIn("hidden", dict_view["attrs"])  # type: ignore[index]
        self.assertIn("hidden", cards_view["attrs"])  # type: ignore[index]

        # Left column: numbered items with context + avatar decision + marker button
        left_items = [
            el
            for el in dom.elements
            if el["tag"] == "article" and "dictation-items" in el["parent_ids"]  # type: ignore[operator]
        ]
        self.assertEqual(len(left_items), 2)
        first_text = "".join(left_items[0]["text"])  # type: ignore[arg-type]
        self.assertIn("#1", first_text)
        self.assertIn("Worum es ging:", first_text)
        self.assertIn("An operator requested a dry-run before writing files.", first_text)
        self.assertIn("Entscheidung des Avatars:", first_text)
        self.assertIn("Run dry-run first and preview the output path.", first_text)

        # Right column: exactly one continuous dictation textarea + status bar
        right_textareas = [
            el
            for el in dom.elements
            if el["tag"] == "textarea" and "dictation-pane" in el["parent_ids"]  # type: ignore[operator]
        ]
        self.assertEqual(len(right_textareas), 1)
        self.assertEqual(right_textareas[0]["attrs"].get("id"), "dictation-text")  # type: ignore[index]
        self.assertEqual(dom.by_id("dictation-saved")["attrs"].get("role"), "status")  # type: ignore[index]
        self.assertIn("0 Wörter · 0 Zeichen", "".join(dom.by_id("dictation-counts")["text"]))  # type: ignore[arg-type]

        # P-022 tap target (>= 44px), keyboard focus, and zero external URLs
        self.assertIn("min-height:44px;min-width:44px", html_out)
        self.assertIn(":focus-visible", html_out)
        for el in dom.elements:
            attrs = el["attrs"]  # type: ignore[assignment]
            for url_attr in ("src", "href", "action"):
                val = str(attrs.get(url_attr) or "")  # type: ignore[union-attr]
                self.assertFalse(val.startswith(("http://", "https://", "//")), f"External URL found: {val}")


class DictationModeHeadlessJsBehaviorTests(unittest.TestCase):
    def test_mode_switch_markers_autosave_export_and_import_preserve_all_inputs(self) -> None:
        import os
        import shutil
        import subprocess

        node_exe = shutil.which("node")
        if not node_exe:
            self.skipTest("node is not installed")

        html_one = rf.render_rating_html(sample_input(), {"voice": {"enabled": False}})
        other_batch = sample_input()
        other_batch["run_id"] = "synthetic-rating-run-2"
        html_two = rf.render_rating_html(other_batch, {"voice": {"enabled": False}})

        script_one = _DomInspector(html_one).scripts[0]
        script_two = _DomInspector(html_two).scripts[0]

        harness = r"""
const fs = require("fs");
const vm = require("vm");

function createEnv(sharedStorage) {
  const downloads = [];
  const elementsById = new Map();
  const allElements = [];

  class FakeClassList {
    constructor(owner) { this.owner = owner; this.set = new Set(); }
    _syncFromAttr(v) { this.set = new Set(String(v || "").split(/\s+/).filter(Boolean)); }
    _writeAttr() { this.owner.className = Array.from(this.set).join(" "); }
    add(...names) { names.forEach(n => this.set.add(n)); this._writeAttr(); }
    remove(...names) { names.forEach(n => this.set.delete(n)); this._writeAttr(); }
    toggle(name, force) {
      const on = force === undefined ? !this.set.has(name) : Boolean(force);
      if (on) this.set.add(name); else this.set.delete(name);
      this._writeAttr();
      return on;
    }
    contains(name) { return this.set.has(name); }
  }

  class FakeElement {
    constructor(tag, id = "") {
      this.tagName = tag.toUpperCase();
      this._id = "";
      this._className = "";
      this.classList = new FakeClassList(this);
      this.dataset = {};
      this.attrs = {};
      this.children = [];
      this.parentElement = null;
      this.hidden = false;
      this.checked = false;
      this.value = "";
      this.textContent = "";
      this.type = "";
      this.download = "";
      this.href = "";
      this.files = [];
      this.selectionStart = 0;
      this.selectionEnd = 0;
      this.listeners = {};
      this.onclick = null;
      this.onchange = null;
      allElements.push(this);
      if (id) this.id = id;
    }
    get id() { return this._id; }
    set id(v) {
      this._id = String(v || "");
      if (this._id) elementsById.set(this._id, this);
    }
    get className() { return this._className; }
    set className(v) {
      this._className = String(v || "");
      this.classList.set = new Set(this._className.split(/\s+/).filter(Boolean));
    }
    setAttribute(k, v) {
      this.attrs[k] = String(v);
      if (k === "id") this.id = v;
      if (k === "class") this.className = v;
      if (k.startsWith("data-")) {
        const camel = k.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
        this.dataset[camel] = String(v);
      }
    }
    getAttribute(k) { return this.attrs[k] ?? null; }
    removeAttribute(k) { delete this.attrs[k]; }
    appendChild(child) { child.parentElement = this; this.children.push(child); return child; }
    addEventListener(ev, fn) { (this.listeners[ev] ||= []).push(fn); }
    dispatch(ev, detail = {}) {
      const event = Object.assign({ target: this, preventDefault(){}, stopPropagation(){ event._stopped = true; } }, detail);
      let cur = this;
      while (cur) {
        for (const fn of (cur.listeners[ev] || [])) fn(event);
        if (event._stopped) break;
        cur = cur.parentElement;
      }
    }
    click() {
      if (typeof this.onclick === "function") this.onclick({ target: this, preventDefault(){}, stopPropagation(){} });
      if (this.tagName === "A" && this.download) {
        downloads.push({ filename: this.download, content: this.href });
      }
      this.dispatch("click");
    }
    focus() {}
    setSelectionRange(a, b) { this.selectionStart = a; this.selectionEnd = b; }
    closest(sel) {
      let cur = this;
      while (cur) {
        if (matches(cur, sel)) return cur;
        cur = cur.parentElement;
      }
      return null;
    }
    set innerHTML(htmlStr) {
      this.children = [];
      // Parse radios, textareas, and mark buttons created by template JS
      const radioRe = /<input type="radio" name="([^"]+)" data-id="([^"]+)" value="(\d+)">/g;
      let m;
      while ((m = radioRe.exec(htmlStr)) !== null) {
        const inp = new FakeElement("input");
        inp.type = "radio";
        inp.name = m[1];
        inp.dataset.id = m[2];
        inp.value = m[3];
        this.appendChild(inp);
      }
      const taRe = /<textarea[^>]*data-id="([^"]+)"[^>]*><\/textarea>/g;
      while ((m = taRe.exec(htmlStr)) !== null) {
        const ta = new FakeElement("textarea");
        ta.dataset.id = m[1];
        this.appendChild(ta);
      }
    }
    querySelectorAll(sel) {
      const out = [];
      function walk(node) {
        for (const ch of node.children) {
          if (matches(ch, sel)) out.push(ch);
          walk(ch);
        }
      }
      walk(this);
      return out;
    }
    querySelector(sel) { return this.querySelectorAll(sel)[0] || null; }
  }

  function matches(el, sel) {
    if (sel === 'input[type="radio"]') return el.tagName === "INPUT" && el.type === "radio";
    if (sel === "textarea") return el.tagName === "TEXTAREA";
    if (sel === ".dict-item") return el.classList.contains("dict-item");
    if (sel === "[data-insert-mark]") return Boolean(el.dataset.insertMark);
    const radioMatch = /^input\[type="radio"\]\[data-id="([^"]+)"\]\[value="([^"]+)"\]$/.exec(sel);
    if (radioMatch) return el.tagName === "INPUT" && el.type === "radio" && el.dataset.id === radioMatch[1] && el.value === radioMatch[2];
    const taMatch = /^textarea\[data-id="([^"]+)"\]$/.exec(sel);
    if (taMatch) return el.tagName === "TEXTAREA" && el.dataset.id === taMatch[1];
    return false;
  }

  const body = new FakeElement("body");
  body.dataset.mode = "dictation";
  ["page-title", "page-desc", "cnt", "saved", "dictation-counts", "dictation-saved"].forEach(id => body.appendChild(new FakeElement("span", id)));
  ["mode-dictation", "mode-cards", "save", "save-txt", "bulk", "import"].forEach(id => body.appendChild(new FakeElement("button", id)));
  body.appendChild(new FakeElement("input", "import-file"));
  const dictView = body.appendChild(new FakeElement("section", "dictation-view"));
  const dictItems = dictView.appendChild(new FakeElement("div", "dictation-items"));
  // Seed pre-rendered dictation items matching Python _render_dictation_items_html
  for (const [nr, id] of [[1, "DEC-001"], [2, "DEC-002"]]) {
    const art = new FakeElement("article", "dict-item-" + nr);
    art.className = "dict-item";
    art.dataset.id = id;
    art.dataset.nr = String(nr);
    const btn = new FakeElement("button");
    btn.className = "sec mark-btn";
    btn.dataset.insertMark = "[#" + nr + "]";
    btn.dataset.id = id;
    art.appendChild(btn);
    dictItems.appendChild(art);
  }
  const dictPane = dictView.appendChild(new FakeElement("div", "dictation-pane"));
  const dictTa = dictPane.appendChild(new FakeElement("textarea", "dictation-text"));
  const list = body.appendChild(new FakeElement("div", "list"));
  list.hidden = true;

  const blobs = new Map();
  let blobSeq = 0;
  const sandbox = {
    document: {
      body,
      getElementById: id => elementsById.get(id) || null,
      createElement: tag => new FakeElement(tag),
      querySelectorAll: sel => body.querySelectorAll(sel),
    },
    window: { getSelection: () => "" },
    location: { protocol: "file:" },
    localStorage: {
      getItem: k => (sharedStorage.has(k) ? sharedStorage.get(k) : null),
      setItem: (k, v) => sharedStorage.set(k, String(v)),
    },
    CSS: { escape: s => String(s) },
    Blob: class { constructor(parts, opts) { this.text = parts.join(""); this.type = (opts && opts.type) || ""; } },
    URL: {
      createObjectURL: blob => { const u = "blob:" + (++blobSeq); blobs.set(u, blob.text); return u; },
    },
    setTimeout,
    clearTimeout,
    Date,
    JSON,
    Number,
    String,
    Object,
    Array,
    Set,
  };
  return { sandbox, elementsById, downloads, blobs };
}

const scriptOne = fs.readFileSync(process.argv[2], "utf8");
const scriptTwo = fs.readFileSync(process.argv[3], "utf8");
const storage = new Map();

// 1. Open batch 1 -> default is dictation mode
const env1 = createEnv(storage);
vm.runInNewContext(scriptOne, env1.sandbox);
const e1 = id => env1.elementsById.get(id);
if (env1.sandbox.document.body.dataset.mode !== "dictation") throw new Error("Expected dictation default");
if (e1("dictation-view").hidden || !e1("list").hidden) throw new Error("Visibility mismatch in default mode");

// 2. Click [#1] marker, dictate continuous text with pauses, click [#2] marker
const mark1 = e1("dict-item-1").children[0];
mark1.click();
const ta = e1("dictation-text");
ta.value += "Erster Posten passt genau so.";
ta.selectionStart = ta.selectionEnd = ta.value.length;
ta.dispatch("input");
const mark2 = e1("dict-item-2").children[0];
mark2.click();
ta.value += "Hier bitte vorab nachfragen.";
ta.selectionStart = ta.selectionEnd = ta.value.length;
ta.dispatch("input");

// 3. Switch to cards mode -> score DEC-001 = 9 + card note -> switch back to dictation -> zero loss!
e1("mode-cards").click();
if (e1("dictation-view").hidden !== true || e1("list").hidden !== false) throw new Error("Cards mode toggle failed");
const radio9 = e1("list").querySelector('input[type="radio"][data-id="DEC-001"][value="9"]');
radio9.checked = true;
radio9.dispatch("change");
const cardTa1 = e1("list").querySelector('textarea[data-id="DEC-001"]');
cardTa1.value = "Einzelnotiz bleibt erhalten";
cardTa1.dispatch("input");

e1("mode-dictation").click();
if (e1("dictation-view").hidden !== false || e1("list").hidden !== true) throw new Error("Return to dictation failed");

// 4. Open batch 2 in same localStorage -> must not overwrite or collide with batch 1
const env2 = createEnv(storage);
vm.runInNewContext(scriptTwo, env2.sandbox);
if (env2.elementsById.get("dictation-text").value !== "") throw new Error("Storage key collision across batches");

// 5. Export JSON and TXT from batch 1
e1("save").click();
e1("save-txt").click();
const jsonRaw = env1.blobs.get(env1.downloads[0].content);
const txtRaw = env1.blobs.get(env1.downloads[1].content);

// 6. Re-import JSON into a clean storage session and verify full roundtrip
const cleanStorage = new Map();
const env3 = createEnv(cleanStorage);
vm.runInNewContext(scriptOne, env3.sandbox);
const imp = env3.elementsById.get("import-file");
imp.files = [{ text: async () => jsonRaw }];
(async () => {
  await imp.onchange();
  console.log(JSON.stringify({
    exportedJson: JSON.parse(jsonRaw),
    exportedTxt: txtRaw,
    countsText: e1("dictation-counts").textContent,
    activeAttr2: e1("dict-item-2").getAttribute("aria-current"),
    reimportedDictation: env3.elementsById.get("dictation-text").value,
    reimportedCardNote: env3.elementsById.get("list").querySelector('textarea[data-id="DEC-001"]').value,
    reimportedScoreChecked: env3.elementsById.get("list").querySelector('input[type="radio"][data-id="DEC-001"][value="9"]').checked,
  }));
})();
"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            s1_path = base / "s1.js"
            s2_path = base / "s2.js"
            h_path = base / "harness.js"
            s1_path.write_text(script_one, encoding="utf-8")
            s2_path.write_text(script_two, encoding="utf-8")
            h_path.write_text(harness, encoding="utf-8")
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            proc = subprocess.run(
                [node_exe, str(h_path), str(s1_path), str(s2_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                timeout=15,
                check=True,
                creationflags=creationflags,
            )

        res = json.loads(proc.stdout.strip())
        exported = res["exportedJson"]
        validated = rf.validate_response_payload(exported)
        self.assertEqual(validated["mode"], "dictation")
        self.assertIn("[#1] Erster Posten passt genau so.", validated["dictation"])
        self.assertIn("[#2] Hier bitte vorab nachfragen.", validated["dictation"])
        self.assertEqual(validated["ratings"][0]["score"], 9)
        self.assertEqual(validated["ratings"][0]["note"], "Einzelnotiz bleibt erhalten")
        self.assertIsNone(validated["ratings"][1]["score"])

        self.assertIn("=== DIKTAT ===", res["exportedTxt"])
        self.assertIn("[#1] Erster Posten passt genau so.", res["exportedTxt"])
        self.assertIn("=== POSTEN & KARTEN-BEWERTUNGEN ===", res["exportedTxt"])
        self.assertIn("Karten-Bewertung: 9/10", res["exportedTxt"])
        self.assertIn("Karten-Notiz: Einzelnotiz bleibt erhalten", res["exportedTxt"])
        self.assertEqual(res["activeAttr2"], "true")
        self.assertIn("Wörter", res["countsText"])
        self.assertEqual(res["reimportedDictation"], validated["dictation"])
        self.assertEqual(res["reimportedCardNote"], "Einzelnotiz bleibt erhalten")
        self.assertTrue(res["reimportedScoreChecked"])

    def test_dictation_response_converts_to_feedback_markdown_and_bridge_store(self) -> None:
        resp = sample_response()
        resp["mode"] = "dictation"
        resp["dictation"] = "[#1] Genau richtig entschieden.\n[#2] Bitte vorher nachfragen."
        resp["dictation_source"] = "text"
        md = rf.response_to_feedback_markdown(resp)
        self.assertIn("## Dictation Feedback (2026-11-21)", md)
        self.assertIn("[#1] Genau richtig entschieden.", md)
        fb = sp.parse_feedback(md)
        self.assertEqual(fb[("2026-11-21", "dec-001")], "hit")

        with tempfile.TemporaryDirectory() as tmp:
            store_dir = Path(tmp)
            rf.store_rating_state(store_dir, "run-dict-1", {"DEC-001": {"s": 8}}, dictation="Fortlaufender Text")
            loaded = rf.load_rating_state(store_dir, "run-dict-1")
            self.assertEqual(loaded["dictation"], "Fortlaufender Text")
            self.assertEqual(loaded["state"]["DEC-001"]["s"], 8)


class PrefilterReadbackTests(unittest.TestCase):
    def test_prefilter_drops_empty_context_solved_done_tickets_and_resolved_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            tickets_root = base / "tickets"
            (tickets_root / "SOLVED").mkdir(parents=True)
            (tickets_root / "DONE").mkdir(parents=True)
            (tickets_root / "OPEN").mkdir(parents=True)
            (tickets_root / "SOLVED" / "T-20261110-100000001_already-fixed.md").write_text("solved", encoding="utf-8")
            (tickets_root / "DONE" / "T-20261112-200000002.txt").write_text("done", encoding="utf-8")
            (tickets_root / "OPEN" / "T-20261125-300000003.md").write_text("open", encoding="utf-8")

            decisions_dir = base / "decisions"
            (decisions_dir / "_tools").mkdir(parents=True)
            decisions_index_path = decisions_dir / "_tools" / "decisions.index.json"
            decisions_index_path.write_text(
                json.dumps(
                    {
                        "schema": "decisions.index/1",
                        "entries": [
                            {"id": "D-20261101-001", "domain": "done", "status_class": "DONE"},
                            {"id": "D-20261125-009", "domain": "active", "status_class": "OFFEN", "decision_ready": True},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            decided_md = decisions_dir / "DECIDED-AND-DONE.md"
            decided_md.write_text("## D-20261105-002 — Archived policy\nSTATUS: DONE 2026-11-06\n", encoding="utf-8")

            raw_entries = [
                {
                    "nr": 1,
                    "id": "ITEM-EMPTY-CTX",
                    "kontext": "   ",
                    "entscheidung": "Some avatar choice.",
                    "konfidenz": "🟡",
                    "ziel": "USER",
                },
                {
                    "nr": 2,
                    "id": "ITEM-PLACEHOLDER-DEC",
                    "kontext": "Valid operator question with full background.",
                    "entscheidung": "TBD",
                    "konfidenz": "🟡",
                    "ziel": "USER",
                },
                {
                    "nr": 3,
                    "id": "T-20261110-100000001",
                    "kontext": "Question whose ticket was already solved.",
                    "entscheidung": "Apply default.",
                    "konfidenz": "🟢",
                    "ziel": "ACTIONABLE",
                },
                {
                    "nr": 4,
                    "id": "AV-034",
                    "kontext": "Follow-up for ticket T-20261112-200000002 in batch.",
                    "entscheidung": "Keep local-only mode.",
                    "konfidenz": "🟡",
                    "ziel": "ACTIONABLE",
                },
                {
                    "nr": 5,
                    "id": "D-20261101-001",
                    "kontext": "Decision already marked DONE in decisions.index.json.",
                    "entscheidung": "Option A.",
                    "konfidenz": "🟢",
                    "ziel": "USER",
                },
                {
                    "nr": 6,
                    "id": "AV-036",
                    "kontext": "References D-20261105-002 from DECIDED-AND-DONE.md.",
                    "entscheidung": "Option B.",
                    "konfidenz": "🟡",
                    "ziel": "USER",
                },
                {
                    "nr": 7,
                    "id": "MANUAL-RESOLVED-7",
                    "kontext": "Explicitly listed in resolved_ids.",
                    "entscheidung": "Skip.",
                    "konfidenz": "🟢",
                    "ziel": "ACTIONABLE",
                },
                {
                    "nr": 8,
                    "id": "D-20261125-009",
                    "kontext": "Genuine open question referencing T-20261125-300000003 (even after D-20261101-001).",
                    "entscheidung": "Propose safe dry-run with explicit preview.",
                    "konfidenz": "🟡",
                    "ziel": "USER",
                },
            ]

            report = rf.prefilter_items(
                raw_entries,
                tickets_root=tickets_root,
                decisions_index=decisions_dir,
                resolved_ids=["MANUAL-RESOLVED-7"],
            )
            self.assertEqual(report["counts"], {"input": 8, "kept": 1, "filtered_out": 7})
            self.assertEqual([x["id"] for x in report["kept"]], ["D-20261125-009"])
            reasons = {row["id"]: row["reason"] for row in report["filtered_out"]}
            self.assertEqual(
                reasons,
                {
                    "ITEM-EMPTY-CTX": "missing_context",
                    "ITEM-PLACEHOLDER-DEC": "missing_decision",
                    "T-20261110-100000001": "ticket_resolved",
                    "AV-034": "ticket_resolved",
                    "D-20261101-001": "decision_resolved",
                    "AV-036": "decision_resolved",
                    "MANUAL-RESOLVED-7": "resolved_id",
                },
            )

            # End-to-end CLI build with prefilter report
            in_json = base / "raw_input.json"
            out_html = base / "filtered_rating.html"
            out_report = base / "filter_report.json"
            in_json.write_text(
                json.dumps(
                    {
                        "schema": rf.INPUT_SCHEMA,
                        "run_id": "synthetic-prefilter-batch",
                        "entries": raw_entries,
                    }
                ),
                encoding="utf-8",
            )
            rc = rf.main(
                [
                    "build",
                    "--input",
                    str(in_json),
                    "--out",
                    str(out_html),
                    "--tickets-root",
                    str(tickets_root),
                    "--decisions-index",
                    str(decisions_dir),
                    "--resolved-id",
                    "MANUAL-RESOLVED-7",
                    "--filter-report",
                    str(out_report),
                ]
            )
            self.assertEqual(rc, 0)
            rendered_html = out_html.read_text(encoding="utf-8")
            self.assertIn("D-20261125-009", rendered_html)
            self.assertNotIn("T-20261110-100000001", rendered_html)
            self.assertNotIn("ITEM-EMPTY-CTX", rendered_html)
            saved_report = json.loads(out_report.read_text(encoding="utf-8"))
            self.assertEqual(saved_report["kept_ids"], ["D-20261125-009"])
            self.assertEqual(saved_report["counts"]["filtered_out"], 7)


if __name__ == "__main__":
    unittest.main()
