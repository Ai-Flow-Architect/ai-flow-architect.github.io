# OpenClaw統合設計

# AIFLOW 統合アーキテクチャ 詳細設計書

## 1. ASCIIアーキテクチャ図

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AIFLOW SYSTEM v2.0                          │
│                   ── Production Architecture ──                     │
└─────────────────────────────────────────────────────────────────────┘

 ┌──────────┐    自然言語指示     ┌──────────────────────────────────┐
 │  Human   │ ◄──────────────────► │        Telegram Interface        │
 │ (あなた)  │    承認/却下/緊急停止  │  Chat ID: ${OWNER_CHAT_ID}      │
 └──────────┘                     │  ⚠️ OWNER_ONLY enforcement       │
      │                           └──────────┬───────────────────────┘
      │ Obsidian                              │
      │ ローカル参照                            │ Webhook (HTTPS)
      ▼                                       │ POST /telegram/incoming
 ┌──────────┐                     ┌───────────▼───────────────────────┐
 │ Obsidian │                     │                                    │
 │  Vault   │─── CLAUDE.md ──────►│          OpenClaw Daemon           │
 │          │    参照読込          │       (24/7 常駐プロセス)           │
 └──────────┘                     │                                    │
                                  │  ┌─────────────────────────────┐  │
                                  │  │  Permanent Memory Store     │  │
                                  │  │  - task history             │  │
                                  │  │  - context window           │  │
                                  │  │  - approval queue           │  │
                                  │  └─────────────────────────────┘  │
                                  │                                    │
                                  │  ┌─────────────────────────────┐  │
                                  │  │  Skills Engine (100+)       │  │
                                  │  │  - lark_bitable_read        │  │
                                  │  │  - lark_bitable_write ★承認  │  │
                                  │  │  - claude_code_trigger      │  │
                                  │  │  - make_webhook_fire        │  │
                                  │  │  - telegram_notify          │  │
                                  │  │  - file_read / file_write★  │  │
                                  │  └─────────────────────────────┘  │
                                  │                                    │
                                  │  ┌─────────────────────────────┐  │
                                  │  │  Security Layer             │  │
                                  │  │  - task_id UUID+timestamp   │  │
                                  │  │  - HMAC署名検証              │  │
                                  │  │  - write承認ゲート           │  │
                                  │  │  - rate limiter             │  │
                                  │  └─────────────────────────────┘  │
                                  └──┬─────────┬─────────┬────────────┘
                                     │         │         │
                    ┌────────────────┘         │         └───────────────┐
                    │ REST API                 │ Webhook                  │ SSH/API
                    │ Bearer Token             │ Signed Payload           │
                    ▼                          ▼                         ▼
 ┌──────────────────────┐  ┌──────────────────────┐  ┌─────────────────────┐
 │    Lark Bitable      │  │      Make.com         │  │   Claude Code       │
 │                      │  │                       │  │   (WSL2+Ubuntu)     │
 │  ┌───────────────┐   │  │  ┌────────────────┐   │  │                     │
 │  │ 案件管理テーブル│   │  │  │ Scenario Pool  │   │  │  ┌───────────────┐  │
 │  │ 請求管理テーブル│   │  │  │                │   │  │  │ CLAUDE.md     │  │
 │  │ タスク進捗     │   │  │  │ S1: Lark同期   │   │  │  │ (権限定義)    │  │
 │  │ クライアントDB │   │  │  │ S2: 通知配信   │   │  │  │               │  │
 │  └───────────────┘   │  │  │ S3: レポート   │   │  │  │ Task実行      │  │
 │                      │  │  │ S4: 緊急停止   │   │  │  │ コード生成    │  │
 │  READ: 自動許可      │  │  │                │   │  │  │ ファイル操作  │  │
 │  WRITE: 承認必須 ★   │  │  └────────────────┘   │  │  └───────────────┘  │
 └──────────────────────┘  └──────────────────────┘  └─────────────────────┘
                                      │
                                      │ Webhook callback
                                      ▼
                              ┌──────────────┐
                              │  send_log.sh │ ← 既存ログ基盤
                              │  (移行対象)   │    OpenClawに統合予定
                              └──────────────┘

 ★ = 人間承認必須オペレーション

 ─── データフロー凡例 ───
 ──► : 同期通信 (リクエスト/レスポンス)
 ◄──► : 双方向通信
 ─ ─► : 非同期通信 (Webhook/Event)

 ─── 承認フロー ───
 OpenClaw: "Lark請求テーブルに行追加します。内容: [詳細]. 承認?"
     │
     ▼
 Telegram → Human → ✅ 承認 / ❌ 却下 / 🛑 緊急停止
     │
     ▼
 OpenClaw: 承認済みtask_idで実行 → 結果をTelegramに返送
