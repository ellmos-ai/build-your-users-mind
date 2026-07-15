# SOURCE-ADAPTERS — Where each model reads its user prompts from

> The **only model-specific part** of the module (Step 1 in `SKILL.md`). Each adapter delivers
> the same normalized row, including a stable evidence `id` and redacted `text`.
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
- Tracks `session_meta`/`turn_context` for project context and drops Codex internal-context/plugin records.

## Gemini / agy (antigravity)  ✅ Implemented → `scripts/adapters/gemini_adapter.py`
- **Path:** `~/.gemini/antigravity/conversations/<uuid>.db` (SQLite).
- **Findings:** `steps` table stores `metadata` + `step_payload` as **Protobuf blobs**; user turns = `step_type==14`, text = payload field 19→2, timestamp from metadata field 1. Custom varint parser in the adapter.
- Opens SQLite databases read-only and rejects malformed/truncated protobuf fields.

## Kimi Code CLI  ✅ Implemented → `scripts/adapters/kimi_adapter.py`
- **Path:** `~/.kimi-code/sessions/.../<sessionDir>/agents/main/wire.jsonl` (JSONL); index `~/.kimi-code/session_index.jsonl` (sessionId/sessionDir/workDir).
- **Filter:** `type=="turn.prompt"` & `origin.kind=="user"`; text from `input` (text blocks/string); `time` = Unix ms.
- Validates finite positive Unix-ms timestamps and filters the same synthetic artifact classes.

## Adapter Contract
1. Only **human-typed** prompts. 2. Filterable time window (`--since`). 3. UTF-8, genuine characters
(`PYTHONIOENCODING=utf-8`; logs are valid UTF-8 — do **not** "repair", only set console encoding).
4. Missing roots, invalid dates, no eligible rows, missing timestamps, and malformed/unreadable
   records fail closed. Use `--allow-empty` only for an intentional empty replacement and
   `--allow-partial` only after inspecting and accepting input loss.
   Known tool-result/image-only records are intentionally excluded because they contain no typed
   prompt; unknown/empty block shapes are treated as schema drift, not silently ignored.
5. Output = atomic private JSONL, one normalized line per prompt. For several sources, give each
   adapter a distinct `--output-name` and merge them:

```text
python scripts/adapters/codex_adapter.py --output-name corpus_codex.jsonl --out ./STUDIE
python scripts/adapters/kimi_adapter.py --root ~/.kimi-code/sessions --output-name corpus_kimi.jsonl --out ./STUDIE
python scripts/merge_corpora.py ./STUDIE/corpus_codex.jsonl ./STUDIE/corpus_kimi.jsonl --out ./STUDIE/00_corpus.jsonl
```

Optional `--redaction-rules rules.json` appends operator-reviewed regex replacements to the built-ins.
