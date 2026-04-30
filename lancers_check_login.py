#!/usr/bin/env python3
"""ランサーズ: ログインフォーム確認"""
import os
import time
from playwright.sync_api import sync_playwright

EMAIL = os.environ["LANCERS_EMAIL"]
PASSWORD = os.environ["LANCERS_PASSWORD"]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()

    print("ランサーズログインページにアクセス...")
    page.goto("https://www.lancers.jp/user/login", timeout=30000)
    page.wait_for_load_state("domcontentloaded")
    time.sleep(3)

    page.screenshot(path="/tmp/lancers_login.png")
    print(f"URL: {page.url}")

    # フォーム要素を確認
    inputs = page.query_selector_all("input")
    print(f"input要素数: {len(inputs)}")
    for inp in inputs:
        name = inp.get_attribute("name")
        type_ = inp.get_attribute("type")
        id_ = inp.get_attribute("id")
        placeholder = inp.get_attribute("placeholder")
        print(f"  name={name} type={type_} id={id_} placeholder={placeholder}")

    browser.close()
