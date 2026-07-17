/**
 * openai-proxy の防御テスト（node --test・依存なし）。
 *
 * 方針: 「緑が緑であることを証明する」＝2026-07-17に実測した"本物の攻撃"をそのまま
 * テストケースにする。旧実装で 200 が返った入力が、新実装で確実に弾かれることを固定する。
 * 実測ログ:
 *   - Origin: https://evil.example.com + model:"gpt-4o" → HTTP 200 / gpt-4o-2024-08-06 が応答
 *   - Origin ヘッダ無し(素のcurl)               → HTTP 200
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';

import worker, { isAllowedOrigin, buildSafePayload } from '../src/index.js';

const LP = 'https://ai-flow-architect.github.io';

/** OpenAIを実際には叩かないための env。fetch は差し替える。 */
function envWith(overrides = {}) {
  return { OPENAI_API_KEY: 'sk-test-not-real', ...overrides };
}

function req(body, { origin = LP, method = 'POST', path = '/chat' } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (origin !== null) headers.Origin = origin;
  return new Request(`https://proxy.example.workers.dev${path}`, {
    method,
    headers,
    body: method === 'POST' ? JSON.stringify(body) : undefined,
  });
}

const okBody = { model: 'gpt-4o-mini', messages: [{ role: 'user', content: 'hi' }], max_tokens: 50 };

// ── ① Origin 検証（旧実装の実測穴） ─────────────────────────────
test('evil origin は 403（旧実装は 200 で実応答を返していた）', async () => {
  const res = await worker.fetch(req(okBody, { origin: 'https://evil.example.com' }), envWith());
  assert.equal(res.status, 403);
});

test('Origin ヘッダ無しの素のcurlは 403（旧実装は 200）', async () => {
  const res = await worker.fetch(req(okBody, { origin: null }), envWith());
  assert.equal(res.status, 403);
});

test('弾く時は OpenAI を一度も呼ばない（＝課金しない）', async () => {
  let called = 0;
  const orig = globalThis.fetch;
  globalThis.fetch = async () => { called++; return new Response('{}'); };
  try {
    await worker.fetch(req(okBody, { origin: 'https://evil.example.com' }), envWith());
    await worker.fetch(req(okBody, { origin: null }), envWith());
  } finally {
    globalThis.fetch = orig;
  }
  assert.equal(called, 0, '拒否したのに upstream を呼んでいる＝課金が発生する');
});

test('LPのOriginは通り、CORSヘッダが返る', async () => {
  const orig = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({ choices: [{ message: { content: 'ok' } }] }), {
    status: 200, headers: { 'Content-Type': 'application/json' },
  });
  try {
    const res = await worker.fetch(req(okBody), envWith());
    assert.equal(res.status, 200);
    assert.equal(res.headers.get('Access-Control-Allow-Origin'), LP);
    const j = await res.json();
    assert.equal(j.choices[0].message.content, 'ok', 'LP側の契約(choices[0].message.content)が壊れている');
  } finally {
    globalThis.fetch = orig;
  }
});

test('isAllowedOrigin: 部分一致で通さない（サブドメイン/前方一致の偽装）', () => {
  assert.equal(isAllowedOrigin(LP), true);
  assert.equal(isAllowedOrigin('https://ai-flow-architect.github.io.evil.com'), false);
  assert.equal(isAllowedOrigin('https://evil.ai-flow-architect.github.io'), false);
  assert.equal(isAllowedOrigin('http://ai-flow-architect.github.io'), false, 'httpは別オリジン');
  assert.equal(isAllowedOrigin(null), false);
  assert.equal(isAllowedOrigin(undefined), false);
});

// ── ② モデル固定（旧実装は client 指定を素通しし gpt-4o が通った） ──
test('client が gpt-4o を指定しても gpt-4o-mini に固定される', () => {
  const r = buildSafePayload({ model: 'gpt-4o', messages: [{ role: 'user', content: 'x' }] });
  assert.equal(r.ok, true);
  assert.equal(r.payload.model, 'gpt-4o-mini');
});

test('高額モデルを指定しても素通りしない（o1/gpt-4-turbo 等）', () => {
  for (const m of ['o1', 'o1-preview', 'gpt-4-turbo', 'gpt-4o-2024-08-06']) {
    const r = buildSafePayload({ model: m, messages: [{ role: 'user', content: 'x' }] });
    assert.equal(r.payload.model, 'gpt-4o-mini', `${m} が素通りした`);
  }
});

