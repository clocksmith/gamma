// The commit gate's version token closes the window between the gate's lock read and the server's
// commit by making the server enforce the version. An approval names the form's own
// optimistic-concurrency field ({ selector, value }); the value travels with the save, and the
// server refuses a save whose version is not the stored one (OpenProject answers 409 to a stale
// lockVersion, ERPNext raises TimestampMismatchError on a stale `modified`). Fakes only.
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { loadServiceConfig } from '../../src/config.js';
import { WorkspaceService } from '../../src/service.js';
import { approveCommit, validApproval } from '../../src/write-binding.js';
import { createOwnerSession, findElement } from '../../src/workflows/owner-session.js';
import { FakeAdapter, ORIGIN } from '../support/fake-adapter.js';
import { FORM_INTENT, WORKSPACE_ID } from '../support/harness.js';

const FORM_URL = `${ORIGIN}/form`;
const FIELD = '#name';
const SAVE = '#send';
const TOKEN = '#lock_version';
const CONFLICT = '#conflict';
const OUTCOME = { completedWhen: [{ kind: 'element-present', selector: '#receipt' }],
  failedWhen: [{ kind: 'element-present', selector: CONFLICT }] };

/** The form carries a hidden version field; the server compares it with the stored version on Save. */
class VersionedFormAdapter extends FakeAdapter {
  constructor(options, db) {
    super(options);
    Object.assign(this, { db, saveClicks: [], responses: [] });
  }

  _elements(page) {
    const elements = super._elements(page);
    if (page.url !== FORM_URL) return elements;
    const extra = (selector, attributes, more = {}) => ({ selector, tag: 'input', attributes, text: '', handle: `h${selector.slice(1).replace(/_/g, '')}`,
      value: null, href: null, formAction: null, digest: `${selector}:${page.values[selector] ?? ''}`, ...more });
    return [...elements,
      ...(TOKEN in page.values ? [extra(TOKEN, [['type', 'hidden'], ['name', 'lock_version']], { value: page.values[TOKEN] })] : []),
      ...(page.conflict ? [{ ...extra(CONFLICT, [['role', 'alert']]), tag: 'p', text: 'Conflict' }] : [])];
  }

  async execute(workspaceId, request) {
    if (request.kind !== 'submit' || request.target.selector !== SAVE) return super.execute(workspaceId, request);
    const page = this._page(workspaceId);
    this.saveClicks.push(request.actionId);
    const row = this.db.row;
    if (page.values[TOKEN] !== String(row.recordVersion)) {
      // The server's own optimistic-concurrency check: stale version, nothing stored.
      this.executions.push(request.actionId);
      this.responses.push(409);
      page.conflict = true;
      return { selector: SAVE };
    }
    this.db.commits.push({ fromVersion: row.recordVersion, name: page.values[FIELD] });
    Object.assign(row, { name: page.values[FIELD], recordVersion: row.recordVersion + 1 });
    this.responses.push(200);
    return super.execute(workspaceId, request);
  }
}

const makeDb = () => ({ commits: [], lagging: null,
  row: { entity: 'contact', account: 'acct-a', recordId: 'row-1', predicate: 'editable', recordVersion: 7, termsSha256: 'a'.repeat(64), name: 'Old' } });

function approvalOf(db, { token = true } = {}) {
  const { name, entity, ...lock } = db.row;
  return approveCommit({ approvalId: 'approval-a', target: { url: FORM_URL, entity, rowId: lock.recordId }, lock,
    fields: { [FIELD]: 'Ada' }, commit: SAVE, readBack: { name: 'Ada' },
    ...(token ? { versionToken: { selector: TOKEN, value: String(lock.recordVersion) } } : {}) });
}

async function openWorkspace({ db = makeDb(), token = true, hooks = {} } = {}) {
  const approval = approvalOf(db, { token });
  const root = mkdtempSync(join(tmpdir(), 'version-token-'));
  const base = loadServiceConfig();
  const config = { ...base, dispatch: { ...base.dispatch, completionTimeoutMs: 40, completionPollMs: 5, valueSettleMs: 10 } };
  let adapter = null;
  const service = await WorkspaceService.open({
    stateDir: join(root, 'state'), config, clock: Date.now, hooks, // completion waits run on the clock
    createAdapter: () => (adapter = new VersionedFormAdapter({ receiptsPath: join(root, 'receipts.jsonl') }, db)),
    commitAuthority: {
      approvalFor: async () => approval,
      // `lagging` stands for a lock read that has not yet seen a concurrent edit (a replica, a cache).
      readLock: async () => { const { name, ...lock } = db.row; return db.lagging ? { ...lock, ...db.lagging } : lock; },
      readRecord: async () => ({ account: db.row.account, recordId: db.row.recordId, recordVersion: db.row.recordVersion,
        fields: { name: db.row.name } }),
    },
    adviseWrite: async () => ({ status: 'eligible-for-review' }),
  });
  const { adminCredential } = await service.createWorkspace({ workspaceId: WORKSPACE_ID });
  await service.grantAuthorization({ workspaceId: WORKSPACE_ID, adminCredential, grantId: 'grant-agent', ownerId: 'agent',
    intents: [FORM_INTENT], actionKinds: ['navigate', 'fill', 'submit'], targetOrigins: [ORIGIN] });
  const owner = await service.assignOwner({ workspaceId: WORKSPACE_ID, adminCredential, ownerId: 'agent' });
  const session = createOwnerSession(service, { workspaceId: WORKSPACE_ID, ...owner });
  await session.act(await session.observe(), { actionId: 'nav', authorizedIntent: FORM_INTENT, kind: 'navigate', target: { url: FORM_URL } });
  const page = adapter.pages.get(WORKSPACE_ID);
  page.values[TOKEN] = String(db.row.recordVersion); // the form was rendered at the stored version
  const act = async (actionId, kind, selector, extra) => {
    const obs = await session.observe();
    return session.act(obs, { actionId, authorizedIntent: FORM_INTENT, kind,
      target: findElement(obs, el => el.selector === selector, selector), ...extra });
  };
  const write = async ({ outcome = OUTCOME, beforeSave } = {}) => {
    const fill = await act('fill', 'fill', FIELD, { params: { value: 'Ada' } });
    assert.equal(fill.outcome, 'completed');
    beforeSave?.();
    return act('save', 'submit', SAVE, { completion: outcome });
  };
  return { db, adapter, page, write, close: async () => { await service.close(); rmSync(root, { recursive: true, force: true }); } };
}

