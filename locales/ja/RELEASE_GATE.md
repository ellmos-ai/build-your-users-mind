> **Translation status (2026-07-15): historical pre-1.1 draft. The root English documents are authoritative; do not use this translation as the current operational or security contract.**

# RELEASE_GATE — build-your-users-mind

**日付:** 2026-06-17
**スクリプト:** `.MODULES/_scripts/final_gate_check.py`
**結果:** **10 PASS / 0 FAIL / 0 WARN → 一般公開の準備完了**
**対象リポジトリ:** `ellmos-ai/build-your-users-mind` (最初は **プライベート**)
**コミット:** ローカルで初期化済み、プッシュ未実行 (明示的な指示待ち)。

| # | チェック項目 | 結果 |
|---|---|---|
| 1 | .gitignore の必須エントリ | PASS |
| 2 | README.md (英語版) | PASS |
| 3 | LICENSE | PASS |
| 4 | .db ファイルが追跡されていないこと | PASS |
| 5 | .env ファイルが追跡されていないこと | PASS |
| 6 | 秘密情報（シークレット）がないこと | PASS |
| 7 | ハードコードされたプライベートパスがないこと | PASS |
| 8 | 個人情報（PII）パターンがないこと | PASS |
| 9 | BACH 内部ドキュメントがないこと | PASS |
| 10 | STATUSテーブル付きの TODO.md | PASS |

## 意図的に許容された未解決事項 (ゲートブロッカーではありません)
- Codex/Gemini/Kimi 用のソースアダプターは現在スケッチ段階です (Claude パスは完了しています) — `TODO.md` で優先度 HIGH として記録されています。
- 自動化された分類のスポットチェック/評価者間一致率（Kappa）の測定は未実装です (オプションの品質向上ステップ、`TODO.md` 内)。
- リポジトリ内にプライベートコーパスや生成されたアバターファイルはありません (`.gitignore` で強制)。

## 実際のプッシュ前（オペレーターの手順）
1. GitHub リポジトリ `ellmos-ai/build-your-users-mind` を **プライベート** として作成します。
2. リモートを設定し、プッシュします。
3. トピックを設定します: theory-of-mind, llm, user-modeling, personalization, ai-agents, prompt-analysis.
4. 明示的な公開の承認後にのみパブリック（公開）に切り替えます（ゲートは緑色で、内容的には Claude パスで十分です）。
