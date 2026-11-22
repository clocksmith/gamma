import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { setTimeout as delay } from 'node:timers/promises';
import { WorkspaceController } from '../../src/client/controller.js';
import { WorkflowStore } from '../../src/client/workflow-store.js';
import { sha256Hex } from '../../src/journal.js';

const root = mkdtempSync(join(tmpdir(), 'gamma-review-batch-'));
const config = JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url)));
const template = 'local-review-fixture', accountScope = 'account-test', origin = 'https://review.invalid';
const taskSourceHashes = { fixture: sha256Hex(readFileSync(new URL(import.meta.url))) };
const records = new Map(['teach', 'A', 'B'].map(key => [key, { id: key, value: '' }]));
let generation = 0, observed = 0, businessWrites = 0, plannerCalls = 0, denied = false;
let finalizerGate = null, reviewGate = null, wrongRecord = null, failCleanup = false;
let failedAgentReply = false, failHumanFence = false, currentOwner = 'human';
const grants = new Map();
const effects = [], sequence = [];
const service = {
  createWorkspace: async () => ({ adminCredential: 'fixture-admin' }),
  inspect: async () => ({ grants: [...grants.values()], actions: [], pages: [...records.keys()].map(pageId => ({ pageId })) }),
  grantAuthorization: async grant => { grants.set(grant.grantId, grant); },
  revokeAuthorization: async ({ grantId }) => {
    sequence.push('cleanup');
    if (failCleanup) { failCleanup = false; throw Error('synthetic grant cleanup failure'); }
    if (finalizerGate) {
      const gate = finalizerGate;
      finalizerGate = null;
      gate.entered.resolve();
      await gate.resume.promise;
    }
    grants.delete(grantId);
  },
  assignOwner: async ({ ownerId }) => {
    if (ownerId === 'human' && failHumanFence) throw Error('synthetic failed ownership fence');
    currentOwner = ownerId;
    generation++;
    if (ownerId === 'agent' && failedAgentReply) {
      failedAgentReply = false;
      throw Object.assign(Error('synthetic lost setup response after owner assigned'), { code: 'fixture-assign-lost' });
    }
    return { ownerId, ownerGeneration: generation, ownerCredential: 'fixture-owner', outstanding: [] };
  },
  outstanding: async () => [],
  observe: async ({ pageId }) => ({ url: origin + '/same-form', text: 'Review', isTruncated: false,
    observationVersion: ++observed, elements: [{ handle: 'name', selector: '#name', digest: 'same',
      label: 'Name', role: 'textbox', tag: 'input', inputType: 'text', value: records.get(pageId).value }] }),
  submitAction: async ({ pageId, kind, params }) => {
    if (kind === 'fill') { records.get(pageId).value = params.value; effects.push(pageId); sequence.push(pageId); }
    else businessWrites++;
    return { result: Promise.resolve({ outcome: 'completed' }) };
  },
};
const definition = {
  accountScope, task: 'Fill local value and review, never submit', verificationId: 'local-review-fixture', taskSourceHashes,
  verifyAccount: async () => accountScope,
  verifyReview: async ({ pageId }) => {
    if (reviewGate) {
      const gate = reviewGate;
      reviewGate = null;
      gate.entered.resolve();
      await gate.resume.promise;
    }
    return { completed: records.get(pageId).value === 'same-value' };
  },
  disclosurePolicy: { origin, intermediateClicks: [], fields: [
    { kind: 'fill', slot: 'name', locator: ['textbox', 'Name', 'input', 'text'] },
  ] },
  planner: { identity: { model: 'scripted' }, next: async ({ observation }) => {
    plannerCalls++;
    return observation.elements[0].value
      ? { tool: 'finish', input: { summary: 'Review' } }
      : { tool: 'act', input: { kind: 'fill', handle: 'name', slot: 'name' } };
  } },
  reviewBatch: { maxItems: 3, maxWallMs: 5000,
    verifyRecord: async ({ pageId, expectedRecordId }) => (wrongRecord ?? records.get(pageId).id) === expectedRecordId,
    authorizeReadOnlyStep: async ({ step }) => !denied && step.kind === 'fill' && step.locator[1] === 'Name',
  },
};
const workflows = new WorkflowStore({ directory: join(root, 'workflows'), ownerScope: 'fixture',
  limits: { maxNodes: 32, maxEdges: 32, maxSteps: 8 }, maxBytes: 100000, lockWaitMs: 200, lockRetryMs: 5 });
const stateDir = join(root, 'controller');
const controller = new WorkspaceController({ stateDir, service, config, workflowStore: workflows,
  workflowTasks: new Map([[template, definition], ['not-opted-in', { ...definition, reviewBatch: null }]]) });
