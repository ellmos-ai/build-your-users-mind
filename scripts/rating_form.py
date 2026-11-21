#!/usr/bin/env python3
"""Render, serve, and import feedback from the generic avatar rating form.

Generates a standalone light/dark HTML rating page from a schema-validated JSON
input file, gates optional local voice input (`ellmos-voice-io`) behind config
and module availability, and converts downloaded rating responses into the
existing Markdown feedback format consumed by ``score_predictions.py``.
"""
from __future__ import annotations

import argparse
import copy
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from pipeline_common import atomic_write_text, validate_since, validate_timestamp

INPUT_SCHEMA = "byum.avatar-rating-input.v1"
RESPONSE_SCHEMA = "byum.avatar-rating-response.v1"
CONFIG_SCHEMA = "byum.avatar-rating-config.v1"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE_PATH = REPO_ROOT / "templates" / "AVATAR-RATING.template.html"
DEFAULT_VOICE_CONFIG: dict[str, Any] = {
    "enabled": False,
    "provider": "ellmos-voice-io",
    "endpoint": "http://127.0.0.1:8765/transcribe",
    "engine": "auto",
    "language": "de",
    "model_path": "",
    "python_executable": "",
}
_ALLOWED_INPUT_KEYS = {"schema", "run_id", "title", "description", "entries"}
_ALLOWED_ENTRY_KEYS = {"nr", "id", "kontext", "entscheidung", "konfidenz", "ziel", "ebene", "date"}
_ALLOWED_RESPONSE_KEYS = {"schema", "run_id", "saved_at", "ratings"}
_ALLOWED_RATING_KEYS = {"nr", "id", "entscheidung", "score", "note", "note_source"}
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
_MAX_AUDIO_BYTES = 15 * 1024 * 1024

_VOICE_CSS = (
    ".voice-mic-btn{background:transparent;color:var(--acc);border:1px solid var(--line);"
    "border-radius:6px;padding:6px 9px;display:inline-flex;align-items:center;justify-content:center;"
    "gap:4px;flex-shrink:0;min-height:38px}\n"
    ".voice-mic-btn:hover{border-color:var(--acc)}\n"
    ".voice-mic-btn.recording{color:#fff;background:var(--rec);border-color:var(--rec)}\n"
    ".voice-mic-btn svg{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2;"
    "stroke-linecap:round;stroke-linejoin:round}\n"
    ".voice-status{display:block;font-size:12px;color:var(--mut);margin-top:4px}"
)
_VOICE_NOTICE_CSS = (
    ".voice-notice{background:var(--warn-bg);color:var(--warn-fg);border:1px solid var(--warn-line);"
    "border-radius:8px;padding:10px 12px;margin:10px 0 14px;font-size:14px}"
)

