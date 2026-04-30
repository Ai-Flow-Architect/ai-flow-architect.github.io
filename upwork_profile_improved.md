# Upwork Profile — 改善案（2026-03-19）

---

## 改善方針サマリー

| 項目 | 現状 | 改善後 |
|------|------|--------|
| タイトル | 57文字・汎用的 | 79文字・キーワード強化 |
| 概要文 | 機能列挙型 | 成果・ROI訴求型に刷新 |
| スキルタグ | 12個（上限超え） | 上位10個に絞り込み |
| 時間単価 | $65推奨 | $55スタート → $75目標の段階戦略 |

---

## ① タイトル（改善案）

### 現状
```
AI Workflow Automation Specialist | Make.com × GPT Expert
```
（57文字）

### 改善案A — SEO重視（検索流入最大化）
```
AI Automation Engineer | Make.com · GPT-4 · Python · Playwright | Workflow & RPA Expert
```
（89文字 / 主要キーワードを前半に集中配置）

### 改善案B — 成果訴求型（ROI訴求）
```
Workflow Automation Specialist | Make.com × GPT × Python | 10x Efficiency for SMBs
```
（84文字 / 「10x Efficiency」で即効性を伝達）

### 改善案C — ニッチ特化型（競合少・単価高）
```
AI-Powered RPA Developer | Make.com + Playwright + OpenAI | Business Process Automation
```
（89文字 / RPA × AI の掛け合わせで差別化）

**推奨: 改善案A**（検索ヒット率を最優先。実績が積まれたら改善案Bへ移行）

### 改善理由
- Upwork検索は「Make.com」「GPT-4」「Playwright」「Python」「RPA」が高頻度キーワード
- 現状タイトルは `Make.com × GPT` のみ → 残りのキーワードが検索で拾われない
- `|` で区切ることでスキャンしやすく、アルゴリズムにも優しい

---

## ② 概要文（改善案）

### 現状の課題
- 機能・ツール列挙が中心で「クライアントが得られる価値」が弱い
- 導入部が受動的（"I specialize in..." より能動的な書き出しが効果的）
- 実績の数字が少ない（具体性不足）

### 改善案（全文）

```
If your team is drowning in repetitive tasks — manual data entry, slow follow-ups,
copy-paste reporting — I build AI systems that handle those automatically.

I'm Kosuke, an AI automation consultant based in Japan. Under the AIFLOW brand,
I design and ship end-to-end intelligent workflows for SMBs and solo founders
who want to scale without scaling headcount.

━━ What I've built ━━

▸ AI Job Application Engine
  Searches 3 freelance platforms, GPT-scores every opportunity, writes tailored proposals,
  and auto-submits 20+ applications/day — reducing manual effort from 3 hours to under 10 minutes.

▸ 24/7 Inquiry Auto-Reply System
  Monitors CrowdWorks, Coconala, and Lancers for new inquiries. GPT classifies each message,
  generates appropriate responses instantly, and flags edge cases for human review via Lark.
  Response time: hours → under 5 minutes. Zero manual monitoring.

▸ Automated Business Dashboard
  Pulls KPI data from Google Sheets, Lark Bitable, and external APIs every morning,
  transforms it, and delivers a formatted report to a Lark channel automatically.
  30 minutes of daily manual work → fully eliminated.

▸ E-commerce Re-listing Automation
  Full Playwright flow for product re-listing on Mercari: data collection → image download
  → delisting → re-listing. Processes items in bulk with zero manual steps.

━━ Core Tech Stack ━━

• Automation:   Make.com · n8n · Python (cron/asyncio)
• AI/LLM:       OpenAI API (GPT-4o) · Gemini API · prompt engineering
• RPA/Browser:  Playwright · headless Chrome automation
• Data & APIs:  Google Sheets API · Lark/Feishu API · REST/Webhook integration
• Infra:        Linux/WSL2 · systemd · GitHub Actions

━━ Why work with me ━━

→ Solo operator = fast decisions, direct communication, no middlemen
→ I build what I actually use — every system has been tested in production
→ I document everything: architecture diagrams, runbooks, handoff materials included
→ Available 20–30 hrs/week | Response within 12 hours (JST)

If you have a workflow that's burning your team's time, let's talk.
Drop me a message with a short description of what you'd like to automate.
```

