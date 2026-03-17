"""
ランサーズ サービス新規出品スクリプト
業務自動化パッケージ（¥50,000）を出品する
"""
import os
import sys
import time
import subprocess
from playwright.sync_api import sync_playwright


def get_credentials():
    """~/.bashrc から認証情報を取得"""
    result = subprocess.run(
        "source ~/.bashrc && echo $LANCERS_EMAIL && echo $LANCERS_PASSWORD",
        shell=True, capture_output=True, text=True, executable="/bin/bash"
    )
    lines = result.stdout.strip().split("\n")
    return lines[0] if len(lines) > 0 else "", lines[1] if len(lines) > 1 else ""


def login(page):
    """ランサーズにログイン"""
    email, password = get_credentials()
    print(f"ログイン中: {email}")

    page.goto("https://www.lancers.jp/user/login", wait_until="domcontentloaded")
    time.sleep(3)

    # ログインフォーム入力
    email_field = page.query_selector('input[type="email"], input[name*="email"], input[name*="login_email"]')
    pass_field = page.query_selector('input[type="password"], input[name*="password"]')

    if not email_field or not pass_field:
        print("エラー: ログインフォームが見つかりません", file=sys.stderr)
        page.screenshot(path="/tmp/lancers_login_error.png")
        return False

    email_field.fill(email)
    pass_field.fill(password)
    time.sleep(1)

    # サブミット
    submit_btn = page.query_selector('button[type="submit"], input[type="submit"]')
    if submit_btn:
        submit_btn.click()
    else:
        pass_field.press("Enter")

    time.sleep(4)

    # ログイン確認
    if "login" in page.url or "ログイン" in page.title():
        print("エラー: ログインに失敗しました", file=sys.stderr)
        page.screenshot(path="/tmp/lancers_login_fail.png")
        return False

    print(f"ログイン成功: {page.url}")
    return True


