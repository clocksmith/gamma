// The request-level write guard (src/request-guard.js): while an approved commit is dispatched, the
// page's write requests are held at the browser (CDP Fetch) and only one request matching the
// approval's method, URL, body values and version may continue. Fake CDP sessions only; the
// real-browser check is test/unit/request-guard-browser.test.mjs.
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { createCdpAdapter } from '../../src/adapters/cdp-adapter.js';
import { loadServiceConfig } from '../../src/config.js';
import { checkWriteRequest, guardWrites } from '../../src/request-guard.js';
import { WorkspaceService } from '../../src/service.js';
import { approveCommit } from '../../src/write-binding.js';
import { createOwnerSession, findElement } from '../../src/workflows/owner-session.js';
import { FakeAdapter, ORIGIN } from '../support/fake-adapter.js';
import { FORM_INTENT, WORKSPACE_ID } from '../support/harness.js';

const API = 'https://app.test/api/items/42';
const RULE = Object.freeze({ method: 'PATCH', url: API, fields: { estimatedTime: 'PT56H' }, versionPath: 'lockVersion' });
const patch = body => ({ method: 'PATCH', url: API, postData: typeof body === 'string' ? body : JSON.stringify(body) });
const GOOD = patch({ lockVersion: 7, estimatedTime: 'PT56H' });

function fakeSession({ failOn = null } = {}) {
  const calls = [], listeners = new Set(), held = new Map(), arrived = [];
  let next = 1;
  return {
    calls, arrived,
    methods: () => calls.map(([method]) => method),
    send: async (method, params = {}) => {
      calls.push([method, params]);
      if (method === failOn) throw Error(`${method} failed`);
      if (method === 'Fetch.continueRequest') arrived.push(held.get(params.requestId));
      return {};
    },
    subscribe: listener => { listeners.add(listener); return () => listeners.delete(listener); },
    pause: request => {
      const requestId = `r${next++}`;
      held.set(requestId, request);
      for (const listener of listeners) listener('Fetch.requestPaused', { requestId, request });
    },
    listening: () => listeners.size,
  };
}
const guard = (session, run, extra = {}) => guardWrites(session, { rule: RULE, version: 7, windowMs: 30, settleMs: 5, ...extra }, run);

test('pure check: method, URL, body values, version and extra fields', () => {
  assert.deepEqual(checkWriteRequest(RULE, 7, GOOD), { ok: true, write: true });
  assert.deepEqual(checkWriteRequest(RULE, 7, { method: 'GET', url: API }), { ok: true, write: false });
  assert.equal(checkWriteRequest(RULE, 7, { ...GOOD, method: 'POST' }).reason, 'unexpected-write');
  assert.equal(checkWriteRequest(RULE, 7, { ...GOOD, url: `${API}?x=1` }).reason, 'unexpected-write');
  assert.equal(checkWriteRequest(RULE, 7, patch({ lockVersion: 6, estimatedTime: 'PT56H' })).reason, 'request-version-mismatch');
  assert.equal(checkWriteRequest(RULE, 7, patch({ estimatedTime: 'PT56H' })).reason, 'request-version-mismatch');
  assert.equal(checkWriteRequest(RULE, 7, patch({ lockVersion: 7, estimatedTime: 'PT856H' })).reason, 'request-payload-mismatch');
  assert.deepEqual(checkWriteRequest(RULE, 7, patch({ lockVersion: 7, estimatedTime: 'PT56H', remainingTime: 'PT0H' })),
    { ok: false, reason: 'request-payload-mismatch', extra: ['remainingTime'] });
  assert.equal(checkWriteRequest(RULE, 7, { method: 'PATCH', url: API }).reason, 'request-payload-mismatch');
  assert.equal(checkWriteRequest(RULE, 7, patch('not json')).reason, 'request-payload-mismatch');
  // A document sent as one JSON-string field of a form body, with the version inside it.
  const docRule = { method: 'POST', url: API, fields: { 'doc.terms': 'BIND-1', action: 'Save' }, versionPath: 'doc.modified', allowPaths: ['doc.*'] };
  const modified = '2026-11-25 10:00:00.123456';
  const form = doc => ({ method: 'POST', url: API, postData: new URLSearchParams({ doc: JSON.stringify(doc), action: 'Save' }).toString() });
  assert.deepEqual(checkWriteRequest(docRule, modified, form({ name: 'PO-1', modified, terms: 'BIND-1' })), { ok: true, write: true });
  assert.equal(checkWriteRequest(docRule, modified, form({ name: 'PO-1', modified: '2026-11-25 10:00:01.000000', terms: 'BIND-1' })).reason,
    'request-version-mismatch');
  assert.equal(checkWriteRequest(docRule, modified, { ...form({ modified, terms: 'BIND-1' }), postData: `${form({ modified, terms: 'BIND-1' }).postData}&extra=1` }).reason,
    'request-payload-mismatch');
});

