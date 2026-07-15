/* =====================================================
   AI Flow Architect — 業務自動化 見極め診断エンジン
   -----------------------------------------------------
   ブラウザ(<script src>)とNode(require)の両対応(UMD風)。
   純粋関数: 回答オブジェクト -> 診断結果。副作用なし=単体テスト可能。
   Day2骨格: 診断ロジック + 提案文テンプレ（連絡先取得/通知はDay3）
===================================================== */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.DiagnoseEngine = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  /* ---- 設問定義（UIとロジックの単一の正） ---- */
  var QUESTIONS = [
    {
      id: 'industry', type: 'single', required: true,
      title: 'あなたの業種に最も近いものは？',
      help: '業種に合わせた自動化事例をご提案します',
      options: [
        { v: 'shigyo', label: '士業・管理部門（経理／総務／人事）' },
        { v: 'ec', label: 'EC・小売・卸' },
        { v: 'realestate', label: '不動産' },
        { v: 'medical', label: '医療・介護・福祉' },
        { v: 'maker', label: '製造・建設' },
        { v: 'itweb', label: 'IT・Web・広告' },
        { v: 'service', label: '飲食・サービス・教育' },
        { v: 'other', label: 'その他' }
      ]
    },
    {
      id: 'hours', type: 'single', required: true,
      title: '毎月、繰り返しの手作業にどれくらい時間を使っていますか？',
      help: '社内全体のおおよその合計でOKです',
      options: [
        { v: 'lt10', label: '月10時間くらいまで', score: 10, mid: 6 },
        { v: '10_30', label: '月10〜30時間', score: 26, mid: 20 },
        { v: '30_60', label: '月30〜60時間', score: 45, mid: 45 },
        { v: 'gt60', label: '月60時間以上', score: 60, mid: 85 }
      ]
    },
    {
      id: 'areas', type: 'multi', required: true,
      title: '特に負担が大きい作業はどれですか？（複数選択可）',
      help: '自動化と相性の良い領域ほど効果が出ます',
      options: [
        { v: 'entry', label: 'データ入力・転記', affinity: 1.0 },
        { v: 'invoice', label: '帳票・請求書・見積書の作成', affinity: 1.0 },
        { v: 'mail', label: 'メール・問い合わせ対応', affinity: 0.8 },
        { v: 'research', label: '情報収集・リサーチ・スクレイピング', affinity: 0.9 },
        { v: 'schedule', label: '予約・日程・シフト調整', affinity: 0.8 },
        { v: 'report', label: 'レポート・集計・分析', affinity: 0.9 },
        { v: 'sns', label: 'SNS投稿・コンテンツ更新', affinity: 0.7 }
      ]
    },
    {
      id: 'repetition', type: 'single', required: true,
      title: 'その作業は、毎回ほぼ同じ手順で進みますか？',
      help: '手順が決まっているほど自動化しやすくなります',
      options: [
        { v: 'same', label: 'ほぼ毎回同じ手順', score: 25 },
        { v: 'half', label: '半分くらいは決まっている', score: 12 },
        { v: 'vary', label: '毎回かなり違う', score: 3 }
      ]
    },
    {
      id: 'tools', type: 'single', required: true,
      title: '今、その作業は主に何で行っていますか？',
      help: '現状のツールから最適な連携方法を判断します',
      options: [
        { v: 'excel', label: 'Excel・Googleスプレッドシート中心', score: 10 },
        { v: 'saas', label: 'kintone・Notion等のSaaS', score: 8 },
        { v: 'core', label: '基幹システム・専用ソフトがある', score: 6 },
        { v: 'paper', label: 'ほぼ紙・手作業', score: 7 }
      ]
    },
    {
      id: 'people', type: 'single', required: true,
      title: 'その作業に関わっている人数は？',
      help: 'ROI（投資対効果）の試算に使います',
      options: [
        { v: 'p1', label: '1人', score: 3, people: 1 },
        { v: 'p2_5', label: '2〜5人', score: 8, people: 3 },
        { v: 'p6', label: '6人以上', score: 14, people: 8 }
      ]
    },
    {
      id: 'itlevel', type: 'single', required: true,
      title: '社内のIT習熟度はどのくらいですか？',
      help: '納品後の運用しやすさを設計に反映します',
      options: [
        { v: 'high', label: '詳しい人がいる', score: 3 },
        { v: 'mid', label: '平均的（普通に使える）', score: 2 },
        { v: 'low', label: 'あまり得意でない', score: 1 }
      ]
    },
    {
      id: 'budget', type: 'single', required: true,
      title: '初期費用の予算感は？',
      help: '無理のないプランをご提案します（見積もりは無料です）',
      options: [
        { v: 'b_lt3', label: '〜3万円ではじめたい' },
        { v: 'b_3_15', label: '3〜15万円' },
        { v: 'b_gt15', label: '15万円以上でしっかり' },
        { v: 'b_unknown', label: 'まだ分からない' }
      ]
    }
  ];

  var INDUSTRY_EXAMPLE = {
    shigyo: '請求書発行・経費データの転記・給与計算の前処理',
    ec: '受注データの取り込み・在庫更新・出荷通知メール',
    realestate: '物件情報の収集・反響メール対応・帳票作成',
    medical: '予約管理・記録の転記・レセプト周辺の集計',
    maker: '見積書作成・在庫/発注表の更新・日報集計',
    itweb: 'レポート集計・スクレイピング・SNS運用の自動化',
    service: '予約・シフト調整・問い合わせ一次対応',
    other: '定型の入力作業・帳票作成・情報収集'
  };

  var AREA_LABEL = {};
  QUESTIONS[2].options.forEach(function (o) { AREA_LABEL[o.v] = o.label; });
  var INDUSTRY_LABEL = {};
  QUESTIONS[0].options.forEach(function (o) { INDUSTRY_LABEL[o.v] = o.label; });

  function opt(qid, v) {
    var q = QUESTIONS.filter(function (x) { return x.id === qid; })[0];
    if (!q) return null;
    return q.options.filter(function (o) { return o.v === v; })[0] || null;
  }

  /* ---- 円フォーマット ---- */
  function yen(n) {
    return '¥' + Math.round(n).toLocaleString('ja-JP');
  }

  /* ---- スコアリング（0〜100に正規化） ---- */
  function score(ans) {
    var s = 0;
    var oHours = opt('hours', ans.hours); if (oHours) s += oHours.score;
    var oRep = opt('repetition', ans.repetition); if (oRep) s += oRep.score;
    var oTools = opt('tools', ans.tools); if (oTools) s += oTools.score;
    var oPeople = opt('people', ans.people); if (oPeople) s += oPeople.score;
    var oIt = opt('itlevel', ans.itlevel); if (oIt) s += oIt.score;
    // 領域: 親和性合計 × 4（上限16）
    var areas = ans.areas || [];
    var aff = 0;
    areas.forEach(function (v) { var o = opt('areas', v); if (o) aff += o.affinity; });
    s += Math.min(16, aff * 4);
    // 最大理論値 ≒ 60+25+10+14+3+16 = 128 → 100正規化
    var norm = Math.round((s / 128) * 100);
    return Math.max(0, Math.min(100, norm));
  }

  /* ---- レベル判定 ---- */
  function levelOf(sc, ans) {
    var oRep = opt('repetition', ans.repetition);
    // 実現性ゲート: 毎回違う作業はROIが出にくい → 上限を1段下げる
    var repVary = oRep && oRep.v === 'vary';
    var lv;
    if (sc >= 66) lv = 3;
    else if (sc >= 36) lv = 2;
    else lv = 1;
    if (repVary && lv > 1) lv -= 1;
    return lv;
  }

  var LEVEL_META = {
    1: {
      key: 'lite', tag: 'スモールスタート型',
      plan: 'Lite', planRange: '¥29,000〜¥39,000',
      headline: 'まず1つ、確実に効く作業から自動化するのが最適です',
      color: '#4a8ff7'
    },
    2: {
      key: 'standard', tag: '本格自動化型',
      plan: 'Standard', planRange: '¥40,000〜¥150,000',
      headline: '複数ステップをまとめて自動化すると、投資回収が早く見込めます',
      color: '#f07840'
    },
    3: {
      key: 'full', tag: '全社最適化型',
      plan: 'Full Package', planRange: '¥150,000〜¥300,000',
      headline: '複数の作業を横断して仕組み化すると、削減インパクトが大きくなります',
      color: '#3dd68c'
    }
  };

  /* ---- ROI試算 ---- */
  function roi(ans) {
    var oHours = opt('hours', ans.hours);
    var oPeople = opt('people', ans.people);
    var mid = oHours ? oHours.mid : 20;      // 月間手作業時間（推定中央値）
    var rate = 2000;                          // 平均時給（既存ROI試算機と同値）
    var reduction = 0.9;                      // 削減率（既存ROI試算機の既定値）
    var monthlySaving = mid * rate * reduction;
    var annualSaving = monthlySaving * 12;
    return {
      monthlyHours: mid,
      hourlyRate: rate,
      reductionRate: reduction,
      monthlySaving: monthlySaving,
      annualSaving: annualSaving,
      monthlySavingText: yen(monthlySaving),
      annualSavingText: yen(annualSaving)
    };
  }

  /* ---- パーソナライズ提案文（レベル別テンプレ） ---- */
  function proposalText(ans, sc, lv, r) {
    var meta = LEVEL_META[lv];
    var indLabel = INDUSTRY_LABEL[ans.industry] || 'お客様';
    var example = INDUSTRY_EXAMPLE[ans.industry] || '定型作業';
    var areas = (ans.areas || []).map(function (v) { return AREA_LABEL[v]; }).filter(Boolean);
    var areaText = areas.length ? areas.slice(0, 3).join('・') : 'ご負担の大きい作業';

    var lines = [];
    lines.push('【' + indLabel + '／' + meta.tag + '】');
    lines.push('');
    lines.push('■ 特に効果が見込める作業');
    lines.push('　' + areaText + '（貴社の業種では ' + example + ' なども好相性です）。');
    lines.push('');
    lines.push('■ 想定される削減効果（概算）');
    lines.push('　月あたり約 ' + r.monthlySavingText + ' ／ 年間で約 ' + r.annualSavingText + ' の人件費削減が目安です。');
    lines.push('　※月' + r.monthlyHours + '時間・時給' + yen(r.hourlyRate) + '・削減率' + Math.round(r.reductionRate * 100) + '%で試算。実数値は無料相談で精査します。');
    lines.push('');
    lines.push('■ おすすめプラン');
    lines.push('　' + meta.plan + '（' + meta.planRange + '・税込・1回限り）');

    if (lv === 1) {
      lines.push('　まず1つの作業で「効く」体験をしていただき、手応えを見てから広げるのが安心です。');
    } else if (lv === 2) {
      lines.push('　AI連携・複数ステップをまとめて構築でき、最もROIが高いプランです。');
    } else {
      lines.push('　複数の作業を横断して仕組み化し、全社的な削減インパクトを狙えます。');
    }

    var oRep = opt('repetition', ans.repetition);
    if (oRep && oRep.v === 'vary') {
      lines.push('');
      lines.push('※「毎回手順が違う」作業は、まず一部の定型部分から切り出すのが効果的です。この見極めも無料相談でご一緒します。');
    }
    return lines.join('\n');
  }

  /* ---- 診断メイン（純粋関数） ---- */
  function diagnose(ans) {
    var sc = score(ans);
    var lv = levelOf(sc, ans);
    var r = roi(ans);
    var meta = LEVEL_META[lv];
    return {
      score: sc,
      level: lv,
      levelTag: meta.tag,
      recommendedPlan: meta.plan,
      planRange: meta.planRange,
      color: meta.color,
      roi: r,
      proposal: proposalText(ans, sc, lv, r)
    };
  }

  /* ---- 未回答チェック ---- */
  function firstUnanswered(ans) {
    for (var i = 0; i < QUESTIONS.length; i++) {
      var q = QUESTIONS[i];
      if (!q.required) continue;
      var a = ans[q.id];
      if (q.type === 'multi') { if (!a || !a.length) return q.id; }
      else { if (a === undefined || a === null || a === '') return q.id; }
    }
    return null;
  }

  return {
    QUESTIONS: QUESTIONS,
    diagnose: diagnose,
    score: score,
    levelOf: levelOf,
    roi: roi,
    proposalText: proposalText,
    firstUnanswered: firstUnanswered,
    LEVEL_META: LEVEL_META
  };
});
