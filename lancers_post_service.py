"""
ランサーズ パッケージ新規出品スクリプト
業務自動化パッケージ（¥50,000）を出品する
ステップ: 基本情報 → 料金表 → 業務内容 → 確認事項 → 画像ほか → 公開
"""
import sys
import time
import subprocess
from playwright.sync_api import sync_playwright


# =====================================
# 出品内容
# =====================================
# 末尾に「ます」が自動付加される仕様のため除いて入力
# 実際の表示: "Make.com×AIで業務プロセスを自動化｜月20時間削減保証パッケージます"
TITLE = "Make.com×AIで業務プロセスを自動化｜月20時間削減保証パッケージ"
SUBTITLE = "繰り返し作業・手動コピペ・レポート作成をMake.com+AIで丸ごと自動化します"

# プラン[0]（ライトプラン）に¥50,000を設定（シングルプランとして使用）
PLAN_PRICE = "50000"
PLAN_DELIVERY = "14"  # 14日
PLAN_DESCRIPTION = """・業務フロー現状分析（ヒアリング1時間）
・自動化設計書の作成
・Make.com + AI（GPT/Claude）による自動化構築
・テスト・納品・操作マニュアル付き
・導入後サポート（1週間）"""

# 業務内容（詳細説明）
BUSINESS_CONTENT = """【Make.com×AI】で繰り返し作業を丸ごと自動化します

━━━━━━━━━━━━━━━
■ こんな方にぴったりです
━━━━━━━━━━━━━━━
・毎日同じコピペ作業に時間を取られている
・スプレッドシートへの手動入力・集計が面倒
・問い合わせ対応・レポート作成を自動化したい
・AIを使って業務効率化したいが何から始めていいかわからない

━━━━━━━━━━━━━━━
■ 提供内容（4ステップ）
━━━━━━━━━━━━━━━

① 業務フロー現状分析（ヒアリング1時間）
　→ 自動化できる箇所を特定し、優先度をご提示

② 自動化設計書の作成
　→ Make.com + AI（GPT/Claude）を使った設計図をご提示

③ 自動化システムの構築・テスト
　→ Make.com シナリオ + AI連携を実装・動作確認

④ 納品・操作説明
　→ 操作マニュアル付きでお渡し。導入後サポート1週間付き

━━━━━━━━━━━━━━━
■ 実績・効果
━━━━━━━━━━━━━━━
・対応時間 90% 削減
・月 20 時間以上の工数削減を実現
・継続的な運用コスト削減に貢献

━━━━━━━━━━━━━━━
■ 料金・納期
━━━━━━━━━━━━━━━
料金: 50,000円（税込）
納期: 7〜14日（内容により調整）

まずはお気軽にご相談ください。"""

# 確認事項（購入者への質問）
NOTICE = """ご購入いただく際に、下記3点についてご連絡いただけますと幸いです。

1. 自動化したい業務の内容（例：Googleスプレッドシートへの手動入力など）
2. 現在使用しているツール（例：Gmail、Slack、Notion、Googleスプレッドシートなど）
3. ご希望の完成イメージ・削減したい作業時間の目安"""

# カテゴリ設定
MAIN_CATEGORY_VALUE = "90"    # AI・プログラミング・システム開発
SUB_CATEGORY_VALUE = "108"    # Webプログラミング・システム開発/運用
INDUSTRY_VALUE = "2116"       # IT・通信・インターネット


def get_credentials():
    result = subprocess.run(
        "source ~/.bashrc && echo $LANCERS_EMAIL && echo $LANCERS_PASSWORD",
        shell=True, capture_output=True, text=True, executable="/bin/bash"
    )
    lines = result.stdout.strip().split("\n")
    return lines[0], lines[1]


def login(page):
    email, password = get_credentials()
    print(f"ログイン中: {email}")
    page.goto("https://www.lancers.jp/user/login", wait_until="domcontentloaded")
    time.sleep(3)
    email_field = page.query_selector('input[type="email"], input[name*="email"]')
    pass_field = page.query_selector('input[type="password"]')
    if not email_field or not pass_field:
        print("ERROR: ログインフォームが見つかりません")
        return False
    email_field.fill(email)
    pass_field.fill(password)
    time.sleep(1)
    submit_btn = page.query_selector('button[type="submit"]')
    if submit_btn:
        submit_btn.click()
    else:
        pass_field.press("Enter")
    time.sleep(4)
    if "login" in page.url:
        print("ERROR: ログイン失敗")
        return False
    print(f"ログイン成功: {page.url}")
    return True


