# CLAUDE.md

## このプロジェクトについて
Claude Code の個人設定・スキル管理・外部ツール連携を統合する作業ハブ。
Lark / GPT / Obsidian / n8n を活用して日常タスクを自動化・効率化する。

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

### LP（GitHub Pages）のAPIキー方針 ← 2026-07-17 全面改訂

- **リポジトリ**: `Ai-Flow-Architect/ai-flow-architect.github.io`
- **🔴 鉄則: 公開HTMLにAPIキーを載せない。プレースホルダー方式も禁止**（＝旧ルール「プレースホルダー形式を維持すること」は**撤回**）。
  - **なぜ撤回したか**: GitHub Pages は静的配信で、`deploy.yml` の "Inject API Keys" が実キーを焼き込んでいた。結果 **Gemini実キーが view-source で誰でも読める状態**になり、しかも実測でそのキーは有効なままだった（2026-07-17 発覚）。**プレースホルダーは鍵を隠さない**＝旧ルール自体が事故の指示になっていた。
  - リファラ制限も対策にならない（`Referer` は curl で偽装可能）。課金上限は被害額を決めるだけで漏洩を止めない。
- **方式**: LLMを呼ぶ経路は**必ずサーバー側プロキシ**を通し、鍵をブラウザへ配らない。
  - OpenAI = Cloudflare Worker（`WORKER_URL`）経由。冗長化が要る場合も**Worker側にモデルを足す**（ブラウザに鍵を戻さない）。
  - LLMが使えない時は静的FAQ（`FAQ_DB`）→問い合わせ誘導へ落とす設計を維持。
- **強制**: `scripts/assert_no_secrets.py` が deploy 前に公開HTMLを走査し、キーを検出したら**デプロイを止める**（コメントで注意喚起しても次に触る者が戻せば再発するため機械で止める）。**このステップを外さないこと。**

### GWS CLI（Google Workspace CLI）
- **バージョン**: v0.11.1（オープンソースベータ、v1.0未満）
- **バイナリ**: `~/.local/bin/gws`
- **対応サービス**: Drive / Sheets / Gmail / Calendar / Docs / Slides / Tasks / People / Chat / Classroom / Forms / Keep / Meet
- **認証**: OAuth 2.0（Google Cloud Console でクライアントID発行 → `gws auth login`）
- **設定ディレクトリ**: `~/.config/gws`
- **使い方**: `gws <service> <resource> <method> --params '{...}'`（JSON出力、Claude Codeと相性◎）
- **リポジトリ**: https://github.com/googleworkspace/cli

### Claude-link（Larkブリーフィングボット）
- **用途**: `/summary-mid` `/summary-end` 実行時にOKR進捗+タスク状況をLarkチャットに自動送信
- **認証変数**: `$CLAUDE_LINK_APP_ID` / `$CLAUDE_LINK_APP_SECRET`
- **chat_id**: `oc_01a50d5000a68e33718b938d2b177a27`
- **送信スクリプト**: `~/.claude/scripts/claude_link_send.py`
- **データソース**: Obsidian日次ログ（自動読取り）+ JSON引数

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
| `/gym-menu` | 筋トレメニュー自動生成（n8n） |
| `/auto-gantt` | ガントチャート自動生成（n8n） |
| `/mermaid-to-obsidian` | Mermaid図を生成してObsidianノートに書き込み |
| `/okr-plan` | 月次OKR戦略検討（AIFLOWプラン参照→Claude対話→Lark OKR記入テキスト生成） |
| `/okr-check` | 週次OKR進捗FB（Lark OKR読み込み→状況ヒアリング→更新提案出力） |
| `/mercari-relist` | メルカリ再出品自動化（出品データ収集→画像DL→取り下げ→新規出品をPlaywrightで全自動） |
| `/excalidraw` | Excalidraw形式の図（フローチャート・マインドマップ等）を生成してファイル保存 |
| `/clair` | Clair（クレア）AI秘書（思考・TODO・アイデアを雑に投げる→整理・分類・Obsidian記録・ルーティング提案） |
| `/day-strategy` | 日次タスク設計（前日持越し+新規統合→依存・認知負荷考慮→得点表で提示、計画のみ） |
| `/blind-spot` | 毎週土曜：最新AI情報をWeb検索→現在設定と比較→盲点TOP5をROI付きで提案 |
| `/agent-teams` | ROI評価付き開発フロー（CEO/FM評価→GPT壁打ち→実装→スキル化まで一貫） |
| `/make-dev` | n8n開発ナレッジ（設計→JSON生成→テスト→デバッグ＋落とし穴集） |
| `/make-token-refresh` | n8n APIトークン自動取得（Playwrightでログインセッション管理・~/.bashrc更新） |
| `/skill-creator` | 新規スキル作成・既存スキル改善・評価・ベンチマーク（Anthropic公式） |
| `/cw-scout` | CW案件自動スカウト＆応募（検索→GPTスコアリング→応募文生成→Playwright自動応募10件/日） |
| `/clarify` | 思考整理（雑なアイデア→構造化→欠けているピース指摘→改善提案） |
| `/research` | 構造化リサーチ（Web検索→インサイト・トレンド・データ→レポート） |
| `/solve` | 問題分解・解決（根本原因特定→分解→解決策比較→実行ステップ） |
| `/week-strategy` | 週次スケジュール設計（Larkカレンダー連携→不要削除→最適配置→最終チェック） |
| `/ai-unstuck-playbook` | 詰まり自己診断（停滞宣言→状態圧縮→解法切替の3ステップ） |
| `/youtube-learn-do` | YouTube字幕取得→要約→ROIアクション抽出→即実践 |
| `/neta-trend` | 毎朝の情報収集（HackerNews・Reddit・Dev.to→興味度スコア付きトレンド） |
| `/pro-image` | プロ品質日本語画像生成（Gemini 3.1 Flash Image一発生成、日本語テキスト100%正確） |
| `/normal-image` | 汎用画像生成（FLUX.2+GPT+Gemini 3エンジン競争、日本語テキスト不要のフロー図等向け） |
| `/gemini-image` | Gemini画像生成（英語生成→few-shot翻訳で日本語化、ビジネス画像特化）※pro-imageに統合予定 |
| `/auto-reply` | お問い合わせ自動返信（CW+ココナラ+ランサーズ監視→GPT分類→自動返信+Lark通知、cron 30分間隔） |
| `/coconala-scout` | ココナラ公開募集スカウト（検索→GPTスコアリング→応募文生成→CDP経由自動応募5件/日） |
| `/lancers-scout` | ランサーズ案件スカウト（検索→GPTスコアリング→提案文生成→Playwright自動提案7件/日） |
| `/daily-scout` | CW+ココナラ+ランサーズ日次一括スカウト（cron毎朝8:30、合計20件+/日自動応募） |
| `/auto-business` | 自律型ビジネスオペレーション（集客/教育/販売/リピートを2時間自律バッチ実行→レポート） |
| `/x-post` | X自動投稿（AIニュース+ストック、cron平日11:58&17:58の2回、GPT生成+Larkシート連携） |
| `/decision-making` | 最適解を導く意思決定フレームワーク（State Check→目的基準→選択肢→評価マトリクス→決断→振り返り条件の6ステップ） |
| `/lp-dev` | LP制作・改善（Anthropic公式デザイン哲学+/simplify統合。新規作成・既存改善・デザイン→SEO→コード品質まで一貫） |
