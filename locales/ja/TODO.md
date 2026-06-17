# リリース前 TODO: build-your-users-mind

**監査日:** 2026-06-17
**監査担当者:** Claude (Lukas Geiger の代理)
**対象リポジトリ:** `ellmos-ai/build-your-users-mind` (最初はプライベート)
**ステータス:** `development` — Claude パスは完了。プライベートな参照実装が存在。

---

## ゲートブロッカー（最優先課題）
> 一般公開前に解決する必要があります。

- [x] **シークレット（秘密情報）:** 追跡対象ファイルに APIキー/トークン/パスワードがないこと。
- [x] **個人情報（プライベートデータ）:** PIIや実際のパスがないこと（漏洩スキャンはグリーン）。
- [x] **ハードコードされたパス:** すべてのスクリプトで汎用/相対パスを使用していること。
- [x] **データベースファイル:** `.db` ファイルが追跡されていないこと。
- [x] **.env ファイル:** `.env` ファイルが追跡されていないこと。
- [x] **BACH 内部資料:** BACH 内部ドキュメントが含まれていないこと。
- [x] **.gitignore:** 必要な最小限のエントリが存在すること。
- [x] **LICENSE:** MIT ライセンスが存在すること。
- [x] **README.md:** 英語版が完成していること。

## 優先度：高 (HIGH PRIORITY)
- [ ] Codex (rollout) と Gemini (SQLite) 用のソースアダプターの実装 (現在はスケッチ)。
- [ ] オプションの品質管理ステップとして、分類のスポットチェック / 評価者間 Kappa 一致率の測定を追加。
- [ ] `domains.json` のサンプルを同梱。

## 優先度：中 (MEDIUM PRIORITY)
- [x] `SECURITY.md` を追加。
- [ ] v1.0.0 以降の `CHANGELOG.md` を作成。
- [ ] `CONTRIBUTING.md` を作成。
- [ ] Kimi アダプターの実装 (最初の使用時のログフォーマットの確認)。

## 優先度：低 (LOW PRIORITY)
- [ ] テスト/スモークスイート、GitHub Actions CI、バッジの整備。

## 意図的に含まれていないもの
- プライベートコーパス、生成されたアバターファイル (詳細は `.gitignore` 参照)。
- プロンプトごとのフック (意図的にバッチ処理 + ログブック方式を選択)。

---

## ステータス (STATUS)

| カテゴリ | ステータス | 備考 |
|----------|--------|-------|
| シークレット | :green_circle: | 漏洩スキャン合格 |
| 個人情報 (PII) | :green_circle: | PII/実パスなし |
| .gitignore | :green_circle: | 最小エントリ + コーパス/アバターの除外設定 |
| 言語 (英語) | :green_circle: | README は英語 |
| BACH 内部資料 | :green_circle: | なし |
| データベースファイル | :green_circle: | 追跡なし |
| README.md | :green_circle: | 完成 |
| LICENSE | :green_circle: | MIT |
| **全体ステータス** | **準備完了 (READY)** | プライベート公開可能。Codex/Geminiアダプターは依然スケッチ段階 |

**監査日:** 2026-06-17
**ゲートチェック終了コード:** `pending` (保留中)

---

*ベース: MODULES/_templates/TODO_TEMPLATE.md*
