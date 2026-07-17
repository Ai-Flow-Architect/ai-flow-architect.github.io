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
 *    CUSTOMER_BOT_APP_ID / CUSTOMER_BOT_APP_SECRET … Lark通知の送信ボット（推奨・Acquisitionチャットに参加済）
 *    CLAUDE_LINK_APP_ID / CLAUDE_LINK_APP_SECRET … 旧・フォールバック用（任意・Acquisition未参加のため単独では届かない）
 * 3. 「デプロイ」→「デプロイを管理」→ 既存ウェブアプリを「新バージョン」で更新
 *    （URLは変わらない＝index.html側の GAS_ENDPOINT はそのままでOK）
 */

// ─── 設定 ────────────────────────────────────────────────────────────────
const LARK_BASE_URL  = 'https://open.larksuite.com/open-apis';
const NOTIFY_CHAT_ID = 'oc_e372e12e2be03722a470241bb36af4f2';  // Lark通知先=Acquisition（集客）チャット（2026-07-16変更）
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

    // 🔴 durable経路の成否を集約する（2026-07-17）。
    //    旧実装は全経路を握り潰して常に status:'ok' を返していたため、事業者メールとシートが
    //    両方死んでもフォームは成功画面を出し、リードは誰にも届かず消えた（3月〜7月の実障害と同一構造）。
    //    「記録が1つも残らなかった」時だけは必ず error を返し、送信者に別導線を案内する。
    var ownerOk = false, sheetOk = false;

    // ① 事業者へメール通知（最優先・確実）
    try { notifyOwner_(props, source, name, company, email, message, budget); ownerOk = true; }
    catch(err){ Logger.log('owner通知エラー: ' + err); }

    // ② リード台帳シートへ追記（durable）
    try { appendToSheet_(props, source, name, company, email, message, budget); sheetOk = true; }
    catch(err){ Logger.log('シート追記エラー: ' + err); }

    // ③ Lark通知（best-effort・設定時のみ）※失敗してもリードは①②に残るので status に影響させない
    try { sendLarkNotification_(props, source, name, company, email, message, budget); }
    catch(err){ Logger.log('Lark通知エラー: ' + err); }

    // ④ 顧客へ自動返信メール ※同上（届かなくてもリード自体は失われない）
    try { sendAutoReply_(name, email); }
    catch(err){ Logger.log('自動返信エラー: ' + err); }

    if (!ownerOk && !sheetOk) {
      // ここに来た＝問い合わせが1バイトも残っていない。成功を装ってはいけない。
      Logger.log('🔴 durable経路が全滅: owner/sheet 双方失敗 → error を返す');
      return json_({status:'error', delivered:false,
                    msg:'送信に失敗しました。お手数ですが公式LINEまたはメールでご連絡ください。'});
    }
    return json_({status:'ok', delivered:true, via:{owner:ownerOk, sheet:sheetOk}});

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
  // 送信ボット: Acquisition(集客)チャットに居る CUSTOMER_BOT を優先。
  // 未設定時のみ従来の CLAUDE_LINK にフォールバック（ただし CLAUDE_LINK は
  // Acquisitionチャット未参加のため、その場合 NOTIFY_CHAT_ID も要確認）。
  const appId = props.getProperty('CUSTOMER_BOT_APP_ID') || props.getProperty('CLAUDE_LINK_APP_ID');
  const appSecret = props.getProperty('CUSTOMER_BOT_APP_SECRET') || props.getProperty('CLAUDE_LINK_APP_SECRET');
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
// 🔴 踏み台化ガード（2026-07-17）:
//   このWebアプリは未認証で誰でも叩ける。旧実装は宛先(email)を検証せず自動返信を送っていたため、
//   「攻撃者が指定した宛先」へ当方のGmailから送れる状態だった（スパム踏み台）。さらに
//   MailApp の日次クォータ(無料100通)を焼かれると、① 事業者通知メールまで巻き添えで止まり
//   実リードが届かなくなる＝リード喪失に直結する。
//   対策: ①宛先の形式検証 ②自動返信の1日総量上限（超過しても①②のリード記録は継続）。
const AUTOREPLY_DAILY_CAP = 30;          // 自動返信の1日上限（実需要は数通/日）
const AUTOREPLY_COUNT_KEY = 'autoreply_count_';

function isValidEmail_(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) && email.length <= 254;
}

function sendAutoReply_(name, email) {
  if (!isValidEmail_(email)) {
    Logger.log('自動返信スキップ: 宛先の形式が不正');
    return;
  }
  // 1日総量ガード（メール単位のレート制限だけでは宛先を変えられると素通りする）
  const props = PropertiesService.getScriptProperties();
  const dayKey = AUTOREPLY_COUNT_KEY +
        Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyyMMdd');
  const sentToday = parseInt(props.getProperty(dayKey) || '0');
  if (sentToday >= AUTOREPLY_DAILY_CAP) {
    // ここで止めても事業者通知①とシート②は既に完了しているためリードは失われない
    Logger.log('🔴 自動返信の1日上限に到達（' + sentToday + '通）→ 送信停止。悪用の可能性を確認すること');
    return;
  }
  props.setProperty(dayKey, String(sentToday + 1));

  // 宛名は外部入力。改行を潰し長さを切る（本文へ任意テキストを流し込ませない）
  const safeName = String(name).replace(/[\r\n]+/g, ' ').slice(0, 40);
  const subject = 'AI Flow Architect: お問い合わせありがとうございます';
  const body =
    safeName + ' 様\n\n' +
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
