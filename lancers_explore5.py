"""
カテゴリ選択の詳細デバッグ
大カテゴリ選択後にサブカテゴリが正しく選択できるかを確認
"""
import sys
import time
import subprocess
from playwright.sync_api import sync_playwright


def get_credentials():
    result = subprocess.run(
        "source ~/.bashrc && echo $LANCERS_EMAIL && echo $LANCERS_PASSWORD",
        shell=True, capture_output=True, text=True, executable="/bin/bash"
    )
    lines = result.stdout.strip().split("\n")
    return lines[0], lines[1]


def login(page):
    email, password = get_credentials()
    page.goto("https://www.lancers.jp/user/login", wait_until="domcontentloaded")
    time.sleep(3)
    email_field = page.query_selector('input[type="email"], input[name*="email"]')
    pass_field = page.query_selector('input[type="password"]')
    email_field.fill(email)
    pass_field.fill(password)
    time.sleep(1)
    submit_btn = page.query_selector('button[type="submit"]')
    if submit_btn:
        submit_btn.click()
    else:
        pass_field.press("Enter")
    time.sleep(4)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        login(page)

        page.goto("https://www.lancers.jp/myplan/add", wait_until="domcontentloaded")
        time.sleep(3)

        # 手動作成ボタンをクリック
        manual_btn = page.query_selector('button:has-text("手動でパッケージを作成する")')
        manual_btn.click()
        time.sleep(3)

        # タイトルを入力
        title_field = page.query_selector('textarea[name="ProjectPlanForm.title"]')
        title_field.fill("Make.com×AIで業務プロセスを自動化します｜月20時間削減保証")
        time.sleep(0.5)

        # 大カテゴリを選択（change イベントを発火）
        print("大カテゴリ選択前のセレクト一覧:")
        selects_before = page.query_selector_all("select")
        for s in selects_before:
            print(f"  {s.get_attribute('name')}")

        main_cat = page.query_selector('select[name="___main_category_id"]')
        main_cat.select_option(value="90")
        print("大カテゴリ選択完了")
        time.sleep(1)

        # changeイベントを手動で発火
        page.evaluate("""
            const sel = document.querySelector('select[name="___main_category_id"]');
            sel.dispatchEvent(new Event('change', {bubbles: true}));
        """)
        time.sleep(3)

        print("\n大カテゴリ選択後のセレクト一覧:")
        selects_after = page.query_selector_all("select")
        for s in selects_after:
            name = s.get_attribute("name") or ""
            opts = s.query_selector_all("option")
            selected_val = s.input_value() if s else ""
            print(f"  {name}: 選択中={selected_val}, 選択肢数={len(opts)}")

        # project_category_id の状態確認
        sub_cat = page.query_selector('select[name="ProjectPlanForm.project_category_id"]')
        if sub_cat:
            current_val = sub_cat.input_value()
            print(f"\nサブカテゴリ現在値: {current_val}")
            opts = sub_cat.query_selector_all("option")
            print(f"選択肢数: {len(opts)}")
            for opt in opts[:5]:
                print(f"  value={opt.get_attribute('value')}: {opt.inner_text().strip()}")

            # 選択を試みる
            try:
                sub_cat.select_option(value="108")
                time.sleep(1)
                new_val = sub_cat.input_value()
                print(f"選択後の値: {new_val}")
            except Exception as e:
                print(f"選択エラー: {e}")
        else:
            print("サブカテゴリが見つかりません")

        page.screenshot(path="/tmp/lancers_cat_debug.png")

        # 「次へ」を押してバリデーション確認
        next_btn = page.query_selector('button:has-text("次へ")')
        if next_btn:
            next_btn.click()
            time.sleep(3)
            page.screenshot(path="/tmp/lancers_cat_debug2.png")
            print(f"\n次へ後URL: {page.url}")
            body_text = page.inner_text("body")
            # エラーメッセージを探す
            if "確認" in body_text or "エラー" in body_text or "必須" in body_text:
                idx = body_text.find("確認")
                if idx == -1:
                    idx = body_text.find("エラー")
                print(f"エラー周辺:\n{body_text[max(0,idx-100):idx+500]}")

        browser.close()


if __name__ == "__main__":
    main()
