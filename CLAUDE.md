# CLAUDE.md

## このプロジェクトについて
Claude Code の個人設定・スキル管理・外部ツール連携を統合する作業ハブ。
Lark / GPT / Obsidian / Make.com を活用して日常タスクを自動化・効率化する。

## 開発ルール
- 出力・コメントは日本語で統一する

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
