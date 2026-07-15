> **Translation status (2026-07-15): historical pre-1.1 draft. The root English documents are authoritative; do not use this translation as the current operational or security contract.**

# SOURCE-ADAPTERS — 各モデルがユーザーのプロンプトを読み込む場所

> モジュールの**唯一のエージェント固有の部分**（`SKILL.md` のステップ1）。すべてのエアダプターは、次の正規化された行を出力します：`{ts, source, project, session, sender:"human", text}`。
> 参照エクストラクター（Claude）：`scripts/corpus_extract.py`（このリポジトリ内）。

## Claude Code  ✅ 実装済み
- **パス:** `~/.claude/projects/<slug>/<session>.jsonl`
- **フィルター:** `type=="user"` & `message.role=="user"`; 文字列または `content[].type=="text"` からテキストを取得。
- **除外対象:** tool_result ブロック、`<system-reminder>`、`<task-notification>`、`<local-command-stdout>`、フックによる注入、コンテキスト圧縮の要約（「This session is being continued…」）。
- **スラッシュコマンド:** `<command-name>` + `<command-args>` を抽出し、`slash` としてタグ付け。

## Codex CLI (GPT)  ✅ 実装済み → `scripts/adapters/codex_adapter.py`
- **パス:** `~/.codex/sessions/<YYYY>/<MM>/<DD>/rollout-*.jsonl`（+ `~/.codex/archived_sessions/`）。
- **フィルター:** `type=="response_item"` & `payload.role=="user"` & `payload.content[].type=="input_text"`。
- **除外対象:** `<environment_context>`、`<user_instructions>`、ツール出力。
- Codex自身によって記述（指示：`_prompts/adapter-codex.md`）、スモークテスト済み（946プロンプト、スキーマ準拠）。

## Gemini / agy (antigravity)  ✅ 実装済み → `scripts/adapters/gemini_adapter.py`
- **パス:** `~/.gemini/antigravity/conversations/<uuid>.db`（SQLite）。
- **詳細:** `steps` テーブルは `metadata` + `step_payload` を **Protobufバイナリ（blob）** として保存。ユーザーのターンは `step_type==14`、テキストは payload の 19→2 フィールド、タイムスタンプは metadata の 1 フィールド。アダプター内の独自の varint パーサー。
- agy/Gemini自身によって記述（指示：`_prompts/adapter-gemini.md`）、スモークテスト済み（188プロンプト、クリーンなテキスト）。

## Kimi Code CLI  ✅ 実装済み → `scripts/adapters/kimi_adapter.py`
- **パス:** `~/.kimi-code/sessions/.../<sessionDir>/agents/main/wire.jsonl`（JSONL）; インデックス `~/.kimi-code/session_index.jsonl`（sessionId/sessionDir/workDir）。
- **フィルター:** `type=="turn.prompt"` & `origin.kind=="user"`; `input`（テキストブロック/文字列）からテキストを取得。`time` = Unixミリ秒。
- Kimi（kimi-code）自身によって記述（指示：`_prompts/adapter-kimi.md`）、スモークテスト済み（18プロンプト）。

## アダプターの要件（コントラクト）
1. **人間によって入力された**プロンプトのみを対象とすること。2. 時間枠でフィルタリングできること（`--since`）。3. UTF-8、本物の文字（`PYTHONIOENCODING=utf-8`、ログは有効な UTF-8 です。修復はせず、コンソールのエンコーディングのみを設定してください）。
4. 出力 = JSONL、1プロンプトにつき1つの正規化された行。その後、共通のパイプライン（ステップ2〜6）が引き継ぎます。
