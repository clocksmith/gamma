import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';
import {
  auditSessionLog, createAppSurface, createMcpHandler, DEFAULT_LIMITS, refusePath,
} from '../../qualification/workflow-generalization/three-arm/app-surface.mjs';

const SERVER = fileURLToPath(new URL('../../qualification/workflow-generalization/three-arm/app-surface.mjs', import.meta.url));

test('paths stay inside API v3 of the one instance', () => {
  for (const ok of ['/api/v3/work_packages/5', '/api/v3/projects/stage2-qual-proj/work_packages?pageSize=5',
    '/api/v3/work_packages?filters=[{"parent":{"operator":"=","values":["5"]}}]']) assert.equal(refusePath(ok), null, ok);
  for (const bad of ['http://example.com/api/v3/x', '//example.com/api/v3/x', '/api/v3/../../admin', '/api/v3/%2e%2e/admin',
    '/api/v3/a%2Fb', '/api/v3/..%5cadmin', '/api/v2/x', '/login', '/api/v3/x#frag', '/api/v3/x\\..\\y', '/api/v3/@example.com',
    '/api/v3/./x', '/api/v3/x\n/y', '', null, 5, '/api/v3/' + 'a'.repeat(600)]) assert.notEqual(refusePath(bad), null, String(bad));
});

function recorder() {
  const calls = [];
  const log = [];
  const request = async (account, method, path, body) => {
    calls.push({ account, method, path, body });
    return { status: method === 'POST' ? 201 : 200, body: { id: calls.length } };
  };
  return { calls, log, request };
}

test('discovery forwards allowed calls and logs refused ones without sending them', async () => {
  const { calls, log, request } = recorder();
  const surface = createAppSurface({ mode: 'discovery', request, log: e => log.push(e) });
  assert.deepEqual(Object.keys(surface.tools), ['app_request']);
  const ok = await surface.tools.app_request({ as: 'author', method: 'POST', path: '/api/v3/projects/p/work_packages', body: { subject: 's' } });
  assert.equal(ok.status, 201);
  for (const bad of [
    { as: 'admin', method: 'GET', path: '/api/v3/users' },
    { as: 'author', method: 'PUT', path: '/api/v3/users' },
    { as: 'author', method: 'GET', path: 'http://example.com/api/v3/x' },
    { as: 'author', method: 'GET', path: '/api/v3/../admin' },
    { as: 'author', method: 'POST', path: '/api/v3/work_packages', body: 'text' },
    { as: 'author', method: 'GET', path: '/api/v3/x', body: {} },
    undefined,
  ]) assert.equal((await surface.tools.app_request(bad)).ok, false);
  assert.equal(calls.length, 1);
  assert.equal(log.length, 8);
  assert.equal(log.filter(e => e.refused).length, 7);
  assert.deepEqual(surface.counts(), { requests: 1, reads: 0, recordsCreated: 1, refused: 7 });
});

test('discovery stops at its record and request limits', async () => {
  const { calls, request } = recorder();
  const limits = { ...DEFAULT_LIMITS, discovery: { requests: 4, recordsCreated: 2 } };
  const surface = createAppSurface({ mode: 'discovery', request, limits });
  const create = () => surface.tools.app_request({ as: 'author', method: 'POST', path: '/api/v3/work_packages', body: {} });
  assert.equal((await create()).ok, true);
  assert.equal((await create()).ok, true);
  assert.match((await create()).refused, /record limit of 2/);
  const read = () => surface.tools.app_request({ as: 'approver', method: 'GET', path: '/api/v3/work_packages/1' });
  assert.equal((await read()).ok, true);
  assert.equal((await read()).ok, true);
  assert.match((await read()).refused, /request limit of 4/);
  assert.equal(calls.length, 4);
});

test('decision mode can only read, only as the approver, only a few times', async () => {
  const { calls, request } = recorder();
  const surface = createAppSurface({ mode: 'decision', request, limits: { ...DEFAULT_LIMITS, decision: { reads: 2 } } });
  assert.deepEqual(Object.keys(surface.tools), ['app_get']);
  await surface.tools.app_get({ path: '/api/v3/work_packages/1' });
  await surface.tools.app_get({ path: '/api/v3/work_packages/2', as: 'author', method: 'PATCH', body: { x: 1 } });
  assert.match((await surface.tools.app_get({ path: '/api/v3/work_packages/3' })).refused, /read limit of 2/);
  assert.deepEqual(calls.map(c => [c.account, c.method, c.body]), [['approver', 'GET', undefined], ['approver', 'GET', undefined]]);
});

test('a long response is cut, not passed whole', async () => {
  const surface = createAppSurface({ mode: 'decision', limits: { ...DEFAULT_LIMITS, responseChars: 50 },
    request: async () => ({ status: 200, body: { text: 'x'.repeat(500) } }) });
  const result = await surface.tools.app_get({ path: '/api/v3/work_packages/1' });
  assert.equal(result.truncated, true);
  assert.equal(result.bodyText.length, 50);
  assert.equal(result.body, undefined);
});