_VOICE_CLIENT_JS = r"""
(function(){
  const vcfg=PAYLOAD.voice||{};
  if(!vcfg.active||!vcfg.endpoint)return;
  const MIC_SVG='<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="2" width="6" height="11" rx="3"/><path d="M5 10a7 7 0 0 0 14 0"/><line x1="12" y1="17" x2="12" y2="22"/><line x1="8" y1="22" x2="16" y2="22"/></svg>';
  let activeRec=null;
  function resampleMono(samples,fromRate,toRate){
    if(fromRate===toRate)return samples;
    const ratio=fromRate/toRate;
    const outLen=Math.max(1,Math.round(samples.length/ratio));
    const out=new Float32Array(outLen);
    for(let i=0;i<outLen;i++){
      const pos=i*ratio;
      const idx=Math.floor(pos);
      const frac=pos-idx;
      const a=samples[idx]||0;
      const b=samples[Math.min(idx+1,samples.length-1)]||a;
      out[i]=a+(b-a)*frac;
    }
    return out;
  }
  function encodeWav16k(chunks,sampleRate){
    let total=0;
    for(const c of chunks)total+=c.length;
    const merged=new Float32Array(total);
    let offset=0;
    for(const c of chunks){merged.set(c,offset);offset+=c.length;}
    const pcm=resampleMono(merged,sampleRate,16000);
    const buf=new ArrayBuffer(44+pcm.length*2);
    const v=new DataView(buf);
    function str(o,s){for(let i=0;i<s.length;i++)v.setUint8(o+i,s.charCodeAt(i));}
    str(0,"RIFF");
    v.setUint32(4,36+pcm.length*2,true);
    str(8,"WAVE");
    str(12,"fmt ");
    v.setUint32(16,16,true);
    v.setUint16(20,1,true);
    v.setUint16(22,1,true);
    v.setUint32(24,16000,true);
    v.setUint32(28,32000,true);
    v.setUint16(32,2,true);
    v.setUint16(34,16,true);
    str(36,"data");
    v.setUint32(40,pcm.length*2,true);
    let pos=44;
    for(let i=0;i<pcm.length;i++){
      const s=Math.max(-1,Math.min(1,pcm[i]));
      v.setInt16(pos,s<0?s*0x8000:s*0x7fff,true);
      pos+=2;
    }
    return new Blob([buf],{type:"audio/wav"});
  }
  async function stopRecording(rec){
    activeRec=null;
    rec.btn.classList.remove("recording");
    rec.btn.setAttribute("aria-pressed","false");
    rec.btn.innerHTML=MIC_SVG;
    rec.status.textContent="Transkribiere lokal …";
    try{rec.proc.disconnect();rec.src.disconnect();}catch(e){}
    try{rec.stream.getTracks().forEach(t=>t.stop());}catch(e){}
    try{await rec.ctx.close();}catch(e){}
    try{
      const wav=encodeWav16k(rec.chunks,rec.sampleRate);
      const res=await fetch(vcfg.endpoint,{
        method:"POST",
        headers:{"Content-Type":"audio/wav","X-Voice-Language":vcfg.language||"de"},
        body:wav
      });
      const data=await res.json().catch(()=>({}));
      if(!res.ok||!data.ok)throw new Error(data.error||("HTTP "+res.status));
      const text=(data.text||"").trim();
      if(text){
        const cur=rec.textarea.value.trim();
        rec.textarea.value=cur?(cur+" "+text):text;
        st[rec.id]=Object.assign(st[rec.id]||{},{note:rec.textarea.value,note_source:"voice"});
        persist();
        rec.status.textContent="Transkript übernommen (editierbar).";
      }else{
        rec.status.textContent="Keine Sprache erkannt.";
      }
    }catch(err){
      rec.status.textContent="Lokale Transkription fehlgeschlagen: "+(err&&err.message?err.message:String(err));
    }
  }
  L.querySelectorAll(".note-area").forEach(area=>{
    const ta=area.querySelector("textarea");
    const controls=area.querySelector(".note-controls");
    if(!ta||!controls)return;
    const id=ta.dataset.id;
    const btn=document.createElement("button");
    btn.type="button";
    btn.className="voice-mic-btn";
    btn.dataset.voiceMic=id;
    btn.setAttribute("aria-label","Sprachnotiz aufnehmen");
    btn.setAttribute("aria-pressed","false");
    btn.title="Sprachnotiz lokal aufnehmen und transkribieren";
    btn.innerHTML=MIC_SVG;
    const status=document.createElement("span");
    status.className="voice-status";
    controls.appendChild(btn);
    area.appendChild(status);
    btn.addEventListener("click",async()=>{
      if(activeRec&&activeRec.id===id){
        await stopRecording(activeRec);
        return;
      }
      if(activeRec){
        await stopRecording(activeRec);
      }
      if(!navigator.mediaDevices||!navigator.mediaDevices.getUserMedia){
        status.textContent="Mikrofon-API im Browser nicht verfügbar; Texteingabe bleibt nutzbar.";
        return;
      }
      try{
        const stream=await navigator.mediaDevices.getUserMedia({audio:true});
        const AudioCtx=window.AudioContext||window.webkitAudioContext;
        const ctx=new AudioCtx();
        const src=ctx.createMediaStreamSource(stream);
        const proc=ctx.createScriptProcessor(4096,1,1);
        const chunks=[];
        proc.onaudioprocess=e=>{chunks.push(new Float32Array(e.inputBuffer.getChannelData(0)));};
        src.connect(proc);
        proc.connect(ctx.destination);
        activeRec={id,btn,status,textarea:ta,stream,ctx,src,proc,chunks,sampleRate:ctx.sampleRate};
        btn.classList.add("recording");
        btn.setAttribute("aria-pressed","true");
        btn.textContent="■ Stopp";
        status.textContent="Aufnahme läuft lokal … erneut klicken zum Transkribieren.";
      }catch(err){
        status.textContent="Mikrofon nicht verfügbar: "+(err&&err.message?err.message:String(err));
      }
    });
  });
})();
"""


