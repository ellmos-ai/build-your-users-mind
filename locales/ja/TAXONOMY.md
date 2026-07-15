> **Translation status (2026-07-15): historical pre-1.1 draft. The root English documents are authoritative; do not use this translation as the current operational or security contract.**

# TAXONOMY — 8つのプロンプトタイプ + 分類フィールド

> スタンドアロン版（モジュールは自己完結しています）。**方法論的基盤：** *Prompt-Archaeology*（L. Geiger） — 人間とAIの完全なインタラクションプロトコルを分類する手法。

## 8つのプロンプトタイプ

| タイプ | コード | 定義 | 指標 |
|---|---|---|---|
| 開始プロンプト | **SP** | 新しい分析やフェーズを開始する | 事前コンテキストへの参照がない |
| 追加質問（トピック） | **NT** | 既存のトピックを深掘りする | 「〜についてはどうですか？」など |
| 追加質問（メソッド） | **NM** | メソッド/ツール/レビュー/検索/エージェントを起動する | 動詞による指示 |
| 追加質問（制御） | **NS** | 順序や優先順位を制御する | 「待って」、「まず」、「ストップ」など |
| 修正 | **KO** | エラーや仮定を訂正する | 否定表現、反例 |
| 確認 | **BE** | 中間状態を検証する | 短い同意表現 |
| 方向転換 | **RA** | 根本的な方向転換 | フレームワーク全体の前提を疑う |
| メタプロンプト | **MP** | プロセスや対話自体に関するもの | プロセスに関する用語 |

**境界線のケース：** SP と NT（新規か接続しているか） · NM と NS（メソッドの起動か順序変更のみか） · BE と KO（「はい、でも…」は通常KO） · RA は KO より稀で、フレームワーク全体に関わります。

## 分類フィールド（プロンプトごと）

| フィールド | 値 |
|---|---|
| `type_code` | SP/NT/NM/NS/KO/BE/RA/MP |
| `topic` | 短いトピック（プロジェクト関連） |
| `is_decision` | 決定、優先度、ルール、修正、方向転換の場合は true |
| `decision_kind` | preference / correction / rule / direction_change / approval / rejection / process / none |
| `formulation_pattern` | ユーザー特有の特徴的なフレーズ（オリジナルの表現、短文） |
| `method_triggered` | WebSearch / WebFetch / Multi-Agent / Review / Cross-Model / Script / LaTeX / -- |
| `is_turning_point` | true/false |
| `outcome_signal` *(決定論的、ステージ0/1)* | praise / correction / reissue / none（次のユーザーのターンから取得） |

## バイアス指標（ステージ4）
- **確認：修正 (B:K) 比率** — 不均衡は承認バイアスを示唆します。**暗黙の承認は不可視**（入力されない）ため、修正が過大に表現される傾向があります。
- **トピックごとの修正率** — エラーが発生しやすいトピックを特定します。
- **プロアクティブ：リアクティブ** — ユーザーが主導しているか、それともAI主導か。
- **方向転換率** — 認識的な柔軟性。
