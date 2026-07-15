> **Translation status (2026-07-15): historical pre-1.1 draft. The root English documents are authoritative; do not use this translation as the current operational or security contract.**

# SOURCE-ADAPTERS —— 每个模型从何处读取用户提示词

> 本模块中**唯一与特定智能体相关的部分**（`SKILL.md` 中的步骤 1）。每个适配器输出相同格式的规范化行：`{ts, source, project, session, sender:"human", text}`。
> 参考提取器（Claude）：`scripts/corpus_extract.py`（在此仓库中）。

## Claude Code  ✅ 已实现
- **路径：** `~/.claude/projects/<slug>/<session>.jsonl`
- **过滤条件：** `type=="user"` & `message.role=="user"`；从字符串或 `content[].type=="text"` 中提取文本。
- **排除项：** tool_result 块、`<system-reminder>`、`<task-notification>`、`<local-command-stdout>`、钩子注入、上下文压缩摘要（“This session is being continued…”）。
- **斜杠命令：** 提取 `<command-name>` + `<command-args>`，标记为 `slash`。

## Codex CLI (GPT)  ✅ 已实现 → `scripts/adapters/codex_adapter.py`
- **路径：** `~/.codex/sessions/<YYYY>/<MM>/<DD>/rollout-*.jsonl`（+ `~/.codex/archived_sessions/`）。
- **过滤条件：** `type=="response_item"` & `payload.role=="user"` & `payload.content[].type=="input_text"`。
- **排除项：** `<environment_context>`、`<user_instructions>`、工具输出。
- 由 Codex 自身编写（提示词：`_prompts/adapter-codex.md`），已通过冒烟测试（946 个提示词，符合 schema）。

## Gemini / agy (antigravity)  ✅ 已实现 → `scripts/adapters/gemini_adapter.py`
- **路径：** `~/.gemini/antigravity/conversations/<uuid>.db`（SQLite）。
- **详细信息：** `steps` 表将 `metadata` + `step_payload` 存储为 **Protobuf 二进制大对象（blob）**；用户轮次为 `step_type==14`，文本为 payload 的 19→2 字段，时间戳来自 metadata 的 1 字段。适配器中内置了自定义的 varint 解析器。
- 由 agy/Gemini 自身编写（提示词：`_prompts/adapter-gemini.md`），已通过冒烟测试（188 个提示词，文本干净）。

## Kimi Code CLI  ✅ 已实现 → `scripts/adapters/kimi_adapter.py`
- **路径：** `~/.kimi-code/sessions/.../<sessionDir>/agents/main/wire.jsonl`（JSONL）；索引为 `~/.kimi-code/session_index.jsonl`（sessionId/sessionDir/workDir）。
- **过滤条件：** `type=="turn.prompt"` & `origin.kind=="user"`；从 `input`（文本块/字符串）中提取文本；`time` = Unix 毫秒。
- 由 Kimi (kimi-code) 自身编写（提示词：`_prompts/adapter-kimi.md`），已通过冒烟测试（18 个提示词）。

## 适配器契约（Contract）
1. 仅限**人类键入的**提示词。2. 时间窗口可过滤（`--since`）。3. UTF-8，真实字符（`PYTHONIOENCODING=utf-8`；日志为有效的 UTF-8 —— **请勿**“修复”，仅设置控制台编码）。
4. 输出 = JSONL，每个提示词一行规范化数据。此后，交由通用流水线处理（步骤 2–6）。
