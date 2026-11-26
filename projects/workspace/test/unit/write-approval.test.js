// Guard advice never authorizes a write. Only the service commit gate (WorkspaceService
// #commitVerifiedWrite, bindings in src/write-binding.js) does: an approval bound to the write's
// target URL, entity, row id, field, method and SHA-256 payload digest, plus the live record lock,
// re-checked at submission and again at dispatch.
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { InvestigationStore } from '../../src/client/investigation.js';
import { TraceDag } from '../../src/client/trace-dag.js';
import { runWorkflow } from '../../src/client/workflow-agent.js';
import { loadServiceConfig } from '../../src/config.js';
import { WorkspaceService } from '../../src/service.js';
import {
  adviceAbstains, approveCommit, checkLiveLock, checkWriteBinding, payloadDigest, validApproval,
} from '../../src/write-binding.js';
import { createOwnerSession, findElement } from '../../src/workflows/owner-session.js';
import { FakeAdapter, ORIGIN } from '../support/fake-adapter.js';
import { FORM_INTENT, WORKSPACE_ID, createClock } from '../support/harness.js';

// Every guard output shape that means "proceed" in this repository.
const PROCEED = Object.freeze([
  { status: 'eligible-for-review' }, // checkRepairBoundary
  { schema: 'gammatron.live-lookahead-certificate/v1', decision: 'repair', stage: 'verified' }, // evaluateLiveLookahead
  { decision: 'review', winner: 'v1-reuse' }, // decideBranch
  { tool: 'act', input: { kind: 'fill', handle: 'hname', slot: 'work' } }, // model planner
]);
const FORM_URL = `${ORIGIN}/form`;
const FIELD = '#name';
const SAVE = '#send';
const DONE = { completedWhen: [{ kind: 'element-present', selector: '#receipt' }] };

const liveRow = (over = {}) => ({ entity: 'contact', account: 'acct-a', recordId: 'row-1', predicate: 'editable',
  recordVersion: 3, termsSha256: 'a'.repeat(64), ...over });
const approvalOf = ({ url = FORM_URL, value = 'Ada', row = liveRow() } = {}) => {
  const { entity, ...lock } = row;
  return approveCommit({ approvalId: 'approval-a', target: { url, entity, rowId: lock.recordId }, lock,
    fields: { [FIELD]: value }, commit: SAVE, readBack: { name: value } });
};

test('pure decision: the approval binds target, field, method and payload; advice cannot raise', () => {
  const approval = approvalOf();
  const fill = { url: FORM_URL, method: 'fill', field: FIELD, payload: { value: 'Ada' } };
  for (const advice of PROCEED) assert.equal(adviceAbstains(advice), false);
  for (const advice of [{ status: 'abstain' }, { decision: 'abstain' }, { tool: 'ask_human' }, false]) assert.equal(adviceAbstains(advice), true);
  // (a) target URL, field, method or payload changed after approval.
  assert.deepEqual(checkWriteBinding(approval, { ...fill, url: `${ORIGIN}/form?id=2` }), { ok: false, reason: 'approved-target-changed', changed: ['url'] });
  assert.deepEqual(checkWriteBinding(approval, { ...fill, field: '#email' }), { ok: false, reason: 'approved-target-changed', changed: ['field'] });
  assert.equal(checkWriteBinding(approval, { ...fill, method: 'select' }).reason, 'approved-method-changed');
  assert.equal(checkWriteBinding(approval, { ...fill, payload: { value: 'Eve' } }).reason, 'approved-payload-changed');
  assert.equal(checkWriteBinding(approval, { ...fill, payload: new Uint8Array([1]) }).reason, 'payload-unreadable');
  // (a) live entity, row id or lock changed after approval.
  assert.deepEqual(checkLiveLock(approval, liveRow({ recordId: 'row-2' })), { ok: false, reason: 'approved-target-changed', changed: ['rowId'] });
  assert.deepEqual(checkLiveLock(approval, liveRow({ entity: 'invoice' })), { ok: false, reason: 'approved-target-changed', changed: ['entity'] });
  for (const key of ['account', 'predicate', 'recordVersion', 'termsSha256']) {
    assert.deepEqual(checkLiveLock(approval, liveRow({ [key]: key === 'recordVersion' ? 4 : 'changed' })),
      { ok: false, reason: 'approval-lock-changed', changed: [key] });
  }
  assert.equal(checkLiveLock(approval, null).reason, 'live-lock-unavailable');
  // (b) unchanged write, unchanged lock.
  assert.deepEqual(checkWriteBinding(approval, fill), { ok: true });
  assert.deepEqual(checkWriteBinding(approval, { url: FORM_URL, method: 'submit', field: SAVE }), { ok: true });
  assert.deepEqual(checkLiveLock(approval, liveRow()), { ok: true });
  // A forged approval (a value edited after its digest was bound) is not an approval.
  assert.equal(validApproval({ ...approval, fields: { [FIELD]: 'Eve' } }), false);
  assert.equal(validApproval({ ...approval, target: { ...approval.target, rowId: 'row-2' } }), false);
  // Equivalent encodings share a digest; opaque bodies cannot be approved.
  assert.equal(payloadDigest('{"b":2,"a":1}'), payloadDigest({ a: 1, b: 2 }));
  assert.notEqual(payloadDigest({ value: 'Ada' }), payloadDigest({ value: 'Eve' }));
  assert.equal(payloadDigest(new Uint8Array([1])), null);
});

