# Lark Bot 棲み分け設計書
作成日: 2026-03-21

## 確定Bot構成

| Bot名 | App ID | 役割 | 送信トリガー | 送信先 |
|-------|--------|------|------------|--------|
| **Cloud code report** | CLAUDE_LINK_APP_ID（既存） | 1日のサマリー | /summary-mid・/summary-end | グループチャット |
| **Acquisition** | 新規作成必要 | お客様からの連絡専用 | auto-reply・lancers_watch | こうすけさん個人 |
| **OpenClaw-Bot** | 新規作成必要 | OpenClawからの通知 | openclaw.json通知フック | こうすけさん個人 |
| **Claude code-Bot** | LARK_APP_ID（既存・昇格） | Claude Code系通知全般 | daily-scout・cron完了・エラー等 | こうすけさん個人 |

## 各Botの詳細

### ① Cloud code report（既存・変更なし）
- App ID: CLAUDE_LINK_APP_ID
- スクリプト: ~/.claude/scripts/claude_link_send.py
- トリガー: /summary-mid・/summary-end 実行時のみ
- 内容: OKR進捗 + タスクまとめ
- 頻度: 1日2〜3回

### ② Acquisition（新規作成）
- App ID: CUSTOMER_BOT_APP_ID（要発行）
- 変更対象スクリプト:
  - ~/.claude/skills/auto-reply/inquiry_monitor.py
  - ~/.claude/scripts/lancers_watch_azoo.py
- トリガー: CW・ここなら・ランサーズの受信メッセージ
- 内容: お客様からの連絡通知・要対応アラート

### ③ OpenClaw-Bot（新規作成）
- App ID: OPENCLAW_BOT_APP_ID（要発行）
- 変更対象: ~/.claude/openclaw.json に通知フック追加
- トリガー: OpenClawが応答生成したとき・重要提案・エラー時
- 内容: OpenClawからの重要メッセージ

### ④ Claude code-Bot（既存LARK_APP_IDを昇格・役割明確化）
- App ID: LARK_APP_ID
- 対象スクリプト:
  - ~/.claude/skills/daily-scout/daily_scout.py（現在CLAUDE_LINK兼用→こちらに移行）
  - ~/.claude/scripts/screen_analyzer.py
  - ~/.claude/skills/sleep-tracking/monthly_assessment.py
- トリガー: スカウト完了・cron完了・システムエラー等
- 内容: Claude Code各種自動処理の完了報告

## 実装ステップ

### Step1（今週）: Acquisition Bot作成
1. Lark Developer Console でアプリ新規作成（名前: Acquisition）
2. App ID/Secret を ~/.bashrc に追記（CUSTOMER_BOT_APP_ID / CUSTOMER_BOT_APP_SECRET）
3. inquiry_monitor.py・lancers_watch_azoo.py の LARK_APP_ID → CUSTOMER_BOT_APP_ID に変更
4. BotをLarkワークスペースに追加・チャンネル設定

### Step2（今週）: Claude code-Bot 昇格
1. daily_scout.py の送信先を LARK_APP_ID に統一（現在CLAUDE_LINK混在）
2. 役割を「Claude Code系システム通知専用」として固定

### Step3（来週）: OpenClaw-Bot作成
1. Lark Developer Console でアプリ新規作成（名前: OpenClaw-Bot）
2. openclaw.json に通知フック追加（重要応答・エラー時にLark送信）
