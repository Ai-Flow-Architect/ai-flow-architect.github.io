"""
ランサーズ パッケージ新規出品スクリプト v2
根本原因: 「業務」ラジオボタン（必須）が未選択だったため

修正ポイント:
1. 「業務」セクションのラジオボタンを選択（service_type = 116: スクリプティング）
2. 「もしかして」候補リンクは無視（バリデーションに影響しない）
3. セレクトボックスで大・中カテゴリを設定すれば十分
"""
import sys
import time
import subprocess
from playwright.sync_api import sync_playwright


# =====================================
# 出品内容
# =====================================
TITLE = "Make.com×AIで業務プロセスを自動化｜月20時間削減保証パッケージ"
SUBTITLE = "繰り返し作業・手動コピペ・レポート作成をMake.com+AIで丸ごと自動化します"

# 3プラン必須（80文字以内）
PLANS = [
    {
        "price": "30000",
        "delivery": "7",
        "description": "ヒアリング+設計書+1業務自動化+テスト納品（修正2回）",  # 30文字
    },
    {
        "price": "50000",
        "delivery": "14",
        "description": "ヒアリング+設計書+2業務自動化+テスト納品+操作説明（修正3回）",  # 34文字
    },
    {
        "price": "80000",
        "delivery": "21",
        "description": "ヒアリング+設計書+3業務自動化+テスト納品+操作説明+1ヶ月サポート（修正無制限）",  # 44文字
    },
]

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

NOTICE = """ご購入いただく際に、下記3点についてご連絡いただけますと幸いです。

1. 自動化したい業務の内容（例：Googleスプレッドシートへの手動入力など）
2. 現在使用しているツール（例：Gmail、Slack、Notion、Googleスプレッドシートなど）
3. ご希望の完成イメージ・削減したい作業時間の目安"""

MAIN_CATEGORY_VALUE = "90"    # AI・プログラミング・システム開発
SUB_CATEGORY_VALUE = "108"    # Webプログラミング・システム開発/運用
INDUSTRY_VALUE = "2116"       # IT・通信・インターネット
SERVICE_TYPE_VALUE = "116"    # スクリプティング（業務ラジオボタン・必須）


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
    page.query_selector('input[type="email"]').fill(email)
    page.query_selector('input[type="password"]').fill(password)
    time.sleep(1)
    btn = page.query_selector('button[type="submit"]')
    btn.click() if btn else page.query_selector('input[type="password"]').press("Enter")
    time.sleep(4)
    if "login" in page.url:
        print("ERROR: ログイン失敗")
        return False
    print(f"ログイン成功: {page.url}")
    return True