test('the MCP handler lists only the mode\'s tool and refuses any other', async () => {
  const out = [];
  const surface = createAppSurface({ mode: 'decision', request: async () => ({ status: 200, body: {} }) });
  const handle = createMcpHandler(surface, m => out.push(m));
  await handle({ jsonrpc: '2.0', id: 1, method: 'initialize', params: { protocolVersion: '2025-06-18' } });
  await handle({ jsonrpc: '2.0', method: 'notifications/initialized' });
  await handle({ jsonrpc: '2.0', id: 2, method: 'tools/list' });
  await handle({ jsonrpc: '2.0', id: 3, method: 'tools/call', params: { name: 'app_request', arguments: { as: 'author', method: 'DELETE', path: '/api/v3/work_packages/1' } } });
  await handle({ jsonrpc: '2.0', id: 4, method: 'resources/list' });
  assert.equal(out.length, 4);
  assert.equal(out[0].result.protocolVersion, '2025-06-18');
  assert.deepEqual(out[1].result.tools.map(t => t.name), ['app_get']);
  assert.equal(out[2].result.isError, true);
  assert.match(out[2].result.content[0].text, /no such tool/);
  assert.equal(out[3].error.code, -32601);
});

test('the server process reaches only its instance, with the right account, and logs every call', async () => {
  const seen = [];
  const http = createServer((req, res) => {
    seen.push({ method: req.method, url: req.url, auth: Buffer.from(req.headers.authorization.split(' ')[1], 'base64').toString() });
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ id: 9 }));
  });
  await new Promise(done => http.listen(0, '127.0.0.1', done));
  const dir = mkdtempSync(join(tmpdir(), 'arm-surface-'));
  const stateFile = join(dir, 'state.json');
  const logFile = join(dir, 'surface.jsonl');
  writeFileSync(stateFile, JSON.stringify({ new: { url: `http://127.0.0.1:${http.address().port}`, seed: { authorToken: 'A', approverToken: 'B' } } }));
  const child = spawn(process.execPath, [SERVER], { stdio: ['pipe', 'pipe', 'inherit'],
    env: { ...process.env, GAMMATRON_ARM_SURFACE: JSON.stringify({ mode: 'discovery', arm: 'test-arm', stateFile, logFile }) } });
  const replies = [];
  let buffer = '';
  child.stdout.on('data', chunk => {
    buffer += chunk;
    for (let i; (i = buffer.indexOf('\n')) !== -1; buffer = buffer.slice(i + 1)) replies.push(JSON.parse(buffer.slice(0, i)));
  });
  const send = m => child.stdin.write(JSON.stringify(m) + '\n');
  const call = (id, args) => send({ jsonrpc: '2.0', id, method: 'tools/call', params: { name: 'app_request', arguments: args } });
  try {
    send({ jsonrpc: '2.0', id: 1, method: 'initialize', params: { protocolVersion: '2024-11-05' } });
    call(2, { as: 'approver', method: 'GET', path: '/api/v3/work_packages/7' });
    call(3, { as: 'author', method: 'GET', path: 'http://example.com/api/v3/x' });
    call(4, { as: 'author', method: 'GET', path: '/api/v3/../../etc/passwd' });
    call(5, { as: 'author', method: 'POST', path: '/api/v3/work_packages', body: { subject: 's' } });
    for (let waited = 0; replies.length < 5 && waited < 5000; waited += 20) await new Promise(r => setTimeout(r, 20));
    assert.equal(replies.length, 5);
    assert.equal(replies[2].result.isError, true);
    assert.equal(replies[3].result.isError, true);
    assert.deepEqual(seen, [
      { method: 'GET', url: '/api/v3/work_packages/7', auth: 'apikey:B' },
      { method: 'POST', url: '/api/v3/work_packages', auth: 'apikey:A' },
    ]);
    const log = readFileSync(logFile, 'utf8').trim().split('\n').map(l => JSON.parse(l));
    assert.equal(log.length, 4);
    assert.equal(log.filter(e => e.refused).length, 2);
    assert.ok(log.every(e => e.arm === 'test-arm'));
    assert.ok(!readFileSync(logFile, 'utf8').includes('apikey'));
  } finally {
    child.kill();
    http.close();
    rmSync(dir, { recursive: true, force: true });
  }
});

test('the session audit flags tools off the list and file tools aimed outside the working directory', () => {
  const use = (name, input) => JSON.stringify({ type: 'assistant', message: { content: [{ type: 'text', text: 'ok' }, { type: 'tool_use', name, input }] } });
  const options = { allowedTools: ['Read', 'Write', 'Edit', 'Glob', 'Grep', 'mcp__app__app_request'], workDir: '/tmp/arm-a' };
  const clean = auditSessionLog([
    use('Write', { file_path: '/tmp/arm-a/guard.mjs', content: 'x' }),
    use('Read', { file_path: 'guard.mjs' }),
    use('Grep', { pattern: 'x', path: '/tmp/arm-a' }),
    use('mcp__app__app_request', { as: 'author', method: 'GET', path: '/api/v3/x' }),
    JSON.stringify({ type: 'user', message: { content: [{ type: 'tool_result', content: 'fine' }] } }),
    'not json',
  ], options);
  assert.deepEqual(clean.outOfSurface, []);
  assert.equal(clean.toolCalls, 4);
  assert.equal(clean.byTool.Read, 1);
  const dirty = auditSessionLog([
    use('Bash', { command: 'cat ~/secrets' }),
    use('Read', { file_path: '/tmp/arm-a/../arm-b/guard.mjs' }),
    use('Read', { file_path: '/tmp/arm-a-other/x' }),
    use('Glob', { pattern: '*', path: '/' }),
    use('WebFetch', { url: 'https://example.com' }),
    use('mcp__bus__bus_send', { to: 'x' }),
  ], options);
  assert.deepEqual(dirty.outOfSurface.map(o => o.tool), ['Bash', 'Read', 'Read', 'Glob', 'WebFetch', 'mcp__bus__bus_send']);
});