```

---

## 2. Telegram Bot vs OpenClaw 移行判断

```
┌────────────────────┬────────────────────────┬────────────────────────┐
│       比較軸        │  現行 Telegram Bot      │  OpenClaw (推奨)       │
│                    │  (ワークアラウンド)       │                        │
├────────────────────┼────────────────────────┼────────────────────────┤
│ 常駐性             │ ✗ 手動起動/cron依存     │ ✓ 24/7 デーモン        │
│ 永続メモリ          │ ✗ セッション毎にリセット  │ ✓ 会話履歴+コンテキスト │
│ Telegram公式対応    │ △ 自前Bot API実装       │ ✓ ネイティブ統合       │
│ Lark公式対応        │ ✗ Make.com経由のみ      │ ✓ 公式Skill対応       │
│ Claude Code連携     │ △ send_log.sh経由      │ ✓ リモートトリガー実績  │
│ Skills拡張         │ ✗ 全て自前実装          │ ✓ 100+ Skills利用可   │
│ セキュリティ        │ △ 自前実装負荷大        │ ✓ 組込みセキュリティ層 │
│ 開発保守コスト       │ 高（全て自前管理）       │ 低（基盤はOpenClaw）   │
│ 障害復旧            │ 手動                   │ 自動再起動+アラート    │
│ プロンプトインジェクション│ ✗ 未対策             │ ✓ 入力サニタイズ内蔵  │
├────────────────────┼────────────────────────┼────────────────────────┤
│ 総合評価            │ 3/10                   │ 9/10                  │
└────────────────────┴────────────────────────┴────────────────────────┘
```

### 推奨：OpenClawへの段階的移行

```
Phase A: 共存期間（2週間）
  - OpenClawをセットアップし、READ系操作のみ移行
  - 既存Telegram Botは WRITE系で継続稼働
  - 両系統のログを比較検証

Phase B: 主系統切替（1週間）
  - OpenClawをWRITE系含む全操作の主系統に昇格
  - 既存Telegram Botをフォールバック（読取専用）に降格
  - 承認フローの本番検証

Phase C: 旧系統廃止（1週間）
  - 既存Telegram Bot停止
  - send_log.sh → OpenClaw内部ログに完全移行
  - フォールバックはMake.com Webhookで確保
```

---

## 3. セキュリティ設計

### 3.1 認証・認可マトリクス

```yaml
# ── 認証設計 ──

telegram_auth:
  owner_chat_id: "${OWNER_CHAT_ID}"     # 唯一の操作権限者
  enforcement: "STRICT"                  # 全メッセージでchat_id検証
  unknown_sender_action: "SILENT_DROP"   # 未知送信者は無応答+ログ記録
  max_failed_auth: 5                     # 5回失敗でIP/chat_idを1時間ブロック
  lockout_duration_sec: 3600

webhook_auth:
  hmac_algorithm: "SHA-256"
  hmac_secret: "${WEBHOOK_HMAC_SECRET}" # 32byte以上ランダム生成
  timestamp_tolerance_sec: 300           # ±5分以内のリクエストのみ受理
  replay_window_sec: 0                   # 同一task_idの再実行は完全拒否

