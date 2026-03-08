#!/usr/bin/env python3
"""
Step 2: codeをトークンに交換して~/.bashrcに保存する

使い方:
  python3 lark_oauth_step2.py <code>

  または リダイレクト先URL全体を渡す場合:
  python3 lark_oauth_step2.py "http://localhost:3000/callback?code=XXXX&state=..."
"""
import os
import sys
import json
import urllib.request
import urllib.parse

APP_ID = os.environ.get("LARK_APP_ID", "")
APP_SECRET = os.environ.get("LARK_APP_SECRET", "")
REDIRECT_URI = "http://localhost:3000/callback"

if not APP_ID or not APP_SECRET:
    print("エラー: LARK_APP_ID / LARK_APP_SECRET が未設定です")
    sys.exit(1)

if len(sys.argv) < 2:
    print("使い方: python3 lark_oauth_step2.py <code または リダイレクトURL>")
    sys.exit(1)

arg = sys.argv[1]

# URL全体が渡された場合はcodeを抽出
if arg.startswith("http"):
    parsed = urllib.parse.urlparse(arg)
    params = urllib.parse.parse_qs(parsed.query)
    if "code" not in params:
        print("エラー: URLにcodeが見つかりません")
        sys.exit(1)
    auth_code = params["code"][0]
else:
    auth_code = arg

print(f"認証コード: {auth_code[:10]}...")

# トークン交換
print("user_access_token を取得中...")

payload = {
    "grant_type": "authorization_code",
    "code": auth_code,
    "redirect_uri": REDIRECT_URI,
    "client_id": APP_ID,
    "client_secret": APP_SECRET,
}

req = urllib.request.Request(
    "https://open.larksuite.com/open-apis/authen/v2/oauth/token",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
except Exception as e:
    print(f"エラー: {e}")
    sys.exit(1)

print("APIレスポンス:", json.dumps(data, indent=2, ensure_ascii=False))

if data.get("code", 0) != 0 or "error" in data:
    print(f"エラー: トークン取得失敗")
    sys.exit(1)

user_access_token = data.get("access_token") or data.get("user_access_token")
refresh_token = data.get("refresh_token")

# user_access_token を ~/.bashrc に保存（有効期間: 2時間）
bashrc_path = os.path.expanduser("~/.bashrc")
with open(bashrc_path, "r") as f:
    lines = f.read().splitlines()
lines = [l for l in lines if "LARK_USER_ACCESS_TOKEN" not in l]
lines.append(f'export LARK_USER_ACCESS_TOKEN="{user_access_token}"')

# refresh_token がある場合は一緒に保存
if refresh_token:
    lines = [l for l in lines if "LARK_REFRESH_TOKEN" not in l]
    lines.append(f'export LARK_REFRESH_TOKEN="{refresh_token}"')
    print(f"✅ refresh_token も保存しました（長期利用可能）")

with open(bashrc_path, "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"\n✅ user_access_token を ~/.bashrc に保存しました（有効期間: 2時間）")
print(f"   user_access_token: {user_access_token[:30]}...")
print(f"\n次を実行して環境変数を反映してください:")
print("  source ~/.bashrc")
print()
print("※ 2時間後に期限切れになったら再度 lark_oauth_step1.py → step2.py を実行してください")
