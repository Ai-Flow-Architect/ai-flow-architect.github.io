const { chromium } = require('/home/kosuke_igarashi/projects/mercari-bot/node_modules/playwright');
const SESSION_DIR = '/home/kosuke_igarashi/.coconala-session';

const EMAIL = process.env.COCONALA_EMAIL || '';
const PASSWORD = process.env.COCONALA_PASSWORD || '';

const PROFILE_TEXT = `「めんどくさい」を10秒で消す。AI自動化で本当の仕事に集中しませんか？

売上の集計、報告メールの送信、スプレッドシートへの転記——
毎日・毎週やっているのに、誰もうれしくない「消耗タスク」。
それ、AIとツール連携で自動化できます。

◆ 得意な自動化領域
・EC売上の自動集計 → GPT分析 → LINE毎日通知
・問い合わせ対応の自動仕分け・返信
・スプレッドシート / Google / Notion / Lark への自動入力
・Webhook連携による複数ツールの連結
・Make.com × Claude AI × LINE / Slack の組み合わせ設計

◆ 進め方（シンプル・最短3日）
① ヒアリング（30分・無料）
② デモ動画でイメージ共有
③ 実装・テスト
④ 引き渡し ＋ 操作説明

◆ こんな方に向いています
・「毎日Excelに手でコピーしている」作業がある
・LINE / メールを毎日手動送信している
・ツールは導入したが連携できていない
・エンジニアに頼むほどでもない小さな自動化がしたい

◆ 対応ツール
Make.com / Zapier / Google Apps Script / ChatGPT API /
LINE API / Slack API / Google スプレッドシート / Notion / Lark

「こんな作業、自動化できるかな？」という相談だけでもOKです。
まず小さく試すプランからご提案します。お気軽にどうぞ。`;

async function fillProfileText(page) {
  const textareas = await page.$$('textarea');
  console.log(`textarea数: ${textareas.length}`);
  for (let i = 0; i < textareas.length; i++) {
    const ph = await textareas[i].getAttribute('placeholder') || '';
    const name = await textareas[i].getAttribute('name') || '';
    const rows = await textareas[i].getAttribute('rows') || '1';
    const val = (await textareas[i].inputValue()).substring(0, 40);
    console.log(`  [${i}] name="${name}" ph="${ph.substring(0,25)}" rows=${rows} val="${val}"`);
  }

  // 自己紹介欄を特定（フィードバック欄は除外）
  for (const ta of textareas) {
    const ph = await ta.getAttribute('placeholder') || '';
    const name = (await ta.getAttribute('name') || '').toLowerCase();
    const rows = parseInt(await ta.getAttribute('rows') || '1');
    if (ph.includes('ご意見') || ph.includes('ご要望')) continue;
    if (name.includes('pr') || name.includes('profile') || name.includes('intro') ||
        name.includes('description') || name.includes('body') || rows >= 4) {
      await ta.scrollIntoViewIfNeeded();
      await ta.click({ clickCount: 3 });
      await ta.fill(PROFILE_TEXT);
      console.log(`✅ 入力完了 (name="${name}", rows=${rows})`);
      return true;
    }
  }
  return false;
}

(async () => {
  console.log('ブラウザ起動中...');
  const browser = await chromium.launchPersistentContext(SESSION_DIR, {
    headless: false,
    args: ['--disable-sync', '--no-first-run'],
  });
  const page = await browser.newPage();

  // ログイン
  await page.goto('https://coconala.com/login', { waitUntil: 'domcontentloaded', timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(2000);

  if (page.url().includes('/login')) {
    const emailEl = await page.$('input[type="email"], input[name*="email"]');
    const passEl = await page.$('input[type="password"]');
    if (emailEl) await emailEl.fill(EMAIL);
    if (passEl) await passEl.fill(PASSWORD);
    const btn = await page.$('button[type="submit"]');
    if (btn) await btn.click();
    console.log('ログイン中... reCAPTCHAが出たらブラウザで解決してください');
    // ログイン完了を最大2分ポーリングで待機
    for (let i = 0; i < 120; i++) {
      await page.waitForTimeout(1000);
      if (!page.url().includes('/login')) break;
    }
    console.log('ログイン後URL:', page.url());
  } else {
    console.log('✅ セッション有効');
  }

  // user_account経由でプロフィール編集へクリック
  console.log('\nプロフィール編集ページへ...');
  await page.goto('https://coconala.com/mypage/user_account', { waitUntil: 'domcontentloaded', timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(2000);

  // "プロフィール編集" リンクをクリック
  const profLink = await page.$('a[href="/mypage/user"], a[href*="/mypage/user?ref=common_header_button"]');
  if (profLink) {
    console.log('プロフィール編集リンクをクリック...');
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 15000 }).catch(() => {}),
      profLink.click()
    ]);
    await page.waitForTimeout(3000);
  } else {
    // 直接navigateを試行
    await page.goto('https://coconala.com/mypage/user', { waitUntil: 'commit', timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(4000);
  }
  console.log('URL:', page.url());
  await page.screenshot({ path: '/home/kosuke_igarashi/projects/new-project/coconala-prof-edit.png' });

  // 自己紹介欄を探して入力
  let filled = await fillProfileText(page);

  // 見つからない場合、user_informationを試す
  if (!filled) {
    console.log('\nuser_informationページを試します...');
    await page.goto('https://coconala.com/mypage/user_information', { waitUntil: 'domcontentloaded', timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(3000);
    console.log('URL:', page.url());
    await page.screenshot({ path: '/home/kosuke_igarashi/projects/new-project/coconala-user-info.png' });
    filled = await fillProfileText(page);
  }

  if (filled) {
    await page.screenshot({ path: '/home/kosuke_igarashi/projects/new-project/coconala-filled.png' });
    console.log('\n✅ 入力完了！ブラウザで確認して「保存」ボタンを押してください。');
  } else {
    console.log('\n❌ 自己紹介欄が見つかりませんでした。スクリーンショットを確認してください。');
  }

  await page.waitForEvent('close', { timeout: 300000 }).catch(() => {});
  await browser.close();
})();
