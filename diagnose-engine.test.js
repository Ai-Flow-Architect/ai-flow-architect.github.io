/* diagnose-engine の単体テスト（node実行・依存なし） */
var E = require('./diagnose-engine.js');
var pass = 0, fail = 0;
function ok(cond, msg){ if(cond){pass++;} else {fail++; console.log('  ❌ FAIL:', msg);} }
function eq(a,b,msg){ ok(a===b, msg + '  (期待' + b + ' / 実際' + a + ')'); }

console.log('=== diagnose-engine 単体テスト ===');

// 1) 設問数=8・required揃い
eq(E.QUESTIONS.length, 8, '設問数=8');
ok(E.QUESTIONS.every(function(q){return q.id && q.type && q.title;}), '全設問にid/type/title');

// 2) 高ポテンシャル → Lv3・Full
var high = { industry:'ec', hours:'gt60', areas:['entry','invoice','research'],
  repetition:'same', tools:'excel', people:'p6', itlevel:'high', budget:'b_gt15' };
var rh = E.diagnose(high);
ok(rh.score >= 66, '高負荷ケース score>=66 (実' + rh.score + ')');
eq(rh.level, 3, '高負荷ケース Lv3');
eq(rh.recommendedPlan, 'Full Package', '高負荷 → Full Package');
ok(rh.roi.annualSaving > 0, '高負荷 年間削減>0');

// 3) 低負荷 → Lv1・Lite
var low = { industry:'other', hours:'lt10', areas:['mail'],
  repetition:'half', tools:'core', people:'p1', itlevel:'low', budget:'b_lt3' };
var rl = E.diagnose(low);
ok(rl.score < 36, '低負荷 score<36 (実' + rl.score + ')');
eq(rl.level, 1, '低負荷 Lv1');
eq(rl.recommendedPlan, 'Lite', '低負荷 → Lite');

// 4) 実現性ゲート: 毎回違う(vary) はレベルを1段下げる
var varyHi = { industry:'itweb', hours:'gt60', areas:['entry','invoice'],
  repetition:'vary', tools:'excel', people:'p6', itlevel:'high', budget:'b_gt15' };
var rv = E.diagnose(varyHi);
var sameHi = Object.assign({}, varyHi, {repetition:'same'});
var rs = E.diagnose(sameHi);
ok(rv.level < rs.level || rv.level === 1, 'vary はレベルが下がる (vary=' + rv.level + ' / same=' + rs.level + ')');
ok(rv.proposal.indexOf('毎回手順が違う') > -1, 'vary は提案文に注記が入る');

// 5) 中位 → Lv2・Standard
var mid = { industry:'shigyo', hours:'10_30', areas:['invoice','report'],
  repetition:'same', tools:'excel', people:'p2_5', itlevel:'mid', budget:'b_3_15' };
var rm = E.diagnose(mid);
eq(rm.level, 2, '中位 Lv2');
eq(rm.recommendedPlan, 'Standard', '中位 → Standard');

// 6) 提案文にパーソナライズ要素（業種・領域・金額）が入る
ok(rm.proposal.indexOf('士業') > -1, '提案文に業種ラベル');
ok(rm.proposal.indexOf('請求書') > -1 || rm.proposal.indexOf('帳票') > -1, '提案文に選択領域');
ok(rm.proposal.indexOf('¥') > -1, '提案文に金額');

// 7) スコアは常に0..100
[high,low,varyHi,mid].forEach(function(a,i){
  var s = E.score(a);
  ok(s>=0 && s<=100, 'score範囲0..100 ケース'+i+' (実'+s+')');
});

// 8) firstUnanswered: 未回答検出
var partial = { industry:'ec', hours:'gt60' };
ok(E.firstUnanswered(partial) === 'areas', '未回答をareasで検出');
ok(E.firstUnanswered(high) === null, '全回答済みはnull');

// 9) ROI試算の妥当性（月85h・時給2000・削減90% → 年約183.6万）
var expectedAnnual = 85 * 2000 * 0.9 * 12;
eq(rh.roi.annualSaving, expectedAnnual, '高負荷ROI年間削減=' + expectedAnnual);

console.log('---');
console.log('PASS ' + pass + ' / FAIL ' + fail);
if(fail>0){ process.exit(1); }
console.log('全テスト成功 ✅');
