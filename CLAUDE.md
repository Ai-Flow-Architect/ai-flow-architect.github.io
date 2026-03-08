# CLAUDE.md

## このプロジェクトについて
Claude Code の個人設定・スキル管理・外部ツール連携を統合する作業ハブ。
Lark / GPT / Obsidian / Make.com を活用して日常タスクを自動化・効率化する。

## ツール実行の許可ルール
通常のBashコマンドは確認なしで実行する。
以下の操作は実行前にユーザーに確認すること：
- rm -rf などの復元不可能な削除
- git push --force
- sudo（apt install 以外）
- 外部への公開・デプロイ操作

## 外部ツール連携（詳細）
グローバル CLAUDE.md の「外部ツール連携」セクションを参照。
認証変数（`$LARK_APP_ID` 等）は `~/.bashrc` で管理済み。

## 会社マネジメント
コスト確認ルールはグローバル CLAUDE.md の「会社マネジメントルール」セクションを参照。
会社ファイル: `~/projects/company/docs/`

## スキル一覧（主要）
| スキル | 用途 |
|--------|------|
| `/summary-mid` | 途中サマリー（時間・進捗確認） |
| `/summary-end` | 最終サマリー（ログ・Lark更新・リセット）＋セキュリティ・ルール整合性チェック（④） |
| `/lark` | Lark APIでメッセージ送信・情報取得 |
| `/gpt` | GPT呼び出し |
| `/obsidian-cleanup` | Obsidianノート整理 |
| `/gym-menu` | 筋トレメニュー自動生成（Make.com） |
| `/auto-gantt` | ガントチャート自動生成（Make.com） |
| `/mermaid-to-obsidian` | Mermaid図を生成してObsidianノートに書き込み |
| `/okr-plan` | 月次OKR戦略検討（AIFLOWプラン参照→Claude対話→Lark OKR記入テキスト生成） |
| `/okr-check` | 週次OKR進捗FB（Lark OKR読み込み→状況ヒアリング→更新提案出力） |
| `/mercari-relist` | メルカリ再出品自動化（出品データ収集→画像DL→取り下げ→新規出品をPlaywrightで全自動） |
| `/excalidraw` | Excalidraw形式の図（フローチャート・マインドマップ等）を生成してファイル保存 |
| `/day-strategy` | 日次タスク設計（前日持越し+新規統合→依存・認知負荷考慮→得点表で提示、計画のみ） |
| `/blind-spot` | 毎週土曜：最新AI情報をWeb検索→現在設定と比較→盲点TOP5をROI付きで提案 |
| `/agent-teams` | ROI評価付き開発フロー（CEO/FM評価→GPT壁打ち→実装→スキル化まで一貫） |
| `/make-dev` | Make.com開発ナレッジ（設計→JSON生成→テスト→デバッグ＋落とし穴集） |
| `/make-token-refresh` | Make.com APIトークン自動取得（Playwrightでログインセッション管理・~/.bashrc更新） |
| `/skill-creator` | 新規スキル作成・既存スキル改善・評価・ベンチマーク（Anthropic公式） |
| `/clarify` | 思考整理（雑なアイデア→構造化→欠けているピース指摘→改善提案） |
| `/research` | 構造化リサーチ（Web検索→インサイト・トレンド・データ→レポート） |
| `/solve` | 問題分解・解決（根本原因特定→分解→解決策比較→実行ステップ） |
| `/week-strategy` | 週次スケジュール設計（Larkカレンダー連携→不要削除→最適配置→最終チェック） |
| `/ai-unstuck-playbook` | 詰まり自己診断（停滞宣言→状態圧縮→解法切替の3ステップ） |
| `/youtube-learn-do` | YouTube字幕取得→要約→ROIアクション抽出→即実践 |
| `/neta-trend` | 毎朝の情報収集（HackerNews・Reddit・Dev.to→興味度スコア付きトレンド） |
