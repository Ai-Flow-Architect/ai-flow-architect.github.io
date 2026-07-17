/**
 * LPチャット用 OpenAI プロキシ（Cloudflare Worker）
 *
 * 【このWorkerが存在する理由】
 *   公開LPからOpenAIを呼ぶには鍵が要るが、ブラウザに鍵を置けば view-source で盗まれる。
 *   そこで鍵はWorker Secretに置き、ブラウザはこのWorkerを叩く。
 *
 * 【2026-07-17 の再実装で塞いだ穴】
 *   旧実装は「鍵を隠す」ことだけを達成し、「鍵の使用を制限する」を全くしていなかった。
 *   実測: Origin: https://evil.example.com から model:"gpt-4o" を投げて HTTP 200 で実応答。
 *   Origin なしの素のcurlでも 200。＝当方のOpenAI課金で誰でもLLMを回せる状態だった。
 *   真因は「CORSを認可だと誤解した」こと。旧実装は ACAO ヘッダを静的に付けるだけで、
 *   サーバー側で1件も弾いていない。CORSは"他人のブラウザ"しか止めない（curlには無力）。
 *
 * 【前提: 完全な認証は不可能】
 *   匿名の公開ページからの呼び出しは、原理的に「本物の訪問者」を証明できない。
 *   Origin も Referer も curl で偽装できる（＝リファラ制限をLPで却下したのと同じ理由）。
 *   よって設計は「侵入を防ぐ」ではなく【1回を安くする × 量を絞る】の多層防御に倒す。
 *     ① Origin 検証   … 雑な悪用を止める（偽装は可能＝これ単体を防御と呼ばない）
 *     ② モデル固定     … 旧実装は client 指定の model を素通しし gpt-4o が通った。単価を固定する
 *     ③ 上限クランプ   … max_tokens / 本文長 / messages 数＝1リクエストの最大コストを決める
 *     ④ レート制限     … IP単位。量を絞る＝被害額の主たる決定要因
 *   最後の砦は OpenAI 側の Usage limit（このWorkerでは担保できない・別途設定すること）。
 */

const ALLOWED_ORIGINS = new Set([
  'https://ai-flow-architect.github.io',
]);

// ② モデルは固定。client の model は読まない（旧実装はここが素通しで gpt-4o を許していた）。
const PINNED_MODEL = 'gpt-4o-mini';

// ③ 1リクエストのコスト上限。LPチャットの実需要（callLLM の maxTokens は既定500・最大でも数百）
//    に対し十分な余裕を持たせつつ、青天井にしない。
const MAX_TOKENS_CAP = 800;
const MAX_MESSAGES = 24;        // 会話履歴の上限（LPは短いやり取り）
const MAX_CHARS_TOTAL = 24000;  // messages 全体の文字数上限
const MAX_BODY_BYTES = 64 * 1024;

const OPENAI_URL = 'https://api.openai.com/v1/chat/completions';

/** ① Origin 検証。偽装可能だが、雑な悪用と他サイトからの埋め込みは止まる。 */
export function isAllowedOrigin(origin) {
  return typeof origin === 'string' && ALLOWED_ORIGINS.has(origin);
}

/**
 * ③ 受信ボディを検証し、OpenAIへ送る安全なペイロードだけを組み立てて返す。
 * client の指定をそのまま信じない（model は無視・max_tokens はクランプ）。
 * @returns {{ok: true, payload: object} | {ok: false, status: number, msg: string}}
 */