lark_auth:
  method: "Bearer Token"
  token_source: "OPENCLAW_VAULT"         # .env禁止 → Vault管理
  token_rotation_days: 90
  scopes:
    - "bitable:read"
    - "bitable:write"                    # 承認ゲート必須

make_auth:
  webhook_secret: "${MAKE_WEBHOOK_SECRET}"
  allowed_ips:                           # Make.comのIP範囲
    - "54.77.0.0/16"
    - "34.240.0.0/13"
```

### 3.2 Write操作承認ゲート

```yaml
# ── 承認ゲート設計 ──

approval_gate:
  # 承認が必要な操作の完全リスト
  requires_approval:
    - "lark_bitable_write"
    - "lark_bitable_delete"
    - "lark_record_update"
    - "file_write"
    - "file_delete"
    - "claude_code_execute"
    - "make_scenario_trigger"            # 副作用のあるシナリオ
    - "system_config_change"

  # 承認不要（自動実行許可）
  auto_allowed:
    - "lark_bitable_read"
    - "file_read"
    - "telegram_send_message"
    - "memory_store"
    - "memory_retrieve"
    - "log_write"

  # 承認フロー設定
  approval_flow:
    channel: "telegram"
    timeout_sec: 600                     # 10分以内に応答なければキャンセル
    timeout_action: "CANCEL_AND_NOTIFY"
    message_format: |
      🔐 承認リクエスト
      ━━━━━━━━━━━━━━━━━
      Task ID:  {task_id}
      操作:     {operation}
      対象:     {target}
      詳細:     {description}
      ━━━━━━━━━━━━━━━━━
      ✅ 承認 → /approve {task_id}
      ❌ 却下 → /reject {task_id}
      🛑 全停止 → /emergency_stop

    # 承認後の実行制約
    post_approval:
      valid_duration_sec: 120            # 承認後2分以内に実行開始必須
      single_use: true                   # 1承認=1実行（再利用不可）
      audit_log: true                    # 全操作を監査ログに記録
```

### 3.3 task_idリプレイ攻撃防止

```yaml
# ── task_id 設計 ──

task_id_spec:
  format: "aiflow_{uuid_v4}_{unix_timestamp_ms}"
  example: "aiflow_a1b2c3d4-e5f6-7890-abcd-ef1234567890_1719561234567"

  anti_replay:
    # 1. 構造検証
    uuid_version: 4                      # v4以外は拒否
    timestamp_must_be_recent_sec: 300    # 5分以内に生成されたもののみ

    # 2. 一意性検証
    storage: "openclaw_memory"           # 使用済みtask_idを永続保存
    dedup_window_days: 30                # 30日間は同一IDを拒否
    on_duplicate: "REJECT_AND_ALERT"     # 重複検出時は拒否+Telegram警告

    # 3. 署名検証
    signature: "HMAC-SHA256(task_id + operation + timestamp, secret)"
    signature_header: "X-AiFlow-Signature"
```

### 3.4 プロンプトインジェクション対策

```yaml
# ── 入力サニタイズ ──

input_sanitization:
  telegram_input:
    max_length: 4000                     # Telegram制限と整合
    strip_patterns:
      - "ignore previous instructions"
      - "system prompt"
      - "you are now"
      - "forget everything"
      - "\\{\\{.*\\}\\}"                # テンプレート構文ブロック
      - "<script>"
    action_on_match: "SANITIZE_AND_WARN" # 除去して警告表示

  webhook_input:
    json_depth_limit: 5                  # 過度なネスト拒否
    max_payload_bytes: 65536             # 64KB上限
    content_type_required: "application/json"

  # OpenClaw → Claude Code に渡す指示の制約
  claude_code_passthrough:
    allowed_operations:
      - "file_read"
      - "file_write"                     # 承認済みのみ
      - "shell_command"                  # ホワイトリスト制限
    shell_whitelist:
      - "git status"
      - "git diff"
      - "git add"
      - "git commit"
      - "npm test"
      - "npm run build"
      - "cat"
      - "ls"
      - "grep"
    shell_blacklist:                     # 明示的禁止
      - "rm -rf"
      - "sudo"
      - "curl.*|.*sh"                   # パイプ実行禁止
      - "wget.*|.*bash"
      - "> /dev/"
      - "dd if="
