#!/usr/bin/env python3
"""
Step 1: 認証URLを表示する
このURLをWindowsブラウザで開いて「許可」してください。
認証後にブラウザのアドレスバーに表示されるURLから
code=XXXX の部分をコピーして Step 2 に渡してください。
"""
import os
import urllib.parse

APP_ID = os.environ.get("LARK_APP_ID", "")
REDIRECT_URI = "http://localhost:3000/callback"
SCOPES = "okr:okr offline_access calendar:calendar"

auth_url = (
    "https://open.larksuite.com/open-apis/authen/v1/authorize"
    f"?app_id={APP_ID}"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    f"&scope={urllib.parse.quote(SCOPES)}"
    f"&state=claude_okr_setup"
)

print("=" * 60)
print("【Step 1】 以下のURLをWindowsブラウザで開いてください")
print("=" * 60)
print()
print(auth_url)
print()
print("=" * 60)
print("Larkにログインして「許可」した後、")
print("ブラウザのアドレスバーに表示されるURLを確認してください。")
print()
print("例: http://localhost:3000/callback?code=XXXXXXXX&state=...")
print()
print("→ code= の後の値をコピーして、以下を実行してください:")
print()
print("  python3 lark_oauth_step2.py <コピーしたcode>")
print("=" * 60)
