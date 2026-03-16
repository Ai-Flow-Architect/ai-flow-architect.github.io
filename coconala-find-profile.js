// セッション再利用してプロフィール編集ページのURLを特定するスクリプト
const { chromium } = require('/home/kosuke_igarashi/projects/mercari-bot/node_modules/playwright');
const SESSION_DIR = '/home/kosuke_igarashi/.coconala-session';

(async () => {
  const browser = await chromium.launchPersistentContext(SESSION_DIR, {
    headless: false,
    args: ['--disable-sync', '--no-first-run'],
  });
  const page = await browser.newPage();

  // 試すURL候補
  const urls = [
    'https://coconala.com/mypage/profile',
    'https://coconala.com/mypage/profile/edit',
    'https://coconala.com/mypage',
  ];

  for (const url of urls) {
    console.log(`\n試すURL: ${url}`);
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 }).catch(e => console.log('エラー:', e.message));
    await page.waitForTimeout(2000);
    console.log('実際のURL:', page.url());

    const textareas = await page.$$('textarea');
    const links = await page.$$eval('a[href*="profile"]', els => els.map(e => e.href).slice(0, 10));
    console.log(`textareas: ${textareas.length}, profile links:`, links);

    if (textareas.length > 0) {
      console.log('✅ テキストエリア発見！このURLが正解かもしれません');
      await page.screenshot({ path: '/home/kosuke_igarashi/projects/new-project/coconala-found.png', fullPage: false });
      break;
    }
  }

  // さらにmypageから自己紹介リンクを探す
  console.log('\nマイページから自己紹介リンクを探しています...');
  await page.goto('https://coconala.com/mypage', { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(2000);

  const allLinks = await page.$$eval('a', els =>
    els.map(e => ({ text: e.textContent.trim(), href: e.href }))
       .filter(l => l.text.includes('自己紹介') || l.text.includes('基本情報') || l.text.includes('プロフィール') || l.href.includes('profile'))
       .slice(0, 20)
  );
  console.log('プロフィール関連リンク:', JSON.stringify(allLinks, null, 2));

  await page.screenshot({ path: '/home/kosuke_igarashi/projects/new-project/coconala-mypage.png', fullPage: false });
  console.log('📸 マイページのスクリーンショット保存');

  await browser.close();
})();