def _nonempty_str(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def validate_loopback_endpoint(endpoint: str) -> str:
    """Reject non-loopback endpoints so audio never leaves the local machine."""
    url = _nonempty_str(endpoint, "voice.endpoint")
    parsed = urlparse(url)
    if parsed.scheme != "http" or parsed.hostname not in _LOOPBACK_HOSTS:
        raise ValueError("voice.endpoint must be an explicit HTTP loopback address (127.0.0.1, localhost, ::1)")
    if parsed.username or parsed.password or not parsed.path:
        raise ValueError("voice.endpoint must not contain credentials and needs an API path")
    return url


def validate_input_payload(payload: object) -> dict[str, Any]:
    """Validate an avatar rating input JSON object against the v1 schema."""
    if not isinstance(payload, dict):
        raise ValueError("input payload must be a JSON object")
    unexpected = set(payload) - _ALLOWED_INPUT_KEYS
    if unexpected:
        raise ValueError(f"unexpected top-level field(s): {sorted(unexpected)!r}")
    if payload.get("schema") != INPUT_SCHEMA:
        raise ValueError(f"schema must be {INPUT_SCHEMA!r}")
    run_id = _nonempty_str(payload.get("run_id"), "run_id")

    for optional_text in ("title", "description"):
        if optional_text in payload and not isinstance(payload[optional_text], str):
            raise ValueError(f"{optional_text} must be a string")

    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("entries must be a non-empty list")

    seen_ids: set[str] = set()
    normalized_entries: list[dict[str, Any]] = []
    for idx, raw_entry in enumerate(entries, 1):
        prefix = f"entries[{idx - 1}]"
        if not isinstance(raw_entry, dict):
            raise ValueError(f"{prefix} must be an object")
        extra = set(raw_entry) - _ALLOWED_ENTRY_KEYS
        if extra:
            raise ValueError(f"{prefix} has unexpected field(s): {sorted(extra)!r}")
        for required_key in ("id", "kontext", "entscheidung", "konfidenz", "ziel"):
            if required_key not in raw_entry:
                raise ValueError(f"{prefix} is missing required field {required_key!r}")
        entry_id = _nonempty_str(raw_entry["id"], f"{prefix}.id")
        if entry_id in seen_ids:
            raise ValueError(f"duplicate entry id: {entry_id!r}")
        seen_ids.add(entry_id)

        if not isinstance(raw_entry["kontext"], str):
            raise ValueError(f"{prefix}.kontext must be a string")
        entscheidung = _nonempty_str(raw_entry["entscheidung"], f"{prefix}.entscheidung")
        konfidenz = _nonempty_str(raw_entry["konfidenz"], f"{prefix}.konfidenz")
        ziel = _nonempty_str(raw_entry["ziel"], f"{prefix}.ziel")

        nr = idx
        if "nr" in raw_entry:
            raw_nr = raw_entry["nr"]
            if isinstance(raw_nr, bool) or not isinstance(raw_nr, int) or raw_nr < 1:
                raise ValueError(f"{prefix}.nr must be a positive integer")
            nr = raw_nr

        item: dict[str, Any] = {
            "nr": nr,
            "id": entry_id,
            "kontext": raw_entry["kontext"],
            "entscheidung": entscheidung,
            "konfidenz": konfidenz,
            "ziel": ziel,
        }
        if "ebene" in raw_entry:
            if not isinstance(raw_entry["ebene"], str):
                raise ValueError(f"{prefix}.ebene must be a string")
            if raw_entry["ebene"].strip():
                item["ebene"] = raw_entry["ebene"].strip()
        if "date" in raw_entry:
            validate_since(str(raw_entry["date"]))
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(raw_entry["date"])):
                raise ValueError(f"{prefix}.date must be YYYY-MM-DD")
            item["date"] = raw_entry["date"]
        normalized_entries.append(item)

    result: dict[str, Any] = {
        "schema": INPUT_SCHEMA,
        "run_id": run_id,
        "entries": normalized_entries,
    }
    if "title" in payload:
        result["title"] = payload["title"]
    if "description" in payload:
        result["description"] = payload["description"]
    return result