def step1_basic_info(page):
    """ステップ1: 基本情報"""
    print("\n=== STEP1: 基本情報 ===")

    manual_btn = page.query_selector('button:has-text("手動でパッケージを作成する")')
    if not manual_btn:
        print("ERROR: 手動作成ボタンが見つかりません")
        return False
    manual_btn.click()
    time.sleep(3)
    print("手動作成モードに切替")

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
        print("サブタイトル入力完了")
        time.sleep(0.5)

    # 大カテゴリ
    main_cat = page.query_selector('select[name="___main_category_id"]')
    if main_cat:
        main_cat.select_option(value=MAIN_CATEGORY_VALUE)
        print("大カテゴリ: AI・プログラミング・システム開発")
        time.sleep(3)  # サブカテゴリ読み込み待ち

    # 中カテゴリ
    sub_cat = page.query_selector('select[name="ProjectPlanForm.project_category_id"]')
    if sub_cat:
        sub_cat.select_option(value=SUB_CATEGORY_VALUE)
        print("中カテゴリ: Webプログラミング・システム開発/運用")
        time.sleep(2)  # 業務チェックボックス読み込み待ち

    # 業務ラジオボタン選択（必須）
    # value=116: スクリプティング
    service_radio = page.query_selector(f'input[name="ProjectPlanCategoryForm.service_type[0]"][value="{SERVICE_TYPE_VALUE}"]')
    if service_radio:
        # labelをクリックする（radioはlabelクリックが確実）
        label = page.query_selector(f'label[for="{SERVICE_TYPE_VALUE}"]')
        if label:
            label.click()
            print(f"業務選択: スクリプティング (value={SERVICE_TYPE_VALUE})")
            time.sleep(0.5)
        else:
            service_radio.click()
            print(f"業務選択（radio直接クリック）: {SERVICE_TYPE_VALUE}")
            time.sleep(0.5)
    else:
        # radioが見つからない場合、利用可能な選択肢を確認
        print("WARNING: 業務ラジオボタンが見つかりません。利用可能な選択肢を確認:")
        radios = page.query_selector_all('input[name*="service_type"]')
        for r in radios:
            val = r.get_attribute("value") or ""
            rid = r.get_attribute("id") or ""
            label = page.query_selector(f'label[for="{rid}"]')
            label_text = label.inner_text().strip() if label else ""
            print(f"  value={val} id={rid}: {label_text}")
        # 最初のラジオを選択
        if radios:
            first_radio = radios[0]
            first_id = first_radio.get_attribute("id") or ""
            first_label = page.query_selector(f'label[for="{first_id}"]')
            if first_label:
                first_label.click()
                print(f"業務選択（最初の選択肢）: id={first_id}")
            else:
                first_radio.click()
            time.sleep(0.5)

    # 業種選択
    ind = page.query_selector('select[name="ProjectPlanForm.industry_type_id"]')
    if ind:
        ind.select_option(value=INDUSTRY_VALUE)
        print("業種: IT・通信・インターネット")
        time.sleep(0.5)

    page.screenshot(path="/tmp/lancers_v2_step1_filled.png")

    # 「次へ」クリック
    next_btn = page.query_selector('button:has-text("次へ")')
    if not next_btn:
        print("ERROR: 「次へ」ボタンが見つかりません")
        return False
    next_btn.click()
    time.sleep(3)
    print(f"次へクリック後URL: {page.url}")

    # 結果確認
    body = page.inner_text("body")
    page.screenshot(path="/tmp/lancers_v2_step1_result.png")

    if "入力内容をご確認" in body:
        # まだエラー → エラー内容を表示
        idx = body.find("入力内容をご確認")
        print(f"バリデーションエラー継続:\n{body[idx:idx+500]}")
        return False
    else:
        print("STEP1クリア → STEP2へ")
        return True


def step2_pricing(page):
    """ステップ2: 料金表（3プラン全て必須）"""
    print("\n=== STEP2: 料金表 ===")
    page.screenshot(path="/tmp/lancers_v2_step2.png")

    body = page.inner_text("body")
    print(f"ページ先頭100文字: {body[:100]}")

    for plan_idx, plan in enumerate(PLANS):
        # 価格入力
        pf = page.query_selector(f'input[name="ProjectPlanMenuForm[{plan_idx}].price"]')
        if pf:
            pf.fill(plan["price"])
            print(f"価格 [plan{plan_idx}]: ¥{plan['price']}")
            time.sleep(0.3)

        # 納期選択
        ds = page.query_selector(f'select[name="ProjectPlanMenuForm[{plan_idx}].delivery_time"]')
        if ds:
            ds.select_option(value=plan["delivery"])
            print(f"納期 [plan{plan_idx}]: {plan['delivery']}日")
            time.sleep(0.3)

        # プラン説明（80文字以内）
        df = page.query_selector(f'textarea[name="ProjectPlanMenuForm[{plan_idx}].description"]')
        if df:
            desc = plan["description"][:80]  # 念のため80文字にトリム
            df.fill(desc)
            print(f"説明 [plan{plan_idx}]: {desc} ({len(desc)}文字)")
            time.sleep(0.3)

    page.screenshot(path="/tmp/lancers_v2_step2_filled.png")

    next_btn = page.query_selector('button:has-text("次へ")')
    if not next_btn:
        print("ERROR: 「次へ」なし")
        return False
    next_btn.click()
    time.sleep(3)

    body = page.inner_text("body")
    if "入力内容をご確認" in body:
        print("STEP2バリデーションエラー:")
        idx = body.find("入力内容をご確認")
        print(body[idx:idx+300])
        page.screenshot(path="/tmp/lancers_v2_step2_error.png")
        return False

    print(f"STEP2完了 → URL: {page.url}")
    return True


