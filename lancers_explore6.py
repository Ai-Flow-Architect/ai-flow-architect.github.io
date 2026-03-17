"""
STEP1通過の詳細デバッグ
カテゴリ候補クリック後、業種が保持されているか / 次へ後にどうなるか確認
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
    print(f"ログイン後URL: {page.url}")


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

        # タイトル・サブタイトル入力
        title_field = page.query_selector('textarea[name="ProjectPlanForm.title"]')
        title_field.fill("Make.com×AIで業務プロセスを自動化｜月20時間削減保証パッケージ")
        time.sleep(0.5)

        subtitle_field = page.query_selector('textarea[name="ProjectPlanForm.subtitle"]')
        if subtitle_field:
            subtitle_field.fill("繰り返し作業・手動コピペ・レポート作成をMake.com+AIで丸ごと自動化します")
            time.sleep(0.5)

        # 大カテゴリ選択
        main_cat = page.query_selector('select[name="___main_category_id"]')
        main_cat.select_option(value="90")
        print("大カテゴリ選択")
        time.sleep(3)

        # 中カテゴリ選択
        sub_cat = page.query_selector('select[name="ProjectPlanForm.project_category_id"]')
        if sub_cat:
            sub_cat.select_option(value="108")
            print("中カテゴリ選択")
            time.sleep(1)

        # 業種選択
        industry = page.query_selector('select[name="ProjectPlanForm.industry_type_id"]')
        if industry:
            industry.select_option(value="2116")
            print("業種選択")
            time.sleep(0.5)

        page.screenshot(path="/tmp/lancers_d1.png")

        # 1回目「次へ」（カテゴリ候補を出す）
        next_btn = page.query_selector('button:has-text("次へ")')
        next_btn.click()
        time.sleep(3)
        page.screenshot(path="/tmp/lancers_d2.png")
        print(f"1回目次へ後URL: {page.url}")

        # 現在のフォーム状態を確認
        print("\n=== セレクト状態 ===")
        selects = page.query_selector_all("select")
        for sel in selects:
            name = sel.get_attribute("name") or ""
            val = sel.input_value()
            print(f"  {name}: {val}")

        # 「Webプログラミング」候補リンクをクリック
        body = page.inner_text("body")
        if "もしかして" in body:
            print("カテゴリ候補が表示されています")

            # aタグを探す
            links = page.query_selector_all("a")
            for link in links:
                text = link.inner_text().strip()
                if "Webプログラミング" in text:
                    href = link.get_attribute("href") or ""
                    print(f"カテゴリリンク: [{text}] href={href}")
                    link.click()
                    time.sleep(3)
                    break

            page.screenshot(path="/tmp/lancers_d3.png")
            print(f"カテゴリクリック後URL: {page.url}")

            # セレクト状態再確認
            print("\n=== カテゴリクリック後セレクト状態 ===")
            selects = page.query_selector_all("select")
            for sel in selects:
                name = sel.get_attribute("name") or ""
                val = sel.input_value()
                print(f"  {name}: {val}")

            # ページテキストでエラーを確認
            body2 = page.inner_text("body")
            if "もしかして" in body2:
                print("まだカテゴリ候補表示中")
            idx = body2.find("入力内容をご確認")
            if idx != -1:
                print(f"バリデーションエラー:\n{body2[idx:idx+500]}")

            # 業種が失われていれば再選択
            industry2 = page.query_selector('select[name="ProjectPlanForm.industry_type_id"]')
            if industry2:
                val = industry2.input_value()
                print(f"業種現在値: {val}")
                if not val:
                    industry2.select_option(value="2116")
                    print("業種再選択")
                    time.sleep(0.5)

        # 2回目「次へ」
        next_btn2 = page.query_selector('button:has-text("次へ")')
        if next_btn2:
            next_btn2.click()
            time.sleep(3)
            page.screenshot(path="/tmp/lancers_d4.png")
            print(f"2回目次へ後URL: {page.url}")

            body3 = page.inner_text("body")
            if "料金" in body3 and "価格" in body3:
                print("★ 料金表ページへ遷移成功！")
            elif "もしかして" in body3:
                print("まだカテゴリ未確定")
                idx = body3.find("もしかして")
                print(body3[idx:idx+400])
            elif "入力内容をご確認" in body3:
                print("バリデーションエラー継続")
                idx = body3.find("入力内容をご確認")
                print(body3[idx:idx+600])
            else:
                print(f"ページ先頭: {body3[:300]}")

        browser.close()


if __name__ == "__main__":
    main()
