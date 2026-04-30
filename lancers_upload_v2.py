#!/usr/bin/env python3
"""ランサーズ: 画像ほかタブで画像アップロード"""

import os
import time
from playwright.sync_api import sync_playwright

EMAIL = os.environ["LANCERS_EMAIL"]
PASSWORD = os.environ["LANCERS_PASSWORD"]
PLAN_ID = "1321084"

IMAGES = [
    "/home/kosuke_igarashi/projects/new-project/coconala_4125290_img_1.png",
    "/home/kosuke_igarashi/projects/new-project/coconala_4125290_img_2.png",
    "/home/kosuke_igarashi/projects/new-project/coconala_4125290_img_3.png",
    "/home/kosuke_igarashi/projects/new-project/coconala_4125290_img_4.png",
    "/home/kosuke_igarashi/projects/new-project/coconala_4125290_img_5.png",
]

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
        print(f"  ✅ ログイン: {page.url}")

        # 編集ページへ
        print(f"\n[2] 編集ページへ移動...")
        page.goto(f"https://www.lancers.jp/myplan/{PLAN_ID}/edit")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        print(f"  URL: {page.url}")

        # 「画像ほか」タブをクリック
        print("\n[3] 「画像ほか」タブに移動...")
        try:
            # ステップタブを探す
            image_tab = page.query_selector('li:has-text("画像ほか"), a:has-text("画像ほか"), span:has-text("画像ほか")')
            if image_tab:
                image_tab.click()
                page.wait_for_load_state("networkidle")
                time.sleep(2)
                print("  ✅ 画像ほかタブをクリック")
            else:
                # 直接URLで試す
                page.goto(f"https://www.lancers.jp/myplan/{PLAN_ID}/edit/image")
                page.wait_for_load_state("networkidle")
                time.sleep(2)
                print(f"  直接URL試行: {page.url}")
        except Exception as e:
            print(f"  ⚠️ タブクリックエラー: {e}")

        page.screenshot(path="/tmp/lancers_image_tab.png")
        print(f"  スクリーンショット: /tmp/lancers_image_tab.png")
        print(f"  現在URL: {page.url}")

        # ファイル入力を確認
        file_inputs = page.query_selector_all('input[type="file"]')
        print(f"\n  ファイル入力フィールド数: {len(file_inputs)}")

        # ページ内の画像関連要素を広く探す
        all_inputs = page.query_selector_all("input")
        for inp in all_inputs:
            type_ = inp.get_attribute("type") or ""
            name = inp.get_attribute("name") or ""
            if "file" in type_.lower() or "image" in name.lower() or "photo" in name.lower():
                print(f"  [画像input] type={type_} name={name}")

        if len(file_inputs) > 0:
            print("\n[4] 画像アップロード中...")
            for i, img_path in enumerate(IMAGES):
                if i < len(file_inputs):
                    try:
                        file_inputs[i].set_input_files(img_path)
                        time.sleep(2)
                        print(f"  ✅ 画像{i+1}: {os.path.basename(img_path)}")
                    except Exception as e:
                        print(f"  ⚠️ 画像{i+1} エラー: {e}")
                else:
                    print(f"  ⚠️ 画像{i+1}: フィールド不足")

            time.sleep(2)
            page.screenshot(path="/tmp/lancers_after_upload.png")
            print("  スクリーンショット: /tmp/lancers_after_upload.png")

            # 保存/次へ
            for btn_text in ["保存", "次へ", "更新", "完了"]:
                btn = page.query_selector(f'button:has-text("{btn_text}"), input[value="{btn_text}"]')
                if btn:
                    btn.click()
                    page.wait_for_load_state("networkidle")
                    time.sleep(2)
                    print(f"  ✅ 「{btn_text}」クリック完了")
                    page.screenshot(path="/tmp/lancers_saved.png")
                    print(f"  保存後URL: {page.url}")
                    break
        else:
            print("  ⚠️ ファイル入力なし。HTMLを保存して確認します")
            content = page.content()
            with open("/tmp/lancers_image_tab.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("  HTML保存: /tmp/lancers_image_tab.html")

        browser.close()
        print("\n完了")

if __name__ == "__main__":
    run()