test('fake CDP session: a matching write continues; reads pass; Fetch is enabled then disabled', async () => {
  const session = fakeSession();
  const { requestGuard } = await guard(session, async () => { session.pause({ method: 'GET', url: API }); session.pause(GOOD); });
  assert.equal(requestGuard.admitted, 1);
  assert.deepEqual(requestGuard.blocked, []);
  assert.deepEqual(session.arrived, [{ method: 'GET', url: API }, GOOD]);
  assert.equal(session.methods()[0], 'Fetch.enable');
  assert.equal(session.methods().at(-1), 'Fetch.disable');
  assert.equal(session.listening(), 0);
});

test('fake CDP session: wrong version, extra field and a second write are failed with BlockedByClient', async () => {
  for (const [request, reason] of [
    [patch({ lockVersion: 6, estimatedTime: 'PT56H' }), 'request-version-mismatch'],
    [patch({ lockVersion: 7, estimatedTime: 'PT56H', remainingTime: 'PT0H' }), 'request-payload-mismatch'],
    [{ ...GOOD, url: 'https://app.test/api/items/43' }, 'unexpected-write'],
  ]) {
    const session = fakeSession();
    const { requestGuard } = await guard(session, async () => session.pause(request));
    assert.equal(requestGuard.admitted, 0);
    assert.deepEqual(requestGuard.blocked.map(entry => entry.reason), [reason]);
    assert.deepEqual(session.arrived, []);
    assert.deepEqual(session.calls.find(([method]) => method === 'Fetch.failRequest')[1], { requestId: 'r1', errorReason: 'BlockedByClient' });
    assert.equal(session.methods().at(-1), 'Fetch.disable');
  }
  const twice = fakeSession();
  const { requestGuard } = await guard(twice, async () => { twice.pause(GOOD); twice.pause(GOOD); });
  assert.equal(requestGuard.admitted, 1);
  assert.deepEqual(requestGuard.blocked.map(entry => [entry.reason, entry.detail]), [['unexpected-write', 'second write']]);
  assert.deepEqual(twice.arrived, [GOOD]);
  // A second write the click starts asynchronously, inside the settle window, is blocked too.
  const late = fakeSession();
  const lateRun = await guard(late, async () => { late.pause(GOOD); setTimeout(() => late.pause(GOOD), 1); }, { settleMs: 20 });
  assert.deepEqual(lateRun.requestGuard.blocked.map(entry => entry.reason), ['unexpected-write']);
  assert.deepEqual(late.arrived, [GOOD]);
});

test('fake CDP session: Fetch.disable runs on a failed click, a failed decision and a timeout', async () => {
  const thrown = fakeSession();
  await assert.rejects(guard(thrown, async () => { throw Error('click failed'); }), error => error.requestGuard?.admitted === 0);
  assert.equal(thrown.methods().at(-1), 'Fetch.disable');
  assert.equal(thrown.listening(), 0);
  const failing = fakeSession({ failOn: 'Fetch.continueRequest' });
  const { requestGuard } = await guard(failing, async () => failing.pause(GOOD));
  assert.equal(failing.methods().at(-1), 'Fetch.disable');
  // The continue failed, so whether the write left is unknown: reported, and the gate then treats it as unknown.
  assert.deepEqual(failing.arrived, []);
  assert.equal(requestGuard.admitted, 1);
  assert.deepEqual(requestGuard.blocked.map(entry => entry.reason), ['request-guard-error']);
  const silent = fakeSession();
  const quiet = await guard(silent, async () => 'clicked');
  assert.equal(quiet.result, 'clicked');
  assert.equal(quiet.requestGuard.admitted, 0);
  assert.deepEqual(silent.methods(), ['Fetch.enable', 'Fetch.disable']);
});

