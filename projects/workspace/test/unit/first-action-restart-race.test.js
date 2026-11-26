// The service commit gate (WorkspaceService #commitVerifiedWrite) against the first-write race seen
// on OpenProject: the Work field already held 8, the typed 56 was joined to it, the server answered
// 200 and stored 856. That write, and any write whose target, version, terms, predicate or account
// changed after approval, must fail closed. Guard advice says proceed throughout and never helps.
// Fakes only: an in-process service, a fake page and an in-memory record store.
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { loadServiceConfig } from '../../src/config.js';
import { WorkspaceService } from '../../src/service.js';
import { approveCommit } from '../../src/write-binding.js';
import { createOwnerSession, findElement } from '../../src/workflows/owner-session.js';
import { FakeAdapter, ORIGIN } from '../support/fake-adapter.js';
import { FORM_INTENT, WORKSPACE_ID, createClock } from '../support/harness.js';

const FORM_URL = `${ORIGIN}/form`;
const WORK_FIELD = '#name'; // the fixture form's first input stands in for the Work field
const SAVE = '#send';
const DONE = { completedWhen: [{ kind: 'element-present', selector: '#receipt' }] };
const PROCEED = [{ status: 'eligible-for-review' }, { decision: 'repair', stage: 'verified' }, { tool: 'act' }];

function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Record store plus the page's server: Save stores what the form holds and always answers 200. */
class WorkPackageAdapter extends FakeAdapter {
  constructor(options, db, fault) {
    super(options);
    Object.assign(this, { db, fault, httpStatuses: [] });
  }

  async execute(workspaceId, request) {
    const page = this._page(workspaceId);
    if (request.kind === 'fill' && this.fault.appendOnFill) {
      // A stale or restarted first action: the typed value is joined to the one the field held.
      this.executions.push(request.actionId);
      page.values[request.target.selector] = (page.values[request.target.selector] ?? '') + request.params.value;
      return { selector: request.target.selector };
    }
    if (request.kind === 'submit' && request.target.selector === SAVE) {
      if (this.fault.appendAtSave) page.values[WORK_FIELD] = String(this.db.rows[this.db.current].estimatedHours) + page.values[WORK_FIELD];
      const row = this.db.rows[this.db.current];
      if (!this.fault.ignoreSave) {
        this.db.commits.push({ recordId: row.recordId, fromVersion: row.recordVersion, termsSha256: row.termsSha256,
          predicate: row.predicate, account: row.account, estimatedHours: Number(page.values[WORK_FIELD]) });
        row.estimatedHours = Number(page.values[WORK_FIELD]);
        row.recordVersion += 1;
      }
      this.httpStatuses.push(200);
    }
    return super.execute(workspaceId, request);
  }
}

function makeDb({ existing, version }) {
  const row = (recordId, over = {}) => ({ account: 'acct-a', recordId, predicate: 'work-editable',
    recordVersion: version, termsSha256: 'a'.repeat(64), estimatedHours: existing, remainingHours: 4, ...over });
  return { current: 'wp-42', commits: [], rows: { 'wp-42': row('wp-42'), 'wp-43': row('wp-43', { recordVersion: version + 3 }) } };
}

const lockOf = row => ({ entity: 'work-package', account: row.account, recordId: row.recordId, predicate: row.predicate,
  recordVersion: row.recordVersion, termsSha256: row.termsSha256 });

async function openWorkspace({ db, fault = {}, approvals, advice = PROCEED[0], hooks = {} }) {
  const root = mkdtempSync(join(tmpdir(), 'first-action-race-'));
  const base = loadServiceConfig();
  const config = { ...base, dispatch: { ...base.dispatch, completionTimeoutMs: 40, completionPollMs: 5, valueSettleMs: 10 } };
  let adapter = null;
  const service = await WorkspaceService.open({
    stateDir: join(root, 'state'), config, clock: createClock().now, hooks,
    createAdapter: () => (adapter = new WorkPackageAdapter({ receiptsPath: join(root, 'receipts.jsonl') }, db, fault)),
    commitAuthority: {
      approvalFor: async ({ approvalId }) => approvals.get(approvalId) ?? null,
      readLock: async () => lockOf(db.rows[db.current]),
      readRecord: async ({ approval }) => {
        const row = db.rows[approval.lock.recordId];
        return { account: row.account, recordId: row.recordId, recordVersion: row.recordVersion,
          fields: { estimatedHours: row.estimatedHours, remainingHours: row.remainingHours } };
      },
    },
    adviseWrite: async () => advice,
  });
  const { adminCredential } = await service.createWorkspace({ workspaceId: WORKSPACE_ID });
  await service.grantAuthorization({ workspaceId: WORKSPACE_ID, adminCredential, grantId: 'grant-agent', ownerId: 'agent',
    intents: [FORM_INTENT], actionKinds: ['navigate', 'fill', 'submit'], targetOrigins: [ORIGIN] });
  const owner = await service.assignOwner({ workspaceId: WORKSPACE_ID, adminCredential, ownerId: 'agent' });
  const session = createOwnerSession(service, { workspaceId: WORKSPACE_ID, ...owner });
  await session.act(await session.observe(), { actionId: 'nav', authorizedIntent: FORM_INTENT, kind: 'navigate', target: { url: FORM_URL } });
  // The field shows the stored value, as the Work dialog does.
  adapter.pages.get(WORKSPACE_ID).values[WORK_FIELD] = String(db.rows[db.current].estimatedHours);
  const act = async (actionId, spec) => {
    const obs = await session.observe();
    return session.act(obs, { actionId, authorizedIntent: FORM_INTENT,
      target: findElement(obs, el => el.selector === spec.selector, spec.selector), ...spec, selector: undefined });
  };
  return { adapter, act, close: async () => { await service.close(); rmSync(root, { recursive: true, force: true }); } };
}

