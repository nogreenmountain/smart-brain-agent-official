const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const { once } = require('node:events');

process.env.CPA_MANAGEMENT_KEY = 'synthetic-management-only';
const { createProxyServer } = require('./proxy-server');

async function listen(server, host = '127.0.0.1') {
  server.listen(0, host);
  await once(server, 'listening');
  return `http://${host}:${server.address().port}`;
}

test('direct clients cannot use a personal key on the Windows relay', async t => {
  let authorizeCalls = 0;
  let upstreamCalls = 0;
  const upstream = http.createServer((_req, res) => {
    upstreamCalls += 1;
    res.end('{"object":"list","data":[]}');
  });
  await listen(upstream);
  t.after(() => { upstream.closeAllConnections(); upstream.close(); });

  const relay = createProxyServer({
    apiPort: upstream.address().port,
    upstreamKey: 'synthetic-loopback-only',
    trustedProxyIps: ['192.168.10.165'],
    authorizeKey: async () => { authorizeCalls += 1; return true; },
  });
  const base = await listen(relay);
  t.after(() => { relay.closeAllConnections(); relay.close(); });

  const response = await fetch(`${base}/v1/models`, {
    headers: {
      authorization: 'Bearer synthetic-personal-key',
      'x-smartbrain-gateway-proxy': 'personal-api',
    },
  });
  assert.equal(response.status, 403);
  assert.equal(authorizeCalls, 0);
  assert.equal(upstreamCalls, 0);
});

test('only the trusted production proxy hop can reach the model relay', async t => {
  let received;
  const upstream = http.createServer((req, res) => {
    received = {
      path: req.url,
      authorization: req.headers.authorization,
      gatewayMarker: req.headers['x-smartbrain-gateway-proxy'],
      managementKey: req.headers['x-management-key'],
    };
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end('{"object":"list","data":[{"id":"synthetic-model"}]}');
  });
  await listen(upstream);
  t.after(() => { upstream.closeAllConnections(); upstream.close(); });

  const relay = createProxyServer({
    apiPort: upstream.address().port,
    upstreamKey: 'synthetic-loopback-only',
    trustedProxyIps: ['127.0.0.1'],
    authorizeKey: async key => key === 'synthetic-personal-key',
  });
  const base = await listen(relay);
  t.after(() => { relay.closeAllConnections(); relay.close(); });

  const missingMarker = await fetch(`${base}/v1/models`, {
    headers: { authorization: 'Bearer synthetic-personal-key' },
  });
  assert.equal(missingMarker.status, 403);

  const accepted = await fetch(`${base}/v1/chat/completions?client=fixture%2Fpart&trace=a%2Eb`, {
    headers: {
      authorization: 'Bearer synthetic-personal-key',
      'x-smartbrain-gateway-proxy': 'personal-api',
      'x-management-key': 'client-supplied-management-key',
    },
  });
  assert.equal(accepted.status, 200);
  assert.deepEqual(received, {
    path: '/v1/chat/completions?client=fixture%2Fpart&trace=a%2Eb',
    authorization: 'Bearer synthetic-loopback-only',
    gatewayMarker: undefined,
    managementKey: undefined,
  });
});

test('trusted AI callers cannot tunnel non-canonical paths to management routes', async t => {
  let upstreamCalls = 0;
  const upstream = http.createServer((_req, res) => {
    upstreamCalls += 1;
    res.end('{"ok":true}');
  });
  await listen(upstream);
  t.after(() => { upstream.closeAllConnections(); upstream.close(); });

  const relay = createProxyServer({
    apiPort: upstream.address().port,
    upstreamKey: 'synthetic-loopback-only',
    trustedProxyIps: ['127.0.0.1'],
    authorizeKey: async () => true,
  });
  const port = await listen(relay).then(() => relay.address().port);
  t.after(() => { relay.closeAllConnections(); relay.close(); });

  const unsafePaths = [
    '/v1/../v8/management/config',
    '/v1/%2e%2e/v8/management/config',
    '/v1/%2E%2E/v8/management/config',
    '/v1/%252e%252e/v8/management/config',
    '/v1/%2f../v8/management/config',
    '/v1/%5c../v8/management/config',
    '/v1//chat/completions',
    '/v1/\\../v8/management/config',
  ];
  for (const path of unsafePaths) {
    const response = await new Promise((resolve, reject) => {
      const request = http.request({
        host: '127.0.0.1',
        port,
        path,
        headers: {
          authorization: 'Bearer synthetic-personal-key',
          'x-smartbrain-gateway-proxy': 'personal-api',
          'x-management-key': 'client-supplied-management-key',
        },
      }, resolve);
      request.on('error', reject);
      request.end();
    });
    response.resume();
    await once(response, 'end');
    assert.equal(response.statusCode, 400, path);
  }
  assert.equal(upstreamCalls, 0);
});

test('management routes and the injected panel are loopback-only', async t => {
  let upstreamCalls = 0;
  const upstream = http.createServer((_req, res) => {
    upstreamCalls += 1;
    res.end('{"ok":true}');
  });
  await listen(upstream);
  t.after(() => { upstream.closeAllConnections(); upstream.close(); });

  const relay = createProxyServer({
    apiPort: upstream.address().port,
    upstreamKey: 'synthetic-loopback-only',
    trustedProxyIps: ['127.0.0.1'],
    managementPeerIps: ['192.168.10.146'],
    authorizeKey: async () => true,
  });
  const base = await listen(relay);
  t.after(() => { relay.closeAllConnections(); relay.close(); });

  for (const path of ['/', '/management.html', '/panel', '/v0/management/config', '/v8/management/config']) {
    const response = await fetch(`${base}${path}`);
    assert.equal(response.status, 403, path);
  }
  assert.equal(upstreamCalls, 0);
});