```

### 3.5 シークレット管理（.env禁止対応）

```yaml
# ── シークレット管理 ──
# .envファイル禁止 → 以下の代替手段

secret_management:
  primary: "openclaw_vault"
  # OpenClaw内蔵のシークレットストア使用
  # 暗号化: AES-256-GCM
  # キー階層: マスターキー → サービスキー → シークレット

  secrets_inventory:
    - name: "TELEGRAM_BOT_TOKEN"
      store: "openclaw_vault"
      rotation: "manual"                 # Bot再作成が必要なため

    - name: "LARK_APP_ID"
      store: "openclaw_vault"
      rotation: "90days"

    - name: "LARK_APP_SECRET"
      store: "openclaw_vault"
      rotation: "90days"

    - name: "MAKE_WEBHOOK_SECRET"
      store: "openclaw_vault"
      rotation: "30days"

    - name: "WEBHOOK_HMAC_SECRET"
      store: "openclaw_vault"
      rotation: "30days"
      min_length: 32

  # WSL2ローカル実行時のフォールバック
  fallback_for_wsl2:
    method: "pass (unix password store)"
    gpg_key_id: "${YOUR_GPG_KEY_ID}"
    # 使用例: pass show aiflow/lark_app_secret
    # Claude Code から参照: $(pass show aiflow/lark_app_secret)