function approvalFor(db, hours) {
  const { entity, ...lock } = lockOf(db.rows['wp-42']);
  return approveCommit({ approvalId: 'approval-1', target: { url: FORM_URL, entity, rowId: lock.recordId }, lock,
    fields: { [WORK_FIELD]: String(hours) }, commit: SAVE, readBack: { estimatedHours: hours } });
}

// A refusal at submission rejects the call; one at dispatch settles the action as never dispatched.
const settle = promise => promise.catch(error => {
  assert.equal(error.code, 'write-not-approved', error.message);
  return { rejected: error, dispatchStatus: 'rejected-at-admission' };
});
const refusalOf = result => result.rejected?.message ?? result.neverDispatched?.detail ?? '';

async function writeWork(ws, { hours, approvalId = 'approval-1', typed = String(hours) }) {
  const fill = await settle(ws.act('fill-work', { kind: 'fill', selector: WORK_FIELD, params: { value: typed }, approvalId }));
  const save = await settle(ws.act('save-work', { kind: 'submit', selector: SAVE, completion: DONE, approvalId }));
  return { fill, save };
}

const CHANGES = {
  'target-changed': db => { db.current = 'wp-43'; },
  'version-changed': db => { db.rows['wp-42'].recordVersion += 1; db.rows['wp-42'].estimatedHours += 1; },
  'terms-changed': db => { db.rows['wp-42'].termsSha256 = 'b'.repeat(64); },
  'predicate-changed': db => { db.rows['wp-42'].predicate = 'work-locked'; },
  'account-changed': db => { db.rows['wp-42'].account = 'acct-b'; },
};
const SCENARIOS = ['match', 'stale-append', 'http-200-no-commit', 'no-approval', 'payload-changed', ...Object.keys(CHANGES)];

