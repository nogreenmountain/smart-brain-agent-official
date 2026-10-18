const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const { once } = require('node:events');
process.env.CPA_MANAGEMENT_KEY = 'test-management-key';
process.env.CPA_TRUSTED_PROXY_IPS = '127.0.0.1';
const { parseUsage, createProxyServer, createResponseErrorObserver } = require('./proxy-server');
const gatewayHeaders = (headers = {}) => ({
  ...headers,
  'x-smartbrain-gateway-proxy': 'personal-api',
});

// Authentication regression coverage: the compatibility relay must validate
// the caller even when it has an internal upstream key for the local CPA.
test('rejects missing and invalid personal keys before forwarding through an internal upstream key', async t => {
  let calls = 0;
  const upstream = http.createServer((req, res) => {
    calls++;
    assert.equal(req.headers.authorization, 'Bearer internal-upstream-key');
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end('{"ok":true}');
  });
  upstream.listen(0, '127.0.0.1');
  await once(upstream, 'listening');
  t.after(() => { upstream.closeAllConnections(); upstream.close(); });

  const relay = createProxyServer({
    apiPort: upstream.address().port,
    upstreamKey: 'internal-upstream-key',
    authorizeKey: async key => key === 'valid-personal-key'
  });
  relay.listen(0, '127.0.0.1');
  await once(relay, 'listening');
  t.after(() => { relay.closeAllConnections(); relay.close(); });
  const base = `http://127.0.0.1:${relay.address().port}`;

  const missing = await fetch(`${base}/v1/models`, { headers: gatewayHeaders() });
  assert.equal(missing.status, 401);
  const invalid = await fetch(`${base}/v1/models`, { headers: gatewayHeaders({ authorization: 'Bearer old-public-key' }) });
  assert.equal(invalid.status, 401);
  assert.equal(calls, 0);

  const valid = await fetch(`${base}/v1/models`, { headers: gatewayHeaders({ authorization: 'Bearer valid-personal-key' }) });
  assert.equal(valid.status, 200);
  assert.deepEqual(await valid.json(), { ok: true });
  assert.equal(calls, 1);
});

test('parses non-streaming OpenAI usage', () => {
  const usage = parseUsage(Buffer.from(JSON.stringify({ usage: { input_tokens: 10, output_tokens: 5 } })), 'application/json');
  assert.deepEqual(usage, { input_tokens: 10, output_tokens: 5 });
});

test('parses final Responses SSE usage', () => {
  const sse = 'data: {"type":"response.output_text.delta","delta":"ok"}\n\n' +
    'data: {"type":"response.completed","response":{"usage":{"input_tokens":11,"output_tokens":7}}}\n\n' +
    'data: [DONE]\n';
  assert.deepEqual(parseUsage(Buffer.from(sse), 'text/event-stream'), { input_tokens: 11, output_tokens: 7 });
});

async function relayFixture(t, handler, options = {}) {
  const upstream = http.createServer(handler);
  upstream.listen(0, '127.0.0.1');
  await once(upstream, 'listening');
  t.after(() => { upstream.closeAllConnections(); upstream.close(); });

  const relay = createProxyServer({ apiPort: upstream.address().port, upstreamKey: 'test-key', authorizeKey: async () => true, ...options });
  relay.listen(0, '127.0.0.1');
  await once(relay, 'listening');
  t.after(() => { relay.closeAllConnections(); relay.close(); });
  return `http://127.0.0.1:${relay.address().port}`;
}

test('forwards v0 and v8 management requests with management credentials', async t => {
  const received = [];
  const base = await relayFixture(t, (req, res) => {
    received.push({
      path: req.url,
      authorization: req.headers.authorization,
      managementKey: req.headers['x-management-key']
    });
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end('{"ok":true}');
  });

  for (const route of ['/v0/management/config', '/v8/management/config?format=json']) {
    const response = await fetch(`${base}${route}`, {
      headers: { authorization: 'Bearer client-management-key', 'x-management-key': 'untrusted-key' }
    });
    assert.equal(response.status, 200, route);
    assert.deepEqual(await response.json(), { ok: true });
    assert.deepEqual(received.at(-1), {
      path: route,
      authorization: 'Bearer client-management-key',
      managementKey: 'test-management-key'
    });
  }

  const unsupported = await fetch(`${base}/v8/unrelated`);
  assert.equal(unsupported.status, 404);
  assert.equal(received.length, 2);
});

test('default relay exposes the first upstream 429 without retrying locally', async t => {
  let calls = 0;
  const base = await relayFixture(t, (req, res) => {
    calls++;
    if (calls === 1) {
      res.writeHead(429, { 'content-type': 'application/json', 'retry-after': '60' });
      res.end('{"error":{"message":"slow down"}}');
      return;
    }
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end('{"ok":true}');
  });

  const response = await fetch(`${base}/v1/responses`, { method: 'POST', headers: gatewayHeaders({ authorization: 'Bearer valid-personal-key' }), body: '{}' });
  assert.equal(response.status, 429);
  assert.equal(response.headers.get('retry-after'), '60');
  assert.equal(await response.text(), '{"error":{"message":"slow down"}}');
  assert.equal(calls, 1);
});