test('CDP adapter: execute holds the page requests only for a guarded commit', async () => {
  const root = mkdtempSync(join(tmpdir(), 'request-guard-cdp-'));
  try {
    const adapter = createCdpAdapter({ config: loadServiceConfig(), profileRoot: root, artifactRoot: root });
    const calls = [], listeners = new Set();
    let body = patch({ lockVersion: 6, estimatedTime: 'PT56H' });
    const cdp = {
      subscribe: listener => { listeners.add(listener); return () => listeners.delete(listener); },
      send: async (method, params, sessionId) => {
        calls.push(method);
        if (method === 'Runtime.evaluate') return { result: { value: { count: 1, x: 5, y: 5 } } };
        // The click's mouse-up makes the page send its save request.
        if (method === 'Input.dispatchMouseEvent' && params.type === 'mouseReleased' && calls.includes('Fetch.enable')) {
          for (const listener of listeners) listener({ method: 'Fetch.requestPaused', sessionId, params: { requestId: 'r1', request: body } });
        }
        return {};
      },
    };
    adapter._workspaces.set(WORKSPACE_ID, { cdp, sessionId: 's1', pages: new Map([['main', { sessionId: 's1', targetId: 't1' }]]) });
    assert.equal(adapter.supportsRequestGuard, true);
    const submit = { kind: 'submit', target: { selector: '#save' } };
    const requestGuard = { rule: RULE, version: 7, windowMs: 30, settleMs: 5 };
    const stale = await adapter.execute(WORKSPACE_ID, { ...submit, requestGuard });
    assert.deepEqual(stale.requestGuard.blocked.map(entry => entry.reason), ['request-version-mismatch']);
    assert.ok(calls.includes('Fetch.failRequest') && calls.at(-1) === 'Fetch.disable');
    calls.length = 0;
    body = GOOD;
    const good = await adapter.execute(WORKSPACE_ID, { ...submit, requestGuard });
    assert.equal(good.requestGuard.admitted, 1);
    assert.ok(calls.includes('Fetch.continueRequest') && calls.at(-1) === 'Fetch.disable');
    calls.length = 0;
    await adapter.execute(WORKSPACE_ID, submit);
    assert.equal(calls.some(method => method.startsWith('Fetch.')), false);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

// The commit gate end to end: a fake page whose Save sends one PATCH carrying the version the
// page holds, a fake CDP session around it, and a server that counts the writes that reach it.
class GuardedPageAdapter extends FakeAdapter {
  constructor(options, server, { supported = true } = {}) {
    super(options);
    Object.assign(this, { server, supported, saveClicks: 0, pageVersion: 7 });
  }

  get supportsRequestGuard() { return this.supported; }

  async execute(workspaceId, request) {
    if (request.kind !== 'submit') return super.execute(workspaceId, request);
    this.saveClicks += 1;
    const page = this._page(workspaceId);
    const send = { method: 'PATCH', url: API, postData: JSON.stringify({ lockVersion: this.pageVersion, estimatedTime: `PT${page.values['#name']}H` }) };
    const session = fakeSession();
    const { result, requestGuard } = await guardWrites(session, request.requestGuard, async () => {
      session.pause(send);
      return { selector: request.target.selector };
    });
    if (session.arrived.length) {
      this.server.receive(JSON.parse(session.arrived[0].postData));
      await super.execute(workspaceId, request);
    }
    return { ...result, requestGuard };
  }
}

async function openGated({ supported = true } = {}) {
  const row = { entity: 'item', account: 'acct-a', recordId: '42', predicate: 'editable', recordVersion: 7, termsSha256: 'a'.repeat(64), estimatedTime: 'PT8H' };
  const server = { writes: 0, receive(body) {
    this.writes += 1;
    if (body.lockVersion === row.recordVersion) Object.assign(row, { estimatedTime: body.estimatedTime, recordVersion: row.recordVersion + 1 });
  } };
  const { estimatedTime, entity, ...lock } = row;
  const approval = approveCommit({ approvalId: 'approval-a', target: { url: `${ORIGIN}/form`, entity, rowId: '42' }, lock,
    fields: { '#name': '56' }, commit: '#send', readBack: { estimatedTime: 'PT56H' }, request: RULE });
  const root = mkdtempSync(join(tmpdir(), 'request-guard-gate-'));
  const base = loadServiceConfig();
  const config = { ...base, dispatch: { ...base.dispatch, completionTimeoutMs: 40, completionPollMs: 5, valueSettleMs: 10 } };
  let adapter = null;
  const service = await WorkspaceService.open({
    stateDir: join(root, 'state'), config, clock: Date.now,
    createAdapter: () => (adapter = new GuardedPageAdapter({ receiptsPath: join(root, 'receipts.jsonl') }, server, { supported })),
    commitAuthority: {
      approvalFor: async () => approval,
      readLock: async () => { const { estimatedTime: _, ...live } = row; return { ...live }; },
      readRecord: async () => ({ account: row.account, recordId: row.recordId, recordVersion: row.recordVersion, fields: { estimatedTime: row.estimatedTime } }),
    },
    adviseWrite: async () => ({ status: 'eligible-for-review' }),
  });
  const { adminCredential } = await service.createWorkspace({ workspaceId: WORKSPACE_ID });
  await service.grantAuthorization({ workspaceId: WORKSPACE_ID, adminCredential, grantId: 'g', ownerId: 'agent',
    intents: [FORM_INTENT], actionKinds: ['navigate', 'fill', 'submit'], targetOrigins: [ORIGIN] });
  const owner = await service.assignOwner({ workspaceId: WORKSPACE_ID, adminCredential, ownerId: 'agent' });
  const session = createOwnerSession(service, { workspaceId: WORKSPACE_ID, ...owner });
  await session.act(await session.observe(), { actionId: 'nav', authorizedIntent: FORM_INTENT, kind: 'navigate', target: { url: `${ORIGIN}/form` } });
  const act = async (actionId, kind, selector, extra) => {
    const obs = await session.observe();
    return session.act(obs, { actionId, authorizedIntent: FORM_INTENT, kind, target: findElement(obs, el => el.selector === selector, selector), ...extra });
  };
  const write = async () => {
    await act('fill', 'fill', '#name', { params: { value: '56' } });
    return act('save', 'submit', '#send', { completion: { completedWhen: [{ kind: 'element-present', selector: '#receipt' }] } });
  };
  return { server, row, adapter: () => adapter, write, close: async () => { await service.close(); rmSync(root, { recursive: true, force: true }); } };
}

test('commit gate: the approved version reaches the server once; a stale one never does', async () => {
  const good = await openGated();
  try {
    const saved = await good.write();
    assert.equal(saved.outcomeBasis, 'commit-verified');
    assert.equal(good.server.writes, 1);
    assert.equal(saved.evidence.commit.requestGuard.admitted, 1);
  } finally { await good.close(); }
  // The page sends the version it loaded (6), not the approved one (7): blocked in the browser.
  const stale = await openGated();
  try {
    stale.adapter().pageVersion = 6;
    const saved = await stale.write();
    assert.equal(saved.outcome, 'failed');
    assert.equal(saved.outcomeBasis, 'request-version-mismatch');
    assert.equal(saved.evidence.commit.committed, false);
    assert.equal(stale.server.writes, 0);
    assert.equal(stale.row.recordVersion, 7);
  } finally { await stale.close(); }
});

test('commit gate: an approval with a request rule is refused before Save on an adapter without the guard', async () => {
  const ws = await openGated({ supported: false });
  try {
    const saved = await ws.write();
    assert.equal(saved.dispatchStatus, 'never-dispatched');
    assert.match(saved.neverDispatched.detail, /request-guard-unavailable at dispatch/);
    assert.equal(ws.adapter().saveClicks, 0);
    assert.equal(ws.server.writes, 0);
  } finally { await ws.close(); }
});
