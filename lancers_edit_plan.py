#!/usr/bin/env python3
"""ランサーズ: プラン編集ページの詳細確認"""

import os
import time
from playwright.sync_api import sync_playwright

EMAIL = os.environ["LANCERS_EMAIL"]
PASSWORD = os.environ["LANCERS_PASSWORD"]
PLAN_ID = "1321084"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        # ログイン
        print("[1] ログイン...")
        page.goto("https://www.lancers.jp/user/login", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2)
        page.fill('input[name="data[User][email]"]', EMAIL)
        page.fill('input[name="data[User][password]"]', PASSWORD)
        page.click('button:has-text("ログイン")')
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        print(f"  ログイン後URL: {page.url}")

        # 編集ページに直接アクセス
        edit_url = f"https://www.lancers.jp/myplan/{PLAN_ID}/edit"
        print(f"\n[2] 編集ページ: {edit_url}")
        page.goto(edit_url)
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        print(f"  現在URL: {page.url}")
        page.screenshot(path="/tmp/lancers_edit_v2.png")
        print("  スクリーンショット: /tmp/lancers_edit_v2.png")

        # ページタイトル確認
        print(f"  ページタイトル: {page.title()}")

        # すべてのinput要素を確認
        inputs = page.query_selector_all("input, textarea, select")
        print(f"\n  フォーム要素数: {len(inputs)}")
        for el in inputs[:20]:
            name = el.get_attribute("name") or ""
            type_ = el.get_attribute("type") or el.evaluate("el => el.tagName")
            id_ = el.get_attribute("id") or ""
            if "image" in name.lower() or "photo" in name.lower() or "file" in type_.lower() or "image" in id_.lower():
                print(f"  [画像関連] name={name} type={type_} id={id_}")

        # ページ全体のHTML保存
        content = page.content()
        with open("/tmp/lancers_edit_v2.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("\n  HTML保存: /tmp/lancers_edit_v2.html")

        # タイトルフィールドを確認
        title_input = page.query_selector('input[name*="title"], input[name*="Title"], input[id*="title"]')
        if title_input:
            current_title = title_input.input_value()
            print(f"\n  現在のタイトル: {current_title}")

        browser.close()

if __name__ == "__main__":
    run()
