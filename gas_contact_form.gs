/**
 * AI Flow Architect — LP問い合わせ / AI診断リード 受信スクリプト（堅牢版 2026-07-16）
 *
 * 【この版の要点】
 * ・事業者(あなた)への「メール通知」を最優先の確実な経路にした（Lark/CRMの生死に依存しない）
 * ・全リードを Google シートに追記（durableな台帳・消えない）
 * ・旧CRM直書き(Bitable table tblKqSYbQNUGugQ8) は削除
 *   └ 当該テーブルは削除済み(TableIdNotFound)で書込が無言失敗していた
 *   └ AIレコメンド表(tblgJFCtesFJlsKK)は毎朝再生成のため直書き不可（翌朝消える）
 *   └ CRM(deals)への自動記録は「シート→deals ingester」で別途行う（stage-validator経由）
 * ・Lark通知は best-effort で残置（成功すれば従来どおりカードが飛ぶ）
 *
 * 【セットアップ手順（あなたのGoogleアカウントで）】
 * 1. script.google.com で既存プロジェクトを開く（このコードで全置換）
 * 2. 「プロジェクトの設定」→「スクリプト プロパティ」に追加/確認:
 *    NOTIFY_EMAIL          … あなたの通知受信メール（例: 事業用アドレス）※必須
 *    LEADS_SHEET_ID        … リード台帳スプレッドシートのID（任意・空なら台帳スキップ）
 *    CLAUDE_LINK_APP_ID / CLAUDE_LINK_APP_SECRET … Lark通知を使う場合のみ（任意）
 * 3. 「デプロイ」→「デプロイを管理」→ 既存ウェブアプリを「新バージョン」で更新
 *    （URLは変わらない＝index.html側の GAS_ENDPOINT はそのままでOK）
 */

// ─── 設定 ────────────────────────────────────────────────────────────────
const LARK_BASE_URL  = 'https://open.larksuite.com/open-apis';
const NOTIFY_CHAT_ID = 'oc_01a50d5000a68e33718b938d2b177a27';  // Lark通知チャット（任意）
const RATE_KEY_PREFIX = 'rate_';   // スパム対策: 同一メール1分1回

// ─── メインハンドラ ─────────────────────────────────────────────────────
function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    const name    = (body.name    || '').toString().trim();
    const company = (body.company || '').toString().trim();
    const email   = (body.email   || '').toString().trim();
    const message = (body.message || '').toString().trim();
    const budget  = (body.budget  || '').toString().trim();

    if (!name || !email || !message) {
      return json_({status:'error', msg:'必須項目が未入力です'});
    }

    // スパム制限（同一メール1分1回）
    const props = PropertiesService.getScriptProperties();
    const rateKey = RATE_KEY_PREFIX + email;
    const now = Date.now();
    const lastSent = parseInt(props.getProperty(rateKey) || '0');
    if (now - lastSent < 60000) {
      return json_({status:'ok'});  // 正常を装いスパマーに情報を与えない
    }
    props.setProperty(rateKey, String(now));

    const isDiagnosis = message.indexOf('【AI診断リード】') === 0;
    const source = isDiagnosis ? 'AI診断' : 'お問い合わせ';

    // ① 事業者へメール通知（最優先・確実）
    try { notifyOwner_(props, source, name, company, email, message, budget); }
    catch(err){ Logger.log('owner通知エラー: ' + err); }

    // ② リード台帳シートへ追記（durable）
    try { appendToSheet_(props, source, name, company, email, message, budget); }
    catch(err){ Logger.log('シート追記エラー: ' + err); }

    // ③ Lark通知（best-effort・設定時のみ）
    try { sendLarkNotification_(props, source, name, company, email, message, budget); }
    catch(err){ Logger.log('Lark通知エラー: ' + err); }

    // ④ 顧客へ自動返信メール
    try { sendAutoReply_(name, email); }
    catch(err){ Logger.log('自動返信エラー: ' + err); }

    return json_({status:'ok'});

  } catch(err) {
    Logger.log('doPost エラー: ' + err);
    return json_({status:'error', msg:'サーバーエラーが発生しました'});
  }
}