def click_next_btn(page):
    """「次へ」ボタンをクリック"""
    next_btn = page.query_selector('button:has-text("次へ")')
    if next_btn:
        next_btn.click()
        time.sleep(3)
        return True
    print("ERROR: 「次へ」ボタンが見つかりません")
    return False


def is_on_next_step(page, step_text):
    """次のステップに遷移したか確認"""
    body = page.inner_text("body")
    return step_text in body


def step1_basic_info(page):
    """ステップ1: 基本情報"""
    print("\n=== STEP1: 基本情報 ===")

    # 「手動でパッケージを作成する」をクリック
    manual_btn = page.query_selector('button:has-text("手動でパッケージを作成する")')
    if not manual_btn:
        print("ERROR: 手動作成ボタンが見つかりません")
        page.screenshot(path="/tmp/lancers_step1_error.png")
        return False
    manual_btn.click()
    time.sleep(3)
    print("手動作成モードに切替")
    page.screenshot(path="/tmp/lancers_step1.png")

    # タイトル入力
    title_field = page.query_selector('textarea[name="ProjectPlanForm.title"]')
    if not title_field:
        print("ERROR: タイトルフィールドが見つかりません")
        return False
    title_field.fill(TITLE)
    print(f"タイトル入力: {TITLE}")
    time.sleep(0.5)

    # サブタイトル入力
    subtitle_field = page.query_selector('textarea[name="ProjectPlanForm.subtitle"]')
    if subtitle_field:
        subtitle_field.fill(SUBTITLE)
        print(f"サブタイトル入力完了")
        time.sleep(0.5)

    # 大カテゴリ選択
    main_cat = page.query_selector('select[name="___main_category_id"]')
    if main_cat:
        main_cat.select_option(value=MAIN_CATEGORY_VALUE)
        print(f"大カテゴリ選択: AI・プログラミング・システム開発")
        time.sleep(3)  # サブカテゴリが動的に読み込まれるのを待つ

    # 中カテゴリ選択
    sub_cat = page.query_selector('select[name="ProjectPlanForm.project_category_id"]')
    if sub_cat:
        sub_cat.select_option(value=SUB_CATEGORY_VALUE)
        print(f"中カテゴリ選択: Webプログラミング・システム開発/運用")
        time.sleep(1)

    # 業種選択
    industry = page.query_selector('select[name="ProjectPlanForm.industry_type_id"]')
    if industry:
        industry.select_option(value=INDUSTRY_VALUE)
        print(f"業種選択: IT・通信・インターネット")
        time.sleep(0.5)

    page.screenshot(path="/tmp/lancers_step1_filled.png")

    # 「次へ」をクリック（バリデーションがかかることを想定）
    if not click_next_btn(page):
        return False
    print(f"次へクリック後URL: {page.url}")

    # バリデーション後に「もしかしてこのカテゴリですか？」が出るか確認
    body = page.inner_text("body")
    if "もしかして" in body:
        print("「もしかしてこのカテゴリ」候補が表示 → クリックして確定")
        page.screenshot(path="/tmp/lancers_step1_category_suggest.png")

        # "Webプログラミング・システム開発/運用" を含む候補をクリック
        # ページ内のリンク・ボタンを全検索
        all_clickable = page.query_selector_all('button, a, [role="button"]')
        category_confirmed = False
        for el in all_clickable:
            text = el.inner_text().strip()
            if "Webプログラミング" in text:
                print(f"カテゴリ候補クリック: {text}")
                el.click()
                time.sleep(2)
                category_confirmed = True
                break

        if not category_confirmed:
            # テキスト内容でより詳細に確認
            print("Webプログラミング候補が見つからない、他の候補を確認:")
            idx = body.find("もしかして")
            print(body[idx:idx+400])
            # "AI・プログラミング" を含む候補を試みる
            for el in all_clickable:
                text = el.inner_text().strip()
                if "プログラミング" in text and "システム開発" in text:
                    print(f"代替カテゴリ候補クリック: {text}")
                    el.click()
                    time.sleep(2)
                    category_confirmed = True
                    break

        if not category_confirmed:
            print("WARNING: カテゴリ候補確定失敗 - 続行します")

        # カテゴリ確定後、業種が未選択なら再選択
        industry2 = page.query_selector('select[name="ProjectPlanForm.industry_type_id"]')
        if industry2:
            cur = industry2.input_value()
            if not cur:
                industry2.select_option(value=INDUSTRY_VALUE)
                print("業種再選択完了")
                time.sleep(0.5)

        page.screenshot(path="/tmp/lancers_step1_after_category.png")

        # 再度「次へ」をクリック
        if not click_next_btn(page):
            return False
        print(f"カテゴリ確定後 次へ → URL: {page.url}")

    # ステップ2（料金表）に遷移したか確認
    body_after = page.inner_text("body")
    if "料金" in body_after or "プラン" in body_after or "価格" in body_after:
        print("STEP1完了 → 料金表ページへ遷移")
        return True
    elif "もしかして" in body_after or "入力内容をご確認" in body_after:
        print("まだバリデーションエラーが残っています")
        page.screenshot(path="/tmp/lancers_step1_still_error.png")
        idx = body_after.find("確認")
        print(f"エラー内容:\n{body_after[max(0,idx-50):idx+300]}")
        return False
    else:
        print(f"STEP1完了 → {page.url}")
        return True


