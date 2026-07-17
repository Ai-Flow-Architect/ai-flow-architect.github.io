// gas_contact_form.gs の修正（sheetOk戻り値判定 + trim）を GAS 環境スタブで検証する。
// 狙いは「不合格side」の実行証明＝プロパティ未設定で sheet:false になること。
const fs = require('fs');
const path = require('path');

// 第2引数で変異体を渡せる（ミューテーションテスト用）。既定は同ディレクトリの本体。
const TARGET = process.argv[2] || path.join(__dirname, 'gas_contact_form.gs');
const SRC = fs.readFileSync(TARGET, 'utf8');

function build(props, opts) {
  opts = opts || {};
  const calls = { openByIdArg: null, appended: null, mails: 0 };

  const PropertiesService = {
    getScriptProperties: () => ({
      getProperty: (k) => (k in props ? props[k] : null),
      setProperty: () => {},
    }),
  };
  const SpreadsheetApp = {
    openById: (id) => {
      calls.openByIdArg = id;
      if (opts.openByIdThrows) { throw new Error('Unexpected error while getting the method or property openById'); }
      return {
        getName: () => 'AI Flow Architect リード台帳',
        getSheetByName: () => ({ appendRow: (row) => { calls.appended = row; } }),
        insertSheet: () => ({ appendRow: () => {} }),
      };
    },
  };
  const Logger = { log: () => {} };
  const Utilities = { formatDate: () => '2026-07-17 00:00:00' };
  const MailApp = { sendEmail: () => { if (opts.mailThrows) { throw new Error('mail dead'); } calls.mails++; } };
  const ContentService = {
    MimeType: { JSON: 'json' },
    createTextOutput: (t) => ({ setMimeType: () => ({ _text: t }) }),
  };
  const UrlFetchApp = { fetch: () => ({ getContentText: () => '{}' }) };

  const factory = new Function(
    'PropertiesService', 'SpreadsheetApp', 'Logger', 'Utilities', 'MailApp', 'ContentService', 'UrlFetchApp',
    SRC + '\nreturn { doPost, appendToSheet_ };'
  );
  const api = factory(PropertiesService, SpreadsheetApp, Logger, Utilities, MailApp, ContentService, UrlFetchApp);
  return { api, calls, PropertiesService };
}

function post(env, email) {
  const e = { postData: { contents: JSON.stringify({
    name: '検証', company: '', email: email, message: 'テスト', budget: 'full' }) } };
  return JSON.parse(env.api.doPost(e)._text);
}

const results = [];
function check(label, actual, expected) {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  results.push((ok ? 'PASS' : 'FAIL') + ' | ' + label + ' | 実際=' + JSON.stringify(actual));
}

// 1. 不合格side: LEADS_SHEET_ID 未設定 → sheet:false（修正前はここが true になっていた）
let env = build({ NOTIFY_EMAIL: 'a@b.com' });
check('未設定なら sheet:false', post(env, 'x1@example.com').via.sheet, false);

// 2. 合格side: 設定あり → sheet:true かつ1行書かれる
env = build({ NOTIFY_EMAIL: 'a@b.com', LEADS_SHEET_ID: 'SHEET_ID_44' });
check('設定ありなら sheet:true', post(env, 'x2@example.com').via.sheet, true);
check('実際に appendRow される', env.calls.appended !== null, true);

// 3. trim: 前後の空白・改行を落として openById へ渡す
env = build({ NOTIFY_EMAIL: 'a@b.com', LEADS_SHEET_ID: '  SHEET_ID_44\n' });
post(env, 'x3@example.com');
check('trimしてopenByIdへ渡す', env.calls.openByIdArg, 'SHEET_ID_44');

// 4. 例外時: openById が投げたら sheet:false（握り潰して true にしない）
env = build({ NOTIFY_EMAIL: 'a@b.com', LEADS_SHEET_ID: 'BAD' }, { openByIdThrows: true });
check('openById例外なら sheet:false', post(env, 'x4@example.com').via.sheet, false);

// 5. 全滅時: メール死亡 × シート未設定 → status:'error'（この安全装置が偽trueで死んでいた）
env = build({ NOTIFY_EMAIL: 'a@b.com' }, { mailThrows: true });
const r5 = post(env, 'x5@example.com');
check('owner死亡×sheet未設定なら status:error', r5.status, 'error');
check('その時 delivered:false', r5.delivered, false);

// 6. 非退行: メール死亡でもシートが生きていれば ok（リードは残っている）
env = build({ NOTIFY_EMAIL: 'a@b.com', LEADS_SHEET_ID: 'SHEET_ID_44' }, { mailThrows: true });
check('owner死亡でもsheet生存なら ok', post(env, 'x6@example.com').status, 'ok');

results.forEach((r) => console.log(r));
const failed = results.filter((r) => r.startsWith('FAIL')).length;
console.log('\n' + (results.length - failed) + '/' + results.length + ' PASS');
process.exit(failed ? 1 : 0);
