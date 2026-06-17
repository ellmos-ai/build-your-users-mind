# SOURCE-ADAPTERS — Where each model reads its user prompts from

> The **only model-specific part** of the module (Step 1 in `SKILL.md`). Each adapter delivers
> the same normalized row: `{ts, source, project, session, sender:"human", text}`.
> Reference extractor (Claude): `scripts/corpus_extract.py` (in this repo).

## Claude Code  ✅ Implemented
- **Path:** `~/.claude/projects/<slug>/<session>.jsonl`
- **Filter:** `type=="user"` & `message.role=="user"`; text from string or `content[].type=="text"`.
- **Exclude:** tool_result blocks, `<system-reminder>`, `<task-notification>`, `<local-command-stdout>`,
  hook injections, context compacting summaries ("This session is being continued…").
- **Slash Commands:** extract `<command-name>` + `<command-args>`, tag as `slash`.

## Codex CLI (GPT)  ✅ Implemented → `scripts/adapters/codex_adapter.py`
- **Path:** `~/.codex/sessions/<YYYY>/<MM>/<DD>/rollout-*.jsonl` (+ `~/.codex/archived_sessions/`).
- **Filter:** `type=="response_item"` & `payload.role=="user"` & `payload.content[].type=="input_text"`.
- **Exclude:** `<environment_context>`, `<user_instructions>`, tool outputs.
- Written by Codex itself (prompt: `_prompts/adapter-codex.md`), smoke-tested (946 prompts, schema-compliant).

## Gemini / agy (antigravity)  ✅ Implemented → `scripts/adapters/gemini_adapter.py`
- **Path:** `~/.gemini/antigravity/conversations/<uuid>.db` (SQLite).
- **Findings:** `steps` table stores `metadata` + `step_payload` as **Protobuf blobs**; user turns = `step_type==14`, text = payload field 19→2, timestamp from metadata field 1. Custom varint parser in the adapter.
- Written by agy/Gemini itself (prompt: `_prompts/adapter-gemini.md`), smoke-tested (188 prompts, clean text).

## Kimi Code CLI  ✅ Implemented → `scripts/adapters/kimi_adapter.py`
- **Path:** `~/.kimi-code/sessions/.../<sessionDir>/agents/main/wire.jsonl` (JSONL); index `~/.kimi-code/session_index.jsonl` (sessionId/sessionDir/workDir).
- **Filter:** `type=="turn.prompt"` & `origin.kind=="user"`; text from `input` (text blocks/string); `time` = Unix ms.
- Written by Kimi (kimi-code) itself (prompt: `_prompts/adapter-kimi.md`), smoke-tested (18 prompts).

## Adapter Contract
1. Only **human-typed** prompts. 2. Filterable time window (`--since`). 3. UTF-8, genuine characters
(`PYTHONIOENCODING=utf-8`; logs are valid UTF-8 — do **not** "repair", only set console encoding).
4. Output = JSONL, one normalized line per prompt. Afterwards, the universal pipeline takes over (Steps 2–6).
