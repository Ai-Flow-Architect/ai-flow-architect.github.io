"""
「もしかして」後のページ全体構造を確認（フルスクリーンショット＋DOM詳細）
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
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        login(page)

        page.goto("https://www.lancers.jp/myplan/add", wait_until="domcontentloaded")
        time.sleep(3)
        page.query_selector('button:has-text("手動でパッケージを作成する")').click()
        time.sleep(3)

        # 最低限の入力
        page.query_selector('textarea[name="ProjectPlanForm.title"]').fill(
            "Make.com×AIで業務プロセスを自動化｜月20時間削減保証パッケージ"
        )
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

        # 1回目「次へ」でバリデーションを出す
        page.query_selector('button:has-text("次へ")').click()
        time.sleep(3)

        # ページ全体テキストを取得
        body = page.inner_text("body")
        print("=== ページ全体テキスト ===")
        print(body)

        # フルページスクリーンショット
        page.screenshot(path="/tmp/lancers_e9_full.png", full_page=True)

        # service_type フィールドの詳細
        print("\n=== service_type フィールド ===")
        inputs_info = page.evaluate("""
            () => {
                const inputs = document.querySelectorAll('input[name*="service_type"]');
                return Array.from(inputs).map(inp => ({
                    name: inp.name,
                    type: inp.type,
                    value: inp.value,
                    checked: inp.checked,
                    visible: inp.offsetParent !== null,
                    labelText: inp.closest('label') ? inp.closest('label').textContent.trim() : '',
                    parentHTML: inp.parentElement ? inp.parentElement.outerHTML.substring(0, 200) : ''
                }));
            }
        """)
        for info in inputs_info[:10]:
            print(info)

        # 数値nameのinput確認
        print("\n=== 数値name inputの詳細 ===")
        numeric_inputs = page.evaluate("""
            () => {
                const inputs = document.querySelectorAll('input');
                return Array.from(inputs)
                    .filter(inp => /^\\d+$/.test(inp.name))
                    .map(inp => ({
                        name: inp.name,
                        type: inp.type,
                        value: inp.value,
                        checked: inp.checked,
                        labelText: inp.closest('label') ? inp.closest('label').textContent.trim() : '',
                        parentHTML: inp.parentElement ? inp.parentElement.outerHTML.substring(0, 150) : ''
                    }));
            }
        """)
        for info in numeric_inputs[:5]:
            print(info)

        browser.close()


if __name__ == "__main__":
    main()
