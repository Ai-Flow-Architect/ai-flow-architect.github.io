/**
 * AI Flow Architect — LP問い合わせフォーム受信スクリプト
 *
 * 【セットアップ手順】
 * 1. script.google.com → 新規プロジェクト → このコードを貼り付け
 * 2. 「プロジェクトの設定」→「スクリプト プロパティ」に以下4件を追加:
 *    CLAUDE_LINK_APP_ID     … Larkメッセージ送信用アプリID
 *    CLAUDE_LINK_APP_SECRET … 同シークレット
 *    LARK_APP_ID            … LarkBase CRM用アプリID
 *    LARK_APP_SECRET        … 同シークレット
 * 3. 「デプロイ」→「新しいデプロイ」→ 種類:ウェブアプリ
 *    実行ユーザー: 自分 / アクセス: 全員（匿名ユーザー含む）
 * 4. デプロイURLを index.html の GAS_ENDPOINT に貼り付ける
 */

// ─── 設定 ────────────────────────────────────────────────────────────────
const LARK_BASE_URL = 'https://open.larksuite.com/open-apis';
const CRM_APP_TOKEN  = 'Uyz3bs7MGaoyFns7hIuj92Evpve';
const CUSTOMERS_TABLE = 'tblKqSYbQNUGugQ8';
const NOTIFY_CHAT_ID  = 'oc_01a50d5000a68e33718b938d2b177a27';

// スパム対策: 同一メールアドレスからの送信を1分に1回に制限
const RATE_KEY_PREFIX = 'rate_';

