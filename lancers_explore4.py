"""
大カテゴリ選択後のサブカテゴリDOMを詳細調査
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
        if manual_btn:
            manual_btn.click()
            time.sleep(3)

        # 大カテゴリを選択
        main_cat = page.query_selector('select[name="___main_category_id"]')
        main_cat.select_option(value="90")  # AI・プログラミング・システム開発
        print("大カテゴリ選択完了")
        time.sleep(3)  # サブカテゴリ読み込みを待つ

        # 全セレクト要素を確認
        print("\n=== 全SELECT要素（カテゴリ選択後） ===")
        selects = page.query_selector_all("select")
        for sel in selects:
            name = sel.get_attribute("name") or ""
            sid = sel.get_attribute("id") or ""
            print(f"\n<select name={name} id={sid}>")
            options = sel.query_selector_all("option")
            for opt in options[:30]:
                val = opt.get_attribute("value") or ""
                text = opt.inner_text().strip()
                print(f"    <option value={val}>{text}</option>")

        # カテゴリ関連のDOM全体を確認
        print("\n=== カテゴリ周辺のHTML ===")
        cat_section = page.query_selector('[class*="category"], [class*="Category"]')
        if cat_section:
            print(cat_section.inner_html()[:2000])

        # 「もしかしてこのカテゴリ」が表示されているか確認
        suggest = page.query_selector('[class*="suggest"], [class*="Suggest"]')
        if suggest:
            print(f"\n候補表示: {suggest.inner_text()}")

        # チェックボックスやラジオボタンも確認
        print("\n=== RADIO/CHECKBOX ===")
        radios = page.query_selector_all('input[type="radio"], input[type="checkbox"]')
        for r in radios:
            name = r.get_attribute("name") or ""
            val = r.get_attribute("value") or ""
            print(f"  {r.get_attribute('type')}: name={name} value={val}")

        page.screenshot(path="/tmp/lancers_category_after.png")

        # 全ページテキストでカテゴリ関連を確認
        body_text = page.inner_text("body")
        # カテゴリ周辺を探す
        idx = body_text.find("カテゴリ")
        if idx != -1:
            print(f"\n=== カテゴリ周辺テキスト ===")
            print(body_text[idx:idx+500])

        browser.close()


if __name__ == "__main__":
    main()
