"""
「もしかして」を無視してSTEP2に到達できるか縮小テスト
STEP2固有のキーワードを確認する
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
    page.query_selector('input[type="email"]').fill(email)
    page.query_selector('input[type="password"]').fill(password)
    time.sleep(1)
    btn = page.query_selector('button[type="submit"]')
    btn.click() if btn else page.query_selector('input[type="password"]').press("Enter")
    time.sleep(4)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(viewport={"width": 1280, "height": 900}).new_page()
        login(page)

        page.goto("https://www.lancers.jp/myplan/add", wait_until="domcontentloaded")
        time.sleep(3)
        page.query_selector('button:has-text("手動でパッケージを作成する")').click()
        time.sleep(3)

        # 最低限の入力
        page.query_selector('textarea[name="ProjectPlanForm.title"]').fill(
            "Make.com×AIで業務プロセスを自動化｜月20時間削減保証パッケージ"
        )
        time.sleep(0.5)
        sub = page.query_selector('textarea[name="ProjectPlanForm.subtitle"]')
        if sub:
            sub.fill("繰り返し作業・手動コピペを自動化します")
        page.query_selector('select[name="___main_category_id"]').select_option(value="90")
        time.sleep(3)
        sub_cat = page.query_selector('select[name="ProjectPlanForm.project_category_id"]')
        if sub_cat:
            sub_cat.select_option(value="108")
            time.sleep(1)
        ind = page.query_selector('select[name="ProjectPlanForm.industry_type_id"]')
        if ind:
            ind.select_option(value="2116")
            time.sleep(0.5)

        # 1回目「次へ」
        page.query_selector('button:has-text("次へ")').click()
        time.sleep(3)

        # 「もしかして」を無視してそのまま2回目「次へ」
        body = page.inner_text("body")
        print(f"1回目次へ後: もしかして={'もしかして' in body}, 入力確認={'入力内容をご確認' in body}")
        print(f"URL: {page.url}")

        # STEP2固有のキーワードがあるか確認
        step2_keywords = ["ライトプラン", "スタンダードプラン", "プレミアムプラン",
                         "料金表の入力", "プランを設定", "基本料金", "サービス料金"]
        for kw in step2_keywords:
            if kw in body:
                print(f"STEP2キーワード発見: {kw}")

        # 2回目「次へ」ボタンがあるか確認
        next_btn = page.query_selector('button:has-text("次へ")')
        if next_btn:
            next_btn.click()
            time.sleep(3)
            body2 = page.inner_text("body")
            print(f"\n2回目次へ後URL: {page.url}")
            print(f"先頭500文字:\n{body2[:500]}")
            page.screenshot(path="/tmp/lancers_e8.png")

            # STEP2の価格フィールドが存在するか
            inputs = page.query_selector_all("input")
            print(f"\n入力フィールド数: {len(inputs)}")
            for inp in inputs:
                name = inp.get_attribute("name") or ""
                ph = inp.get_attribute("placeholder") or ""
                vis = inp.is_visible()
                print(f"  name={name} placeholder={ph} visible={vis}")

        browser.close()


if __name__ == "__main__":
    main()