test('forwards all concurrent requests immediately without a local queue', async t => {
  let calls = 0;
  let allArrived;
  let release;
  const arrived = new Promise(resolve => { allArrived = resolve; });
  const gate = new Promise(resolve => { release = resolve; });
  const base = await relayFixture(t, async (req, res) => {
    calls++;
    if (calls === 8) allArrived();
    await gate;
    res.end('OK');
  });

  const pending = Array.from({ length: 8 }, () => fetch(`${base}/v1/responses`, { method: 'POST', headers: gatewayHeaders({ authorization: 'Bearer valid-personal-key' }), body: '{}' }));
  await Promise.race([
    arrived,
    new Promise((_, reject) => setTimeout(() => reject(new Error(`only ${calls} requests reached upstream`)), 500))
  ]);
  release();
  const responses = await Promise.all(pending);
  assert.equal(calls, 8);
  assert.deepEqual(await Promise.all(responses.map(response => response.text())), Array(8).fill('OK'));
});

test('preserves authorization, request body, route and SSE response', async t => {
  const received = [];
  const sse = 'data: {"type":"response.completed","response":{"usage":{"input_tokens":1,"output_tokens":1}}}\n\n';
  const base = await relayFixture(t, async (req, res) => {
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    received.push({ path: req.url, authorization: req.headers.authorization, body: Buffer.concat(chunks).toString() });
    res.writeHead(200, { 'content-type': 'text/event-stream' });
    res.end(sse);
  });
  const body = JSON.stringify({ model: 'gpt-5.6-sol', input: 'test', stream: true });
  const response = await fetch(`${base}/responses`, { method: 'POST', headers: gatewayHeaders({ authorization: 'Bearer valid-personal-key' }), body });
  assert.equal(await response.text(), sse);
  assert.deepEqual(received, [{ path: '/v1/responses', authorization: 'Bearer test-key', body }]);
});

test('client disconnect cancels the upstream request', async t => {
  let upstreamClosed;
  const closed = new Promise(resolve => { upstreamClosed = resolve; });
  const base = await relayFixture(t, (req, res) => {
    res.on('close', upstreamClosed);
    res.writeHead(200, { 'content-type': 'text/event-stream' });
    res.write('data: {"delta":"start"}\n\n');
  });
  const response = await fetch(`${base}/v1/responses`, { method: 'POST', headers: gatewayHeaders({ authorization: 'Bearer valid-personal-key' }), body: '{}' });
  await response.body.cancel();
  await Promise.race([
    closed,
    new Promise((_, reject) => setTimeout(() => reject(new Error('upstream was not cancelled')), 300))
  ]);
});

test('error observer ignores quoted capacity messages and recovers after oversized SSE frames', () => {
  const found = [];
  const observer = createResponseErrorObserver('text/event-stream', kind => found.push(kind));
  observer.write(Buffer.from('data: ' + JSON.stringify({ type: 'response.output_text.delta', delta: 'Selected model is at capacity' }) + '\n\n'));
  observer.write(Buffer.from('data: ' + 'x'.repeat(70000)));
  observer.write(Buffer.from('\n\n'));
  observer.write(Buffer.from('data: {"type":"error",\ndata: "error":{"type":"rate_limit_error","message":"slow down"}}\n\n'));
  observer.end();
  assert.deepEqual(found, ['rate_limit']);
});

test('error observer handles fragmented UTF-8 JSON errors and ordinary validation errors', () => {
  const found = [];
  const observer = createResponseErrorObserver('application/json', kind => found.push(kind));
  const body = Buffer.from(JSON.stringify({ error: { message: '服务器：Selected model is at capacity. Please try a different model.' } }));
  for (const byte of body) observer.write(Buffer.from([byte]));
  observer.end();
  const invalid = createResponseErrorObserver('application/json', kind => found.push(kind));
  invalid.write(Buffer.from('{"error":{"type":"invalid_request_error","message":"bad input"}}'));
  invalid.end();
  assert.deepEqual(found, ['capacity', 'upstream_error']);
});

test('diagnostics distinguish stream truncation, cancellation and timeout without retaining error text', () => {
  const found = [];
  for (const message of [
    'stream error: stream disconnected before completion: stream closed before response.completed',
    'context canceled',
    'context deadline exceeded',
  ]) {
    const observer = createResponseErrorObserver('application/json', (kind, details) => found.push({ kind, details }));
    observer.write(Buffer.from(JSON.stringify({ error: { code: 'server_error', type: 'api_error', message } })));
    observer.end();
  }
  assert.deepEqual(found, ['stream_incomplete', 'context_canceled', 'upstream_timeout'].map(reason => ({
    kind: 'upstream_error', details: { reason, code: 'server_error', type: 'api_error' }
  })));
});

test('bare service_unavailable_error is classified as capacity', () => {
  const found = [];
  const observer = createResponseErrorObserver('application/json', (kind, details) => found.push({ kind, details }));
  observer.write(Buffer.from(JSON.stringify({ error: {
    type: 'service_unavailable_error', message: 'Service unavailable'
  } })));
  observer.end();
  assert.deepEqual(found, [{
    kind: 'capacity',
    details: { reason: 'capacity', code: null, type: 'service_unavailable_error' }
  }]);
});



