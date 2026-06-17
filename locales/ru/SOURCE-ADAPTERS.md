# SOURCE-ADAPTERS — Откуда каждая модель читает промты пользователя

> **Единственная специфичная для модели часть** модуля (Шаг 1 в `SKILL.md`). Каждый адаптер выдает одну и ту же нормализованную строку: `{ts, source, project, session, sender:"human", text}`.
> Референсный экстрактор (Claude): `scripts/corpus_extract.py` (в этом репозитории).

## Claude Code  ✅ Реализовано
- **Путь:** `~/.claude/projects/<slug>/<session>.jsonl`
- **Фильтр:** `type=="user"` & `message.role=="user"`; текст из строки или `content[].type=="text"`.
- **Исключить:** блоки tool_result, `<system-reminder>`, `<task-notification>`, `<local-command-stdout>`, внедренные хуки, краткие резюме сжатия контекста ("This session is being continued…").
- **Слэш-команды:** извлечение `<command-name>` + `<command-args>`, тегирование как `slash`.

## Codex CLI (GPT)  ✅ Реализовано → `scripts/adapters/codex_adapter.py`
- **Путь:** `~/.codex/sessions/<YYYY>/<MM>/<DD>/rollout-*.jsonl` (+ `~/.codex/archived_sessions/`).
- **Фильтр:** `type=="response_item"` & `payload.role=="user"` & `payload.content[].type=="input_text"`.
- **Исключить:** `<environment_context>`, `<user_instructions>`, выводы инструментов.
- Написано самим Codex (запрос: `_prompts/adapter-codex.md`), дымовое тестирование пройдено (946 промтов, соответствует схеме).

## Gemini / agy (antigravity)  ✅ Реализовано → `scripts/adapters/gemini_adapter.py`
- **Путь:** `~/.gemini/antigravity/conversations/<uuid>.db` (SQLite).
- **Детали:** таблица `steps` сохраняет `metadata` + `step_payload` в виде **Protobuf-блобов**; шаги пользователя = `step_type==14`, текст = поле payload 19→2, таймстамп из поля metadata 1. Собственный парсер varint в адаптере.
- Написано самим agy/Gemini (запрос: `_prompts/adapter-gemini.md`), дымовое тестирование пройдено (188 промтов, чистый текст).

## Kimi Code CLI  ✅ Реализовано → `scripts/adapters/kimi_adapter.py`
- **Путь:** `~/.kimi-code/sessions/.../<sessionDir>/agents/main/wire.jsonl` (JSONL); индекс `~/.kimi-code/session_index.jsonl` (sessionId/sessionDir/workDir).
- **Фильтр:** `type=="turn.prompt"` & `origin.kind=="user"`; текст из `input` (текстовые блоки/строка); `time` = Unix-мс.
- Написано самим Kimi (kimi-code) (запрос: `_prompts/adapter-kimi.md`), дымовое тестирование пройдено (18 промтов).

## Правила адаптера (контракт)
1. Только **набранные человеком** промты. 2. Фильтрация по временному окну (`--since`). 3. UTF-8, настоящие символы (`PYTHONIOENCODING=utf-8`; логи записаны в валидном UTF-8 — **не** «исправлять», только задать кодировку консоли).
4. Вывод = JSONL, одна нормализованная строка на промт. Далее работает универсальный конвейер (Шаги 2–6).