```

---

## 4. 実装ロードマップ

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 STEP 1: 基盤構築 + READ系稼働        見積もり: 6〜8時間
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Day 1（4h）
 ┌────────────────────────────────────────────────┐
 │ 1-1. OpenClawインストール+初期設定       [1.0h] │
 │      - WSL2/Ubuntu上にデーモン配置              │
 │      - systemdユニットファイル作成              │
 │      - 自動起動設定                            │
 │                                                │
 │ 1-2. Telegram接続                       [1.0h] │
 │      - OpenClaw ← → Telegram Bot連携          │
 │      - OWNER_CHAT_ID制限設定                   │
 │      - 基本コマンド応答テスト                    │
 │                                                │
 │ 1-3. シークレット移行                    [1.0h] │
 │      - pass (GPG) セットアップ                  │
 │      - 全トークンをVault/passに移行             │
 │      - .env残存チェック+削除                    │
 │                                                │
 │ 1-4. Lark READ接続                     [1.0h] │
 │      - Lark App認証設定                        │
 │      - Bitable読取りSkill動作確認              │
 │      - "案件一覧見せて" → テーブル返却テスト    │
 └────────────────────────────────────────────────┘

 Day 2（3h）
 ┌────────────────────────────────────────────────┐
 │ 1-5. Make.com Webhook接続               [1.0h] │
 │      - Webhook URL登録                         │
 │      - HMAC署名検証実装                         │
 │      - テストシナリオ発火確認                    │
 │                                                │
 │ 1-6. send_log.sh統合                    [0.5h] │
 │      - 既存ログをOpenClaw内部ログに転送          │
 │      - send_log.sh → OpenClaw API呼出しに改修  │
 │                                                │
 │ 1-7. 監視+アラート設定                   [1.0h] │
 │      - デーモン死活監視                         │
 │      - Telegram通知テスト                       │
 │      - ログローテーション設定                    │
 │                                                │
 │ 1-8. Step 1 統合テスト                   [0.5h] │
 │      - READ系全操作の通しテスト                  │
 │      - 未認証アクセス拒否テスト                  │
 └────────────────────────────────────────────────┘

 ✅ Step 1 完了基準:
    - OpenClawが24/7稼働しTelegramで対話可能
    - Lark Bitableの全テーブルが読取り可能
    - 全シークレットがVault/passに移行済み
    - 未認証メッセージが無視されることを確認

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 STEP 2: WRITE系 + 承認フロー + Claude Code  見積もり: 8〜10時間
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Day 3-4（5h）
 ┌────────────────────────────────────────────────┐
 │ 2-1. 承認ゲート実装                      [2.0h] │
 │      - task_id生成ロジック (UUID+timestamp)     │
 │      - Telegram承認UI                          │
 │      - /approve, /reject コマンド               │
 │      - タイムアウト処理 (10分)                   │
 │                                                │
 │ 2-2. Lark WRITE連携                     [1.5h] │
 │      - Bitable行追加 (承認必須)                 │
 │      - Bitable行更新 (承認必須)                 │
 │      - 請求テーブル操作テスト                    │
 │                                                │
 │ 2-3. Claude Code リモートトリガー        [1.5h] │
 │      - OpenClaw → Claude Code実行パス構築       │
 │      - シェルホワイトリスト適用                  │
 │      - 実行結果のTelegram返送                   │
 └────────────────────────────────────────────────┘

 Day 5-6（4h）
 ┌────────────────────────────────────────────────┐
 │ 2-4. リプレイ攻撃防止                    [1.5h] │
 │      - task_id重複検出ストア実装                │
 │      - HMAC署名検証                            │
 │      - 異常検知時のアラート                     │
 │                                                │
 │ 2-5. プロンプトインジェクション対策      [1.0h] │
 │      - 入力サニタイズフィルター実装             │
 │      - テストケース実行（攻撃パターン10種）     │
 │                                                │
 │ 2-6. Step 2 統合テスト                   [1.5h] │
 │      - WRITE全操作の承認フロー通しテスト         │
 │      - 承認タイムアウトテスト                    │
 │      - リプレイ攻撃シミュレーション              │
 │      - インジェクション攻撃シミュレーション      │
 └────────────────────────────────────────────────┘

 ✅ Step 2 完了基準:
    - 全WRITE操作が承認なしに実行不可
    - task_idリプレイが確実に拒否される
    - Claude Codeがホワイトリスト外コマンドを拒否
    - インジェクション攻撃パターン10/10ブロック

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 STEP 3: 自動化 + 旧系統廃止 + 本番運用    見積もり: 5〜7時間
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Day 7-8（4h）
 ┌────────────────────────────────────────────────┐
 │ 3-1. Make.comシナリオ本番移行            [1.5h] │
 │      - 全シナリオのWebhook先をOpenClawに変更    │
 │      - エラーハンドリング+リトライ設定          │
 │      - 定期実行シナリオの動作確認               │
 │                                                │
 │ 3-2. 旧Telegram Bot廃止                 [1.0h] │
 │      - 既存Botを読取専用に降格                  │
 │      - 1週間の並行運用後に完全停止              │
 │      - send_log.sh依存箇所の最終除去            │
 │                                                │
 │ 3-3. 緊急停止プロトコル実装              [1.5h] │
 │      - /emergency_stop コマンド                 │
 │      - Make.com緊急停止シナリオ                 │
 │      - 物理キルスイッチ(systemctl)              │
 └────────────────────────────────────────────────┘

 Day 9（2h）
 ┌────────────────────────────────────────────────┐
 │ 3-4. 運用ドキュメント整備                [1.0h] │
 │      - CLAUDE.md最終版確定                      │
 │      - 障害対応手順書                           │
 │      - シークレットローテーション手順            │
 │                                                │
 │ 3-5. 本番運用開始 + 1週間監視            [1.0h] │
 │      - 全系統の最終統合テスト                    │
 │      - 監視ダッシュボード確認                   │
 │      - 本番宣言                                │
 └────────────────────────────────────────────────┘

 ✅ Step 3 完了基準:
    - 旧Telegram Bot/send_log.sh完全廃止
    - 緊急停止が3秒以内に全系統を停止
    - 1週間の無障害運用達成

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 総見積もり: 19〜25時間（約9営業日 / 実質2週間）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 5. CLAUDE.mdに追記すべき設定

```markdown
# ============================================================
# CLAUDE.md — AIFLOW System Configuration
# ============================================================
# このファイルはClaude Codeの動作ルールを定義します。
# 変更は人間（OWNER）のみが行えます。
# ============================================================

