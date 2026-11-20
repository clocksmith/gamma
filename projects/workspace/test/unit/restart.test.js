// Restart recovery with real process kills (fake adapter, external receipts on disk).
import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { loadServiceConfig } from '../../src/config.js';
import { startHost } from '../../qualification/service-client.js';
import { terminationEvidence } from '../../qualification/termination.js';
import { ORIGIN } from '../support/fake-adapter.js';

const config = loadServiceConfig();
const WORKSPACE_ID = 'ws-restart';
const INTENT = 'form:contact';
const FORM_TASK = Object.freeze({
  intent: INTENT,
  formUrl: `${ORIGIN}/form`,
  fields: { name: 'Ada', email: 'ada@example.test' },
  completedWhen: [{ kind: 'element-present', selector: '#receipt' }],
});

function receipts(path) {
  if (!existsSync(path)) return [];
  return readFileSync(path, 'utf8').trim().split('\n').filter(Boolean).map((line) => JSON.parse(line));
}

async function rejectsWith(promise, code) {
  await assert.rejects(promise, (error) => {
    assert.equal(error.code, code, error.message);
    return true;
  });
}

async function prepare() {
  const root = mkdtempSync(join(tmpdir(), 'fawn-restart-'));
  const base = { stateDir: join(root, 'state'), adapter: 'fake', receiptsPath: join(root, 'receipts.jsonl') };
  const host = await startHost(base);
  const { adminCredential } = await host.call('createWorkspace', { workspaceId: WORKSPACE_ID });
  for (const ownerId of ['agent-a', 'agent-b']) {
    await host.call('grantAuthorization', {
      workspaceId: WORKSPACE_ID,
      adminCredential,
      grantId: `grant-${ownerId}`,
      ownerId,
      intents: [INTENT],
      actionKinds: ['navigate', 'fill', 'submit'],
      targetOrigins: [ORIGIN],
    });
  }
  const assigned = await host.call('assignOwner', { workspaceId: WORKSPACE_ID, adminCredential, ownerId: 'agent-a' });
  await host.close();
  const owner = { workspaceId: WORKSPACE_ID, ...assigned };
  return { root, base, adminCredential, owner };
}

async function crashDuringForm(base, owner, hook) {
  const host = await startHost({ ...base, crash: { hook, actionIdSuffix: '-submit' } });
  await assert.rejects(host.workflow('form', owner, { ...FORM_TASK, runId: 'run-1' }), (error) => {
    assert.equal(terminationEvidence(error.exit, host.terminationRequest()).abrupt, true);
    return true;
  });
}

function identity(owner) {
  const { workspaceId, ownerId, ownerGeneration, ownerCredential } = owner;
  return { workspaceId, ownerId, ownerGeneration, ownerCredential };
}

// Failure after intent is durable, before dispatch: provably never dispatched.
{
  const { base, owner } = await prepare();
  await crashDuringForm(base, owner, 'afterIntentPersisted');
  const host = await startHost(base);
  const action = await host.call('action', { ...identity(owner), actionId: 'run-1-submit' });
  assert.equal(action.dispatchStatus, 'never-dispatched');
  assert.equal(action.neverDispatched.code, 'restart-invalidated-queue');
  assert.equal(receipts(base.receiptsPath).length, 0);
  await rejectsWith(host.workflow('form', owner, { ...FORM_TASK, runId: 'run-2' }), 'resubmission-not-permitted');
  const explicit = await host.workflow('form', owner, { ...FORM_TASK, runId: 'run-3', resubmissionOf: 'run-1-submit' });
  assert.equal(explicit.status, 'completed', JSON.stringify(explicit));
  assert.equal(receipts(base.receiptsPath).length, 1);
  await host.close();
}

// Failure after external submission: unknown survives restarts and handoff; no duplicate.
{
  const { base, owner, adminCredential } = await prepare();
  await crashDuringForm(base, owner, 'afterEffect');
  assert.equal(receipts(base.receiptsPath).length, 1);
  let host = await startHost(base);
  let action = await host.call('action', { ...identity(owner), actionId: 'run-1-submit' });
  assert.equal(action.outcome, 'unknown');
  assert.equal(action.outcomeBasis, 'restart-after-dispatch-start');
  assert.equal(action.isUncertain, true);
  await rejectsWith(host.workflow('form', owner, { ...FORM_TASK, runId: 'run-2', resubmissionOf: 'run-1-submit' }),
    'effect-unresolved');
  await host.kill();
  host = await startHost(base);
  action = await host.call('action', { ...identity(owner), actionId: 'run-1-submit' });
  assert.equal(action.outcome, 'unknown');
  assert.equal(action.isUncertain, true);
  const handoff = await host.call('assignOwner', { workspaceId: WORKSPACE_ID, adminCredential, ownerId: 'agent-b' });
  const transferred = handoff.outstanding.find((entry) => entry.actionId === 'run-1-submit');
  assert.equal(transferred.isUncertain, true);
  await rejectsWith(host.call('observe', identity(owner)), 'stale-owner-generation');
  await host.kill();
  host = await startHost(base);
  await rejectsWith(host.call('observe', identity(owner)), 'stale-owner-generation');
  const next = { workspaceId: WORKSPACE_ID, ...handoff };
  const review = await host.call('reconcile', { ...identity(next), actionId: 'run-1-submit', method: 'human-review' });
  assert.equal(review.reconciliation.result, 'human-review-requested');
  await host.call('decideHumanReview', {
    workspaceId: WORKSPACE_ID,
    adminCredential,
    actionId: 'run-1-submit',
    decision: 'effect-present',
    note: 'external receipt log shows one submission',
  });
  await rejectsWith(host.workflow('form', next, { ...FORM_TASK, runId: 'run-4', resubmissionOf: 'run-1-submit' }),
    'effect-already-completed');
  assert.equal(receipts(base.receiptsPath).length, 1);
  await host.close();
}

// Failure after completion, before acknowledgment: completed and still outstanding.
{
  const { base, owner } = await prepare();
  await crashDuringForm(base, owner, 'afterOutcome');
  const host = await startHost(base);
  const action = await host.call('action', { ...identity(owner), actionId: 'run-1-submit' });
  assert.equal(action.outcome, 'completed');
  assert.equal(action.acknowledgedGeneration, null);
  let outstanding = await host.call('outstanding', identity(owner));
  assert.ok(outstanding.some((entry) => entry.actionId === 'run-1-submit'));
  await host.call('acknowledge', { ...identity(owner), actionId: 'run-1-submit' });
  outstanding = await host.call('outstanding', identity(owner));
  assert.equal(outstanding.some((entry) => entry.actionId === 'run-1-submit'), false);
  assert.equal(receipts(base.receiptsPath).length, 1);
  await host.close();
}

// Durable authority that cannot be restored fails closed; a live holder keeps the journal.
{
  const { base } = await prepare();
  const holder = await startHost(base);
  await rejectsWith(startHost(base), 'journal-locked');
  await holder.close();
  const journalPath = join(base.stateDir, config.journal.fileName);
  writeFileSync(journalPath, readFileSync(journalPath, 'utf8').replace('agent-a', 'agent-z'));
  await rejectsWith(startHost(base), 'journal-corrupt');
}

console.log('ok: restart');