/** Fixture form plus its server: Save stores the field in the record store and bumps its version. */
class RecordAdapter extends FakeAdapter {
  constructor(options, db) {
    super(options);
    this.db = db;
  }

  _elements(page) {
    return super._elements(page).map(element => ({
      ...element,
      ...(element.selector === FIELD ? { label: 'Name', role: 'textbox', inputType: 'text' } : {}),
      ...(element.selector === SAVE ? { label: 'Send', role: 'button' } : {}),
    }));
  }

  async execute(workspaceId, request) {
    if (request.kind === 'submit' && request.target.selector === SAVE) {
      const row = this.db.rows[this.db.current];
      const value = this._page(workspaceId).values[FIELD];
      this.db.commits.push({ recordId: row.recordId, fromVersion: row.recordVersion, name: value });
      Object.assign(row, { name: value, recordVersion: row.recordVersion + 1 });
    }
    return super.execute(workspaceId, request);
  }
}

const makeDb = () => ({ current: 'row-1', commits: [],
  rows: { 'row-1': { ...liveRow(), name: '' }, 'row-2': { ...liveRow({ recordId: 'row-2' }), name: '' } } });

async function openWorkspace({ approval = approvalOf(), advice = PROCEED[0], hooks = {}, db = makeDb() } = {}) {
  const root = mkdtempSync(join(tmpdir(), 'write-approval-'));
  const base = loadServiceConfig();
  const config = { ...base, dispatch: { ...base.dispatch, completionTimeoutMs: 40, completionPollMs: 5, valueSettleMs: 10 } };
  let adapter = null;
  const service = await WorkspaceService.open({
    stateDir: join(root, 'state'), config, clock: createClock().now, hooks,
    createAdapter: () => (adapter = new RecordAdapter({ receiptsPath: join(root, 'receipts.jsonl') }, db)),
    // The trusted host: its approval store and the system of record. Neither the owner nor a guard supplies these.
    commitAuthority: {
      approvalFor: async () => approval,
      readLock: async () => { const { name, ...lock } = db.rows[db.current]; return lock; },
      readRecord: async ({ approval: held }) => {
        const row = db.rows[held.lock.recordId];
        return { account: row.account, recordId: row.recordId, recordVersion: row.recordVersion, fields: { name: row.name } };
      },
    },
    adviseWrite: async () => advice,
  });
  const { adminCredential } = await service.createWorkspace({ workspaceId: WORKSPACE_ID });
  await service.grantAuthorization({ workspaceId: WORKSPACE_ID, adminCredential, grantId: 'grant-agent', ownerId: 'agent',
    intents: [FORM_INTENT], actionKinds: ['navigate', 'fill', 'submit'], targetOrigins: [ORIGIN] });
  const owner = await service.assignOwner({ workspaceId: WORKSPACE_ID, adminCredential, ownerId: 'agent' });
  const session = createOwnerSession(service, { workspaceId: WORKSPACE_ID, ...owner });
  const open = async actionId => session.act(await session.observe(), { actionId, authorizedIntent: FORM_INTENT,
    kind: 'navigate', target: { url: FORM_URL } });
  await open('nav');
  const act = async (actionId, kind, selector, extra = {}) => {
    const obs = await session.observe();
    return session.act(obs, { actionId, authorizedIntent: FORM_INTENT, kind,
      target: findElement(obs, el => el.selector === selector, selector), ...extra })
      .catch(error => ({ rejected: error, refusal: error.message }));
  };
  const fill = (actionId, value) => act(actionId, 'fill', FIELD, { params: { value } });
  const save = actionId => act(actionId, 'submit', SAVE, { completion: DONE });
  const writes = () => adapter.executions.filter(id => !id.startsWith('nav'));
  return { service, owner: session.identity, db, fill, save, writes, open, close: async () => { await service.close(); rmSync(root, { recursive: true, force: true }); } };
}
const refusalOf = result => result.refusal ?? result.neverDispatched?.detail ?? '';

test('service gate: (a) changed target or payload after approval issues zero writes despite proceed', async () => {
  for (const advice of PROCEED) {
    const ws = await openWorkspace({ advice });
    try {
      ws.db.current = 'row-2'; // the form now edits another row
      assert.match(refusalOf(await ws.fill('fill-row-2', 'Ada')), /approved-target-changed at admission/);
      ws.db.current = 'row-1';
      assert.match(refusalOf(await ws.fill('fill-eve', 'Eve')), /approved-payload-changed at admission/);
      assert.match(refusalOf(await ws.save('save-unfilled')), /field-read-back-mismatch at dispatch/);
      assert.deepEqual(ws.writes(), []);
      assert.deepEqual(ws.db.commits, []);
    } finally { await ws.close(); }
  }
  const elsewhere = await openWorkspace({ approval: approvalOf({ url: `${ORIGIN}/form?id=2` }) });
  try {
    assert.match(refusalOf(await elsewhere.fill('fill-url', 'Ada')), /approved-target-changed at admission/);
    assert.deepEqual(elsewhere.writes(), []);
  } finally { await elsewhere.close(); }
});

