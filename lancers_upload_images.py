#!/usr/bin/env python3
"""ランサーズ: サービス画像アップロード + タイトル確認"""

import os
import time
from playwright.sync_api import sync_playwright

EMAIL = os.environ["LANCERS_EMAIL"]
PASSWORD = os.environ["LANCERS_PASSWORD"]

IMAGES = [
    "/home/kosuke_igarashi/projects/new-project/coconala_4125290_img_1.png",
    "/home/kosuke_igarashi/projects/new-project/coconala_4125290_img_2.png",
    "/home/kosuke_igarashi/projects/new-project/coconala_4125290_img_3.png",
    "/home/kosuke_igarashi/projects/new-project/coconala_4125290_img_4.png",
    "/home/kosuke_igarashi/projects/new-project/coconala_4125290_img_5.png",
]

PLAN_ID = "1321084"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        # --- ログイン ---
        print("[1/5] ランサーズにログイン中...")
        page.goto("https://www.lancers.jp/user/login", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2)

        page.fill('input[name="data[User][email]"]', EMAIL)
        page.fill('input[name="data[User][password]"]', PASSWORD)
        page.click('button[type="submit"], input[type="submit"], .btn-login, button:has-text("ログイン")')
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        if "login" in page.url:
            page.screenshot(path="/tmp/lancers_login_fail.png")
            print(f"❌ ログイン失敗: {page.url}")
            browser.close()
            return False

        print(f"✅ ログイン成功: {page.url}")

        # --- 出品詳細ページ確認（タイトル）---
        print("[2/5] 出品ページ確認中...")
        page.goto(f"https://www.lancers.jp/menu/detail/{PLAN_ID}")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        page.screenshot(path="/tmp/lancers_detail.png")

        # タイトルを取得
        try:
            title_el = page.query_selector("h1, .service-title, .plan-title")
            if title_el:
                print(f"  サービスタイトル: {title_el.inner_text().strip()}")
        except:
            pass

        # --- 編集ページへ ---
        print("[3/5] 編集ページに移動...")
        # myplanページから編集リンクを探す
        page.goto("https://www.lancers.jp/myplan")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        page.screenshot(path="/tmp/lancers_myplan.png")

        # 編集ボタン/リンクを探す
        edit_url = None
        edit_selectors = [
            f'a[href*="/myplan/edit/{PLAN_ID}"]',
            f'a[href*="edit/{PLAN_ID}"]',
            'a[href*="edit"]:has-text("編集")',
            'a:has-text("編集")',
            '.edit-btn',
        ]
        for sel in edit_selectors:
            try:
                el = page.query_selector(sel)
                if el:
                    edit_url = el.get_attribute("href")
                    print(f"  編集リンク発見: {edit_url}")
                    break
            except:
                pass

        if not edit_url:
            # 直接URLを試す
            candidates = [
                f"https://www.lancers.jp/myplan/edit/{PLAN_ID}",
                f"https://www.lancers.jp/menu/edit/{PLAN_ID}",
                f"https://www.lancers.jp/service/edit/{PLAN_ID}",
            ]
            for url in candidates:
                page.goto(url)
                page.wait_for_load_state("networkidle")
                time.sleep(1)
                if "404" not in page.title() and "not found" not in page.title().lower():
                    edit_url = url
                    print(f"  編集URL確認: {url}")
                    break

        if not edit_url:
            print("  ⚠️ 編集URLが見つかりません。スクリーンショットを確認してください")
            page.screenshot(path="/tmp/lancers_edit_notfound.png")
            browser.close()
            return False

        # --- 編集ページでファイル確認 ---
        print("[4/5] 編集ページでファイル入力を確認...")
        page.screenshot(path="/tmp/lancers_edit.png")
        print(f"  現在URL: {page.url}")

        file_inputs = page.query_selector_all('input[type="file"]')
        print(f"  ファイル入力数: {len(file_inputs)}")

        if len(file_inputs) == 0:
            # ページHTML確認
            content = page.content()
            with open("/tmp/lancers_edit_html.txt", "w") as f:
                f.write(content)
            print("  HTML保存: /tmp/lancers_edit_html.txt")
            print("  ⚠️ ファイル入力なし → 手動で画像アップロード箇所を確認が必要")
            browser.close()
            return False

        # --- 画像アップロード ---
        print("[5/5] 画像アップロード中...")
        for i, img_path in enumerate(IMAGES):
            if i < len(file_inputs):
                try:
                    file_inputs[i].set_input_files(img_path)
                    time.sleep(1.5)
                    print(f"  ✅ 画像{i+1}: {os.path.basename(img_path)}")
                except Exception as e:
                    print(f"  ⚠️ 画像{i+1} エラー: {e}")
            else:
                print(f"  ⚠️ 画像{i+1}: ファイル入力フィールド不足（{len(file_inputs)}個しかない）")

        time.sleep(2)
        page.screenshot(path="/tmp/lancers_after_upload.png")
        print("  スクリーンショット保存: /tmp/lancers_after_upload.png")

        # 保存ボタンをクリック
        save_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("保存")',
            'button:has-text("更新")',
            '.btn-submit',
        ]
        for sel in save_selectors:
            try:
                btn = page.query_selector(sel)
                if btn:
                    btn.click()
                    page.wait_for_load_state("networkidle")
                    time.sleep(2)
                    page.screenshot(path="/tmp/lancers_saved.png")
                    print(f"  ✅ 保存ボタンクリック: {sel}")
                    print(f"  保存後URL: {page.url}")
                    break
            except Exception as e:
                print(f"  保存エラー ({sel}): {e}")

        browser.close()
        print("\n✅ 完了")
        return True

if __name__ == "__main__":
    run()
