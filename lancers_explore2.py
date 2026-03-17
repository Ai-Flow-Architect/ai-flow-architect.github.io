"""
ランサーズ /myplan/add フォーム構造を詳細調査
"""
import os
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
    submit_btn = page.query_selector('button[type="submit"], input[type="submit"]')
    if submit_btn:
        submit_btn.click()
    else:
        pass_field.press("Enter")
    time.sleep(4)
    print(f"ログイン後URL: {page.url}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()
        login(page)

        # パッケージ出品ページへ
        page.goto("https://www.lancers.jp/myplan/add", wait_until="domcontentloaded")
        time.sleep(4)
        page.screenshot(path="/tmp/lancers_myplan_add.png")
        print(f"URL: {page.url}")
        print(f"Title: {page.title()}")

        # フォーム要素を全取得
        print("\n=== INPUT要素 ===")
        inputs = page.query_selector_all("input")
        for inp in inputs:
            itype = inp.get_attribute("type") or "text"
            name = inp.get_attribute("name") or ""
            iid = inp.get_attribute("id") or ""
            placeholder = inp.get_attribute("placeholder") or ""
            print(f"  <input type={itype} name={name} id={iid} placeholder={placeholder}>")

        print("\n=== TEXTAREA要素 ===")
        textareas = page.query_selector_all("textarea")
        for ta in textareas:
            name = ta.get_attribute("name") or ""
            tid = ta.get_attribute("id") or ""
            placeholder = ta.get_attribute("placeholder") or ""
            print(f"  <textarea name={name} id={tid} placeholder={placeholder}>")

        print("\n=== SELECT要素 ===")
        selects = page.query_selector_all("select")
        for sel in selects:
            name = sel.get_attribute("name") or ""
            sid = sel.get_attribute("id") or ""
            print(f"  <select name={name} id={sid}>")
            options = sel.query_selector_all("option")
            for opt in options[:15]:
                val = opt.get_attribute("value") or ""
                text = opt.inner_text().strip()
                print(f"    <option value={val}>{text}</option>")

        print("\n=== BUTTON要素 ===")
        buttons = page.query_selector_all("button")
        for btn in buttons:
            btype = btn.get_attribute("type") or ""
            text = btn.inner_text().strip()
            print(f"  <button type={btype}>{text[:50]}</button>")

        # ページHTMLの一部を取得（フォーム部分）
        print("\n=== フォームHTML（先頭3000文字） ===")
        form = page.query_selector("form")
        if form:
            html = form.inner_html()
            print(html[:3000])
        else:
            print("formタグが見つかりません")
            body = page.content()
            print(body[2000:5000])

        browser.close()


if __name__ == "__main__":
    main()