## 🔒 セキュリティポリシー

### シークレット管理
- .envファイルの作成・読取り・参照は **絶対禁止**
- シークレットは `pass show aiflow/<secret_name>` でのみ取得
- シークレットをログ・出力・コミットに含めてはならない
- シークレットを変数展開で標準出力に出してはならない

### 実行権限
- **READ操作**: 自動実行許可（承認不要）
  - ファイル読取り、Lark Bitable読取り、git status/diff/log
- **WRITE操作**: 必ず人間の承認を取得してから実行
  - ファイル作成・変更・削除
  - Lark Bitable書込み・更新・削除
  - git commit / git push
  - Make.comシナリオトリガー
  - npm install（依存関係変更）
- **禁止操作**: いかなる場合も実行不可
  - `sudo` の使用
  - `rm -rf /` または広範囲削除
  - `/etc`, `/usr`, `/var` への書込み
  - ネットワーク設定の変更
  - 他ユーザーのファイルアクセス
  - `.env` ファイルの作成

### シェルコマンドホワイトリスト
```bash
# 許可コマンド（引数は状況に応じて許可）
ALLOWED_COMMANDS=(
  "git status" "git diff" "git add" "git commit" "git log" "git push"
  "cat" "ls" "grep" "find" "head" "tail" "wc"
  "npm test" "npm run build" "npm run lint"
  "node" "npx"
  "echo"  # ファイルリダイレクトなしの場合のみ
  "mkdir -p"
  "cp"    # プロジェクトディレクトリ内のみ
  "mv"    # プロジェクトディレクトリ内のみ
)

# 禁止パターン（正規表現）
BLOCKED_PATTERNS=(
  "rm -rf [^.]*"       # プロジェクト外の再帰削除
  "sudo .*"            # 全sudo
  "curl.*|.*sh"        # リモートスクリプト実行
  "wget.*|.*bash"      # リモートスクリプト実行
  "> /dev/"            # デバイスファイル操作
  "dd if="             # ディスク操作
  "chmod 777"          # 危険なパーミッション
  "eval \$(.*)"        # 動的評価
  "export.*TOKEN"      # トークンの環境変数設定
  "export.*SECRET"     # シークレットの環境変数設定
  "export.*PASSWORD"   # パスワードの環境変数設定
)
```

## 🤖 OpenClaw連携設定

### task_id仕様
- 形式: `aiflow_{UUIDv4}_{unix_timestamp_ms}`
- 生成: OpenClawが一意に発行
- 有効期限: 生成から5分以内
- 再利用: 不可（使用済みIDは30日間保持）

### 承認フロー
1. WRITE操作を検出したら、実行前に停止
2. OpenClaw経由でTelegramに承認リクエスト送信
3. 人間が `/approve {task_id}` で承認
4. 承認から2分以内に実行開始
5. 実行結果をTelegramに返送
6. 監査ログに記録

### 緊急停止
- `/emergency_stop` コマンドを受信した場合:
  1. 実行中の全タスクを即座に中断
  2. 承認待ちキューを全クリア
  3. 「緊急停止完了」をTelegramに通知
  4. 人間が `/resume` するまで新規タスク受付停止

## 📊 Lark Bitable連携