test('service gate: (a) a target or version change between admission and dispatch is refused at dispatch', async () => {
  for (const [actionId, change, reason] of [
    ['fill-raced', db => { db.current = 'row-2'; }, /approved-target-changed at dispatch/],
    ['save-raced', db => { db.rows['row-1'].recordVersion += 1; }, /approval-lock-changed at dispatch/],
  ]) {
    const db = makeDb();
    const ws = await openWorkspace({ db, hooks: { afterIntentPersisted: request => { if (request.actionId === actionId) change(db); } } });
    try {
      const filled = await ws.fill('fill-raced', 'Ada');
      const saved = actionId === 'save-raced' ? await ws.save('save-raced') : filled;
      assert.equal(saved.dispatchStatus, 'never-dispatched');
      assert.match(refusalOf(saved), reason);
      assert.deepEqual(db.commits, []);
      assert.equal(ws.writes().includes(actionId), false);
    } finally { await ws.close(); }
  }
});

test('service gate: (b) unchanged target with matching approval commits exactly one write', async () => {
  const ws = await openWorkspace();
  try {
    assert.equal((await ws.fill('fill-approved', 'Ada')).outcome, 'completed');
    const saved = await ws.save('save-approved');
    assert.equal(saved.outcome, 'completed');
    assert.equal(saved.outcomeBasis, 'commit-verified');
    assert.deepEqual(ws.db.commits, [{ recordId: 'row-1', fromVersion: 3, name: 'Ada' }]);
    // The approval bound version 3; the record is now at 4, so the same write again is refused.
    await ws.open('nav-back');
    assert.match(refusalOf(await ws.fill('fill-again', 'Ada')), /approval-lock-changed at admission/);
    assert.match(refusalOf(await ws.save('save-again')), /approval-lock-changed at admission/);
    assert.equal(ws.db.commits.length, 1);
    assert.deepEqual(ws.writes(), ['fill-approved', 'save-approved']);
  } finally { await ws.close(); }
});

test('service gate: (c) every proceed shape with no approval issues zero writes', async () => {
  for (const advice of PROCEED) {
    const ws = await openWorkspace({ approval: null, advice });
    try {
      assert.match(refusalOf(await ws.fill('fill-unapproved', 'Ada')), /no-approval at admission/);
      assert.match(refusalOf(await ws.save('save-unapproved')), /no-approval at admission/);
      assert.deepEqual(ws.writes(), []);
      assert.deepEqual(ws.db.commits, []);
    } finally { await ws.close(); }
  }
});

test('runWorkflow path: a planner proposing act writes only through a matching approval', async () => {
  const root = mkdtempSync(join(tmpdir(), 'write-approval-flow-'));
  const store = new InvestigationStore(root);
  let serial = 0;
  const run = async ws => {
    const projectId = `flow-${++serial}`;
    store.create({ id: projectId, goal: 'Review' });
    const planner = { identity: { model: 'controlled-unit' }, next: async context => (
      context.observation.elements.find(el => el.handle === 'hname')?.value === 'Ada'
        ? { tool: 'finish', input: { summary: 'Review' } } : PROCEED[3]) };
    return runWorkflow({ dag: new TraceDag({ maxNodes: 32, maxEdges: 32, maxSteps: 8 }), mode: 'learn',
      service: ws.service, owner: ws.owner, pageId: 'main', intent: FORM_INTENT, template: 'unit',
      inputs: { work: 'Ada' }, intermediateClicks: [], task: 'Fill and review', planner,
      config: { maxTurns: 4, maxInputBytes: 20000 }, store, projectId, signal: new AbortController().signal,
      verifyReview: async () => {
        const obs = await ws.service.observe(ws.owner);
        return { completed: obs.elements.find(el => el.selector === FIELD)?.value === 'Ada' };
      } });
  };
  try {
    const unapproved = await openWorkspace({ approval: null });
    try {
      assert.equal((await run(unapproved)).completed, false);
      assert.deepEqual(unapproved.writes(), []);
    } finally { await unapproved.close(); }
    const moved = await openWorkspace();
    try {
      moved.db.current = 'row-2';
      assert.equal((await run(moved)).completed, false);
      assert.deepEqual(moved.writes(), []);
    } finally { await moved.close(); }
    const approved = await openWorkspace();
    try {
      assert.equal((await run(approved)).completed, true);
      assert.equal(approved.writes().length, 1);
    } finally { await approved.close(); }
  } finally { store.close(); rmSync(root, { recursive: true, force: true }); }
});
