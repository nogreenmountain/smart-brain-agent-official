const http = require('http');
const net = require('net');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { StringDecoder } = require('string_decoder');

const API_PORT = Number(process.env.CPA_API_PORT || 3000);
const PROXY_PORT = Number(process.env.CPA_PROXY_PORT || 9000);
const SMARTBRAIN_URL = (process.env.SMARTBRAIN_GATEWAY_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const UPSTREAM_KEY = process.env.CPA_UPSTREAM_KEY || '';
const MANAGEMENT_KEY = process.env.CPA_MANAGEMENT_KEY || '';
const TRUSTED_PROXY_MARKER = 'personal-api';

function normalizePeerAddress(value) {
  const address = String(value || '').trim().toLowerCase();
  if (address === '::1') return '127.0.0.1';
  return address.startsWith('::ffff:') ? address.slice(7) : address;
}

function parseTrustedProxyIps(value) {
  const values = Array.isArray(value) ? value : String(value || '').split(',');
  const unique = new Set();
  for (const item of values) {
    const address = normalizePeerAddress(item);
    if (!address) continue;
    if (net.isIP(address) !== 4 || address === '0.0.0.0') {
      throw new Error('CPA_TRUSTED_PROXY_IPS must contain concrete IPv4 addresses');
    }
    unique.add(address);
  }
  return [...unique];
}

function parseSafeRequestTarget(value) {
  const target = String(value || '');
  if (!target.startsWith('/') || target.startsWith('//') || target.includes('#')) return null;
  const queryOffset = target.indexOf('?');
  const rawPath = queryOffset === -1 ? target : target.slice(0, queryOffset);
  if (rawPath.includes('\\') || rawPath.includes('//')) return null;
  if (/%(?:25|2e|2f|5c)/i.test(rawPath)) return null;
  let parsed;
  try { parsed = new URL(target, 'http://smartbrain-relay.invalid'); }
  catch (_) { return null; }
  if (parsed.origin !== 'http://smartbrain-relay.invalid' || parsed.pathname !== rawPath) return null;
  if (rawPath.split('/').some(segment => segment === '.' || segment === '..')) return null;
  return { path: rawPath, target };
}

const TRUSTED_PROXY_IPS = parseTrustedProxyIps(process.env.CPA_TRUSTED_PROXY_IPS || '');

async function readRequestBody(req, signal) {
  const chunks = [];
  for await (const chunk of req) {
    if (signal?.aborted) throw signal.reason;
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
}
const OUTBOX_FILE = process.env.CPA_GATEWAY_OUTBOX || path.join(__dirname, 'gateway-outbox.jsonl');
const panelPath = path.join(__dirname, 'static/management.html');
const panelHtml = fs.existsSync(panelPath) ? fs.readFileSync(panelPath, 'utf8') : '';
const injectedHtml = panelHtml.replace('</head>', `<script>window.CPA_MANAGEMENT_KEY=${JSON.stringify(MANAGEMENT_KEY)};</script></head>`);
const pending = [];
if (fs.existsSync(OUTBOX_FILE)) {
  try { for (const line of fs.readFileSync(OUTBOX_FILE, 'utf8').split(/\r?\n/)) { if (line.trim()) pending.push(JSON.parse(line)); } } catch (_) {}
}

function parseUsage(body, contentType) {
  if (!body) return null;
  if ((contentType || '').includes('text/event-stream')) {
    const lines = body.toString('utf8').split(/\r?\n/);
    for (let i = lines.length - 1; i >= 0; i--) {
      if (!lines[i].startsWith('data:')) continue;
      const raw = lines[i].slice(5).trim(); if (!raw || raw === '[DONE]') continue;
      try { const obj = JSON.parse(raw); if (obj.usage) return obj.usage; if (obj.response && obj.response.usage) return obj.response.usage; } catch (_) {}
    }
    return null;
  }
  try { const obj = JSON.parse(body.toString('utf8')); return obj.usage || (obj.response && obj.response.usage) || null; } catch (_) { return null; }
}

// Observe error envelopes only; assistant text is never classified as an error.
// Bound diagnostic parsing independently of the response passed to the client.
function createResponseErrorObserver(contentType, onError) {
  const limit = 64 * 1024;
  const decoder = new StringDecoder('utf8');
  const streaming = String(contentType || '').toLowerCase().includes('text/event-stream');
  let buffered = '', eventData = '', droppingLine = false, droppingEvent = false;
  const parse = value => {
    let payload;
    try { payload = JSON.parse(value); } catch (_) { return; }
    const error = payload?.error || payload?.response?.error || (payload?.type === 'error' ? payload : null);
    if (!error) return;
    const message = typeof error === 'string' ? error : `${error.code || ''} ${error.type || ''} ${error.message || ''}`;
    const kind = /selected model is at capacity|model_capacity|overloaded_error|server_is_overloaded|service_unavailable_error/i.test(message) ? 'capacity' :
      /rate_limit_exceeded|rate_limit_error|too many requests/i.test(message) ? 'rate_limit' : 'upstream_error';
    const reason = kind !== 'upstream_error' ? kind :
      /stream closed before response\.completed|stream disconnected before completion/i.test(message) ? 'stream_incomplete' :
      /context cancel(?:ed|led)|request cancel(?:ed|led)/i.test(message) ? 'context_canceled' :
      /deadline exceeded|timed out|timeout/i.test(message) ? 'upstream_timeout' :
      /connection reset|broken pipe|unexpected EOF|socket hang up/i.test(message) ? 'connection_interrupted' :
      /invalid_request_error|invalid_request/i.test(message) ? 'invalid_request' : 'unclassified';
    const safeCode = value => typeof value === 'string' && /^[a-zA-Z0-9_.-]{1,80}$/.test(value) ? value : null;
    onError(kind, { reason, code: safeCode(error.code), type: safeCode(error.type) });
  };
  const flushEvent = () => {
    if (!droppingEvent && eventData) parse(eventData);
    eventData = ''; droppingEvent = false;
  };
  const consume = value => {
    buffered += value;
    if (!streaming) {
      if (buffered.length > limit) { buffered = ''; droppingEvent = true; }
      return;
    }
    let newline;
    while ((newline = buffered.indexOf('\n')) !== -1) {
      const line = buffered.slice(0, newline).replace(/\r$/, '');
      buffered = buffered.slice(newline + 1);
      if (droppingLine || line.length > limit) { droppingLine = false; droppingEvent = true; continue; }
      if (!line) { flushEvent(); continue; }
      if (line.startsWith('data:') && !droppingEvent) {
        eventData += (eventData ? '\n' : '') + line.slice(5).replace(/^ /, '');
        if (eventData.length > limit) { eventData = ''; droppingEvent = true; }
      }
    }
    if (buffered.length > limit) { buffered = ''; droppingLine = true; droppingEvent = true; }
  };
  return {
    write(chunk) { consume(decoder.write(chunk)); },
    end() {
      consume(decoder.end());
      if (streaming) { consume('\n'); flushEvent(); }
      else if (!droppingEvent) parse(buffered);
    }
  };
}

async function authorize(key) {
  const response = await fetch(`${SMARTBRAIN_URL}/v4/ai-gateway/authorize`, { headers: { authorization: `Bearer ${key}` }, signal: AbortSignal.timeout(5000) });
  if (!response.ok) return false; const payload = await response.json(); return payload.authorized === true;
}
async function sendEvent(item) {
  const response = await fetch(`${SMARTBRAIN_URL}/v4/ai-gateway/events`, { method: 'POST', headers: { 'content-type': 'application/json', authorization: `Bearer ${item.key}` }, body: JSON.stringify({ events: [item.event] }), signal: AbortSignal.timeout(10000) });
  if (!response.ok) throw new Error(`usage ingest ${response.status}`);
}
function queueEvent(key, event) {
  const item = { key, event }; sendEvent(item).catch(() => { pending.push(item); try { fs.appendFileSync(OUTBOX_FILE, JSON.stringify(item) + '\n', { encoding: 'utf8', flag: 'a', mode: 0o600 }); fs.chmodSync(OUTBOX_FILE, 0o600); } catch (_) {} });
}
setInterval(async () => {
  while (pending.length) { try { await sendEvent(pending[0]); pending.shift(); } catch (_) { break; } }
  try { fs.writeFileSync(OUTBOX_FILE, pending.map(item => JSON.stringify(item)).join('\n') + (pending.length ? '\n' : ''), 'utf8'); } catch (_) {}
}, 5000).unref();

function createProxyServer({
  apiPort = API_PORT,
  upstreamKey = UPSTREAM_KEY,
  authorizeKey = authorize,
  trustedProxyIps = TRUSTED_PROXY_IPS,
  managementPeerIps = ['127.0.0.1'],
} = {}) {
const trustedPeers = new Set(parseTrustedProxyIps(trustedProxyIps));
const managementPeers = new Set(parseTrustedProxyIps(managementPeerIps));
return http.createServer(async (req, res) => {
  const peer = normalizePeerAddress(req.socket.remoteAddress);
  const requestTarget = parseSafeRequestTarget(req.url);
  if (!requestTarget) { res.writeHead(400); res.end('Bad request target'); return; }
  const requestPath = requestTarget.path;
  if (requestPath === '/' || requestPath === '/management.html' || requestPath === '/panel') {
    if (!managementPeers.has(peer)) { res.writeHead(403); res.end('Forbidden'); return; }
    res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' }); res.end(injectedHtml); return;
  }
  const isManagementRequest = requestPath.startsWith('/v0/') || requestPath.startsWith('/v8/management/');
  const isAiRequest = requestPath.startsWith('/v1/') || requestPath === '/responses';
  if (!(isManagementRequest || isAiRequest)) { res.writeHead(404); res.end('Not found'); return; }
  if (isManagementRequest) {
    if (!managementPeers.has(peer)) { res.writeHead(403); res.end('Forbidden'); return; }
  } else {
    const marker = String(req.headers['x-smartbrain-gateway-proxy'] || '').trim();
    if (!trustedPeers.has(peer) || marker !== TRUSTED_PROXY_MARKER) {
      res.writeHead(403, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ error: { code: 'direct_access_disabled', message: 'Use the SmartBrain personal API endpoint' } }));
      return;
    }
  }
  const incomingAuth = req.headers.authorization || ''; const employeeKey = incomingAuth.replace(/^Bearer\s+/i, '').trim();
  if (!isManagementRequest && (!employeeKey || !(await authorizeKey(employeeKey).catch(() => false)))) { res.writeHead(401, { 'content-type': 'application/json' }); res.end(JSON.stringify({ error: { message: 'Invalid or revoked Gateway API key' } })); return; }
  const targetPath = (req.url === '/responses' || req.url.startsWith('/responses?')) ? '/v1/responses' + (req.url.includes('?') ? req.url.slice(req.url.indexOf('?')) : '') : req.url;
  const forwardAuthorization = isManagementRequest ? incomingAuth : (upstreamKey ? `Bearer ${upstreamKey}` : incomingAuth);
  const options = { hostname: '127.0.0.1', port: apiPort, path: targetPath, method: req.method, headers: { ...req.headers, host: `127.0.0.1:${apiPort}` } };
  delete options.headers['x-smartbrain-gateway-proxy'];
  delete options.headers['x-management-key'];
  if (forwardAuthorization) options.headers.authorization = forwardAuthorization;
  else delete options.headers.authorization;
  if (isManagementRequest) options.headers['x-management-key'] = MANAGEMENT_KEY;
  const isApiRequest = req.method !== 'GET' && targetPath.startsWith('/v1/');
  const controller = new AbortController();
  req.once('aborted', () => controller.abort());
  req.once('error', () => controller.abort());
  res.once('close', () => { if (!res.writableFinished) controller.abort(); });
  if (req.aborted || res.destroyed) controller.abort();
  options.signal = controller.signal;
  let requestBody = Buffer.alloc(0);
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    try { requestBody = await readRequestBody(req, controller.signal); }
    catch (_) { return; }
  }
  const forward = () => new Promise(resolve => {
    if (controller.signal.aborted) { resolve(); return; }
    const started = Date.now(); const requestId = req.headers['x-request-id'] || crypto.randomUUID(); const proxyReq = http.request(options, proxyRes => {
      const observedErrors = new Set();
      const observer = createResponseErrorObserver(proxyRes.headers['content-type'], (kind, details) => {
        if (!isApiRequest || observedErrors.has(kind)) return;
        observedErrors.add(kind);
        console.warn(JSON.stringify({ event: 'upstream_response_error', time: new Date().toISOString(),
          status: proxyRes.statusCode, kind, ...details, elapsed_ms: Date.now() - started,
          endpoint: ['/v1/responses', '/v1/messages', '/v1/chat/completions'].includes(targetPath.split('?')[0]) ? targetPath.split('?')[0] : 'other' }));
      });
      const chunks = [];
      res.writeHead(proxyRes.statusCode, proxyRes.headers);
      proxyRes.on('data', c => { chunks.push(c); observer.write(c); });
      proxyRes.pipe(res);
      proxyRes.on('end', () => {
        observer.end();
        if (!res.writableEnded) res.end();
        const usage = parseUsage(Buffer.concat(chunks), proxyRes.headers['content-type']); if (usage && !upstreamKey) queueEvent(employeeKey, { event_id: `${requestId}:${proxyRes.statusCode}`, request_id: requestId, model: req.headers['x-model'] || '', request_model: req.headers['x-request-model'] || '', app_type: 'codex', status_code: proxyRes.statusCode || 500, usage, latency_ms: Date.now() - started, started_at: new Date(started).toISOString(), completed_at: new Date().toISOString() }); resolve();
      });
      proxyRes.on('error', () => { res.destroy(); resolve(); });
    });
    proxyReq.on('error', e => {
      if (!res.destroyed) {
        if (!res.headersSent) { res.writeHead(502); res.end(`Proxy error: ${e.message}`); }
        else res.destroy();
      }
      resolve();
    });
    proxyReq.end(requestBody);
  });
  await forward();
});
}
const server = createProxyServer();
if (require.main === module) {
  if (!TRUSTED_PROXY_IPS.length) throw new Error('CPA_TRUSTED_PROXY_IPS is required');
  server.listen(PROXY_PORT, '0.0.0.0', () => console.log(`SmartBrain Gateway :${PROXY_PORT} -> CLIProxy :${API_PORT}; personal-key-auth=true`));
}
module.exports = {
  parseUsage,
  createProxyServer,
  createResponseErrorObserver,
  normalizePeerAddress,
  parseSafeRequestTarget,
  parseTrustedProxyIps,
  server,
};