test('100 randomized first-write trials: zero wrong writes, and a matching write commits exactly once', async () => {
  const seed = 20261125;
  const random = mulberry32(seed);
  const pick = list => list[Math.floor(random() * list.length)];
  const order = [...SCENARIOS, ...Array.from({ length: 100 - SCENARIOS.length }, () => pick(SCENARIOS))];
  const tally = Object.fromEntries(SCENARIOS.map(name => [name, 0]));
  let wrongWrites = 0, matchingCommits = 0;
  for (const [trial, scenario] of order.entries()) {
    tally[scenario] += 1;
    const hours = 10 + Math.floor(random() * 90);
    const existing = 1 + Math.floor(random() * 9);
    const db = makeDb({ existing, version: 1 + Math.floor(random() * 20) });
    const approval = approvalFor(db, hours);
    const approvedRow = { ...db.rows['wp-42'] };
    const whenChanged = pick(['before-fill', 'before-save-dispatch']);
    const change = CHANGES[scenario];
    const hooks = change && whenChanged === 'before-save-dispatch'
      ? { afterIntentPersisted: request => { if (request.actionId === 'save-work') change(db); } } : {};
    const fault = { appendOnFill: scenario === 'stale-append', ignoreSave: scenario === 'http-200-no-commit' };
    const ws = await openWorkspace({ db, fault, approvals: new Map([[approval.approvalId, approval]]), advice: pick(PROCEED), hooks });
    try {
      if (change && whenChanged === 'before-fill') change(db);
      const { fill, save } = await writeWork(ws, { hours,
        approvalId: scenario === 'no-approval' ? 'approval-missing' : 'approval-1',
        typed: scenario === 'payload-changed' ? String(hours + 1) : String(hours) });
      const wrong = db.commits.filter(c => c.recordId !== approvedRow.recordId || c.fromVersion !== approvedRow.recordVersion
        || c.termsSha256 !== approvedRow.termsSha256 || c.predicate !== approvedRow.predicate
        || c.account !== approvedRow.account || c.estimatedHours !== hours);
      wrongWrites += wrong.length;
      const label = `trial ${trial} ${scenario} ${whenChanged}`;
      if (scenario === 'match') {
        assert.equal(db.commits.length, 1, label);
        assert.equal(save.outcome, 'completed', label);
        assert.equal(save.outcomeBasis, 'commit-verified', label);
        matchingCommits += 1;
        continue;
      }
      assert.equal(db.commits.length, 0, label);
      assert.notEqual(save.outcome, 'completed', label);
      if (scenario === 'stale-append') {
        assert.equal(fill.outcome, 'unknown', label); // the page shows 856, not 56
        assert.match(refusalOf(save), /field-read-back-mismatch at dispatch/, label);
      } else if (scenario === 'http-200-no-commit') {
        // The server answered 200 and the page moved on, but the record never changed.
        assert.deepEqual(ws.adapter.httpStatuses, [200], label);
        assert.equal(save.outcomeBasis, 'commit-unverified', label);
      } else if (scenario === 'no-approval') {
        assert.match(refusalOf(fill), /no-approval at admission/, label);
        assert.match(refusalOf(save), /no-approval at admission/, label);
      } else if (scenario === 'payload-changed') {
        assert.match(refusalOf(fill), /approved-payload-changed at admission/, label);
        assert.match(refusalOf(save), /field-read-back-mismatch at dispatch/, label);
      } else {
        // Changed before the fill: refused at submission. Changed after Save was admitted: refused at dispatch.
        const stage = whenChanged === 'before-fill' ? 'admission' : 'dispatch';
        const reason = scenario === 'target-changed' ? 'approved-target-changed' : 'approval-lock-changed';
        assert.match(refusalOf(save), new RegExp(`${reason} at ${stage}`), label);
        if (stage === 'dispatch') assert.equal(save.dispatchStatus, 'never-dispatched', label);
      }
    } finally { await ws.close(); }
  }
  assert.equal(wrongWrites, 0);
  assert.equal(matchingCommits, tally.match);
  console.log(`seed ${seed}: ${order.length} trials, ${wrongWrites} wrong writes, ${matchingCommits} verified commits`, tally);
});

test('guard advice only lowers: abstain refuses a matching write; a recommended check can fail it', async () => {
  for (const advice of [{ status: 'abstain' }, { decision: 'abstain' }, { tool: 'ask_human' }]) {
    const db = makeDb({ existing: 8, version: 5 });
    const approval = approvalFor(db, 56);
    const ws = await openWorkspace({ db, approvals: new Map([[approval.approvalId, approval]]), advice });
    try {
      const { save } = await writeWork(ws, { hours: 56 });
      assert.match(refusalOf(save), /guard-abstained at admission/);
      assert.equal(db.commits.length, 0);
    } finally { await ws.close(); }
  }
  // The guard asks that remainingHours read back unchanged; the save also moved it, so it is not verified.
  const db = makeDb({ existing: 8, version: 5 });
  const approval = approvalFor(db, 56);
  const ws = await openWorkspace({ db, approvals: new Map([[approval.approvalId, approval]]), advice: { recommendedChecks: ['remainingHours'] } });
  try {
    ws.adapter.fault.ignoreSave = false;
    const original = ws.adapter.execute.bind(ws.adapter);
    ws.adapter.execute = async (id, request) => {
      const result = await original(id, request);
      if (request.kind === 'submit') db.rows['wp-42'].remainingHours = 0;
      return result;
    };
    const { save } = await writeWork(ws, { hours: 56 });
    assert.equal(save.outcome, 'unknown');
    assert.equal(save.outcomeBasis, 'committed-value-mismatch');
    assert.deepEqual(save.evidence.commit.mismatched, ['remainingHours']);
  } finally { await ws.close(); }
});

test('limit: a value joined at the moment of Save lands, but is never reported as success', async () => {
  // The field held 56 when checked; the join happens inside the server round trip. No client-side
  // check can stop that write. The post-commit read-back catches it and leaves the outcome unknown.
  const db = makeDb({ existing: 8, version: 5 });
  const approval = approvalFor(db, 56);
  const ws = await openWorkspace({ db, fault: { appendAtSave: true }, approvals: new Map([[approval.approvalId, approval]]) });
  try {
    const { save } = await writeWork(ws, { hours: 56 });
    assert.deepEqual(ws.adapter.httpStatuses, [200]);
    assert.equal(db.rows['wp-42'].estimatedHours, 856);
    assert.equal(save.outcome, 'unknown');
    assert.equal(save.outcomeBasis, 'committed-value-mismatch');
    assert.equal(save.isUncertain, true);
  } finally { await ws.close(); }
});