def validate_response_payload(payload: object) -> dict[str, Any]:
    """Validate a downloaded rating response JSON object against the v1 schema."""
    if not isinstance(payload, dict):
        raise ValueError("response payload must be a JSON object")
    unexpected = set(payload) - _ALLOWED_RESPONSE_KEYS
    if unexpected:
        raise ValueError(f"unexpected response field(s): {sorted(unexpected)!r}")
    if payload.get("schema") != RESPONSE_SCHEMA:
        raise ValueError(f"schema must be {RESPONSE_SCHEMA!r}")
    run_id = _nonempty_str(payload.get("run_id"), "run_id")
    saved_at = validate_timestamp(payload.get("saved_at"))

    ratings = payload.get("ratings")
    if not isinstance(ratings, list):
        raise ValueError("ratings must be a list")

    normalized_ratings: list[dict[str, Any]] = []
    for idx, raw_row in enumerate(ratings):
        prefix = f"ratings[{idx}]"
        if not isinstance(raw_row, dict):
            raise ValueError(f"{prefix} must be an object")
        extra = set(raw_row) - _ALLOWED_RATING_KEYS
        if extra:
            raise ValueError(f"{prefix} has unexpected field(s): {sorted(extra)!r}")
        for req in ("nr", "id", "entscheidung", "score", "note"):
            if req not in raw_row:
                raise ValueError(f"{prefix} is missing required field {req!r}")
        nr = raw_row["nr"]
        if isinstance(nr, bool) or not isinstance(nr, int) or nr < 1:
            raise ValueError(f"{prefix}.nr must be a positive integer")
        entry_id = _nonempty_str(raw_row["id"], f"{prefix}.id")
        entscheidung = _nonempty_str(raw_row["entscheidung"], f"{prefix}.entscheidung")
        score = raw_row["score"]
        if score is not None and (isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 10):
            raise ValueError(f"{prefix}.score must be null or an integer in 0..10")
        note = raw_row["note"]
        if not isinstance(note, str):
            raise ValueError(f"{prefix}.note must be a string")
        item: dict[str, Any] = {
            "nr": nr,
            "id": entry_id,
            "entscheidung": entscheidung,
            "score": score,
            "note": note,
        }
        if "note_source" in raw_row:
            if raw_row["note_source"] not in {"text", "voice"}:
                raise ValueError(f"{prefix}.note_source must be 'text' or 'voice'")
            item["note_source"] = raw_row["note_source"]
        normalized_ratings.append(item)

    return {
        "schema": RESPONSE_SCHEMA,
        "run_id": run_id,
        "saved_at": saved_at,
        "ratings": normalized_ratings,
    }


def _merge_voice_config(config: dict[str, Any] | None) -> dict[str, Any]:
    merged = copy.deepcopy(DEFAULT_VOICE_CONFIG)
    if config is None:
        return merged
    if not isinstance(config, dict):
        raise ValueError("config must be a JSON object")
    raw_voice = config.get("voice", {})
    if raw_voice is None:
        raw_voice = {}
    if not isinstance(raw_voice, dict):
        raise ValueError("config.voice must be an object")
    if "enabled" in raw_voice and not isinstance(raw_voice["enabled"], bool):
        raise ValueError("config.voice.enabled must be a boolean")
    merged.update(raw_voice)
    return merged


