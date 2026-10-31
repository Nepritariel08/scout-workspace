'use strict';
// Real HTTP requests against the isolated release, never against Odoo or providers.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const mongoose = require('mongoose');
const { createModels, runAsSystem } = require('@librechat/data-schemas');
const fixtures = JSON.parse(fs.readFileSync('/app/data/qualification-fixtures.json', 'utf8'));
const base = 'http://127.0.0.1:3080';
const results = [];
const sessions = new Map();
const record = (name, status) => results.push({ name, status });
async function call(path, { token, tenantId, method = 'GET', body } = {}) {
  // The upstream file routes require a browser User-Agent; a bare Node fetch
  // receives an SSE error envelope with HTTP 200, which must never count as a pass.
  const headers = { 'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/142.0.0.0 Safari/537.36' };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (tenantId) headers['X-Tenant-Id'] = tenantId;
  const response = await fetch(base + path, { method, headers,
    body: body === undefined ? undefined : JSON.stringify(body), redirect: 'manual' });
  return { status: response.status, type: response.headers.get('content-type'), text: await response.text() };
}
function positive(name, response, marker) {
  assert.equal(response.status, 200, `${name}: HTTP ${response.status}`);
  if (marker) assert.ok(response.text.includes(marker), `${name}: own marker absent; type=${response.type}; prefix=${response.text.slice(0, 100)}`);
  record(name, response.status);
}
function denied(name, response, codes = [401, 403, 404]) {
  assert.ok(codes.includes(response.status), `${name}: unexpected HTTP ${response.status}; type=${response.type}; prefix=${response.text.slice(0, 100)}`);
  assert.ok(!fixtures.some((f) => response.text.includes(f.marker)), `${name}: private marker exposed`);
  record(name, response.status);
}
(async () => {
  if (!['mongodb://mongo:27017/ScoutQualification',
    'mongodb://mongo-restore:27017/ScoutQualification'].includes(process.env.MONGO_URI)) {
    throw new Error('Refusing unexpected database');
  }
  let ready = false;
  for (let attempt = 0; attempt < 40; attempt++) {
    try {
      const response = await fetch(base + '/api/convos', { signal: AbortSignal.timeout(1500) });
      if (response.status === 401) { ready = true; break; }
    } catch { /* Startup is checked separately from the security assertions. */ }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  assert.ok(ready, 'Disposable server did not become ready');
  denied('strict-login-no-tenant', await call('/api/auth/login', { method: 'POST',
    body: { email: fixtures[0].email, password: process.env.QA_USER_PASSWORD } }), [403]);
  for (const tenantId of ['__SYSTEM__', 'not a tenant']) {
    denied('strict-login-invalid-tenant', await call('/api/auth/login', { method: 'POST',
      tenantId, body: { email: fixtures[0].email, password: process.env.QA_USER_PASSWORD } }), [400, 403]);
  }
  denied('registration-disabled', await call('/api/auth/register', { method: 'POST',
    tenantId: 'staff', body: {} }), [403, 404]);
  denied('anonymous-conversations', await call('/api/convos'));
  for (const f of fixtures) {
    const login = await call('/api/auth/login', { method: 'POST', tenantId: f.tenantId,
      body: { email: f.email, password: process.env.QA_USER_PASSWORD } });
    assert.equal(login.status, 200, `${f.name}: login HTTP ${login.status}`);
    const body = JSON.parse(login.text);
    assert.equal(body.user.id, f.userId, `${f.name}: wrong account`);
    assert.equal(typeof body.token, 'string', `${f.name}: missing bearer`);
    assert.equal(body.user.role, 'USER', `${f.name}: unexpected privilege`);
    sessions.set(f.name, body.token);
    record(`${f.name}-login`, login.status);
  }
  for (const f of fixtures) {
    const token = sessions.get(f.name);
    positive(`${f.name}-own-conversation`, await call(`/api/convos/${f.conversationId}`, { token }), f.marker);
    positive(`${f.name}-own-messages`, await call(`/api/messages/${f.conversationId}`, { token }), f.marker);
    positive(`${f.name}-own-file`, await call(`/api/files/download/${f.userId}/${f.fileId}`, { token }), f.marker);
    const list = await call('/api/convos', { token });
    positive(`${f.name}-own-list`, list, f.marker);
    assert.ok(!fixtures.some((other) => other !== f && list.text.includes(other.marker)), 'List isolation failed');
    positive(`${f.name}-header-cannot-change-identity`, await call(`/api/convos/${f.conversationId}`,
      { token, tenantId: '__SYSTEM__' }), f.marker);
    denied(`${f.name}-mcp-use-disabled`, await call('/api/mcp/servers', { token }), [403]);
    denied(`${f.name}-mcp-tools-disabled`, await call('/api/mcp/tools', { token }), [403]);
    denied(`${f.name}-mcp-create-disabled`, await call('/api/mcp/servers',
      { token, method: 'POST', body: {} }), [403]);
    for (const other of fixtures.filter((other) => other !== f)) {
      const scope = `${f.name}-to-${other.name}`;
      denied(`${scope}-conversation`, await call(`/api/convos/${other.conversationId}`,
        { token, tenantId: other.tenantId }));
      denied(`${scope}-messages`, await call(`/api/messages/${other.conversationId}`,
        { token, tenantId: other.tenantId }));
      denied(`${scope}-file`, await call(`/api/files/download/${other.userId}/${other.fileId}`,
        { token, tenantId: other.tenantId }));
    }
    denied(`${f.name}-bad-signature`, await call('/api/convos', { token: token + 'tampered' }));
  }
  const target = fixtures[0];
  const models = createModels(mongoose);
  await mongoose.connect(process.env.MONGO_URI);
  await Promise.all(Object.values(models).filter((model) => typeof model.init === 'function').map((model) => model.init()));
  try {
    await runAsSystem(async () => {
      await models.User.updateOne({ _id: target.userId }, { $set: { credentialsChangedAt: new Date(Date.now() + 1000) } });
    });
    denied('retired-bearer-after-credential-change', await call('/api/convos',
      { token: sessions.get(target.name) }), [401]);
  } finally {
    await runAsSystem(async () => {
      await models.User.updateOne({ _id: target.userId }, { $unset: { credentialsChangedAt: '' } });
    });
    await mongoose.disconnect();
  }
  const report = { source: 'v0.8.9-rc1', at: new Date().toISOString(),
    checks: results.length, passed: results.length, providerCalls: 0, results };
  fs.writeFileSync('/app/data/http-qualification.json', JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
})().catch(async (error) => {
  console.error(JSON.stringify({ failed: true, name: error.name, message: error.message,
    passedBeforeFailure: results.length, results }));
  await mongoose.disconnect(); process.exitCode = 1;
});