test('an approval token must carry the approved record version', () => {
  const db = makeDb();
  const approval = approvalOf(db);
  assert.equal(validApproval(approval), true);
  assert.equal(validApproval({ ...approval, versionToken: { selector: TOKEN, value: '6' } }), false);
  assert.equal(validApproval({ ...approval, versionToken: { selector: '', value: '7' } }), false);
});

test('(1) the token equals the approved version: one commit', async () => {
  const ws = await openWorkspace();
  try {
    const saved = await ws.write();
    assert.equal(saved.outcome, 'completed');
    assert.equal(saved.outcomeBasis, 'commit-verified');
    assert.deepEqual(ws.db.commits, [{ fromVersion: 7, name: 'Ada' }]);
    assert.deepEqual(ws.adapter.saveClicks, ['save']);
  } finally { await ws.close(); }
});

test('(2) the token was bumped after approval: zero clicks on Save, refused at dispatch', async () => {
  // After approval a concurrent edit moved the record to version 8 and the form's token shows it
  // (a page change after Save was admitted is already refused as a stale observation). The lock
  // read has not caught up, so only the token shows the edit. The server would accept version 8 and
  // the approved value would overwrite an edit nobody approved; the gate refuses before clicking.
  const ws = await openWorkspace();
  try {
    const saved = await ws.write({ beforeSave: () => {
      ws.db.lagging = { recordVersion: 7 };
      Object.assign(ws.db.row, { recordVersion: 8, name: 'Concurrent' });
      ws.page.values[TOKEN] = '8';
    } });
    assert.equal(saved.dispatchStatus, 'never-dispatched');
    assert.match(saved.neverDispatched.detail, /version-token-mismatch at dispatch/);
    assert.deepEqual(ws.adapter.saveClicks, []);
    assert.deepEqual(ws.db.commits, []);
    assert.equal(ws.db.row.name, 'Concurrent');
  } finally { await ws.close(); }
  // A form missing its token is refused the same way.
  const missing = await openWorkspace();
  try {
    assert.match((await missing.write({ beforeSave: () => { delete missing.page.values[TOKEN]; } })).neverDispatched.detail,
      /version-token-mismatch at dispatch/);
    assert.deepEqual(missing.adapter.saveClicks, []);
  } finally { await missing.close(); }
});

test('(3) the server rejects a stale token past every client check; the gate reports not committed', async () => {
  // (a) A concurrent edit lands after the gate's checks, inside the time-of-check/time-of-use window.
  // (b) The client token check is bypassed (no versionToken in the approval) and the form is stale.
  const cases = [
    ['edit after the checks', { hooks: db => ({ afterDispatchStarted: request => {
      if (request.actionId === 'save') Object.assign(db.row, { recordVersion: 8, name: 'Concurrent' });
    } }) }],
    ['client check bypassed', { token: false, before: ws => { ws.page.values[TOKEN] = '6'; } }],
  ];
  for (const [name, { hooks, token = true, before }] of cases) {
    for (const outcome of [OUTCOME, { completedWhen: OUTCOME.completedWhen }]) {
      const db = makeDb();
      const ws = await openWorkspace({ db, token, hooks: hooks ? hooks(db) : {} });
      try {
        before?.(ws);
        const saved = await ws.write({ outcome });
        assert.deepEqual(ws.adapter.saveClicks, ['save'], name);
        assert.deepEqual(ws.adapter.responses, [409], name);
        assert.deepEqual(ws.db.commits, [], name);
        assert.equal(saved.evidence.commit.committed, false, name);
        assert.notEqual(saved.outcome, 'completed', name);
        // With the refusal declared (failedWhen) it is reported as refused; without, it stays unknown.
        if (outcome.failedWhen) {
          assert.equal(saved.outcome, 'failed', name);
          assert.equal(saved.outcomeBasis, 'commit-refused', name);
        } else {
          assert.equal(saved.outcome, 'unknown', name);
          assert.equal(saved.isUncertain, true, name);
        }
      } finally { await ws.close(); }
    }
  }
});