def step2_pricing(page):
    """ステップ2: 料金表"""
    print("\n=== STEP2: 料金表 ===")
    page.screenshot(path="/tmp/lancers_step2.png")

    # プラン[0]に¥50,000を設定
    price_fields = [
        ('input[name="ProjectPlanMenuForm[0].price"]', "ProjectPlanMenuForm[0]"),
        ('input[name="ProjectPlanMenuForm[1].price"]', "ProjectPlanMenuForm[1]"),
    ]

    price_set = False
    for selector, plan_name in price_fields:
        pf = page.query_selector(selector)
        if pf:
            pf.fill(PLAN_PRICE)
            print(f"価格入力 ({plan_name}): ¥{PLAN_PRICE}")
            time.sleep(0.5)
            price_set = True
            break

    if not price_set:
        print("ERROR: 価格フィールドが見つかりません")
        inputs = page.query_selector_all("input")
        for inp in inputs:
            print(f"  input name={inp.get_attribute('name')} placeholder={inp.get_attribute('placeholder')}")

    # 納期選択
    delivery_selectors = [
        'select[name="ProjectPlanMenuForm[0].delivery_time"]',
        'select[name="ProjectPlanMenuForm[1].delivery_time"]',
    ]
    for selector in delivery_selectors:
        ds = page.query_selector(selector)
        if ds:
            ds.select_option(value=PLAN_DELIVERY)
            print(f"納期選択: {PLAN_DELIVERY}日")
            time.sleep(0.5)
            break

    # プランの説明
    desc_selectors = [
        'textarea[name="ProjectPlanMenuForm[0].description"]',
        'textarea[name="ProjectPlanMenuForm[1].description"]',
    ]
    for selector in desc_selectors:
        df = page.query_selector(selector)
        if df:
            df.fill(PLAN_DESCRIPTION)
            print("プラン説明入力完了")
            time.sleep(0.5)
            break

    page.screenshot(path="/tmp/lancers_step2_filled.png")

    if not click_next_btn(page):
        return False
    print(f"STEP2完了 → URL: {page.url}")
    return True