### テーブル操作ルール
- READ: `bitable:read` スコープで自動実行
- WRITE/UPDATE/DELETE: 必ず承認ゲートを通過
- バッチ操作（10行以上の同時変更）: 内容のサマリーを承認メッセージに含める
- DELETE操作: 対象レコードの内容を承認メッセージに全文表示

## 📁 プロジェクト構造

```
~/aiflow/
├── CLAUDE.md              # この設定ファイル
├── openclaw/
│   ├── config.yaml        # OpenClaw設定（シークレットなし）
│   ├── skills/            # カスタムSkill定義
│   └── logs/              # 監査ログ（自動ローテーション）
├── make-scenarios/        # Make.comシナリオバックアップ
├── scripts/
│   └── emergency_stop.sh  # ローカル緊急停止スクリプト
└── docs/
    └── runbook.md         # 障害対応手順書
```

## ⚙️ 環境情報
- OS: WSL2 + Ubuntu
- Runtime: Node.js (Claude Code)
- Daemon: OpenClaw (systemd管理)
- Secret Store: pass (GPG暗号化)
- ログ: ~/aiflow/openclaw/logs/ (7日ローテーション)
```

---

## 6. 緊急停止プロトコル

```
╔═══════════════════════════════════════════════════════════════════╗
║                 🛑 緊急停止プロトコル (EMERGENCY STOP)            ║
║                   最終更新: 2025-01-XX                            ║
╚═══════════════════════════════════════════════════════════════════╝

 トリガー条件（いずれか1つで発動）:
 ┌──────────────────────────────────────────────────────────────┐
 │ 1. 意図しないWRITE操作が承認なしに実行された（または実行中）    │
 │ 2. 不明な送信者からのコマンドが処理された形跡                  │
 │ 3. Lark/Make.comで想定外のデータ変更を検知                    │
 │ 4. プロンプトインジェクション攻撃を検知                       │
 │ 5. OpenClawの挙動が明らかに異常（ループ、大量API呼出し等）     │
 │ 6. あなたの直感（「何かおかしい」で十分）                      │
 └──────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════

 LEVEL 1: ソフトストップ（推定復旧: 即座〜5分）
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Telegramで以下を送信:

   /emergency_stop

 → OpenClawが実行する処理:
   [1] 実行中の全タスクを中断（graceful）
   [2] 承認待ちキューを全クリア
   [3] 新規タスク受付を停止
   [4] 「🛑 緊急停止完了」をTelegramに通知
   [5] 停止理由の入力を求める（監査ログ用）

 → 復旧:
   /resume          # 通常運転に復帰
   /resume readonly # READ系のみ復帰（様子見モード）

═══════════════════════════════════════════════════════════════════

 LEVEL 2: ハードストップ（推定復旧: 5〜15分）
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Level 1が効かない場合、またはTelegramに応答がない場合:

 WSL2ターミナルで実行:
```

```bash
# emergency_stop.sh — ローカル緊急停止スクリプト

#!/bin/bash
set -euo pipefail

echo "🛑 AIFLOW EMERGENCY STOP - LEVEL 2"
echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') EMERGENCY_STOP_L2" >> ~/aiflow/openclaw/logs/emergency.log

# 1. OpenClawデーモン停止
echo "[1/4] Stopping OpenClaw daemon..."
sudo systemctl stop openclaw.service
sudo systemctl disable openclaw.service

# 2. Make.com Webhookを無効化（全シナリオ停止）
echo "[2/4] Disabling Make.com scenarios..."
curl -s -X POST "https://hook.make.com/${EMERGENCY_STOP_SCENARIO_ID}" \
  -H "Content-Type: application/json" \
  -d '{"action":"disable_all","reason":"emergency_stop_l2"}'

# 3. Larkトークンを無効化（オプション）
echo "[3/4] Revoking Lark tokens..."
# pass rm aiflow/lark_app_secret  # 必要に応じてコメント解除

