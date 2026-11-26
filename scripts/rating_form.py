#!/usr/bin/env python3
"""Render, prefilter, serve, and import feedback from the generic avatar rating form.

Generates a standalone light/dark HTML rating page (with split-screen dictation
mode as default plus switchable per-card rating mode) from a schema-validated JSON
input file, prefilters contextless or already-resolved items via live readback,
gates optional local voice input (`ellmos-voice-io`) behind config and module
availability, and converts downloaded rating responses into the existing Markdown
feedback format consumed by ``score_predictions.py``.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import threading
import urllib.request
from collections.abc import Iterable
from datetime import datetime, timezone
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
DEFAULT_PREFILTER_CONFIG: dict[str, Any] = {
    "enabled": True,
    "tickets_root": "",
    "decisions_index": "",
    "decided_and_done": "",
    "resolved_ids": [],
}
_ALLOWED_INPUT_KEYS = {"schema", "run_id", "title", "description", "entries"}
_ALLOWED_ENTRY_KEYS = {
    "nr",
    "id",
    "kontext",
    "entscheidung",
    "konfidenz",
    "ziel",
    "ebene",
    "date",
    "ticket_id",
    "decision_id",
}
_ALLOWED_RESPONSE_KEYS = {"schema", "run_id", "saved_at", "mode", "dictation", "dictation_source", "ratings"}
_ALLOWED_RATING_KEYS = {"nr", "id", "entscheidung", "score", "note", "note_source"}
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
_MAX_AUDIO_BYTES = 15 * 1024 * 1024
_MAX_DICTATION_CHARS = 500_000

_TICKET_ID_RE = re.compile(r"\b(T-\d{4,8}-[A-Za-z0-9_-]+)\b")
_DECISION_ID_RE = re.compile(r"\b(D-\d{8}-\d{2,4}(?:-[A-Za-z0-9]+)*)\b")
_DECIDED_HEADING_RE = re.compile(
    r"^(?:#{1,4}\s+|ID\s*:\s*)(D-\d{8}-\d{2,4}(?:-[A-Za-z0-9]+)*|[A-Za-z]+-\d+[A-Za-z0-9_-]*)\b",
    re.IGNORECASE,
)
_PLACEHOLDER_VALUES = {
    "",
    "-",
    "--",
    "—",
    "–",
    "?",
    "???",
    "...",
    "…",
    "n/a",
    "na",
    "none",
    "null",
    "tbd",
    "todo",
    "offen",
    "open",
    "unklar",
    "missing",
    "kein kontext",
    "(kein kontext)",
    "hier eintragen",
}
_PLACEHOLDER_CHOICE_RE = re.compile(r"^[a-d](?:\s*[/|]\s*[a-d])+$", re.IGNORECASE)
_RESOLVED_DECISION_STATUSES = {
    "done",
    "archiviert",
    "archived",
    "resolved",
    "closed",
    "decided",
    "erledigt",
    "entschieden_umsetzung_offen",
}
_OPEN_DECISION_STATUSES = {"offen", "open", "pending", "active"}

_VOICE_CSS = (
    ".voice-mic-btn{background:transparent;color:var(--acc);border:1px solid var(--line);"
    "border-radius:6px;padding:6px 10px;display:inline-flex;align-items:center;justify-content:center;"
    "gap:4px;flex-shrink:0;min-height:44px;min-width:44px}\n"
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
  // One MediaStream for the whole page: re-calling getUserMedia per click re-prompts
  // wherever the browser does not persist the grant (e.g. Edge on file://).
  let sharedStream=null;
  async function micStream(){
    if(sharedStream&&sharedStream.getAudioTracks().some(t=>t.readyState==="live"))return sharedStream;
    sharedStream=await navigator.mediaDevices.getUserMedia({audio:true});
    return sharedStream;
  }
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
        if(rec.isMainDictation){
          dictationText=rec.textarea.value;
          dictationSource="voice";
          updateDictationCounts();
        }else{
          st[rec.id]=Object.assign(st[rec.id]||{},{note:rec.textarea.value,note_source:"voice"});
        }
        persist();
        rec.status.textContent="Transkript übernommen (editierbar).";
      }else{
        rec.status.textContent="Keine Sprache erkannt.";
      }
    }catch(err){
      rec.status.textContent="Lokale Transkription fehlgeschlagen: "+(err&&err.message?err.message:String(err));
    }
  }
  document.querySelectorAll(".note-area").forEach(area=>{
    const ta=area.querySelector("textarea");
    const controls=area.querySelector(".note-controls");
    if(!ta||!controls)return;
    const isMainDictation=ta.dataset.dictation==="main";
    const id=isMainDictation?"__dictation__":ta.dataset.id;
    if(!id)return;
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
        const stream=await micStream();
        const AudioCtx=window.AudioContext||window.webkitAudioContext;
        const ctx=new AudioCtx();
        const src=ctx.createMediaStreamSource(stream);
        const proc=ctx.createScriptProcessor(4096,1,1);
        const chunks=[];
        proc.onaudioprocess=e=>{chunks.push(new Float32Array(e.inputBuffer.getChannelData(0)));};
        src.connect(proc);
        proc.connect(ctx.destination);
        activeRec={id,isMainDictation,btn,status,textarea:ta,stream,ctx,src,proc,chunks,sampleRate:ctx.sampleRate};
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


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001, D102
        return None  # a 3xx becomes an HTTPError instead of being followed


# Loopback STT calls must never go through http_proxy/HTTPS_PROXY or follow redirects:
# either would let audio or the transcript leave/enter from outside the loopback contract.
_LOOPBACK_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect)


def _has_meaningful_text(value: object, *, min_chars: int) -> bool:
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    if len(stripped) < min_chars:
        return False
    lowered = stripped.lower()
    if lowered in _PLACEHOLDER_VALUES or _PLACEHOLDER_CHOICE_RE.fullmatch(lowered):
        return False
    alnum_count = sum(1 for ch in stripped if ch.isalnum())
    return alnum_count >= 2


def _collect_ticket_sets(tickets_root: Path | str | None) -> tuple[dict[str, str], set[str]]:
    """Scan ``tickets_root`` for resolved (``SOLVED``/``DONE``) and active ticket IDs."""
    resolved: dict[str, str] = {}
    open_ids: set[str] = set()
    if not tickets_root:
        return resolved, open_ids
    root = Path(tickets_root).expanduser()
    if not root.is_dir():
        return resolved, open_ids

    for child in root.iterdir():
        if not child.is_dir():
            continue
        bucket = child.name.upper()
        if bucket in {"SOLVED", "DONE"}:
            for item in child.rglob("*"):
                if not item.is_file():
                    continue
                rel = f"{child.name}/{item.relative_to(child).as_posix()}"
                stem = item.stem.strip()
                if stem:
                    resolved.setdefault(stem.upper(), rel)
                    prefix = stem.split("_", 1)[0].strip()
                    if prefix:
                        resolved.setdefault(prefix.upper(), rel)
                for match in _TICKET_ID_RE.findall(item.name):
                    resolved.setdefault(match.upper(), rel)
        elif bucket in {"OPEN", "USER", "IN_PROGRESS", "ACTIVE"}:
            for item in child.rglob("*"):
                if not item.is_file():
                    continue
                stem = item.stem.strip()
                if stem:
                    open_ids.add(stem.upper())
                    prefix = stem.split("_", 1)[0].strip()
                    if prefix:
                        open_ids.add(prefix.upper())
                for match in _TICKET_ID_RE.findall(item.name):
                    open_ids.add(match.upper())
    return resolved, open_ids


def _parse_decided_markdown(md_path: Path, resolved: dict[str, str]) -> None:
    if not md_path.is_file():
        return
    try:
        text = md_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return
    label = md_path.name
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        heading_match = _DECIDED_HEADING_RE.match(line)
        if heading_match:
            resolved.setdefault(heading_match.group(1).upper(), label)


def _ingest_decisions_object(data: object, source_label: str, resolved: dict[str, str], open_ids: set[str]) -> None:
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        if isinstance(data.get("entries"), list):
            entries = data["entries"]
        elif isinstance(data.get("decisions"), list):
            entries = data["decisions"]
        else:
            # Support compact mapping {"D-20261101-001": "DONE", ...}
            for key, val in data.items():
                if not isinstance(key, str) or key in {"schema", "generated_at", "generator", "root", "counts"}:
                    continue
                status_str = ""
                domain_str = ""
                if isinstance(val, str):
                    status_str = val.strip().lower()
                elif isinstance(val, dict):
                    status_str = str(val.get("status_class") or val.get("status") or "").strip().lower()
                    domain_str = str(val.get("domain") or "").strip().lower()
                norm_id = key.strip().upper()
                if status_str in _OPEN_DECISION_STATUSES or (domain_str == "active" and not status_str):
                    open_ids.add(norm_id)
                elif status_str in _RESOLVED_DECISION_STATUSES or domain_str in {"done", "archive"}:
                    resolved.setdefault(norm_id, f"{source_label} ({status_str or domain_str})")
            return
    else:
        return

    active_open: set[str] = set()
    candidate_resolved: dict[str, str] = {}
    for row in entries:
        if not isinstance(row, dict):
            continue
        raw_id = str(row.get("id") or "").strip()
        if not raw_id:
            continue
        norm_id = raw_id.upper()
        domain = str(row.get("domain") or "").strip().lower()
        status_class = str(row.get("status_class") or row.get("status") or "").strip().lower()
        status_raw = str(row.get("status_raw") or "").strip().lower()
        decision_ready = row.get("decision_ready")

        is_open = (
            decision_ready is True
            or status_class in _OPEN_DECISION_STATUSES
            or (domain == "active" and status_class not in _RESOLVED_DECISION_STATUSES and not row.get("has_decision"))
        )
        is_done = (
            domain in {"done", "archive"}
            or status_class in _RESOLVED_DECISION_STATUSES
            or any(status_raw.startswith(tok) for tok in ("done", "erledigt", "resolved", "archiviert", "closed"))
            or bool(row.get("has_decision"))
        )
        if is_open and not is_done:
            active_open.add(norm_id)
        elif is_done:
            tag = status_class or domain or "done"
            candidate_resolved.setdefault(norm_id, f"{source_label} ({tag})")

    open_ids.update(active_open)
    for dec_id, detail in candidate_resolved.items():
        if dec_id not in active_open:
            resolved.setdefault(dec_id, detail)


def _collect_decision_sets(
    decisions_index: Path | str | dict[str, Any] | list[dict[str, Any]] | None,
    decided_and_done: Path | str | None,
) -> tuple[dict[str, str], set[str]]:
    """Collect resolved and open decision IDs from index JSON and/or ``DECIDED-AND-DONE`` Markdown."""
    resolved: dict[str, str] = {}
    open_ids: set[str] = set()

    if isinstance(decisions_index, (dict, list)):
        _ingest_decisions_object(decisions_index, "decisions_index", resolved, open_ids)
    elif isinstance(decisions_index, (str, Path)) and str(decisions_index).strip():
        idx_path = Path(decisions_index).expanduser()
        if idx_path.is_dir():
            for rel_json in ("_tools/decisions.index.json", "decisions.index.json"):
                cand = idx_path / rel_json
                if cand.is_file():
                    try:
                        _ingest_decisions_object(
                            json.loads(cand.read_text(encoding="utf-8")),
                            cand.name,
                            resolved,
                            open_ids,
                        )
                    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                        pass
            _parse_decided_markdown(idx_path / "DECIDED-AND-DONE.md", resolved)
        elif idx_path.is_file():
            if idx_path.suffix.lower() == ".json":
                data = json.loads(idx_path.read_text(encoding="utf-8"))
                _ingest_decisions_object(data, idx_path.name, resolved, open_ids)
            else:
                _parse_decided_markdown(idx_path, resolved)

    if isinstance(decided_and_done, (str, Path)) and str(decided_and_done).strip():
        _parse_decided_markdown(Path(decided_and_done).expanduser(), resolved)

    for open_id in list(open_ids):
        resolved.pop(open_id, None)
    return resolved, open_ids


def prefilter_items(
    entries: list[dict[str, Any]],
    *,
    tickets_root: Path | str | None = None,
    decisions_index: Path | str | dict[str, Any] | list[dict[str, Any]] | None = None,
    decided_and_done: Path | str | None = None,
    resolved_ids: Iterable[str] | None = None,
    is_resolved: Callable[[dict[str, Any]], str | bool | None] | None = None,
    min_context_chars: int = 5,
    min_decision_chars: int = 3,
) -> dict[str, Any]:
    """Filter rating entries before HTML generation via static quality checks and live readback.

    Drops:
    1. Entries without genuine context (``missing_context``) or without an evaluable
       avatar statement/decision (``missing_decision``).
    2. Entries whose own ID, explicit ``ticket_id``/``decision_id``, or referenced
       ticket/decision token is already resolved in ``tickets_root`` (``SOLVED/`` or
       ``DONE/``), ``decisions_index`` / ``DECIDED-AND-DONE``, ``resolved_ids``, or
       ``is_resolved(entry)``.

    Returns ``{"kept": [...], "filtered_out": [...], "counts": {...}}``.
    """
    if not isinstance(entries, list):
        raise ValueError("entries must be a list")

    explicit_resolved = {str(x).strip().upper() for x in (resolved_ids or ()) if str(x).strip()}
    resolved_tickets, open_tickets = _collect_ticket_sets(tickets_root)
    resolved_decisions, open_decisions = _collect_decision_sets(decisions_index, decided_and_done)

    kept: list[dict[str, Any]] = []
    filtered_out: list[dict[str, Any]] = []

    def _record_drop(entry: dict[str, Any], idx: int, reason: str, detail: str) -> None:
        filtered_out.append(
            {
                "id": str(entry.get("id") or f"entry-{idx}"),
                "nr": entry.get("nr", idx),
                "reason": reason,
                "detail": detail,
                "entry": copy.deepcopy(entry),
            }
        )

    for idx, raw_entry in enumerate(entries, 1):
        if not isinstance(raw_entry, dict):
            filtered_out.append(
                {
                    "id": f"entry-{idx}",
                    "nr": idx,
                    "reason": "invalid_entry",
                    "detail": "Entry is not an object.",
                    "entry": raw_entry,
                }
            )
            continue

        kontext = raw_entry.get("kontext")
        if not _has_meaningful_text(kontext, min_chars=min_context_chars):
            _record_drop(raw_entry, idx, "missing_context", "Kein belastbarer Kontext vorhanden.")
            continue

        entscheidung = raw_entry.get("entscheidung")
        if not _has_meaningful_text(entscheidung, min_chars=min_decision_chars):
            _record_drop(raw_entry, idx, "missing_decision", "Keine bewertbare Avatar-Entscheidung vorhanden.")
            continue

        entry_id = str(raw_entry.get("id") or "").strip()
        norm_entry_id = entry_id.upper()
        explicit_ticket = str(raw_entry.get("ticket_id") or "").strip().upper()
        explicit_decision = str(raw_entry.get("decision_id") or "").strip().upper()

        direct_ids = [x for x in (norm_entry_id, explicit_ticket, explicit_decision) if x]
        if any(x in explicit_resolved for x in direct_ids):
            matched = next(x for x in direct_ids if x in explicit_resolved)
            _record_drop(raw_entry, idx, "resolved_id", f"ID {matched} ist als bereits erledigt markiert.")
            continue

        if explicit_ticket and explicit_ticket in resolved_tickets:
            _record_drop(
                raw_entry,
                idx,
                "ticket_resolved",
                f"Ticket {explicit_ticket} liegt bereits in {resolved_tickets[explicit_ticket]}.",
            )
            continue
        if norm_entry_id and norm_entry_id in resolved_tickets:
            _record_drop(
                raw_entry,
                idx,
                "ticket_resolved",
                f"Ticket {entry_id} liegt bereits in {resolved_tickets[norm_entry_id]}.",
            )
            continue

        if explicit_decision and explicit_decision in resolved_decisions:
            _record_drop(
                raw_entry,
                idx,
                "decision_resolved",
                f"Entscheidung {explicit_decision} ist bereits abgeschlossen ({resolved_decisions[explicit_decision]}).",
            )
            continue
        if norm_entry_id and norm_entry_id in resolved_decisions:
            _record_drop(
                raw_entry,
                idx,
                "decision_resolved",
                f"Entscheidung {entry_id} ist bereits abgeschlossen ({resolved_decisions[norm_entry_id]}).",
            )
            continue

        # Unless the item's own primary ID is explicitly known to be an open ticket or open decision,
        # also inspect ticket/decision tokens referenced inside id/ziel/kontext.
        primary_known_open = norm_entry_id in open_tickets or norm_entry_id in open_decisions
        if not primary_known_open:
            haystack = " ".join(
                str(raw_entry.get(field) or "") for field in ("id", "ticket_id", "decision_id", "ziel", "kontext")
            )
            ref_tickets = [m.upper() for m in _TICKET_ID_RE.findall(haystack)]
            ref_decisions = [m.upper() for m in _DECISION_ID_RE.findall(haystack)]

            hit_resolved_tok = next((t for t in (*ref_tickets, *ref_decisions) if t in explicit_resolved), None)
            if hit_resolved_tok:
                _record_drop(
                    raw_entry,
                    idx,
                    "resolved_id",
                    f"Referenz {hit_resolved_tok} ist als bereits erledigt markiert.",
                )
                continue

            hit_ticket = next((t for t in ref_tickets if t in resolved_tickets and t not in open_tickets), None)
            if hit_ticket:
                _record_drop(
                    raw_entry,
                    idx,
                    "ticket_resolved",
                    f"Referenziertes Ticket {hit_ticket} liegt bereits in {resolved_tickets[hit_ticket]}.",
                )
                continue

            hit_decision = next((d for d in ref_decisions if d in resolved_decisions and d not in open_decisions), None)
            if hit_decision:
                _record_drop(
                    raw_entry,
                    idx,
                    "decision_resolved",
                    f"Referenzierte Entscheidung {hit_decision} ist bereits abgeschlossen ({resolved_decisions[hit_decision]}).",
                )
                continue

        if is_resolved is not None:
            verdict = is_resolved(raw_entry)
            if verdict:
                detail = verdict if isinstance(verdict, str) else f"Posten {entry_id or idx} durch Readback-Callback ausgefiltert."
                _record_drop(raw_entry, idx, "custom_resolved", detail)
                continue

        kept.append(copy.deepcopy(raw_entry))

    return {
        "kept": kept,
        "filtered_out": filtered_out,
        "counts": {
            "input": len(entries),
            "kept": len(kept),
            "filtered_out": len(filtered_out),
        },
    }


prefilter_entries = prefilter_items


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
        for opt_str_key in ("ebene", "ticket_id", "decision_id"):
            if opt_str_key in raw_entry:
                if not isinstance(raw_entry[opt_str_key], str):
                    raise ValueError(f"{prefix}.{opt_str_key} must be a string")
                if raw_entry[opt_str_key].strip():
                    item[opt_str_key] = raw_entry[opt_str_key].strip()
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

    result: dict[str, Any] = {
        "schema": RESPONSE_SCHEMA,
        "run_id": run_id,
        "saved_at": saved_at,
        "ratings": normalized_ratings,
    }
    if "mode" in payload:
        if payload["mode"] not in {"dictation", "cards"}:
            raise ValueError("mode must be 'dictation' or 'cards'")
        result["mode"] = payload["mode"]
    if "dictation" in payload:
        if not isinstance(payload["dictation"], str) or len(payload["dictation"]) > _MAX_DICTATION_CHARS:
            raise ValueError(f"dictation must be a string (max {_MAX_DICTATION_CHARS} chars)")
        result["dictation"] = payload["dictation"]
    if "dictation_source" in payload:
        if payload["dictation_source"] not in {"text", "voice"}:
            raise ValueError("dictation_source must be 'text' or 'voice'")
        result["dictation_source"] = payload["dictation_source"]
    return result


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


def _merge_prefilter_config(config: dict[str, Any] | None) -> dict[str, Any]:
    merged = copy.deepcopy(DEFAULT_PREFILTER_CONFIG)
    if config is None:
        return merged
    if not isinstance(config, dict):
        raise ValueError("config must be a JSON object")
    raw_pf = config.get("prefilter", {})
    if raw_pf is None:
        raw_pf = {}
    if not isinstance(raw_pf, dict):
        raise ValueError("config.prefilter must be an object")
    if "enabled" in raw_pf and not isinstance(raw_pf["enabled"], bool):
        raise ValueError("config.prefilter.enabled must be a boolean")
    merged.update(raw_pf)
    return merged


def probe_voice_module(voice_cfg: dict[str, Any]) -> dict[str, Any]:
    """Read-only probe for local ``ellmos-voice-io`` and STT engine availability."""
    if str(voice_cfg.get("engine") or "").strip() == "remote":
        # Loopback only (zero-egress): an operator may tunnel this port to a bigger STT host.
        remote = urlparse(validate_loopback_endpoint(str(voice_cfg.get("remote_url") or "")))
        try:
            with _LOOPBACK_OPENER.open(f"{remote.scheme}://{remote.netloc}/health", timeout=3) as resp:
                ok = bool(json.loads(resp.read().decode("utf-8")).get("ok"))
        except (OSError, ValueError) as exc:
            return {"installed": False, "stt_available": False, "stt_engine": "remote",
                    "reason": f"Remote-STT-Dienst nicht erreichbar ({exc})."}
        return {"installed": ok, "stt_available": ok, "stt_engine": "remote",
                "reason": "" if ok else "Remote-STT-Dienst meldet keinen Bereitschaftsstatus."}
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


_RUN_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_STATE_ENTRY_KEYS = {"s", "note", "note_source"}
_MAX_STATE_BYTES = 2 * 1024 * 1024
STORE_HISTORY = 20
DEFAULT_RATINGS_DIR = Path.home() / ".byum" / "ratings"


def validate_rating_state(state: object) -> dict[str, Any]:
    """Validate the page's in-browser rating state ``{entry_id: {s, note, note_source}}``."""
    if not isinstance(state, dict):
        raise ValueError("state must be an object")
    for key, value in state.items():
        if not isinstance(key, str) or not key or len(key) > 200:
            raise ValueError("state keys must be non-empty strings (max 200 chars)")
        if not isinstance(value, dict) or set(value) - _STATE_ENTRY_KEYS:
            raise ValueError(f"state[{key!r}] must be an object with s/note/note_source only")
        score = value.get("s")
        if score is not None and (isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 10):
            raise ValueError(f"state[{key!r}].s must be null or an integer in 0..10")
        if "note" in value and (not isinstance(value["note"], str) or len(value["note"]) > 20000):
            raise ValueError(f"state[{key!r}].note must be a string (max 20000 chars)")
        if "note_source" in value and value["note_source"] not in {"text", "voice"}:
            raise ValueError(f"state[{key!r}].note_source must be 'text' or 'voice'")
    return state