def probe_voice_module(voice_cfg: dict[str, Any]) -> dict[str, Any]:
    """Read-only probe for local ``ellmos-voice-io`` and STT engine availability."""
    provider = str(voice_cfg.get("provider") or "ellmos-voice-io").strip()
    if provider != "ellmos-voice-io":
        return {
            "installed": False,
            "stt_available": False,
            "stt_engine": "",
            "reason": f"Voice-Provider '{provider}' wird nicht unterstützt (erwartet 'ellmos-voice-io').",
        }

    if importlib.util.find_spec("ellmos_voice_io") is not None:
        try:
            from ellmos_voice_io import VoiceIO  # type: ignore[import-not-found]

            status = VoiceIO().status().as_dict()
            stt_ok = bool(status.get("stt_available"))
            stt_engine = str(status.get("stt_engine") or "")
            return {
                "installed": True,
                "stt_available": stt_ok,
                "stt_engine": stt_engine,
                "reason": "" if stt_ok else f"ellmos-voice-io installiert, aber STT fehlt ({stt_engine}).",
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "installed": False,
                "stt_available": False,
                "stt_engine": "",
                "reason": f"ellmos-voice-io-Statusprüfung fehlgeschlagen: {exc}",
            }

    python_exe = str(voice_cfg.get("python_executable") or "").strip()
    if python_exe and Path(python_exe).is_file():
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        proc = subprocess.run(
            [python_exe, "-m", "ellmos_voice_io.cli", "status"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=10,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            try:
                status = json.loads(proc.stdout)
                stt_ok = bool(status.get("stt_available"))
                stt_engine = str(status.get("stt_engine") or "")
                return {
                    "installed": True,
                    "stt_available": stt_ok,
                    "stt_engine": stt_engine,
                    "reason": "" if stt_ok else f"ellmos-voice-io installiert, aber STT fehlt ({stt_engine}).",
                }
            except json.JSONDecodeError:
                pass

    return {
        "installed": False,
        "stt_available": False,
        "stt_engine": "",
        "reason": "Modul 'ellmos-voice-io' ist in dieser Python-Umgebung nicht installiert.",
    }


def resolve_voice_state(
    config: dict[str, Any] | None = None,
    *,
    voice_probe: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compute effective runtime state for optional local voice input."""
    voice_cfg = _merge_voice_config(config)
    enabled = bool(voice_cfg["enabled"])
    provider = str(voice_cfg["provider"] or "ellmos-voice-io").strip()
    language = str(voice_cfg.get("language") or "de").strip() or "de"

    if not enabled:
        return {
            "enabled": False,
            "active": False,
            "available": False,
            "provider": provider,
            "endpoint": "",
            "language": language,
            "notice": "",
        }

    endpoint = validate_loopback_endpoint(str(voice_cfg["endpoint"]))
    probe_fn = voice_probe or probe_voice_module
    probe = probe_fn(voice_cfg)
    installed = bool(probe.get("installed"))
    stt_available = bool(probe.get("stt_available"))
    active = installed and stt_available

    notice = ""
    if not active:
        detail = str(probe.get("reason") or "Lokales Sprachmodul nicht verfügbar.").strip()
        notice = (
            f"Spracheingabe ist in der Konfiguration aktiviert, aber {detail} "
            "Mikrofonsymbole bleiben ausgeblendet; die Bewertungsseite funktioniert unverändert."
        )

    return {
        "enabled": True,
        "active": active,
        "available": active,
        "provider": provider,
        "endpoint": endpoint if active else "",
        "language": language,
        "notice": notice,
    }


def render_rating_html(
    input_payload: dict[str, Any],
    config: dict[str, Any] | None = None,
    *,
    template_path: Path | None = None,
    voice_probe: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> str:
    """Render the standalone rating HTML document from validated input and config."""
    validated = validate_input_payload(input_payload)
    voice_state = resolve_voice_state(config, voice_probe=voice_probe)

    tpl_file = template_path or DEFAULT_TEMPLATE_PATH
    template = tpl_file.read_text(encoding="utf-8")

    page_title = validated.get("title") or "Avatar-Entscheidungen bewerten"
    payload_for_page = {
        "run_id": validated["run_id"],
        "title": page_title,
        "description": validated.get("description") or "",
        "entries": validated["entries"],
        "voice": voice_state,
    }
    json_blob = json.dumps(payload_for_page, ensure_ascii=False).replace("</", "<\\/")

    notice_html = ""
    notice_css = ""
    if voice_state["enabled"] and not voice_state["active"] and voice_state["notice"]:
        notice_html = f'<div class="voice-notice" role="status">{html.escape(voice_state["notice"])}</div>'
        notice_css = _VOICE_NOTICE_CSS

    voice_css = _VOICE_CSS if voice_state["active"] else ""
    voice_script = _VOICE_CLIENT_JS if voice_state["active"] else ""

    rendered = template.replace("__PAGE_TITLE__", html.escape(page_title))
    rendered = rendered.replace("__VOICE_NOTICE_CSS__", notice_css)
    rendered = rendered.replace("__VOICE_CSS__", voice_css)
    rendered = rendered.replace("__VOICE_NOTICE__", notice_html)
    rendered = rendered.replace("__RATING_PAYLOAD__", json_blob)
    rendered = rendered.replace("__VOICE_SCRIPT__", voice_script)
    return rendered


def load_config(config_path: Path | None = None, *, search_dir: Path | None = None) -> dict[str, Any] | None:
    """Load an explicit config file or optional ``config.local.json`` in ``search_dir``."""
    target: Path | None = config_path
    if target is None and search_dir is not None:
        candidate = search_dir / "config.local.json"
        if candidate.is_file():
            target = candidate
    if target is None:
        return None
    if not target.is_file():
        raise ValueError(f"config file does not exist: {target}")
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read config file {target}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("config must be a JSON object")
    return data


def _score_to_verdict(score: int) -> str:
    if score >= 7:
        return "👍 confirmed"
    if score >= 4:
        return "✋ corrected"
    return "⛔ rejected"


def response_to_feedback_markdown(
    response_payload: dict[str, Any],
    *,
    feedback_date: str | None = None,
) -> str:
    """Convert a validated rating response JSON into ``score_predictions.py`` Markdown."""
    validated = validate_response_payload(response_payload)
    date_str = validate_since(feedback_date) if feedback_date else validated["saved_at"][:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str):
        raise ValueError("feedback date must be YYYY-MM-DD")

    lines = [
        f"# WHAT USER SAID ABOUT {validated['run_id']}",
        "",
        f"> Imported from `{RESPONSE_SCHEMA}` (`saved_at: {validated['saved_at']}`).",
        "",
    ]
    rated_count = 0
    for item in validated["ratings"]:
        score = item["score"]
        if score is None:
            continue
        rated_count += 1
        verdict = _score_to_verdict(score)
        lines.append(f"## [{date_str}] {item['id']} — verdict: {verdict}")
        lines.append(f"- Score: {score}/10 | Decision: {item['entscheidung']}")
        if item["note"].strip():
            lines.append(f"- Note: {item['note'].strip()}")
        lines.append("")
    if rated_count == 0:
        lines.append("_(no rated entries in response)_")
        lines.append("")
    return "\n".join(lines)


def _transcribe_wav_bytes(wav_bytes: bytes, voice_cfg: dict[str, Any], language: str) -> str:
    if not wav_bytes:
        raise ValueError("audio body must not be empty")
    engine = str(voice_cfg.get("engine") or "auto").strip() or "auto"
    model_path = str(voice_cfg.get("model_path") or "").strip() or None

    if importlib.util.find_spec("ellmos_voice_io") is not None:
        from ellmos_voice_io import SpeechToText, VoiceIO  # type: ignore[import-not-found]

        stt = SpeechToText(engine=engine, model_path=model_path)
        return VoiceIO(stt=stt).transcribe_bytes(wav_bytes, suffix=".wav", language=language)

    python_exe = str(voice_cfg.get("python_executable") or "").strip()
    if python_exe and Path(python_exe).is_file():
        import tempfile

        with tempfile.TemporaryDirectory(prefix="byum-voice-") as tmp_dir:
            wav_path = Path(tmp_dir) / "input.wav"
            wav_path.write_bytes(wav_bytes)
            script = (
                "import sys; from ellmos_voice_io import SpeechToText; "
                "stt = SpeechToText(engine=sys.argv[1], model_path=sys.argv[2] or None); "
                "print(stt.transcribe_file(sys.argv[3], language=sys.argv[4]))"
            )
            env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
            proc = subprocess.run(
                [python_exe, "-c", script, engine, model_path or "", str(wav_path), language],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
                timeout=60,
                check=False,
            )
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.strip() or "voice transcription subprocess failed")
            return proc.stdout.strip()

    raise RuntimeError("ellmos-voice-io is not installed in the configured Python runtime")


def serve_rating_bridge(
    *,
    config: dict[str, Any] | None = None,
    html_path: Path | None = None,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> None:
    """Run a strict loopback-only HTTP bridge for local ``ellmos-voice-io`` STT."""
    if host not in _LOOPBACK_HOSTS:
        raise ValueError("bridge host must be a loopback address (127.0.0.1, localhost, ::1)")
    voice_cfg = _merge_voice_config(config)
    page_bytes = html_path.read_bytes() if html_path and html_path.is_file() else None

    class BridgeHandler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:  # noqa: A002
            return

        def _cors_headers(self) -> None:
            origin = (self.headers.get("Origin") or "").strip()
            if origin == "null":
                self.send_header("Access-Control-Allow-Origin", "null")
            elif origin:
                parsed = urlparse(origin)
                if parsed.hostname in _LOOPBACK_HOSTS:
                    self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Voice-Language")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

        def _send_json(self, data: dict[str, Any], status: int = 200) -> None:
            raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self._cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)

        def do_OPTIONS(self) -> None:  # noqa: N802
            self.send_response(204)
            self._cors_headers()
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path == "/health":
                self._send_json({"ok": True, "voice": resolve_voice_state(config)})
                return
            if path == "/" and page_bytes is not None:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(page_bytes)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(page_bytes)
                return
            self._send_json({"ok": False, "error": "not found"}, status=404)

        def do_POST(self) -> None:  # noqa: N802
            if urlparse(self.path).path != "/transcribe":
                self._send_json({"ok": False, "error": "not found"}, status=404)
                return
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                self._send_json({"ok": False, "error": "invalid Content-Length"}, status=400)
                return
            if length <= 0 or length > _MAX_AUDIO_BYTES:
                self._send_json({"ok": False, "error": "audio payload size out of bounds"}, status=400)
                return
            wav_bytes = self.rfile.read(length)
            lang = (self.headers.get("X-Voice-Language") or str(voice_cfg.get("language") or "de")).strip()
            try:
                text = _transcribe_wav_bytes(wav_bytes, voice_cfg, lang)
            except Exception as exc:  # noqa: BLE001
                self._send_json({"ok": False, "error": str(exc)}, status=500)
                return
            self._send_json({"ok": True, "text": text})

    server = ThreadingHTTPServer((host, port), BridgeHandler)
    print(f"BYUM local voice bridge listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Render standalone rating HTML from input JSON")
    p_build.add_argument("--input", required=True, help="Input JSON matching avatar-rating-input.schema.json")
    p_build.add_argument("--out", required=True, help="Output HTML file path")
    p_build.add_argument("--config", default="", help="Optional config JSON (defaults to config.local.json if present)")
    p_build.add_argument("--template", default="", help="Optional custom HTML template path")

    p_import = sub.add_parser("import-feedback", help="Convert rating response JSON to WHAT-USER-SAID-ABOUT Markdown")
    p_import.add_argument("--response", required=True, help="Response JSON downloaded from the rating page")
    p_import.add_argument("--out", default="", help="Write Markdown feedback to this file instead of stdout")
    p_import.add_argument("--date", default="", help="Override feedback date (YYYY-MM-DD)")

    p_serve = sub.add_parser("serve", help="Run loopback-only local ellmos-voice-io transcription bridge")
    p_serve.add_argument("--config", default="", help="Optional config JSON")
    p_serve.add_argument("--html", default="", help="Optional rendered rating HTML to serve at '/'")
    p_serve.add_argument("--host", default="127.0.0.1", help="Loopback bind host (default: 127.0.0.1)")
    p_serve.add_argument("--port", type=int, default=8765, help="Loopback bind port (default: 8765)")

    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            input_path = Path(args.input).expanduser()
            payload = json.loads(input_path.read_text(encoding="utf-8"))
            cfg_path = Path(args.config).expanduser() if args.config else None
            cfg = load_config(cfg_path, search_dir=REPO_ROOT if cfg_path is None else None)
            tpl = Path(args.template).expanduser() if args.template else None
            rendered = render_rating_html(payload, cfg, template_path=tpl)
            atomic_write_text(Path(args.out).expanduser(), rendered)
            return 0

        if args.command == "import-feedback":
            resp_path = Path(args.response).expanduser()
            resp_payload = json.loads(resp_path.read_text(encoding="utf-8"))
            md = response_to_feedback_markdown(resp_payload, feedback_date=args.date or None)
            if args.out:
                atomic_write_text(Path(args.out).expanduser(), md)
            else:
                print(md)
            return 0

        if args.command == "serve":
            cfg_path = Path(args.config).expanduser() if args.config else None
            cfg = load_config(cfg_path, search_dir=REPO_ROOT if cfg_path is None else None)
            html_file = Path(args.html).expanduser() if args.html else None
            serve_rating_bridge(config=cfg, html_path=html_file, host=args.host, port=args.port)
            return 0
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