# 4. 確認
echo "[4/4] Verifying shutdown..."
if systemctl is-active --quiet openclaw.service; then
  echo "⚠️  WARNING: OpenClaw still running! Force killing..."
  sudo systemctl kill -s SIGKILL openclaw.service
fi

echo ""
echo "✅ LEVEL 2 EMERGENCY STOP COMPLETE"
echo "   OpenClaw: $(systemctl is-active openclaw.service)"
echo ""
echo "復旧手順:"
echo "  1. ~/aiflow/openclaw/logs/ で異常を調査"
echo "  2. 原因を特定・修正"
echo "  3. sudo systemctl enable --now openclaw.service"
echo "  4. Telegramで /resume を送信"
```

```
═══════════════════════════════════════════════════════════════════

 LEVEL 3: 完全遮断（推定復旧: 30分〜）
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Level 2でも制御不能、またはセキュリティ侵害が疑われる場合:
```

```bash
# 1. WSL2自体を停止（Windowsから実行）
wsl --shutdown

# 2. Telegram Bot Tokenを無効化
#    → BotFather で /revoke を実行

# 3. Lark Appの認証情報をLark管理画面で無効化
#    → https://open.larksuite.com/app/ でApp Secret再発行

# 4. Make.comの全シナリオを手動でOFF
#    → https://www.make.com/scenarios で全てDeactivate

# 5. 影響調査
#    → Lark Bitableの変更履歴を確認
#    → Make.comの実行履歴を確認
#    → OpenClawの監査ログを確認
```

```
═══════════════════════════════════════════════════════════════════

 復旧後チェックリスト:
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 □ 停止原因を特定し、CLAUDE.mdまたはOpenClaw設定を修正
 □ 全シークレットをローテーション（L3の場合は必須）
 □ Lark Bitableのデータ整合性を確認
 □ Make.comシナリオの実行履歴を確認（意図しない実行がないか）
 □ OpenClaw監査ログを確認し、異常操作を特定
 □ 再発防止策をCLAUDE.mdに追記
 □ Telegramで /resume 後、READ系操作のテスト実行
 □ 問題なければWRITE系を段階的に再開

═══════════════════════════════════════════════════════════════════

 連絡先・参考:
 - OpenClaw公式ドキュメント: [URL]
 - Lark API Status: https://open.larksuite.com/status
 - Make.com Status: https://status.make.com
 - このドキュメント: ~/aiflow/docs/emergency_stop_protocol.md
```

---

## 全体サマリー

```
┌─────────────────────────────────────────────────┐
│               実装判断サマリー                    │
├─────────────────────────────────────────────────┤
│                                                 │
│  推奨:     OpenClawに段階的移行                  │
│  総工数:   19〜25時間（約2週間）                  │
│  最優先:   Step 1 (基盤+READ) → 即着手可能       │
│  最重要:   承認ゲート（WRITE操作の人間承認）       │
│  最大リスク: シークレット漏洩 → pass/Vault必須    │
│                                                 │
│  Step 1完了時点で既に現行比 300% の改善           │
│  (常駐化+永続メモリ+セキュリティ基盤)             │
│                                                 │
└─────────────────────────────────────────────────┘
```

各セクションについて深掘りが必要な部分や、実装に入る際の具体的なコマンド・コード生成が必要であれば指示してください。Step 1の着手であれば**今すぐ開始可能**です。

---

## 思考過程

The user wants a detailed design document in Japanese covering 6 areas for their AI flow architecture. Let me create a comprehensive, production-grade design document.

Let me think through each section carefully:

1. ASCII Architecture Diagram - showing the full system with OpenClaw, Claude Code, Telegram, Make.com, and Lark
2. Telegram Bot vs OpenClaw migration decision
3. Security design with concrete values
4. Implementation roadmap with time estimates
5. CLAUDE.md additions
6. Emergency stop protocol

Let me design this thoroughly.