def step3_business_content(page):
    """ステップ3: 業務内容"""
    print("\n=== STEP3: 業務内容 ===")
    page.screenshot(path="/tmp/lancers_step3.png")

    # 業務内容テキストエリア（nameなしのもの）
    textareas = page.query_selector_all("textarea")
    content_ta = None
    for ta in textareas:
        name = ta.get_attribute("name") or ""
        placeholder = ta.get_attribute("placeholder") or ""
        if not name and ("オススメ" in placeholder or "提供内容" in placeholder
                         or "ご購入後" in placeholder or "こんな方" in placeholder
                         or "ご提供" in placeholder):
            content_ta = ta
            break

    if not content_ta:
        # name未設定の最初のtextareaを使用
        for ta in textareas:
            name = ta.get_attribute("name") or ""
            if not name:
                content_ta = ta
                break

    if content_ta:
        content_ta.fill(BUSINESS_CONTENT)
        print("業務内容入力完了")
        time.sleep(0.5)
    else:
        print("WARNING: 業務内容フィールドが見つかりません")

    page.screenshot(path="/tmp/lancers_step3_filled.png")

    if not click_next_btn(page):
        return False
    print(f"STEP3完了 → URL: {page.url}")
    return True


def step4_confirmation(page):
    """ステップ4: 確認事項"""
    print("\n=== STEP4: 確認事項 ===")
    page.screenshot(path="/tmp/lancers_step4.png")

    notice_field = page.query_selector('textarea[name="ProjectPlanForm.notice_for_sale"]')
    if notice_field:
        notice_field.fill(NOTICE)
        print("確認事項入力完了")
        time.sleep(0.5)
    else:
        print("WARNING: 確認事項フィールドが見つかりません")

    page.screenshot(path="/tmp/lancers_step4_filled.png")

    if not click_next_btn(page):
        return False
    print(f"STEP4完了 → URL: {page.url}")
    return True


def step5_media(page):
    """ステップ5: 画像ほか（スキップ）"""
    print("\n=== STEP5: 画像ほか（スキップ） ===")
    page.screenshot(path="/tmp/lancers_step5.png")

    if not click_next_btn(page):
        return False
    print(f"STEP5完了（画像スキップ） → URL: {page.url}")
    return True


def step6_publish(page):
    """ステップ6: 公開"""
    print("\n=== STEP6: 公開 ===")
    page.screenshot(path="/tmp/lancers_step6.png")

    body_text = page.inner_text("body")
    print(f"公開ページ内容（先頭400文字）:\n{body_text[:400]}")

    # 公開ボタンを探す
    publish_btn = page.query_selector(
        'button:has-text("公開する"), button:has-text("出品する"), '
        'button:has-text("パッケージを公開"), button:has-text("登録する"), '
        'button:has-text("公開")'
    )
    if publish_btn:
        btn_text = publish_btn.inner_text().strip()
        print(f"公開ボタン: 「{btn_text}」→ クリック")
        publish_btn.click()
        time.sleep(5)
        page.screenshot(path="/tmp/lancers_published.png")
        result_url = page.url
        print(f"公開後URL: {result_url}")
        return result_url
    else:
        print("公開ボタンが見つかりません")
        buttons = page.query_selector_all("button")
        for btn in buttons:
            text = btn.inner_text().strip()
            if text:
                print(f"  ボタン: [{text}]")
        return None


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            if not login(page):
                return

            print("\nパッケージ出品ページへ移動...")
            page.goto("https://www.lancers.jp/myplan/add", wait_until="domcontentloaded")
            time.sleep(3)

            if not step1_basic_info(page):
                print("STEP1失敗")
                return

            if not step2_pricing(page):
                print("STEP2失敗")
                return

            if not step3_business_content(page):
                print("STEP3失敗")
                return

            if not step4_confirmation(page):
                print("STEP4失敗")
                return

            if not step5_media(page):
                print("STEP5失敗")
                return

            result_url = step6_publish(page)

            print("\n=== 完了 ===")
            if result_url:
                print(f"出品URL: {result_url}")
            print("\nスクリーンショット:")
            for f in [
                "/tmp/lancers_step1.png", "/tmp/lancers_step1_filled.png",
                "/tmp/lancers_step2.png", "/tmp/lancers_step2_filled.png",
                "/tmp/lancers_step3.png", "/tmp/lancers_step4.png",
                "/tmp/lancers_step5.png", "/tmp/lancers_step6.png",
                "/tmp/lancers_published.png"
            ]:
                print(f"  {f}")

        except Exception as e:
            print(f"例外エラー: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            page.screenshot(path="/tmp/lancers_exception.png")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