def create_service(page):
    """サービスを新規出品する"""

    # サービス出品ページへ移動
    print("サービス出品ページへ移動中...")
    page.goto("https://www.lancers.jp/profile/services", wait_until="domcontentloaded")
    time.sleep(3)
    page.screenshot(path="/tmp/lancers_services_page.png")
    print(f"現在のURL: {page.url}")

    # 「新規サービス追加」ボタンを探す
    add_btn = page.query_selector('a[href*="service/create"], a[href*="service/add"], button:has-text("新規"), a:has-text("新規サービス"), a:has-text("サービスを追加")')
    if add_btn:
        print("新規サービス追加ボタンをクリック")
        add_btn.click()
        time.sleep(3)
    else:
        # 直接URLで試みる
        print("ボタンが見つからないため直接URLへ移動")
        page.goto("https://www.lancers.jp/service/create", wait_until="domcontentloaded")
        time.sleep(3)

    page.screenshot(path="/tmp/lancers_create_form.png")
    print(f"フォームページURL: {page.url}")

    # フォームの内容を確認
    page_content = page.content()
    print(f"ページタイトル: {page.title()}")

    # タイトル入力
    title = "【Make.com×AI】業務プロセスを丸ごと自動化｜月20時間削減保証パッケージ"
    title_field = page.query_selector('input[name*="title"], input[placeholder*="タイトル"], #title, input[id*="title"]')
    if title_field:
        print(f"タイトル入力: {title}")
        title_field.fill(title)
        time.sleep(1)
    else:
        print("警告: タイトルフィールドが見つかりません")
        # フォームの全inputを確認
        inputs = page.query_selector_all('input[type="text"], input:not([type])')
        print(f"発見したinput数: {len(inputs)}")
        for i, inp in enumerate(inputs[:5]):
            name = inp.get_attribute("name") or ""
            placeholder = inp.get_attribute("placeholder") or ""
            print(f"  input[{i}]: name={name}, placeholder={placeholder}")

    # 説明文
    description = """【Make.com×AI】で繰り返し作業を丸ごと自動化します

━━━━━━━━━━━━━━━━━
■ こんな方にぴったりです
━━━━━━━━━━━━━━━━━
✅ 毎日同じコピペ作業に時間を取られている
✅ スプレッドシートへの手動入力・集計が面倒
✅ 問い合わせ対応・レポート作成を自動化したい
✅ AIを使って業務効率化したいが何から始めていいかわからない

━━━━━━━━━━━━━━━━━
■ 提供内容（4ステップ）
━━━━━━━━━━━━━━━━━

① 業務フロー現状分析（ヒアリング1時間）
　→ 自動化できる箇所を特定し、優先度をご提示

② 自動化設計書の作成
　→ Make.com + AI（GPT/Claude）を使った設計図をご提示

③ 自動化システムの構築・テスト
　→ Make.com シナリオ + AI連携を実装・動作確認

④ 納品・操作説明
　→ 操作マニュアル付きでお渡し。導入後も安心

━━━━━━━━━━━━━━━━━
■ 実績・効果
━━━━━━━━━━━━━━━━━
・対応時間 90% 削減
・月 20 時間以上の工数削減を実現
・継続的な運用コスト削減に貢献

━━━━━━━━━━━━━━━━━
■ 料金・納期
━━━━━━━━━━━━━━━━━
料金: ¥50,000（税込）
納期: 7〜14日（内容により調整）

まずはお気軽にご相談ください。"""

    desc_field = page.query_selector(
        'textarea[name*="description"], textarea[name*="body"], textarea[id*="description"], '
        'textarea[placeholder*="説明"], div[contenteditable="true"]'
    )
    if desc_field:
        print("説明文を入力中...")
        desc_field.fill(description)
        time.sleep(1)
    else:
        print("警告: 説明文フィールドが見つかりません")
        textareas = page.query_selector_all('textarea')
        print(f"発見したtextarea数: {len(textareas)}")
        for i, ta in enumerate(textareas[:5]):
            name = ta.get_attribute("name") or ""
            print(f"  textarea[{i}]: name={name}")

    # 価格入力（¥50,000）
    price_field = page.query_selector(
        'input[name*="price"], input[name*="amount"], input[name*="fee"], '
        'input[placeholder*="金額"], input[placeholder*="価格"], input[id*="price"]'
    )
    if price_field:
        print("価格入力: 50000")
        price_field.fill("50000")
        time.sleep(1)
    else:
        print("警告: 価格フィールドが見つかりません")

    # スクリーンショット（入力後）
    page.screenshot(path="/tmp/lancers_form_filled.png")

    # カテゴリ選択（セレクトボックス）
    category_sel = page.query_selector('select[name*="category"], select[id*="category"]')
    if category_sel:
        # カテゴリの選択肢を確認
        options = page.query_selector_all('select[name*="category"] option')
        print(f"カテゴリ選択肢: {len(options)}件")
        for opt in options[:10]:
            val = opt.get_attribute("value") or ""
            text = opt.inner_text()
            print(f"  value={val}: {text}")

    # 納期選択
    delivery_sel = page.query_selector('select[name*="delivery"], select[name*="period"], select[id*="delivery"]')
    if delivery_sel:
        options = page.query_selector_all('select[name*="delivery"] option, select[name*="period"] option')
        print(f"納期選択肢: {len(options)}件")
        for opt in options[:10]:
            val = opt.get_attribute("value") or ""
            text = opt.inner_text()
            print(f"  value={val}: {text}")

    # フォーム全体のスクリーンショット
    page.screenshot(path="/tmp/lancers_form_before_submit.png")

    return True


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # ログイン
            if not login(page):
                print("ログイン失敗のため中断")
                return

            # サービス出品フォームを探索
            result = create_service(page)

            if result:
                print("\n=== フォーム探索完了 ===")
                print("スクリーンショット保存先:")
                print("  /tmp/lancers_services_page.png")
                print("  /tmp/lancers_create_form.png")
                print("  /tmp/lancers_form_filled.png")
                print("  /tmp/lancers_form_before_submit.png")

        except Exception as e:
            print(f"エラー: {e}", file=sys.stderr)
            page.screenshot(path="/tmp/lancers_error.png")
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
