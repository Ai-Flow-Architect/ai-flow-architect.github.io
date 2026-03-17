"""
ランサーズのサービス出品URL・フォーム構造を探索するスクリプト
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
    return True


def explore_mypage(page):
    """マイページのリンクを全て取得してサービス出品URLを特定"""
    page.goto("https://www.lancers.jp/mypage", wait_until="domcontentloaded")
    time.sleep(3)
    page.screenshot(path="/tmp/lancers_mypage.png")

    # ページ内のリンクを全取得
    links = page.query_selector_all("a[href]")
    print(f"\n=== マイページのリンク（サービス・パッケージ関連） ===")
    for link in links:
        href = link.get_attribute("href") or ""
        text = link.inner_text().strip()
        if any(kw in href.lower() for kw in ["service", "package", "skill", "offer", "profile", "work"]):
            print(f"  [{text[:30]}] -> {href}")

    # 「出品する」ボタンを探す
    print("\n=== 「出品」関連ボタン/リンク ===")
    for link in links:
        text = link.inner_text().strip()
        href = link.get_attribute("href") or ""
        if any(kw in text for kw in ["出品", "追加", "作成", "登録", "新規"]):
            print(f"  [{text[:40]}] -> {href}")


def explore_profile_services(page):
    """プロフィールのサービスページを確認"""
    page.goto("https://www.lancers.jp/profile/services", wait_until="domcontentloaded")
    time.sleep(3)
    page.screenshot(path="/tmp/lancers_profile_services.png")
    print(f"\nURL: {page.url}, Title: {page.title()}")

    links = page.query_selector_all("a[href]")
    for link in links:
        href = link.get_attribute("href") or ""
        text = link.inner_text().strip()
        if any(kw in text for kw in ["出品", "追加", "作成", "登録", "新規", "サービス"]):
            print(f"  [{text[:40]}] -> {href}")


def explore_top_navi(page):
    """トップナビの「出品する」ボタンのリンクを確認"""
    page.goto("https://www.lancers.jp/mypage", wait_until="domcontentloaded")
    time.sleep(3)

    # 「出品する」ボタン
    publish_btn = page.query_selector('a:has-text("出品する"), button:has-text("出品する")')
    if publish_btn:
        href = publish_btn.get_attribute("href") or ""
        print(f"\n「出品する」ボタンのhref: {href}")
        publish_btn.click()
        time.sleep(3)
        print(f"遷移後URL: {page.url}")
        page.screenshot(path="/tmp/lancers_publish_click.png")

        # さらにリンクを探索
        links = page.query_selector_all("a[href]")
        print("出品メニューのリンク:")
        for link in links[:30]:
            href = link.get_attribute("href") or ""
            text = link.inner_text().strip()
            if text:
                print(f"  [{text[:40]}] -> {href}")
    else:
        print("「出品する」ボタンが見つかりません")


def try_package_urls(page):
    """パッケージ/サービス出品の可能性があるURLを試す"""
    candidate_urls = [
        "https://www.lancers.jp/package/create",
        "https://www.lancers.jp/packages/create",
        "https://www.lancers.jp/service/add",
        "https://www.lancers.jp/mypage/service/create",
        "https://www.lancers.jp/work/create",
        "https://www.lancers.jp/profile/service/create",
    ]

    print("\n=== URLを試します ===")
    for url in candidate_urls:
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(2)
        current = page.url
        title = page.title()
        status = "404" if "404" in title or page.url == url and "not" in title.lower() else "OK?"
        print(f"{url}")
        print(f"  -> {current} [{title[:40]}]")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        login(page)
        explore_mypage(page)
        explore_profile_services(page)
        explore_top_navi(page)
        try_package_urls(page)

        browser.close()


if __name__ == "__main__":
    main()
