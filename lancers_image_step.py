#!/usr/bin/env python3
"""ランサーズ: 各ステップを順に経由して画像ほかタブに到達"""

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

def click_next(page):
    """次へボタンをクリック"""
    try:
        btn = page.query_selector('.btn.btn-primary:has-text("次へ"), button:has-text("次へ"), a:has-text("次へ")')
        if btn:
            btn.click()
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            return True
    except Exception as e:
        print(f"    次へエラー: {e}")
    return False

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
        page.goto(f"https://www.lancers.jp/myplan/{PLAN_ID}/edit")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        print(f"\n[2] 編集ページ: {page.url}")

        # タブの構造を確認
        page.screenshot(path="/tmp/lancers_s1.png")

        # ステップナビゲーションを JavaScript でクリック（force）
        print("\n[3] 「画像ほか」ステップへ JavaScript でジャンプ...")
        result = page.evaluate("""
            () => {
                // テキストで要素を探してクリック
                const allElements = document.querySelectorAll('*');
                for (const el of allElements) {
                    if (el.textContent.trim() === '画像ほか' && el.offsetParent !== null) {
                        el.click();
                        return 'clicked: ' + el.tagName + ' class=' + el.className;
                    }
                }
                // すべての画像ほかテキストを探す
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                let found = [];
                let node;
                while (node = walker.nextNode()) {
                    if (node.textContent.includes('画像ほか')) {
                        found.push(node.parentElement.tagName + '|' + node.parentElement.className);
                    }
                }
                return 'found elements: ' + JSON.stringify(found);
            }
        """)
        print(f"  JS結果: {result}")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        page.screenshot(path="/tmp/lancers_s2.png")
        print(f"  現在URL: {page.url}")

        # ステップURLを直接試す
        step_urls = [
            f"https://www.lancers.jp/myplan/{PLAN_ID}/edit?step=5",
            f"https://www.lancers.jp/myplan/{PLAN_ID}/edit?step=image",
            f"https://www.lancers.jp/myplan/{PLAN_ID}/edit/5",
            f"https://www.lancers.jp/myplan/{PLAN_ID}/image",
        ]
        print("\n[4] ステップURLを直接試す...")
        for url in step_urls:
            page.goto(url)
            page.wait_for_load_state("networkidle")
            time.sleep(1)
            title = page.title()
            cur_url = page.url
            file_count = len(page.query_selector_all('input[type="file"]'))
            print(f"  {url}")
            print(f"    → {cur_url} | files={file_count} | title={title[:50]}")

        # 通常の「次へ」連打でステップ5まで進む
        print("\n[5] 通常のステップ移動（次へ×4回）...")
        page.goto(f"https://www.lancers.jp/myplan/{PLAN_ID}/edit")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        for step_num in range(1, 5):
            print(f"  ステップ{step_num} → 次へ...")
            page.screenshot(path=f"/tmp/lancers_step{step_num}.png")

            # 次へボタンを探す（右下）
            next_clicked = False
            next_selectors = [
                'button:has-text("次へ")',
                'a.btn:has-text("次へ")',
                '.btn-primary:has-text("次へ")',
                'input[value="次へ"]',
            ]
            for sel in next_selectors:
                try:
                    btn = page.query_selector(sel)
                    if btn:
                        btn.scroll_into_view_if_needed()
                        btn.click()
                        page.wait_for_load_state("networkidle")
                        time.sleep(2)
                        print(f"    ✅ 次へ: {sel} → {page.url}")
                        next_clicked = True
                        break
                except Exception as e:
                    pass

            if not next_clicked:
                # JavaScript でクリック
                js_result = page.evaluate("""
                    () => {
                        const btns = [...document.querySelectorAll('button, a, input[type="submit"]')];
                        for (const b of btns) {
                            if (b.textContent.trim().includes('次へ')) {
                                b.click();
                                return 'js clicked: ' + b.outerHTML.substring(0, 100);
                            }
                        }
                        return 'not found';
                    }
                """)
                print(f"    JS次へ: {js_result}")
                page.wait_for_load_state("networkidle")
                time.sleep(2)

        # ステップ5（画像ほか）でのファイル入力確認
        page.screenshot(path="/tmp/lancers_step5.png")
        print(f"\n[6] ステップ5（画像ほか）確認: {page.url}")
        print(f"  ページタイトル: {page.title()}")

        file_inputs = page.query_selector_all('input[type="file"]')
        print(f"  ファイル入力数: {len(file_inputs)}")

        if len(file_inputs) > 0:
            print("\n[7] 画像アップロード...")
            for i, img_path in enumerate(IMAGES):
                if i < len(file_inputs):
                    try:
                        file_inputs[i].set_input_files(img_path)
                        time.sleep(2)
                        print(f"  ✅ 画像{i+1}: {os.path.basename(img_path)}")
                    except Exception as e:
                        print(f"  ⚠️ 画像{i+1} エラー: {e}")

            time.sleep(2)
            page.screenshot(path="/tmp/lancers_uploaded.png")
            print("  スクリーンショット: /tmp/lancers_uploaded.png")

            # 保存
            for btn_text in ["次へ", "保存", "更新", "完了"]:
                btn = page.query_selector(f'button:has-text("{btn_text}")')
                if btn:
                    btn.click()
                    page.wait_for_load_state("networkidle")
                    time.sleep(2)
                    print(f"  ✅ 「{btn_text}」クリック → {page.url}")
                    page.screenshot(path="/tmp/lancers_final.png")
                    break
        else:
            content = page.content()
            with open("/tmp/lancers_step5.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("  ⚠️ ファイル入力なし。HTML保存: /tmp/lancers_step5.html")

        browser.close()
        print("\n完了")

if __name__ == "__main__":
    run()