function doGet(e) {
  return json_({status:'ok', service:'AI Flow Architect Contact Form'});
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

// ─── ① 事業者へメール通知 ───────────────────────────────────────────────
function notifyOwner_(props, source, name, company, email, message, budget) {
  const to = props.getProperty('NOTIFY_EMAIL');
  if (!to) { Logger.log('NOTIFY_EMAIL未設定のため事業者通知スキップ'); return; }
  const budgetLabel = budgetLabel_(budget);
  const subject = '【新規リード / ' + source + '】' + name + ' 様' + (company ? '（' + company + '）' : '');
  const bodyText =
    '新しいリードが届きました（' + source + '）\n' +
    '──────────────────────\n' +
    'お名前  : ' + name + '\n' +
    '会社名  : ' + (company || '未記入') + '\n' +
    'メール  : ' + email + '\n' +
    '予算目安: ' + budgetLabel + '\n' +
    '日時    : ' + nowJst_() + '\n' +
    '──────────────────────\n' +
    '内容:\n' + message + '\n' +
    '──────────────────────\n' +
    '※ 返信は上記メールアドレス宛にどうぞ。';
  MailApp.sendEmail({ to: to, subject: subject, body: bodyText, name: 'AI Flow Architect リード通知', replyTo: email });
}

// ─── ② リード台帳シートへ追記 ───────────────────────────────────────────
function appendToSheet_(props, source, name, company, email, message, budget) {
  const sid = props.getProperty('LEADS_SHEET_ID');
  if (!sid) { return; }  // 未設定なら台帳スキップ
  const ss = SpreadsheetApp.openById(sid);
  let sh = ss.getSheetByName('leads');
  if (!sh) {
    sh = ss.insertSheet('leads');
    sh.appendRow(['日時', '種別', 'お名前', '会社名', 'メール', '予算', '内容']);
  }
  sh.appendRow([nowJst_(), source, name, company, email, budgetLabel_(budget), message]);
}

// ─── ③ Lark チャット通知（設定時のみ・best-effort） ─────────────────────
function sendLarkNotification_(props, source, name, company, email, message, budget) {
  const appId = props.getProperty('CLAUDE_LINK_APP_ID');
  const appSecret = props.getProperty('CLAUDE_LINK_APP_SECRET');
  if (!appId || !appSecret) { return; }  // 未設定ならスキップ
  const tokRes = UrlFetchApp.fetch(LARK_BASE_URL + '/auth/v3/tenant_access_token/internal', {
    method:'post', contentType:'application/json',
    payload: JSON.stringify({app_id:appId, app_secret:appSecret}), muteHttpExceptions:true
  });
  const token = JSON.parse(tokRes.getContentText()).tenant_access_token;
  if (!token) { Logger.log('Larkトークン取得失敗'); return; }

  const card = {
    config:{wide_screen_mode:true},
    header:{title:{tag:'plain_text', content:'🔔 新規リード（' + source + '）'}, template:'orange'},
    elements:[
      {tag:'div', text:{tag:'lark_md', content:
        '**👤 お名前**: ' + name + '\n**🏢 会社名**: ' + (company || '未記入') + '\n**📧 メール**: ' + email}},
      {tag:'hr'},
      {tag:'div', text:{tag:'lark_md', content:'**📝 内容**\n' + message}},
      {tag:'hr'},
      {tag:'div', text:{tag:'lark_md', content:'**💰 予算目安**: ' + budgetLabel_(budget)}},
      {tag:'note', elements:[{tag:'lark_md', content:'⏰ ' + nowJst_() + ' | メール通知＋台帳記録済み'}]}
    ]
  };
  UrlFetchApp.fetch(LARK_BASE_URL + '/im/v1/messages?receive_id_type=chat_id', {
    method:'post',
    headers:{'Authorization':'Bearer ' + token, 'Content-Type':'application/json'},
    payload: JSON.stringify({receive_id:NOTIFY_CHAT_ID, msg_type:'interactive', content:JSON.stringify(card)}),
    muteHttpExceptions:true
  });
}

// ─── ④ 顧客へ自動返信メール ─────────────────────────────────────────────
function sendAutoReply_(name, email) {
  const subject = 'AI Flow Architect: お問い合わせありがとうございます';
  const body =
    name + ' 様\n\n' +
    'お問い合わせありがとうございます。\n' +
    'AI Flow Architect(Aiフローアーキテクト)です。\n\n' +
    '内容を確認いたしました。通常12時間以内にご返信いたします。\n\n' +
    '急ぎの場合はXのDM（@Kosuke_free_）もご利用ください。\n\n' +
    '──────────────────────\n' +
    'AI Flow Architect\n' +
    'https://ai-flow-architect.github.io/\n' +
    'X: https://x.com/Kosuke_free_\n' +
    '──────────────────────\n\n' +
    '※ このメールは自動送信です。このメールへの返信は確認されません。';
  MailApp.sendEmail({ to: email, subject: subject, body: body, name: 'AI Flow Architect' });
}

// ─── ユーティリティ ─────────────────────────────────────────────────────
function budgetLabel_(budget) {
  return ({
    'lite':      '¥29,000〜¥39,000（Liteプラン想定）',
    'standard':  '¥40,000〜¥150,000（Standardプラン想定）',
    'full':      '¥150,000〜¥300,000（Full Package想定）',
    'undecided': '未定 / まず相談したい',
    '':          '未回答'
  })[budget] || budget;
}
function nowJst_() {
  return Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy-MM-dd HH:mm:ss');
}