（文字数: 約1,800文字 / 5,000文字制限に対し余裕を持たせた構成）

### 改善ポイント解説

| ポイント | 現状 | 改善後 |
|---------|------|--------|
| 冒頭フック | "I specialize in..." （受動的） | 読み手の痛みを先に言語化 |
| 実績の具体性 | 数字が一部のみ | 4事例すべてに数値・Before→After |
| ツールスタック | 箇条書き羅列 | カテゴリ別に整理・視認性向上 |
| 差別化要素 | "solo consultant" 1行 | 4つのバリュープロポジション |
| CTA | なし | 「Drop me a message...」で次行動を誘導 |

---

## ③ スキルタグ（トップ10）

Upworkのスキルタグは上位15個が検索ランキングに影響。現状12個から10個に絞り込み、検索頻度の高い順に並べる。

| 優先度 | スキルタグ | 理由 |
|--------|-----------|------|
| 1 | **Automation** | 最も広義・検索ボリューム最大 |
| 2 | **Make.com** | 差別化ツール・需要急増中 |
| 3 | **Python** | 必須汎用スキル・高頻度検索 |
| 4 | **OpenAI API** | AI案件の核心キーワード |
| 5 | **API Integration** | 広義・多くの案件でマッチ |
| 6 | **Web Scraping** | Playwright案件への入り口 |
| 7 | **Workflow Automation** | "Automation"と合わせて二重捕捉 |
| 8 | **Chatbot Development** | AI×チャットボット案件が急増 |
| 9 | **Playwright** | RPA案件での差別化 |
| 10 | **Google Sheets API** | 中小企業案件で高頻度 |

**削除候補（検索ボリューム低 or 重複）**
- `n8n` → Make.comと重複、n8n案件はまだ少ない
- `Lark / Feishu` → 日本・中国市場外では認知度低
- `RPA` → Playwrightで代替可能

---

## ④ 時間単価設定（市場調査ベース）

### 市場相場（2026年・Upwork AI/Automation分野）

| レベル | 相場 | 特徴 |
|--------|------|------|
| 新規参入（レビューなし） | $30–50/hr | プロフィール構築フェーズ |
| 実績あり（5件以上） | $55–80/hr | 安定受注フェーズ |
| Top Rated | $80–120/hr | 選ばれる存在フェーズ |
| Expert-Vetted | $120–200/hr | トップ1% |

### 推奨戦略（段階的単価引き上げ）

```
Phase 1（現在〜3件受注）: $55/hr
  → レビュー獲得が最優先。多少安くても実績を作る。
  → 固定価格プロジェクト（Fixed Price）も積極活用。

Phase 2（5件・JSS 90%以上）: $65–70/hr
  → Job Success Score が上がったら単価を引き上げる。
  → 新規プロポーザルから新単価を適用。

Phase 3（Top Rated取得後）: $80–100/hr
  → バッジ取得後は価格競争から脱出。専門性・成果で選ばれる。
```

**現状の $65 設定について**
- レビューゼロの段階では高め。初期は $55 スタートを推奨。
- ただし、固定価格プロジェクトなら $65 相当のスコープで提案しても通る場合あり。
- 最初の1〜2件は「レビューを買う」くらいの感覚で価格より成功率を優先。

---

## ⑤ 追加改善チェックリスト

| 項目 | アクション |
|------|-----------|
| プロフィール写真 | 白背景・ビジネスカジュアル・顔が大きく映るもの（信頼感+20%） |
| ポートフォリオ画像 | 各プロジェクトにスクリーンショット or フロー図を追加 |
| プロフィールビデオ | 60秒英語自己紹介動画（Top Rated への近道） |
| Availability | 「Open to offers」をONにして露出を増やす |
| Specialized Profiles | "AI Automation" 専門プロファイルを別途作成（Upwork機能） |
| Connects配分 | 最初の1ヶ月は1日2〜3件・Boosted Proposalを2〜3件試す |