export function buildSafePayload(raw) {
  if (!raw || typeof raw !== 'object') {
    return { ok: false, status: 400, msg: 'invalid body' };
  }
  const messages = raw.messages;
  if (!Array.isArray(messages) || messages.length === 0) {
    return { ok: false, status: 400, msg: 'messages required' };
  }
  if (messages.length > MAX_MESSAGES) {
    return { ok: false, status: 413, msg: 'too many messages' };
  }

  let total = 0;
  const safeMessages = [];
  for (const m of messages) {
    if (!m || typeof m !== 'object') {
      return { ok: false, status: 400, msg: 'invalid message' };
    }
    // role は許可値のみ。任意文字列を通すとOpenAI側で予期しない解釈をされうる。
    if (!['system', 'user', 'assistant'].includes(m.role)) {
      return { ok: false, status: 400, msg: 'invalid role' };
    }
    if (typeof m.content !== 'string') {
      return { ok: false, status: 400, msg: 'invalid content' };
    }
    total += m.content.length;
    if (total > MAX_CHARS_TOTAL) {
      return { ok: false, status: 413, msg: 'payload too large' };
    }
    safeMessages.push({ role: m.role, content: m.content });
  }

  // max_tokens: 数値でなければ既定、範囲外はクランプ（client の言い値を信じない）
  const wanted = Number(raw.max_tokens);
  const maxTokens = Number.isFinite(wanted)
    ? Math.min(Math.max(Math.trunc(wanted), 1), MAX_TOKENS_CAP)
    : 500;

  const wantedTemp = Number(raw.temperature);
  const temperature = Number.isFinite(wantedTemp)
    ? Math.min(Math.max(wantedTemp, 0), 2)
    : 0.7;

  return {
    ok: true,
    payload: {
      model: PINNED_MODEL,   // ← client 指定は意図的に捨てる
      messages: safeMessages,
      max_tokens: maxTokens,
      temperature,
    },
  };
}

function corsHeaders(origin) {
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Max-Age': '86400',
    Vary: 'Origin',
  };
}

function json(body, status, origin) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...corsHeaders(origin || 'null') },
  });
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin');

    // ① 許可Originでなければ、preflight含め一切処理しない（＝OpenAIを呼ばない＝課金しない）。
    //    旧実装はここで弾かず、ACAOヘッダを付けるだけで本体は実行していた。
    if (!isAllowedOrigin(origin)) {
      return new Response('forbidden', { status: 403 });
    }

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }
    if (request.method !== 'POST') {
      return json({ error: 'method not allowed' }, 405, origin);
    }
    if (new URL(request.url).pathname !== '/chat') {
      return json({ error: 'not found' }, 404, origin);
    }

    const len = Number(request.headers.get('Content-Length') || 0);
    if (len > MAX_BODY_BYTES) {
      return json({ error: 'payload too large' }, 413, origin);
    }

    // ④ レート制限（IP単位）。被害額を決めるのは単価ではなく量なので、ここが主防御。
    //    バインディング未設定でも動作は継続する（＝制限なしで無言に緩む）。
    //    それを隠さないよう、未設定はログに出す。deploy時に必ず設定すること。
    if (env.RATE_LIMITER) {
      const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
      const { success } = await env.RATE_LIMITER.limit({ key: ip });
      if (!success) {
        return json(
          { error: 'rate limited', msg: 'アクセスが集中しています。少し時間をおいてお試しください。' },
          429,
          origin,
        );
      }
    } else {
      console.warn('RATE_LIMITER binding が無い＝レート制限なしで動作中');
    }

    let raw;
    try {
      raw = await request.json();
    } catch {
      return json({ error: 'invalid json' }, 400, origin);
    }

    const built = buildSafePayload(raw);
    if (!built.ok) {
      return json({ error: built.msg }, built.status, origin);
    }

    if (!env.OPENAI_API_KEY) {
      // 鍵が無い＝設定事故。成功を装わず落とす（LP側は staticFAQ へ落ちる）。
      console.error('OPENAI_API_KEY secret が未設定');
      return json({ error: 'upstream not configured' }, 500, origin);
    }

    let upstream;
    try {
      upstream = await fetch(OPENAI_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${env.OPENAI_API_KEY}`,
        },
        body: JSON.stringify(built.payload),
        signal: AbortSignal.timeout(20000),
      });
    } catch (e) {
      console.error('OpenAI upstream error:', e && e.message);
      return json({ error: 'upstream error' }, 502, origin);
    }

    // 応答はそのまま返す（LP側は d.choices[0].message.content を読む＝契約を変えない）。
    const text = await upstream.text();
    return new Response(text, {
      status: upstream.status,
      headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) },
    });
  },
};
