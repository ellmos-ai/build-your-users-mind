> **Translation status (2026-07-15): historical pre-1.1 draft. The root English documents are authoritative; do not use this translation as the current operational or security contract.**

# SOURCE-ADAPTERS — De dónde lee cada modelo sus instrucciones de usuario

> La **única parte específica del modelo** del módulo (Paso 1 en `SKILL.md`). Cada adaptador ofrece la misma fila normalizada: `{ts, source, project, session, sender:"human", text}`.
> Extractor de referencia (Claude): `scripts/corpus_extract.py` (en este repositorio).

## Claude Code  ✅ Implementado
- **Ruta:** `~/.claude/projects/<slug>/<session>.jsonl`
- **Filtro:** `type=="user"` & `message.role=="user"`; texto de cadena o `content[].type=="text"`.
- **Exclusión:** bloques de tool_result, `<system-reminder>`, `<task-notification>`, `<local-command-stdout>`, inyecciones de hooks, resúmenes de compactación de contexto ("This session is being continued…").
- **Comandos Slash:** extraer `<command-name>` + `<command-args>`, etiquetar como `slash`.

## Codex CLI (GPT)  ✅ Implementado → `scripts/adapters/codex_adapter.py`
- **Ruta:** `~/.codex/sessions/<YYYY>/<MM>/<DD>/rollout-*.jsonl` (+ `~/.codex/archived_sessions/`).
- **Filtro:** `type=="response_item"` & `payload.role=="user"` & `payload.content[].type=="input_text"`.
- **Exclusión:** `<environment_context>`, `<user_instructions>`, salidas de herramientas.
- Escrito por el propio Codex (instrucción: `_prompts/adapter-codex.md`), smoke-tested (946 instrucciones, cumple con el esquema).

## Gemini / agy (antigravity)  ✅ Implementado → `scripts/adapters/gemini_adapter.py`
- **Ruta:** `~/.gemini/antigravity/conversations/<uuid>.db` (SQLite).
- **Hallazgos:** la tabla `steps` almacena `metadata` + `step_payload` como **blobs de Protobuf**; turnos de usuario = `step_type==14`, texto = campo de payload 19→2, marca de tiempo del campo de metadata 1. Parser de varint propio en el adaptador.
- Escrito por el propio agy/Gemini (instrucción: `_prompts/adapter-gemini.md`), smoke-tested (188 instrucciones, texto limpio).

## Kimi Code CLI  ✅ Implementado → `scripts/adapters/kimi_adapter.py`
- **Ruta:** `~/.kimi-code/sessions/.../<sessionDir>/agents/main/wire.jsonl` (JSONL); índice `~/.kimi-code/session_index.jsonl` (sessionId/sessionDir/workDir).
- **Filtro:** `type=="turn.prompt"` & `origin.kind=="user"`; texto de `input` (bloques de texto/cadena); `time` = Unix ms.
- Escrito por el propio Kimi (kimi-code) (instrucción: `_prompts/adapter-kimi.md`), smoke-tested (18 instrucciones).

## Contrato del adaptador
1. Solo instrucciones **escritas por humanos**. 2. Ventana de tiempo filtrable (`--since`). 3. UTF-8, caracteres genuinos (`PYTHONIOENCODING=utf-8`; los registros son UTF-8 válidos — **no** "reparar", solo establecer la codificación de la consola).
4. Salida = JSONL, una línea normalizada por instrucción. Después, interviene la pipeline universal (Pasos 2–6).
