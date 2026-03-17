"""公開されたパッケージのURLを取得"""
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


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(viewport={"width": 1280, "height": 900}).new_page()

        email, password = get_credentials()
        page.goto("https://www.lancers.jp/user/login", wait_until="domcontentloaded")
        time.sleep(3)
        page.query_selector('input[type="email"]').fill(email)
        page.query_selector('input[type="password"]').fill(password)
        page.query_selector('button[type="submit"]').click()
        time.sleep(4)

        # 完了ページに直接アクセス
        page.goto("https://www.lancers.jp/myplan/1321084/add/complete", wait_until="domcontentloaded")
        time.sleep(3)
        page.screenshot(path="/tmp/lancers_complete.png")

        # 「公開したパッケージを見る」リンクを探す
        links = page.query_selector_all("a")
        for link in links:
            href = link.get_attribute("href") or ""
            text = link.inner_text().strip()
            if "myplan" in href or "package" in href or "menu" in href:
                print(f"[{text}] -> {href}")

        # パッケージID 1321084 の公開URLを確認
        page.goto("https://www.lancers.jp/myplan/1321084", wait_until="domcontentloaded")
        time.sleep(3)
        print(f"\nパッケージURL: {page.url}")
        print(f"タイトル: {page.title()}")
        page.screenshot(path="/tmp/lancers_package_page.png")

        browser.close()


if __name__ == "__main__":
    main()
