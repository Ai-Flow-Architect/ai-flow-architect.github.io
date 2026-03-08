#!/usr/bin/env python3
"""
refresh_tokenからuser_access_tokenを取得するヘルパースクリプト

使い方:
  python3 lark_get_user_token.py

  または bash から:
  USER_TOKEN=$(python3 lark_get_user_token.py)

初回セットアップ:
  python3 lark_oauth_setup.py を先に実行して
  ~/.bashrc に LARK_USER_REFRESH_TOKEN を保存すること
"""

import os
import sys
import json
import urllib.request

APP_ID = os.environ.get("LARK_APP_ID", "")
APP_SECRET = os.environ.get("LARK_APP_SECRET", "")
REFRESH_TOKEN = os.environ.get("LARK_USER_REFRESH_TOKEN", "")

if not REFRESH_TOKEN:
    print("エラー: LARK_USER_REFRESH_TOKEN が未設定です", file=sys.stderr)
    print("先に python3 lark_oauth_setup.py を実行してください", file=sys.stderr)
    sys.exit(1)

payload = {
    "grant_type": "refresh_token",
    "refresh_token": REFRESH_TOKEN,
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
    print(f"エラー: {e}", file=sys.stderr)
    sys.exit(1)

if data.get("code", 0) != 0 or "error" in data:
    print(f"エラー: {json.dumps(data, ensure_ascii=False)}", file=sys.stderr)
    sys.exit(1)

user_access_token = data.get("access_token") or data.get("user_access_token")
new_refresh_token = data.get("refresh_token")

# 新しいrefresh_tokenが返ってきたら~/.bashrcを更新
if new_refresh_token and new_refresh_token != REFRESH_TOKEN:
    import subprocess
    subprocess.run([
        "sed", "-i",
        f"s/export LARK_USER_REFRESH_TOKEN=.*/export LARK_USER_REFRESH_TOKEN=\"{new_refresh_token}\"/",
        os.path.expanduser("~/.bashrc")
    ])

# user_access_tokenのみ標準出力（bash変数への代入用）
print(user_access_token)
