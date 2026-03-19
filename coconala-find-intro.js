const { chromium } = require('/home/kosuke_igarashi/projects/mercari-bot/node_modules/playwright');
const SESSION_DIR = '/home/kosuke_igarashi/.coconala-session';

(async () => {
  const browser = await chromium.launchPersistentContext(SESSION_DIR, {
    headless: false,
    args: ['--disable-sync', '--no-first-run'],
  });
  const page = await browser.newPage();

  await page.goto('https://coconala.com/mypage/user_account', { waitUntil: 'domcontentloaded', timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(3000);

  // 左メニューの全リンクを取得
  const links = await page.$$eval('a', els =>
    els.map(e => ({ text: e.textContent.trim().replace(/\s+/g, ' ').substring(0, 30), href: e.href }))
       .filter(l => l.href.includes('mypage') || l.href.includes('profile') || l.href.includes('user'))
       .filter(l => l.text.length > 0)
  );
  console.log('マイページ関連リンク:');
  links.forEach(l => console.log(`  "${l.text}" → ${l.href}`));

  // サイドバーのリンクのみを取得
  const sideLinks = await page.$$eval('nav a, aside a, .sidebar a, [class*="side"] a, [class*="menu"] a, [class*="nav"] a', els =>
    els.map(e => ({ text: e.textContent.trim().replace(/\s+/g, ' ').substring(0, 30), href: e.href }))
  );
  console.log('\nサイドバーリンク:');
  sideLinks.forEach(l => console.log(`  "${l.text}" → ${l.href}`));

  await browser.close();
})();