def store_rating_state(
    ratings_dir: Path,
    run_id: str,
    state: object,
    *,
    dictation: object = None,
) -> dict[str, Any]:
    """Atomically write ``<run_id>.json`` with the new state and the previous ``STORE_HISTORY`` versions."""
    if not _RUN_ID_RE.fullmatch(run_id):
        raise ValueError("invalid run_id")
    validated = validate_rating_state(state)
    if dictation is not None and (not isinstance(dictation, str) or len(dictation) > _MAX_DICTATION_CHARS):
        raise ValueError(f"dictation must be a string (max {_MAX_DICTATION_CHARS} chars)")
    path = ratings_dir / f"{run_id}.json"
    current = load_rating_state(ratings_dir, run_id)
    history = list(current.get("history") or [])
    if current.get("state") is not None:
        hist_entry: dict[str, Any] = {"saved_at": current["saved_at"], "state": current["state"]}
        if "dictation" in current and current["dictation"] is not None:
            hist_entry["dictation"] = current["dictation"]
        history.insert(0, hist_entry)
    record: dict[str, Any] = {
        "schema": "byum.avatar-rating-store.v1",
        "run_id": run_id,
        "saved_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "state": validated,
        "history": history[:STORE_HISTORY],
    }
    effective_dictation = dictation if dictation is not None else current.get("dictation")
    if effective_dictation is not None:
        record["dictation"] = effective_dictation
    atomic_write_text(path, json.dumps(record, ensure_ascii=False, indent=1))
    return record


