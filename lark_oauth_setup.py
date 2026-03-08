#!/usr/bin/env python3
"""
Lark user_access_token OAuth2セットアップスクリプト
一度だけ実行してrefresh_tokenを~/.bashrcに保存する

使い方:
  python3 lark_oauth_setup.py

事前準備:
  - Lark Developer Console の Security > Redirect URLs に
    http://localhost:3000/callback を追加済みであること
  - Permissions & Scopes に okr:okr スコープを追加済みであること
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import threading
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

# ================================
# 設定
# ================================
REDIRECT_URI = "http://localhost:3000/callback"
PORT = 3000
SCOPES = "okr:okr offline_access"

# 環境変数から取得
APP_ID = os.environ.get("LARK_APP_ID", "")
APP_SECRET = os.environ.get("LARK_APP_SECRET", "")

if not APP_ID or not APP_SECRET:
    print("エラー: LARK_APP_ID / LARK_APP_SECRET が未設定です")
    sys.exit(1)

# ================================
# OAuth2 コールバック受信サーバー
# ================================
auth_code = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("""
            <html><body style="font-family:sans-serif; text-align:center; padding:50px;">
            <h2>✅ 認証成功！</h2>
            <p>このページを閉じてターミナルに戻ってください。</p>
            </body></html>
            """.encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # ログを非表示

# ================================
# メイン処理
# ================================
def main():
    global auth_code

    # Step 1: 認証URLを開く
    auth_url = (
        "https://open.larksuite.com/open-apis/authen/v1/authorize"
        f"?app_id={APP_ID}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&scope={urllib.parse.quote(SCOPES)}"
        f"&state=claude_okr_setup"
    )

    print("=" * 50)
    print("Lark OKR 認証セットアップ")
    print("=" * 50)
    print(f"\n1. ブラウザで以下のURLを開きます...")
    print(f"\n{auth_url}\n")

    # ローカルサーバー起動（0.0.0.0にバインドしてWSL2からも受信可能にする）
    server = HTTPServer(("0.0.0.0", PORT), CallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    print("2. 上のURLをWindowsブラウザにコピーして開いてください。")
    print("   Larkにログインして「許可」すると自動で処理が続きます。\n")

    # コールバックを待機（最大30秒）
    import time
    for i in range(30):
        if auth_code:
            break
        time.sleep(1)

    server.shutdown()

    if not auth_code:
        # 自動受信できなかった場合: 手動でcodeを入力してもらう
        print("━" * 50)
        print("【手動入力モード】")
        print("ブラウザで上のURLを開いてLarkで「許可」した後、")
        print("ブラウザのアドレスバーに表示されるURLをコピーしてください。")
        print("例: http://localhost:3000/callback?code=XXXXXXXX&state=...")
        print("━" * 50)
        callback_url = input("\nリダイレクト先のURL全体を貼り付けてください:\n> ").strip()

        parsed = urllib.parse.urlparse(callback_url)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" not in params:
            print("エラー: URLにcodeパラメータが見つかりません。")
            sys.exit(1)
        auth_code = params["code"][0]

    print(f"3. 認証コード取得成功 ✅")

    # Step 2: コードをトークンに交換
    print("4. user_access_token を取得中...")

    token_payload = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
    }

    req = urllib.request.Request(
        "https://open.larksuite.com/open-apis/authen/v2/oauth/token",
        data=json.dumps(token_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"エラー: トークン取得失敗 - {e}")
        sys.exit(1)

    if "error" in data or data.get("code", 0) != 0:
        print(f"エラー: {json.dumps(data, ensure_ascii=False)}")
        sys.exit(1)

    user_access_token = data.get("access_token") or data.get("user_access_token")
    refresh_token = data.get("refresh_token")

    if not refresh_token:
        print(f"レスポンス: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print("警告: refresh_tokenが取得できませんでした。")
        print("offline_access スコープが許可されているか確認してください。")
    else:
        print(f"5. refresh_token 取得成功 ✅")

    # Step 3: ~/.bashrc に保存
    print("6. ~/.bashrc に保存中...")

    bashrc_path = os.path.expanduser("~/.bashrc")
    with open(bashrc_path, "r") as f:
        content = f.read()

    # 既存のrefresh_token行を削除して再追加
    lines = content.splitlines()
    lines = [l for l in lines if "LARK_USER_REFRESH_TOKEN" not in l]
    lines.append(f'export LARK_USER_REFRESH_TOKEN="{refresh_token}"')
    new_content = "\n".join(lines) + "\n"

    with open(bashrc_path, "w") as f:
        f.write(new_content)

    print("=" * 50)
    print("セットアップ完了！ ✅")
    print("=" * 50)
    print(f"\nuser_access_token: {user_access_token[:20]}...")
    print(f"refresh_token: {refresh_token[:20]}...")
    print(f"\n~/.bashrc に LARK_USER_REFRESH_TOKEN を保存しました。")
    print("\n次のコマンドで環境変数を反映してください:")
    print("  source ~/.bashrc")
    print("\n以降は lark_get_user_token.py で user_access_token を取得できます。")

if __name__ == "__main__":
    main()