def step3_business_content(page):
    """ステップ3: 業務内容"""
    print("\n=== STEP3: 業務内容 ===")
    page.screenshot(path="/tmp/lancers_v2_step3.png")

    # 業務内容textarea（nameなし）
    textareas = page.query_selector_all("textarea")
    content_ta = None
    for ta in textareas:
        name = ta.get_attribute("name") or ""
        ph = ta.get_attribute("placeholder") or ""
        if not name and ta.is_visible() and ("オススメ" in ph or "提供内容" in ph or
                                              "ご購入後" in ph or "こんな方" in ph):
            content_ta = ta
            break

    if not content_ta:
        for ta in textareas:
            if not ta.get_attribute("name") and ta.is_visible():
                content_ta = ta
                break

    if content_ta:
        content_ta.fill(BUSINESS_CONTENT)
        print("業務内容入力完了")
        time.sleep(0.5)
    else:
        print("WARNING: 業務内容フィールドが見つかりません")

    page.screenshot(path="/tmp/lancers_v2_step3_filled.png")

    next_btn = page.query_selector('button:has-text("次へ")')
    if not next_btn:
        return False
    next_btn.click()
    time.sleep(3)
    print(f"STEP3完了 → URL: {page.url}")
    return True


def step4_confirmation(page):
    """ステップ4: 確認事項"""
    print("\n=== STEP4: 確認事項 ===")
    page.screenshot(path="/tmp/lancers_v2_step4.png")

    notice_field = page.query_selector('textarea[name="ProjectPlanForm.notice_for_sale"]')
    if notice_field and notice_field.is_visible():
        notice_field.fill(NOTICE)
        print("確認事項入力完了")
        time.sleep(0.5)
    else:
        print("WARNING: 確認事項フィールドが見つかりません")

    next_btn = page.query_selector('button:has-text("次へ")')
    if not next_btn:
        return False
    next_btn.click()
    time.sleep(3)
    print(f"STEP4完了 → URL: {page.url}")
    return True


def step5_media_and_publish(page):
    """ステップ5: 画像ほか → 公開する（このステップに公開ボタンあり）"""
    print("\n=== STEP5: 画像ほか → 公開 ===")
    page.screenshot(path="/tmp/lancers_v2_step5.png")

    body = page.inner_text("body")
    print(f"ステップ5ページ先頭: {body[:100]}")

    # 「公開する」ボタンをクリック
    publish_btn = page.query_selector(
        'button:has-text("公開する"), button:has-text("公開"), '
        'button:has-text("出品する"), button:has-text("次へ")'
    )
    if publish_btn:
        btn_text = publish_btn.inner_text().strip()
        print(f"ボタン発見: 「{btn_text}」→ クリック")
        publish_btn.click()
        time.sleep(5)
        page.screenshot(path="/tmp/lancers_v2_published.png")
        result_url = page.url
        print(f"公開後URL: {result_url}")
        return result_url
    else:
        print("公開ボタンが見つかりません。ボタン一覧:")
        for btn in page.query_selector_all("button"):
            t = btn.inner_text().strip()
            if t:
                print(f"  [{t}]")
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
                print("STEP1失敗 → 終了")
                return

            if not step2_pricing(page):
                print("STEP2失敗 → 終了")
                return

            if not step3_business_content(page):
                print("STEP3失敗 → 終了")
                return

            if not step4_confirmation(page):
                print("STEP4失敗 → 終了")
                return

            result_url = step5_media_and_publish(page)

            print("\n=== 完了 ===")
            if result_url:
                print(f"出品URL: {result_url}")
            else:
                print("URLを取得できませんでした")

        except Exception as e:
            print(f"例外エラー: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            try:
                page.screenshot(path="/tmp/lancers_v2_exception.png")
            except Exception:
                pass
        finally:
            browser.close()


if __name__ == "__main__":
    main()
