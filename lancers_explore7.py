"""
カテゴリ候補リンクのクリック問題を解決する
React synthetic event を発火させる方法を試す
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


def fill_step1(page):
    """基本情報を入力して次へを押す（カテゴリ候補を出す）"""
    # タイトル・サブタイトル
    page.query_selector('textarea[name="ProjectPlanForm.title"]').fill(
        "Make.com×AIで業務プロセスを自動化｜月20時間削減保証パッケージ"
    )
    subtitle = page.query_selector('textarea[name="ProjectPlanForm.subtitle"]')
    if subtitle:
        subtitle.fill("繰り返し作業・手動コピペ・レポート作成をMake.com+AIで丸ごと自動化します")
    time.sleep(0.5)

    # 大カテゴリ
    page.query_selector('select[name="___main_category_id"]').select_option(value="90")
    time.sleep(3)

    # 中カテゴリ
    sub = page.query_selector('select[name="ProjectPlanForm.project_category_id"]')
    if sub:
        sub.select_option(value="108")
        time.sleep(1)

    # 業種
    ind = page.query_selector('select[name="ProjectPlanForm.industry_type_id"]')
    if ind:
        ind.select_option(value="2116")
        time.sleep(0.5)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        login(page)

        page.goto("https://www.lancers.jp/myplan/add", wait_until="domcontentloaded")
        time.sleep(3)

        manual_btn = page.query_selector('button:has-text("手動でパッケージを作成する")')
        manual_btn.click()
        time.sleep(3)

        fill_step1(page)

        # 1回目「次へ」（カテゴリ候補を出す）
        page.query_selector('button:has-text("次へ")').click()
        time.sleep(3)

        # 候補リンクをJavaScript経由でクリック
        print("方法1: JavaScriptでReact clickイベントを発火")
        result = page.evaluate("""
            () => {
                // "Webプログラミング" を含むaタグを探す
                const links = document.querySelectorAll('a');
                for (const link of links) {
                    if (link.textContent.includes('Webプログラミング')) {
                        // React fiber からクリックハンドラを取得して実行
                        const key = Object.keys(link).find(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
                        if (key) {
                            const fiber = link[key];
                            // React synthetic event
                            link.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                            return 'clicked: ' + link.textContent.trim();
                        }
                        // フォールバック: 通常のclick
                        link.click();
                        return 'fallback clicked: ' + link.textContent.trim();
                    }
                }
                return 'not found';
            }
        """)
        print(f"JS click結果: {result}")
        time.sleep(3)
        page.screenshot(path="/tmp/lancers_e7_1.png")

        body = page.inner_text("body")
        if "もしかして" not in body:
            print("★ カテゴリ確定成功！")
        else:
            print("まだ「もしかして」が表示中")

            # 方法2: Playwrightの force click
            print("\n方法2: force: True でクリック")
            fill_step1(page)
            page.query_selector('button:has-text("次へ")').click()
            time.sleep(3)

            links = page.query_selector_all("a")
            for link in links:
                text = link.inner_text().strip()
                if "Webプログラミング" in text:
                    print(f"force click: {text}")
                    link.click(force=True)
                    time.sleep(3)
                    break

            page.screenshot(path="/tmp/lancers_e7_2.png")
            body2 = page.inner_text("body")
            if "もしかして" not in body2:
                print("★ 方法2成功！")
            else:
                print("方法2も失敗")

                # 方法3: リンクのhref=# → page.evaluate でReact状態を直接書き換え
                print("\n方法3: React stateを直接操作")
                # カテゴリリンクのdata属性を確認
                link_info = page.evaluate("""
                    () => {
                        const links = document.querySelectorAll('a');
                        const results = [];
                        for (const link of links) {
                            if (link.textContent.includes('Webプログラミング')) {
                                const attrs = {};
                                for (const attr of link.attributes) {
                                    attrs[attr.name] = attr.value;
                                }
                                results.push({
                                    text: link.textContent.trim(),
                                    attrs: attrs,
                                    parentHTML: link.parentElement ? link.parentElement.outerHTML.substring(0, 200) : ''
                                });
                            }
                        }
                        return results;
                    }
                """)
                print(f"リンク情報: {link_info}")

        browser.close()


if __name__ == "__main__":
    main()