test('実際に upstream へ送られる model も固定されている（組み立てだけでなく送信内容）', async () => {
  let sent = null;
  const orig = globalThis.fetch;
  globalThis.fetch = async (_url, opts) => {
    sent = JSON.parse(opts.body);
    return new Response('{}', { status: 200 });
  };
  try {
    await worker.fetch(req({ model: 'gpt-4o', messages: [{ role: 'user', content: 'x' }], max_tokens: 99999 }), envWith());
  } finally {
    globalThis.fetch = orig;
  }
  assert.equal(sent.model, 'gpt-4o-mini');
  assert.equal(sent.max_tokens, 800, 'max_tokens がクランプされていない');
});

// ── ③ 上限クランプ ────────────────────────────────────────
test('max_tokens は上限へクランプされる', () => {
  assert.equal(buildSafePayload({ messages: [{ role: 'user', content: 'x' }], max_tokens: 100000 }).payload.max_tokens, 800);
  assert.equal(buildSafePayload({ messages: [{ role: 'user', content: 'x' }], max_tokens: -5 }).payload.max_tokens, 1);
  assert.equal(buildSafePayload({ messages: [{ role: 'user', content: 'x' }], max_tokens: 'abc' }).payload.max_tokens, 500);
  assert.equal(buildSafePayload({ messages: [{ role: 'user', content: 'x' }], max_tokens: 200 }).payload.max_tokens, 200);
});

test('巨大な本文は 413（1リクエストのコストを青天井にしない）', () => {
  const big = { messages: [{ role: 'user', content: 'あ'.repeat(30000) }] };
  const r = buildSafePayload(big);
  assert.equal(r.ok, false);
  assert.equal(r.status, 413);
});

test('messages が多すぎると 413', () => {
  const many = { messages: Array.from({ length: 50 }, () => ({ role: 'user', content: 'x' })) };
  assert.equal(buildSafePayload(many).status, 413);
});

test('不正な role / content は弾く', () => {
  assert.equal(buildSafePayload({ messages: [{ role: 'root', content: 'x' }] }).ok, false);
  assert.equal(buildSafePayload({ messages: [{ role: 'user', content: 123 }] }).ok, false);
  assert.equal(buildSafePayload({ messages: [] }).ok, false);
  assert.equal(buildSafePayload(null).ok, false);
});

// ── ④ レート制限 ─────────────────────────────────────────
test('レート制限に掛かると 429 で、OpenAI を呼ばない', async () => {
  let called = 0;
  const orig = globalThis.fetch;
  globalThis.fetch = async () => { called++; return new Response('{}'); };
  try {
    const env = envWith({ RATE_LIMITER: { limit: async () => ({ success: false }) } });
    const res = await worker.fetch(req(okBody), env);
    assert.equal(res.status, 429);
  } finally {
    globalThis.fetch = orig;
  }
  assert.equal(called, 0, 'レート制限したのに upstream を呼んでいる＝課金が発生する');
});

test('レート制限は IP (CF-Connecting-IP) をキーにする', async () => {
  let key = null;
  const orig = globalThis.fetch;
  globalThis.fetch = async () => new Response('{}', { status: 200 });
  try {
    const env = envWith({ RATE_LIMITER: { limit: async (a) => { key = a.key; return { success: true }; } } });
    const r = new Request('https://p.workers.dev/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Origin: LP, 'CF-Connecting-IP': '203.0.113.9' },
      body: JSON.stringify(okBody),
    });
    await worker.fetch(r, env);
  } finally {
    globalThis.fetch = orig;
  }
  assert.equal(key, '203.0.113.9');
});

// ── 設定事故 ────────────────────────────────────────────
test('OPENAI_API_KEY 未設定なら成功を装わず 500', async () => {
  const res = await worker.fetch(req(okBody), { OPENAI_API_KEY: undefined });
  assert.equal(res.status, 500);
});

test('/chat 以外のパスは 404', async () => {
  const res = await worker.fetch(req(okBody, { path: '/admin' }), envWith());
  assert.equal(res.status, 404);
});
