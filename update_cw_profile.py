#!/usr/bin/env python3
"""CWプロフィール自己紹介文更新スクリプト"""
import os
import asyncio
from playwright.async_api import async_playwright

EMAIL = os.environ["CROWDWORKS_EMAIL"]
PASSWORD = os.environ["CROWDWORKS_PASSWORD"]

NEW_INTRO_PREFIX = """【問い合わせ自動化→月20h削減・ROI2,000%超】Make.com+ChatGPT+GASで、繰り返し手作業を根絶します。

▶ 実績（数字）
・問い合わせ対応: 返信速度24h→3分、月工数20h→1.8h
・データ収集自動化: 月40h削減、手入力ほぼゼロ
・ツールコスト月2,500円で月54,600円分の工数を削減（ROI 2,000%超）

▶ こんな課題を解決しています
・問い合わせ返信に毎日1〜2時間かかっている
・スプレッドシートへの手入力・転記が多い
・定期レポート・集計を毎回手動で作っている

---

"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # ログイン
        print("ログイン中...")
        await page.goto("https://crowdworks.jp/login")
        await page.fill('input[name="username"]', EMAIL)
        await page.fill('input[name="password"]', PASSWORD)
        await page.click('input[type="submit"], button[type="submit"]')
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(2)
        print(f"ログイン後URL: {page.url}")

        # プロフィール編集ページへ
        print("プロフィール編集ページへ移動...")
        await page.goto("https://crowdworks.jp/employee/edit", timeout=60000)
        await page.wait_for_load_state("domcontentloaded")
        await page.screenshot(path="/mnt/c/Users/hp/Downloads/cw_edit_page.png")

        # 自己紹介欄を探す
        selectors = [
            'textarea[name="employee[introduction]"]',
            'textarea[id*="introduction"]',
            'textarea[placeholder*="自己紹介"]',
            'textarea[name*="introduction"]',
        ]
        textarea = None
        for sel in selectors:
            try:
                el = page.locator(sel)
                if await el.count() > 0:
                    textarea = el.first
                    print(f"自己紹介欄発見: {sel}")
                    break
            except:
                pass

        if textarea is None:
            print("自己紹介欄が見つかりません。スクリーンショットを確認してください。")
            await page.screenshot(path="/mnt/c/Users/hp/Downloads/cw_edit_debug.png")
            await browser.close()
            return

        # 現在のテキストを取得
        current_text = await textarea.input_value()
        print(f"現在の文字数: {len(current_text)}")

        # 既にprefixが付いていない場合のみ追記
        if "問い合わせ自動化→月20h削減" in current_text:
            print("既にプレフィックスが追加済みです。スキップします。")
        else:
            new_text = NEW_INTRO_PREFIX + current_text
            await textarea.fill(new_text)
            print(f"新しい文字数: {len(new_text)}")

            # ページ内のボタンを全て確認
            print("ページ内のボタン一覧:")
            buttons = page.locator('input[type="submit"], button[type="submit"], button')
            count = await buttons.count()
            for i in range(count):
                btn = buttons.nth(i)
                text = await btn.text_content()
                val = await btn.get_attribute("value")
                print(f"  [{i}] text={text!r} value={val!r}")

            # 保存ボタンを押す（スクロールして探す）
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)

            # 「ワーカー情報を更新する」ボタンを直接狙う
            save_btn = page.locator('input[value="ワーカー情報を更新する"]')
            saved = False
            if await save_btn.count() > 0:
                await save_btn.scroll_into_view_if_needed()
                await save_btn.click()
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(3)
                print("保存ボタンクリック: ワーカー情報を更新する")
                saved = True

            if not saved:
                print("保存ボタンが見つかりません。手動で保存してください。")

        await page.screenshot(path="/mnt/c/Users/hp/Downloads/cw_after_save.png")
        print("完了。スクリーンショット保存済み。")
        await asyncio.sleep(3)
        await browser.close()

asyncio.run(main())