const data = { name: 'same-value' };
const gate = () => ({ entered: Promise.withResolvers(), resume: Promise.withResolvers() });
let closed = false;
try {
  const { id } = await controller.create({ goal: 'Review test records' });
  const teach = await controller.runPersonalWorkflow(id, { template, mode: 'learn', pageId: 'teach', inputs: data });
  const taught = await teach.done;
  assert.equal(taught.completed, true);
  const pin = (await workflows.checkout({ accountScope, template })).versionId;
  const input = { template, versionId: pin, budgetMs: 4000, items: [
    { recordId: 'A', pageId: 'A', inputs: data }, { recordId: 'B', pageId: 'B', inputs: data },
  ] };
  await assert.rejects(controller.runPersonalWorkflowBatch(id, { ...input, template: 'not-opted-in' }),
    { code: 'batch-review-policy-required' });
  await assert.rejects(controller.runPersonalWorkflowBatch(id, { ...input, items: [input.items[0], input.items[0]] }),
    { code: 'batch-invalid-item' });
  const beforePlanner = plannerCalls;
  effects.length = 0; sequence.length = 0;
  // Serial through the whole child cleanup, not just through reaching the result.
  const pending = gate();
  finalizerGate = pending;
  const batch = await controller.runPersonalWorkflowBatch(id, input);
  await pending.entered.promise;
  assert.deepEqual(effects, ['A']);
  // The durable workspace reservation also appears to an independent journal reader.
  const journalReader = new (controller.reviewBatches.constructor)(join(stateDir, 'review-batches'));
  assert.throws(() => journalReader.assertAdmission(id), { code: 'batch-owns-workspace' });
  assert.equal(journalReader.read(id).items[1].status, 'pending');
  const competing = controller.runPersonalWorkflow(id, { template, pageId: 'B', inputs: data, mode: 'reuse' });
  competing.catch(() => {});
  pending.resume.resolve();
  await assert.rejects(competing, { code: 'batch-owns-workspace' });
  const receipt = await batch.done;
  assert.equal(receipt.status, 'reviewed');
  assert.deepEqual(sequence, ['A', 'cleanup', 'B', 'cleanup']);
  assert.deepEqual(effects, ['A', 'B']);
  assert.equal(businessWrites, 0);
  assert.equal(plannerCalls, beforePlanner);
  assert.notEqual(receipt.items[0].recordDigest, receipt.items[1].recordDigest);
  assert.notEqual(receipt.items[0].attemptId, receipt.items[1].attemptId);
  const retained = workflows.readAttempts();
  for (const row of receipt.items) {
    assert.equal(row.status, 'reviewed');
    assert.equal(row.receiptStored, true);
    assert.equal(retained.find(a => a.runId === row.attemptId)?.execution?.reviewVerified, true);
  }
  assert.equal((await workflows.checkout({ accountScope, template })).versionId, pin);
  const [journalName] = readdirSync(join(stateDir, 'review-batches'));
  assert.ok(!readFileSync(join(stateDir, 'review-batches', journalName), 'utf8').includes('same-value'));
  const reset = () => { for (const key of ['A', 'B']) records.get(key).value = ''; effects.length = 0; };
  reset();
  const stale = await (await controller.runPersonalWorkflowBatch(id, { ...input, versionId: randomUUID() })).done;
  assert.equal(stale.failureCode, 'batch-version-mismatch');
  assert.deepEqual(effects, []);
  assert.equal(stale.items[1].status, 'pending');
  wrongRecord = 'B';
  const wrong = await (await controller.runPersonalWorkflowBatch(id, input)).done;
  assert.equal(wrong.failureCode, 'batch-record-mismatch');
  assert.deepEqual(effects, []);
  wrongRecord = null;
  denied = true;
  const refused = await (await controller.runPersonalWorkflowBatch(id, input)).done;
  assert.equal(refused.status, 'stopped');
  assert.equal(refused.items[1].status, 'pending');
  assert.deepEqual(effects, []);
  assert.equal(plannerCalls, beforePlanner);
  denied = false;
  const policyCheck = gate();
  reviewGate = policyCheck;
  const cancellable = await controller.runPersonalWorkflowBatch(id, input);
  await policyCheck.entered.promise;
  await controller.takeOver(id);
  assert.equal(controller.reviewBatchStatus(id).status, 'cancelling');
  await assert.rejects(controller.runPersonalWorkflowBatch(id, input));
  policyCheck.resume.resolve();
  const cancelled = await cancellable.done;
  assert.equal(cancelled.status, 'cancelled');
  assert.equal(cancelled.items[1].status, 'pending');
  assert.deepEqual(effects, ['A']);
  reset();
  const budgetCheck = gate();
  reviewGate = budgetCheck;
  const short = await controller.runPersonalWorkflowBatch(id, { ...input, budgetMs: 150 });
  await budgetCheck.entered.promise;
  await delay(170);
  budgetCheck.resume.resolve();
  const expired = await short.done;
  assert.equal(expired.status, 'stopped');
  assert.equal(expired.failureCode, 'batch-deadline');
  assert.equal(expired.items[1].status, 'pending');
  assert.deepEqual(effects, ['A']);
  reset();
  const duringCleanup = gate();
  finalizerGate = duringCleanup;
  const handback = await controller.runPersonalWorkflowBatch(id, input);
  await duringCleanup.entered.promise;
  const takeover = controller.takeOver(id);
  duringCleanup.resume.resolve();
  await takeover;
  const cancelledOnHandback = await handback.done;
  assert.equal(cancelledOnHandback.status, 'cancelled');
  assert.equal(cancelledOnHandback.items[1].status, 'pending');
  assert.deepEqual(effects, ['A']);
  reset();
  failCleanup = true;
  const cleanupFailure = await (await controller.runPersonalWorkflowBatch(id, input)).done;
  assert.equal(cleanupFailure.status, 'needs-attention');
  assert.equal(cleanupFailure.failureCode, 'batch-child-cleanup-failed');
  assert.equal(currentOwner, 'human', 'A failed revocation must not prevent the independent ownership fence');
  assert.equal(grants.size, 1);
  assert.equal(cleanupFailure.items[0].receiptStored, true);
  assert.equal(cleanupFailure.items[1].status, 'pending');
  assert.deepEqual(effects, ['A']);
  await assert.rejects(controller.runPersonalWorkflow(id, { template, pageId: 'B', inputs: data, mode: 'reuse' }),
    { code: 'batch-owns-workspace' });
  await controller.takeOver(id);
  assert.equal(grants.size, 0);
  assert.equal(controller.reviewBatchStatus(id).status, 'interrupted');
  reset();
  failedAgentReply = true;
  const setupFailure = await (await controller.runPersonalWorkflowBatch(id, input)).done;
  assert.equal(setupFailure.failureCode, 'fixture-assign-lost');
  assert.equal(setupFailure.status, 'stopped');
  assert.equal(currentOwner, 'human');
  assert.equal(grants.size, 0);
  assert.deepEqual(effects, []);
  failedAgentReply = true;
  failCleanup = true;
  failHumanFence = true;
  const unsafe = await (await controller.runPersonalWorkflowBatch(id, input)).done;
  assert.equal(unsafe.status, 'needs-attention');
  assert.equal(unsafe.failureCode, 'workflow-setup-cleanup-failed');
  assert.equal(unsafe.items[1].status, 'pending');
  assert.equal(currentOwner, 'agent');
  assert.equal(grants.size, 1);
  assert.deepEqual(effects, []);
  await assert.rejects(controller.takeOver(id), /failed ownership fence/);
  assert.equal(controller.reviewBatchStatus(id).status, 'needs-attention');
  failHumanFence = false;
  await controller.takeOver(id);
  assert.equal(controller.reviewBatchStatus(id).status, 'interrupted');
  assert.equal(currentOwner, 'human');
  assert.equal(grants.size, 0);

  const crashed = await controller.reviewBatches.reserve(id, { ...input, manifest: input.items });
  await controller.reviewBatches.setItem(id, crashed.id, 0, 'running');
  await controller.close();
  closed = true;
  const resumed = new WorkspaceController({ stateDir, service, config, workflowStore: workflows });
  await resumed.restore();
  const interrupted = resumed.reviewBatchStatus(id);
  assert.equal(interrupted.status, 'interrupted');
  assert.deepEqual(interrupted.items.map(x => x.status), ['interrupted', 'pending']);
  // The controller must release resources even when observing a rejected child during shutdown.
  const rejects = Promise.withResolvers();
  resumed.active.set(id, { done: rejects.promise, controller: new AbortController() });
  let released = 0;
  const shutdown = resumed.close({ release: async () => { released++; return {}; } });
  rejects.reject(Error('fixture child rejection'));
  await assert.rejects(shutdown, { name: 'AggregateError' });
  assert.equal(released, 1);
  const reopening = new WorkspaceController({ stateDir, service, config, workflowStore: workflows });
  await reopening.close();
  assert.equal(businessWrites, 0);
  console.log('ok: serial guarded review, exact-version and record refusal, durable receipts, takeover, deadline and restart fencing');
} finally {
  if (!closed) await controller.close();
  rmSync(root, { recursive: true, force: true });
}
