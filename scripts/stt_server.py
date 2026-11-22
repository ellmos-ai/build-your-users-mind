#!/usr/bin/env python3
"""Minimal loopback-only speech-to-text worker backed by mlx-whisper.

Counterpart of ``voice.engine: "remote"`` in ``rating_form.py``: the browser keeps
talking to the loopback bridge, and the bridge forwards the WAV body to
``voice.remote_url``. Like the bridge, this worker binds and answers on loopback only;
to use a bigger Apple-silicon host, the operator forwards the port explicitly, e.g.
``ssh -N -L 127.0.0.1:8766:127.0.0.1:8766 user@stt-host``.

    python scripts/stt_server.py --port 8766 --model mlx-community/whisper-large-v3-turbo
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

MAX_AUDIO_BYTES = 15 * 1024 * 1024


def is_loopback_client(addr: str) -> bool:
    try:
        return ipaddress.ip_address(addr).is_loopback
    except ValueError:
        return False


def is_loopback_host_header(value: str | None) -> bool:
    """DNS-rebinding guard: ``Host`` must name loopback (optional port)."""
    try:
        parsed = urlparse(f"//{(value or '').strip()}")
        _ = parsed.port
    except ValueError:
        return False
    if not value or parsed.username is not None or parsed.path or parsed.query or parsed.fragment:
        return False
    return parsed.hostname in {"127.0.0.1", "localhost", "::1"}


def mlx_transcriber(model: str) -> Callable[[Path, str], str]:
    import mlx_whisper  # type: ignore[import-not-found]

    def run(path: Path, language: str) -> str:
        result = mlx_whisper.transcribe(str(path), path_or_hf_repo=model, language=language or None)
        return str(result.get("text") or "").strip()

    return run


def make_handler(transcribe: Callable[[Path, str], str], model: str) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:  # noqa: A002
            return

        def _json(self, data: dict[str, object], status: int = 200) -> None:
            raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _foreign(self) -> bool:
            # Only the bridge calls this worker, server-side and without an Origin header;
            # any browser request (it always carries Origin on POST/CORS) is refused.
            if not is_loopback_client(self.client_address[0]):
                error = "forbidden client"
            elif not is_loopback_host_header(self.headers.get("Host")):
                error = "forbidden host"
            elif self.headers.get("Origin") is not None:
                error = "forbidden origin"
            else:
                return False
            self._json({"ok": False, "error": error}, 403)
            return True

        def do_GET(self) -> None:  # noqa: N802
            if self._foreign():
                return
            if self.path == "/health":
                self._json({"ok": True, "engine": "mlx-whisper", "model": model})
            else:
                self._json({"ok": False, "error": "not found"}, 404)

        def do_POST(self) -> None:  # noqa: N802
            if self._foreign():
                return
            if self.path != "/transcribe":
                self._json({"ok": False, "error": "not found"}, 404)
                return
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            if length <= 0 or length > MAX_AUDIO_BYTES:
                self._json({"ok": False, "error": "audio payload size out of bounds"}, 400)
                return
            body = self.rfile.read(length)
            lang = (self.headers.get("X-Voice-Language") or "de").strip()
            try:
                with tempfile.TemporaryDirectory(prefix="byum-stt-") as tmp:
                    wav = Path(tmp) / "input.wav"
                    wav.write_bytes(body)
                    text = transcribe(wav, lang)
            except Exception as exc:  # noqa: BLE001
                self._json({"ok": False, "error": str(exc)}, 500)
                return
            self._json({"ok": True, "text": text})

    return Handler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", default="127.0.0.1", help="Loopback address to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--model", default="mlx-community/whisper-large-v3-turbo")
    args = parser.parse_args(argv)
    if not is_loopback_client(args.host):
        parser.error("--host must be a loopback address")
    # HTTPServer is single-threaded on purpose: one transcription at a time on the GPU.
    server = HTTPServer((args.host, args.port), make_handler(mlx_transcriber(args.model), args.model))
    print(f"BYUM STT worker ({args.model}) on http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
