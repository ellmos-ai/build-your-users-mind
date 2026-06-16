# SOURCE-ADAPTERS — woher jedes Modell seine User-Prompts liest

> Der **einzig modellspezifische Teil** des Moduls (Schritt 1 in `SKILL.md`). Jeder Adapter liefert
> dieselbe normalisierte Zeile: `{ts, source, project, session, sender:"human", text}`.
> Referenz-Extraktor (Claude): `scripts/corpus_extract.py` (in diesem Repo).

## Claude Code  ✅ implementiert
- **Pfad:** `~/.claude/projects/<slug>/<session>.jsonl`
- **Filter:** `type=="user"` & `message.role=="user"`; Text aus String oder `content[].type=="text"`.
- **Raus:** tool_result-Blöcke, `<system-reminder>`, `<task-notification>`, `<local-command-stdout>`,
  Hook-Injektionen, Kontext-Kompaktierungs-Summaries („This session is being continued…").
- **Slash-Commands:** `<command-name>` + `<command-args>` extrahieren, als `slash` taggen.

## Codex CLI (GPT)  ✅ implementiert → `scripts/adapters/codex_adapter.py`
- **Pfad:** `~/.codex/sessions/<YYYY>/<MM>/<DD>/rollout-*.jsonl` (+ `~/.codex/archived_sessions/`).
- **Filter:** `type=="response_item"` & `payload.role=="user"` & `payload.content[].type=="input_text"`.
- **Raus:** `<environment_context>`, `<user_instructions>`, Tool-Outputs.
- Von Codex selbst geschrieben (Auftrag: `_prompts/adapter-codex.md`), Smoke-getestet (946 Prompts, Schema-konform).

## Gemini / agy (antigravity)  ⏳ Adapter-Skizze
- **Pfad:** `~/.gemini/antigravity/conversations/<uuid>.db` (SQLite).
- **Filter:** Tabelle `steps` → User-Turns (Spalten beim Bau mappen). WAL beachten.

## Kimi Code CLI  ⏳ offen
- Log-Format beim ersten Einsatz bestimmen; Adapter nach gleichem Vertrag ergänzen.

## Adapter-Vertrag
1. Nur **menschlich getippte** Prompts. 2. Zeitfenster filterbar (`--since`). 3. UTF-8, echte Umlaute
(`PYTHONIOENCODING=utf-8`; Logs sind valides UTF-8 — **nicht** „reparieren", nur Konsolen-Encoding setzen).
4. Output = JSONL, eine normalisierte Zeile je Prompt. Danach greift die universelle Pipeline (Schritt 2–6).
