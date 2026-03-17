# X (Twitter) API 投稿権限 修正手順

## 問題
403 Forbidden - Write権限がない

## 修正手順（5分）

1. https://developer.twitter.com/en/apps にアクセス
2. アプリ「Claude code-2」の「Settings」を開く
3. 「App permissions」を **Read → Read and Write** に変更して保存
4. **重要**: Settings → Keys and Tokens に戻り
   - Access Token and Secret の「Regenerate」をクリック
   - 新しいトークンを必ずコピー
5. ~/.bashrc を更新:
   ```bash
   export X_ACCESS_TOKEN="新しいアクセストークン"
   export X_ACCESS_TOKEN_SECRET="新しいアクセストークンシークレット"
   ```
6. `source ~/.bashrc` を実行
7. `python3 ~/.claude/skills/x-post/scripts/post_tweet.py "テスト投稿"` で確認

## 修正後の自動化

毎日 11:58 & 17:58 に以下が自動投稿される:
- Make.com × AI自動化の事例・TIPs
- ROI・工数削減の数字を含む実績ツイート
- 詳細はDMまで → リード獲得

→ 月30万達成に向けた重要なインバウンドチャンネル