def load_rating_state(ratings_dir: Path, run_id: str) -> dict[str, Any]:
    if not _RUN_ID_RE.fullmatch(run_id):
        raise ValueError("invalid run_id")
    path = ratings_dir / f"{run_id}.json"
    if not path.is_file():
        return {"saved_at": None, "state": None, "history": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _render_dictation_items_html(entries: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for idx, entry in enumerate(entries, 1):
        nr = entry.get("nr") or idx
        entry_id = html.escape(str(entry["id"]))
        meta_parts = [entry_id]
        if entry.get("ebene"):
            meta_parts.append(html.escape(str(entry["ebene"])))
        meta_parts.append(html.escape(str(entry["konfidenz"])))
        meta_parts.append("→ " + html.escape(str(entry["ziel"])))
        if entry.get("date"):
            meta_parts.append(html.escape(str(entry["date"])))
        kontext_esc = html.escape(str(entry["kontext"]))
        entscheidung_esc = html.escape(str(entry["entscheidung"]))
        blocks.append(
            f'    <article class="dict-item" id="dict-item-{nr}" data-id="{entry_id}" data-nr="{nr}" tabindex="0">'
            f'<div class="dict-item-head"><span class="dict-nr">#{nr}</span>'
            f'<span class="meta">{" · ".join(meta_parts)}</span>'
            f'<button type="button" class="sec mark-btn" data-insert-mark="[#{nr}]" data-id="{entry_id}" '
            f'aria-label="Positionsmarke [#{nr}] in das Diktatfeld einfügen">[#{nr}] einfügen</button></div>'
            f'<div class="dict-context"><b>Worum es ging:</b> {kontext_esc}</div>'
            f'<div class="dict-decision"><b>Entscheidung des Avatars:</b> {entscheidung_esc}</div>'
            f"</article>"
        )
    return "\n".join(blocks)


def render_rating_html(
    input_payload: dict[str, Any],
    config: dict[str, Any] | None = None,
    *,
    template_path: Path | None = None,
    voice_probe: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    prefilter: bool = True,
    tickets_root: Path | str | None = None,
    decisions_index: Path | str | dict[str, Any] | list[dict[str, Any]] | None = None,
    decided_and_done: Path | str | None = None,
    resolved_ids: Iterable[str] | None = None,
    is_resolved: Callable[[dict[str, Any]], str | bool | None] | None = None,
    filter_report_out: dict[str, Any] | None = None,
) -> str:
    """Render the standalone rating HTML document from validated (and optionally prefiltered) input."""
    if not isinstance(input_payload, dict):
        raise ValueError("input payload must be a JSON object")

    pf_cfg = _merge_prefilter_config(config)
    effective_prefilter = bool(prefilter and pf_cfg.get("enabled", True))
    working_payload = copy.deepcopy(input_payload)

    if effective_prefilter and isinstance(working_payload.get("entries"), list) and working_payload["entries"]:
        eff_tickets = tickets_root if tickets_root is not None else (pf_cfg.get("tickets_root") or None)
        eff_decisions = decisions_index if decisions_index is not None else (pf_cfg.get("decisions_index") or None)
        eff_done_md = decided_and_done if decided_and_done is not None else (pf_cfg.get("decided_and_done") or None)
        cfg_resolved = pf_cfg.get("resolved_ids") or []
        merged_resolved: list[str] = [str(x) for x in cfg_resolved]
        if resolved_ids is not None:
            merged_resolved.extend(str(x) for x in resolved_ids)

        report = prefilter_items(
            working_payload["entries"],
            tickets_root=eff_tickets,
            decisions_index=eff_decisions,
            decided_and_done=eff_done_md,
            resolved_ids=merged_resolved,
            is_resolved=is_resolved,
        )
        if filter_report_out is not None:
            filter_report_out.clear()
            filter_report_out.update(report)
        if not report["kept"]:
            raise ValueError("all entries were filtered out by prefilter before HTML generation")
        working_payload["entries"] = report["kept"]

    validated = validate_input_payload(working_payload)
    voice_state = resolve_voice_state(config, voice_probe=voice_probe)

    tpl_file = template_path or DEFAULT_TEMPLATE_PATH
    template = tpl_file.read_text(encoding="utf-8")

    batch_fingerprint_src = validated["run_id"] + "|" + "|".join(e["id"] for e in validated["entries"])
    batch_hash = hashlib.sha256(batch_fingerprint_src.encode("utf-8")).hexdigest()[:10]

    page_title = validated.get("title") or "Avatar-Entscheidungen bewerten"
    payload_for_page = {
        "run_id": validated["run_id"],
        "batch_hash": batch_hash,
        "title": page_title,
        "description": validated.get("description") or "",
        "entries": validated["entries"],
        "voice": voice_state,
    }
    json_blob = json.dumps(payload_for_page, ensure_ascii=False).replace("</", "<\\/")
    dictation_items_html = _render_dictation_items_html(validated["entries"])

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
    rendered = rendered.replace("__DICTATION_ITEMS__", dictation_items_html)
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
    dictation_text = (validated.get("dictation") or "").strip()
    if dictation_text:
        lines.append(f"## Dictation Feedback ({date_str})")
        lines.append("")
        lines.append(dictation_text)
        lines.append("")

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
    if rated_count == 0 and not dictation_text:
        lines.append("_(no rated entries in response)_")
        lines.append("")
    return "\n".join(lines)


def _transcribe_wav_bytes(wav_bytes: bytes, voice_cfg: dict[str, Any], language: str) -> str:
    if not wav_bytes:
        raise ValueError("audio body must not be empty")
    engine = str(voice_cfg.get("engine") or "auto").strip() or "auto"
    model_path = str(voice_cfg.get("model_path") or "").strip() or None

    if engine == "remote":
        req = urllib.request.Request(
            validate_loopback_endpoint(str(voice_cfg.get("remote_url") or "")),
            data=wav_bytes,
            headers={"Content-Type": "audio/wav", "X-Voice-Language": language},
            method="POST",
        )
        with _LOOPBACK_OPENER.open(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if not data.get("ok"):
            raise RuntimeError(str(data.get("error") or "remote transcription failed"))
        return str(data.get("text") or "").strip()

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


def is_loopback_host_header(host_header: str | None) -> bool:
    """Accept only loopback ``Host`` values (optional port), e.g. ``127.0.0.1:8765`` or ``[::1]``."""
    value = (host_header or "").strip()
    if not value:
        return False
    try:
        parsed = urlparse(f"//{value}")
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError:
        return False
    if parsed.username is not None or parsed.path or parsed.query or parsed.fragment:
        return False
    return hostname in _LOOPBACK_HOSTS


_ORIGIN_SCHEMES = {"http": "http", "https": "https"}
_ORIGIN_HOSTS = {"127.0.0.1": "127.0.0.1", "localhost": "localhost", "::1": "[::1]"}


def canonical_bridge_origin(origin: str) -> str | None:
    """Return a rebuilt allowed origin (``null`` or http(s) loopback), else ``None``.

    The result is assembled from fixed literals plus an integer port, never from the raw
    header text, so a CR/LF or other stray character can never reach a response header.
    """
    if origin == "null":
        return "null"
    try:
        parsed = urlparse(origin)
        port = parsed.port
    except ValueError:
        return None
    scheme = _ORIGIN_SCHEMES.get(parsed.scheme)
    host = _ORIGIN_HOSTS.get(parsed.hostname or "")
    if scheme is None or host is None or parsed.path or parsed.query or parsed.fragment or parsed.username:
        return None
    canonical = f"{scheme}://{host}" if port is None else f"{scheme}://{host}:{int(port)}"
    return canonical if canonical == origin else None


def is_allowed_bridge_origin(origin: str) -> bool:
    """Allow ``null`` (``file://`` pages) and ``http(s)`` loopback origins only."""
    return canonical_bridge_origin(origin) is not None


def make_bridge_handler(
    config: dict[str, Any] | None = None,
    html_path: Path | None = None,
    ratings_dir: Path | None = None,
) -> type[BaseHTTPRequestHandler]:
    """Build the request handler class for the loopback voice bridge."""
    voice_cfg = _merge_voice_config(config)
    store_dir = ratings_dir or DEFAULT_RATINGS_DIR
    store_lock = threading.Lock()

    class BridgeHandler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:  # noqa: A002
            return

        def _own_origin(self) -> str | None:
            """Canonical Origin if it is ``null`` (file:// page) or this bridge's own loopback port."""
            allowed = canonical_bridge_origin((self.headers.get("Origin") or "").strip())
            if allowed is None or allowed == "null":
                return allowed
            return allowed if urlparse(allowed).port == self.server.server_address[1] else None

        def _cors_headers(self) -> None:
            allowed_origin = self._own_origin()
            if allowed_origin is not None:
                self.send_header("Access-Control-Allow-Origin", allowed_origin)
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

        def _reject_foreign_request(self) -> bool:
            """Return True (after sending 403) for non-loopback Host or foreign Origin."""
            if not is_loopback_host_header(self.headers.get("Host")):
                self._send_json({"ok": False, "error": "forbidden host"}, status=403)
                return True
            origin = self.headers.get("Origin")
            if origin is not None and self._own_origin() is None:
                self._send_json({"ok": False, "error": "forbidden origin"}, status=403)
                return True
            return False

        def _reject_foreign_store_request(self) -> bool:
            """The ratings store holds private notes: only the bridge's own page may use it.

            ``Origin: null`` (any local HTML file, sandboxed iframes) is refused here, unlike
            ``/transcribe``; ``file://`` pages keep localStorage plus import/export.
            """
            if self.headers.get("Origin") is not None and self._own_origin() in (None, "null"):
                self._send_json({"ok": False, "error": "forbidden origin"}, status=403)
                return True
            return False

        def do_OPTIONS(self) -> None:  # noqa: N802
            if self._reject_foreign_request():
                return
            self.send_response(204)
            self._cors_headers()
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            if self._reject_foreign_request():
                return
            path = urlparse(self.path).path
            if path == "/health":
                self._send_json({"ok": True, "voice": resolve_voice_state(config)})
                return
            if path.startswith("/ratings/"):
                if self._reject_foreign_store_request():
                    return
                try:
                    with store_lock:
                        record = load_rating_state(store_dir, path[len("/ratings/"):])
                except OSError:
                    self._send_json({"ok": False, "error": "storage error"}, status=500)
                    return
                except ValueError as exc:
                    self._send_json({"ok": False, "error": str(exc)}, status=400)
                    return
                resp_data: dict[str, Any] = {
                    "ok": True,
                    "saved_at": record.get("saved_at"),
                    "state": record.get("state"),
                }
                if "dictation" in record and record["dictation"] is not None:
                    resp_data["dictation"] = record["dictation"]
                self._send_json(resp_data)
                return
            # Read per request so a re-rendered page is served without restarting the bridge.
            page_bytes = html_path.read_bytes() if html_path and html_path.is_file() else None
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
            if self._reject_foreign_request():
                return
            path = urlparse(self.path).path
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                self._send_json({"ok": False, "error": "invalid Content-Length"}, status=400)
                return
            if path.startswith("/ratings/"):
                if self._reject_foreign_store_request():
                    return
                if length <= 0 or length > _MAX_STATE_BYTES:
                    self._send_json({"ok": False, "error": "state payload size out of bounds"}, status=400)
                    return
                try:
                    body = json.loads(self.rfile.read(length).decode("utf-8"))
                    if not isinstance(body, dict):
                        raise ValueError("body must be a JSON object")
                    with store_lock:
                        record = store_rating_state(
                            store_dir,
                            path[len("/ratings/"):],
                            body.get("state"),
                            dictation=body.get("dictation") if "dictation" in body else None,
                        )
                except OSError:
                    self._send_json({"ok": False, "error": "storage error"}, status=500)
                    return
                except (UnicodeDecodeError, ValueError) as exc:
                    self._send_json({"ok": False, "error": str(exc)}, status=400)
                    return
                self._send_json({"ok": True, "saved_at": record["saved_at"]})
                return
            if path != "/transcribe":
                self._send_json({"ok": False, "error": "not found"}, status=404)
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

    return BridgeHandler


def serve_rating_bridge(
    *,
    config: dict[str, Any] | None = None,
    html_path: Path | None = None,
    host: str = "127.0.0.1",
    port: int = 8765,
    ratings_dir: Path | None = None,
) -> None:
    """Run a strict loopback-only HTTP bridge for local STT and the rating autosave store."""
    if host not in _LOOPBACK_HOSTS:
        raise ValueError("bridge host must be a loopback address (127.0.0.1, localhost, ::1)")
    BridgeHandler = make_bridge_handler(config, html_path, ratings_dir)
    server = ThreadingHTTPServer((host, port), BridgeHandler)
    print(f"BYUM local voice bridge listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _add_prefilter_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--tickets-root", default="", help="Optional tickets directory with SOLVED/ and DONE/")
    parser.add_argument(
        "--decisions-index",
        default="",
        help="Optional decisions.index.json, DECIDED-AND-DONE.md, or decisions directory",
    )
    parser.add_argument("--decided-and-done", default="", help="Optional DECIDED-AND-DONE.md path")
    parser.add_argument(
        "--resolved-id",
        action="append",
        default=[],
        help="Mark an explicit ticket/decision/entry ID as resolved (repeatable)",
    )
    parser.add_argument("--filter-report", default="", help="Optional JSON output path for the prefilter report")


def _write_filter_report(report_path: Path, run_id: str, report: dict[str, Any]) -> None:
    serializable = {
        "run_id": run_id,
        "counts": report["counts"],
        "kept_ids": [str(item.get("id") or "") for item in report["kept"]],
        "filtered_out": [
            {
                "id": item["id"],
                "nr": item["nr"],
                "reason": item["reason"],
                "detail": item["detail"],
            }
            for item in report["filtered_out"]
        ],
    }
    atomic_write_text(report_path, json.dumps(serializable, ensure_ascii=False, indent=2) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Render standalone rating HTML from input JSON")
    p_build.add_argument("--input", required=True, help="Input JSON matching avatar-rating-input.schema.json")
    p_build.add_argument("--out", required=True, help="Output HTML file path")
    p_build.add_argument("--config", default="", help="Optional config JSON (defaults to config.local.json if present)")
    p_build.add_argument("--template", default="", help="Optional custom HTML template path")
    p_build.add_argument("--no-prefilter", action="store_true", help="Disable prefilter/readback before HTML build")
    _add_prefilter_args(p_build)

    p_prefilter = sub.add_parser("prefilter", help="Filter contextless or resolved entries before building")
    p_prefilter.add_argument("--input", required=True, help="Input JSON with entries")
    p_prefilter.add_argument("--out", required=True, help="Output path for filtered input JSON")
    _add_prefilter_args(p_prefilter)

    p_import = sub.add_parser("import-feedback", help="Convert rating response JSON to WHAT-USER-SAID-ABOUT Markdown")
    p_import.add_argument("--response", required=True, help="Response JSON downloaded from the rating page")
    p_import.add_argument("--out", default="", help="Write Markdown feedback to this file instead of stdout")
    p_import.add_argument("--date", default="", help="Override feedback date (YYYY-MM-DD)")

    p_serve = sub.add_parser("serve", help="Run loopback-only local ellmos-voice-io transcription bridge")
    p_serve.add_argument("--config", default="", help="Optional config JSON")
    p_serve.add_argument("--html", default="", help="Optional rendered rating HTML to serve at '/'")
    p_serve.add_argument("--host", default="127.0.0.1", help="Loopback bind host (default: 127.0.0.1)")
    p_serve.add_argument("--port", type=int, default=8765, help="Loopback bind port (default: 8765)")
    p_serve.add_argument("--ratings-dir", default="", help=f"Autosave directory (default: {DEFAULT_RATINGS_DIR})")

    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            input_path = Path(args.input).expanduser()
            payload = json.loads(input_path.read_text(encoding="utf-8"))
            cfg_path = Path(args.config).expanduser() if args.config else None
            cfg = load_config(cfg_path, search_dir=REPO_ROOT if cfg_path is None else None)
            tpl = Path(args.template).expanduser() if args.template else None
            report_box: dict[str, Any] = {}
            rendered = render_rating_html(
                payload,
                cfg,
                template_path=tpl,
                prefilter=not args.no_prefilter,
                tickets_root=args.tickets_root or None,
                decisions_index=args.decisions_index or None,
                decided_and_done=args.decided_and_done or None,
                resolved_ids=args.resolved_id or None,
                filter_report_out=report_box,
            )
            atomic_write_text(Path(args.out).expanduser(), rendered)
            if args.filter_report and report_box:
                _write_filter_report(
                    Path(args.filter_report).expanduser(),
                    str(payload.get("run_id") or ""),
                    report_box,
                )
            return 0

        if args.command == "prefilter":
            input_path = Path(args.input).expanduser()
            payload = json.loads(input_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or not isinstance(payload.get("entries"), list):
                raise ValueError("input must be a JSON object with an 'entries' list")
            report = prefilter_items(
                payload["entries"],
                tickets_root=args.tickets_root or None,
                decisions_index=args.decisions_index or None,
                decided_and_done=args.decided_and_done or None,
                resolved_ids=args.resolved_id or None,
            )
            if args.filter_report:
                _write_filter_report(Path(args.filter_report).expanduser(), str(payload.get("run_id") or ""), report)
            if not report["kept"]:
                raise ValueError("all entries were filtered out by prefilter")
            out_payload = copy.deepcopy(payload)
            out_payload["entries"] = report["kept"]
            validated = validate_input_payload(out_payload)
            atomic_write_text(Path(args.out).expanduser(), json.dumps(validated, ensure_ascii=False, indent=2) + "\n")
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
            ratings_dir = Path(args.ratings_dir).expanduser() if args.ratings_dir else None
            serve_rating_bridge(config=cfg, html_path=html_file, host=args.host, port=args.port, ratings_dir=ratings_dir)
            return 0
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