// ─── メインハンドラ ─────────────────────────────────────────────────────
function doPost(e) {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Content-Type': 'application/json'
  };
  try {
    const body = JSON.parse(e.postData.contents);
    const name    = body.name    || '';
    const company = body.company || '';
    const email   = body.email   || '';
    const message = body.message || '';
    const budget  = body.budget  || '';

    // 必須項目チェック
    if (!name || !email || !message) {
      return ContentService
        .createTextOutput(JSON.stringify({status:'error', msg:'必須項目が未入力です'}))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // スパム制限チェック
    const props = PropertiesService.getScriptProperties();
    const rateKey = RATE_KEY_PREFIX + email;
    const lastSent = parseInt(props.getProperty(rateKey) || '0');
    const now = Date.now();
    if (now - lastSent < 60000) {
      return ContentService
        .createTextOutput(JSON.stringify({status:'ok'})) // 正常を装ってスパマーに情報漏洩しない
        .setMimeType(ContentService.MimeType.JSON);
    }
    props.setProperty(rateKey, String(now));

    // ① Lark 通知（エラーでも継続）
    try { sendLarkNotification(name, company, email, message, budget); } catch(err) { Logger.log('Lark通知エラー: ' + err); }

    // ② CRM 記録（エラーでも継続）
    try { addToCrm(name, company, email, message, budget); } catch(err) { Logger.log('CRMエラー: ' + err); }

    // ③ 相手に自動返信メール
    try { sendAutoReply(name, email); } catch(err) { Logger.log('メール送信エラー: ' + err); }

    return ContentService
      .createTextOutput(JSON.stringify({status:'ok'}))
      .setMimeType(ContentService.MimeType.JSON);

  } catch(err) {
    Logger.log('doPost エラー: ' + err);
    return ContentService
      .createTextOutput(JSON.stringify({status:'error', msg:'サーバーエラーが発生しました'}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// CORSプリフライト対応
function doGet(e) {
  return ContentService
    .createTextOutput(JSON.stringify({status:'ok', service:'AI Flow Architect Contact Form'}))
    .setMimeType(ContentService.MimeType.JSON);
}

// ─── Lark トークン取得 ──────────────────────────────────────────────────
function getLarkToken(appIdKey, appSecretKey) {
  const props = PropertiesService.getScriptProperties();
  const appId     = props.getProperty(appIdKey);
  const appSecret = props.getProperty(appSecretKey);
  const res = UrlFetchApp.fetch(LARK_BASE_URL + '/auth/v3/tenant_access_token/internal', {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify({app_id: appId, app_secret: appSecret}),
    muteHttpExceptions: true
  });
  return JSON.parse(res.getContentText()).tenant_access_token;
}

// ─── ① Lark チャット通知 ────────────────────────────────────────────────
function sendLarkNotification(name, company, email, message, budget) {
  const token = getLarkToken('CLAUDE_LINK_APP_ID', 'CLAUDE_LINK_APP_SECRET');
  const budgetLabel = {
    'lite':      '¥40,000〜¥75,000（Liteプラン）',
    'standard':  '¥80,000〜¥150,000（Standardプラン）',
    'full':      '¥150,000〜（Full Package）',
    'undecided': '未定 / まず相談したい',
    '':          '未回答'
  }[budget] || budget;

  const card = {
    config: {wide_screen_mode: true},
    header: {
      title: {tag: 'plain_text', content: '🔔 LP問い合わせが届きました'},
      template: 'orange'
    },
    elements: [
      {tag: 'div', text: {tag: 'lark_md', content:
        '**👤 お名前**: ' + name + '\n' +
        '**🏢 会社名**: ' + (company || '未記入') + '\n' +
        '**📧 メール**: ' + email
      }},
      {tag: 'hr'},
      {tag: 'div', text: {tag: 'lark_md', content: '**📝 相談内容**\n' + message}},
      {tag: 'hr'},
      {tag: 'div', text: {tag: 'lark_md', content: '**💰 予算目安**: ' + budgetLabel}},
      {tag: 'note', elements: [{tag: 'lark_md', content: '⏰ ' + new Date().toLocaleString('ja-JP', {timeZone:'Asia/Tokyo'}) + ' | CRM自動記録済み'}]}
    ]
  };

  UrlFetchApp.fetch(LARK_BASE_URL + '/im/v1/messages?receive_id_type=chat_id', {
    method: 'post',
    headers: {
      'Authorization': 'Bearer ' + token,
      'Content-Type': 'application/json'
    },
    payload: JSON.stringify({
      receive_id: NOTIFY_CHAT_ID,
      msg_type: 'interactive',
      content: JSON.stringify(card)
    }),
    muteHttpExceptions: true
  });
}

// ─── ② CRM 顧客テーブルに追加 ──────────────────────────────────────────
function addToCrm(name, company, email, message, budget) {
  const token = getLarkToken('LARK_APP_ID', 'LARK_APP_SECRET');
  const memo = '【LP問い合わせ】' +
    (company ? '会社: ' + company + ' / ' : '') +
    '予算: ' + (budget || '未記入') + '\n相談内容: ' + message;

  const fields = {
    '顧客名':    name,
    'ステータス': '🆕 新規',
    'メモ':      memo,
    '最終接触日': Date.now()
  };
  if (company) fields['会社名'] = company;
  if (email)   fields['メール'] = email;

  UrlFetchApp.fetch(
    'https://open.larksuite.com/open-apis/bitable/v1/apps/' + CRM_APP_TOKEN + '/tables/' + CUSTOMERS_TABLE + '/records',
    {
      method: 'post',
      headers: {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
      },
      payload: JSON.stringify({fields: fields}),
      muteHttpExceptions: true
    }
  );
}

// ─── ③ 相手へ自動返信メール ────────────────────────────────────────────
function sendAutoReply(name, email) {
  const subject = 'AI Flow Architect: お問い合わせありがとうございます';
  const body =
    name + ' 様\n\n' +
    'この度はお問い合わせいただきありがとうございます。\n' +
    'AI Flow Architect（五十嵐 こうすけ）です。\n\n' +
    'ご連絡の内容を確認いたしました。\n' +
    '通常12時間以内にご返信いたします。\n\n' +
    '急ぎのご連絡はXのDM（@Kosuke_free_）もご利用ください。\n\n' +
    '──────────────────────\n' +
    'AI Flow Architect\n' +
    'https://ai-flow-architect.github.io/\n' +
    'X: https://x.com/Kosuke_free_\n' +
    '──────────────────────\n\n' +
    '※ このメールは自動送信されています。このメールへの返信は確認されません。';

  MailApp.sendEmail({
    to: email,
    subject: subject,
    body: body,
    name: 'AI Flow Architect'
  });
}
