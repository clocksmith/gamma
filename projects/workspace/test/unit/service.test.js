// Service authority, dispatch-time checks, handoff and uncertain-outcome rules (fake adapter).
import assert from 'node:assert/strict';
import { loadServiceConfig } from '../../src/config.js';
import { createOwnerSession, findElement } from '../../src/workflows/owner-session.js';
import { FORM_INTENT, ORIGIN, WORKSPACE_ID, setupWorkspace } from '../support/harness.js';

const FORM_URL = `${ORIGIN}/form`;
const DONE = { completedWhen: [{ kind: 'element-present', selector: '#receipt' }] };
const config = loadServiceConfig();

function navigateSpec(actionId, url = FORM_URL) {
  return { actionId, authorizedIntent: FORM_INTENT, kind: 'navigate', target: { url } };
}

async function openForm(session, actionId) {
  const record = await session.act(await session.observe(), navigateSpec(actionId));
  assert.equal(record.outcome, 'completed', JSON.stringify(record));
  return session.observe();
}

function submitSpec(observation, actionId, extra = {}) {
  return {
    actionId,
    authorizedIntent: FORM_INTENT,
    kind: 'submit',
    target: findElement(observation, (element) => element.selector === '#send', 'send'),
    effect: { external: true, effectKey: 'contact-once', ...extra.effect },
    completion: DONE,
    ...extra.spec,
  };
}

async function rejects(promise, code) {
  await assert.rejects(promise, (error) => {
    assert.equal(error.code, code, error.message);
    return true;
  });
}

// Happy path and admission refusals.
{
  const { service, session, receiptsPath, adapter } = await setupWorkspace();
  const form = await openForm(session, 'nav-1');
  const filled = await session.act(form, {
    actionId: 'fill-1',
    authorizedIntent: FORM_INTENT,
    kind: 'fill',
    target: findElement(form, (element) => element.selector === '#name', 'name'),
    params: { value: 'Ada' },
  });
  assert.equal(filled.outcome, 'completed');
  assert.equal(filled.outcomeBasis, 'value-verified');
  const ready = await session.observe();
  const forged = createOwnerSession(service, { ...session.identity, ownerCredential: 'forged' });
  await rejects(forged.submit(ready, submitSpec(ready, 'forged')), 'unauthenticated');
  await rejects(session.submit(ready, { ...submitSpec(ready, 'intent'), authorizedIntent: 'form:other' }),
    'unauthorized-intent');
  await rejects(session.submit(ready, navigateSpec('evil', 'https://evil.test/')), 'unauthorized-target');
  await rejects(session.submit(ready, { ...submitSpec(ready, 'kind'), kind: 'evaluate-script' }),
    'unsupported-action-kind');
  await rejects(session.submit(ready, { ...submitSpec(ready, 'cond'), preconditions: [{ kind: 'always', value: 'x' }] }),
    'unsupported-condition');
  await rejects(session.submit(ready, { ...submitSpec(ready, 'nocompletion'), completion: undefined }),
    'invalid-command');
  await rejects(session.submit(ready, submitSpec(ready, 'local-key', { effect: { externalIdempotencyKey: 'local-key' } })),
    'invalid-idempotency-key');
  await rejects(session.submit(ready, { ...submitSpec(ready, 'ghost'), target: { selector: '#ghost', digest: 'x' } }),
    'unknown-target');
  await rejects(session.submit(ready, { ...submitSpec(ready, 'click-submit'), kind: 'click', effect: undefined, completion: undefined }),
    'invalid-command');
  const submitted = await session.act(ready, submitSpec(ready, 'submit-1'));
  assert.equal(submitted.outcome, 'completed', JSON.stringify(submitted));
  assert.equal(submitted.dispatchStatus, 'dispatched');
  assert.equal(adapter.receipts().length, 1);
  const done = await session.observe();
  await rejects(session.submit(done, navigateSpec('nav-1')), 'duplicate-action-id');
  await rejects(session.submit(done, submitSpec(ready, 'again', { spec: { observationVersion: done.observationVersion } })),
    'unknown-target');
  assert.equal((await session.acknowledge('submit-1')).acknowledgedGeneration, 1);
  await rejects(session.reconcile({ actionId: 'submit-1', method: 'human-review' }), 'reconciliation-not-applicable');
  assert.ok(receiptsPath);
  await service.close();
}

// Observation binding: stale and expired observations, page change before dispatch.
{
  const { service, session, clock, adapter } = await setupWorkspace({
    hooks: { afterIntentPersisted: (request) => request.actionId === 'changed' && adapter.mutate(WORKSPACE_ID) },
  });
  const first = await openForm(session, 'nav-1');
  const second = await session.observe();
  assert.equal(second.observationVersion, first.observationVersion + 1);
  await assert.rejects(session.submit(first, navigateSpec('stale')), error => {
    assert.equal(error.code, 'stale-observation');
    assert.deepEqual(error.details.neverDispatched, { code: 'stale-observation' });
    assert.equal(adapter.executions.includes('stale'), false);
    return true;
  });
  clock.advance(config.observation.maxAgeMs);
  await rejects(session.submit(second, navigateSpec('expired')), 'expired-observation');
  const current = await session.observe();
  const changed = await session.act(current, navigateSpec('changed'));
  assert.equal(changed.dispatchStatus, 'never-dispatched');
  assert.equal(changed.neverDispatched.code, 'stale-observation');
  assert.equal(changed.neverDispatched.stage, 'dispatch');
  assert.equal(adapter.executions.includes('changed'), false);
  await service.close();
}

// Regions scope: background changes outside the scoped regions do not stale an action; changes
// inside them do, and target identity is still checked.
{
  const { service, session, adapter } = await setupWorkspace();
  await openForm(session, 'nav-1');
  const scoped = (observation, actionId, selector, extra = {}) => ({
    actionId,
    authorizedIntent: FORM_INTENT,
    kind: 'fill',
    target: findElement(observation, (element) => element.selector === selector, selector),
    params: { value: 'Ada' },
    observationScope: { kind: 'regions', selectors: ['#contact'] },
    ...extra,
  });
  const observeContact = () => service.observe({ ...session.identity, regions: ['#contact'] });
  let observed = await observeContact();
  assert.ok(observed.regions['#contact']);
  await rejects(session.submit(observed, { ...scoped(observed, 'missing', '#name'),
    observationScope: { kind: 'regions', selectors: ['#absent'] } }), 'invalid-command');
  adapter.mutate(WORKSPACE_ID);
  const background = await session.act(observed, scoped(observed, 'background', '#name'));
  assert.equal(background.outcome, 'completed', JSON.stringify(background));
  observed = await observeContact();
  adapter.mutate(WORKSPACE_ID);
  const pageScope = await session.act(observed, { ...scoped(observed, 'page-scope', '#email'), observationScope: undefined });
  assert.equal(pageScope.neverDispatched.code, 'stale-observation');
  observed = await observeContact();
  adapter.mutate(WORKSPACE_ID, '#contact');
  const inside = await session.act(observed, scoped(observed, 'inside', '#email'));
  assert.equal(inside.neverDispatched.code, 'stale-observation');
  const unrecorded = await service.observe(session.identity);
  await rejects(session.submit(unrecorded, scoped(unrecorded, 'unrecorded-region', '#email')), 'invalid-command');
  observed = await observeContact();
  adapter.changeText(WORKSPACE_ID, '#other', 'Other (moved)');
  const target = await session.act(observed, {
    ...scoped(observed, 'target', '#other'),
    kind: 'click',
    params: undefined,
  });
  assert.equal(target.neverDispatched.code, 'target-changed');
  assert.deepEqual(adapter.executions, ['nav-1', 'background']);
  await service.close();
}

// Outline view: compact regions with stable handles, deltas against a base version, handle targets.
{
  const { service, session, adapter } = await setupWorkspace();
  await openForm(session, 'nav-1');
  const read = { ...session.identity, view: 'outline', regions: ['#contact'] };
  const first = await service.observe(read);
  assert.deepEqual(Object.keys(first).sort(), ['baseVersion', 'boundary', 'observationVersion', 'regionGroups', 'regions', 'url']);
  assert.equal(first.regions['#contact'].outline, '[hname] | [hemail] | [hsend]');
  adapter.mutate(WORKSPACE_ID);
  const delta = await service.observe({ ...read, sinceVersion: first.observationVersion });
  assert.deepEqual(delta.regions['#contact'], { unchanged: true });
  assert.equal(delta.baseVersion, first.observationVersion);
  const byHandle = await session.act(delta, {
    actionId: 'fill-by-handle',
    authorizedIntent: FORM_INTENT,
    kind: 'fill',
    target: { handle: 'hname' },
    params: { value: 'Ada' },
    observationScope: { kind: 'regions', selectors: ['#contact'] },
  });
  assert.equal(byHandle.outcome, 'completed', JSON.stringify(byHandle));
  const changed = await service.observe({ ...read, sinceVersion: delta.observationVersion });
  assert.ok(changed.regions['#contact'].outline);
  await rejects(session.submit(changed, {
    actionId: 'ghost-handle',
    authorizedIntent: FORM_INTENT,
    kind: 'click',
    target: { handle: 'hghost' },
  }), 'unknown-target');
  const navigated = await session.act(changed, {
    ...navigateSpec('nav-unscoped', `${ORIGIN}/other`),
    observationScope: { kind: 'regions', selectors: [] },
  });
  assert.equal(navigated.outcome, 'completed');
  await service.close();
}

// Link-following actions need a grant for the link's destination origin.
{
  const { service, session, adapter } = await setupWorkspace();
  const form = await openForm(session, 'nav-1');
  await rejects(session.submit(form, {
    actionId: 'follow-elsewhere',
    authorizedIntent: FORM_INTENT,
    kind: 'click',
    target: findElement(form, (element) => element.selector === '#elsewhere', 'elsewhere'),
  }), 'unauthorized-target');
  assert.deepEqual(adapter.executions, ['nav-1']);
  await service.close();
}

// Dispatch-time authorization and preconditions.
{
  let revoke = null;
  const { service, session, adminCredential, adapter } = await setupWorkspace({
    hooks: { afterIntentPersisted: (request) => request.actionId === 'revoked' && revoke() },
  });
  revoke = () => service.revokeAuthorization({ workspaceId: WORKSPACE_ID, adminCredential, grantId: 'grant-agent-a' });
  const form = await openForm(session, 'nav-1');
  const unmet = await session.act(form, {
    ...navigateSpec('unmet'),
    preconditions: [{ kind: 'input-value-equals', selector: '#name', value: 'Ada' }],
  });
  assert.equal(unmet.neverDispatched.code, 'precondition-unestablished');
  const revoked = await session.act(await session.observe(), navigateSpec('revoked'));
  assert.equal(revoked.neverDispatched.code, 'unauthorized-intent');
  assert.deepEqual(adapter.executions, ['nav-1']);
  await service.close();
}

// Handoff: queued old-owner commands end undispatched; in-flight effects are disclosed.
{
  const { service, session, adminCredential, adapter } = await setupWorkspace();
  const form = await openForm(session, 'nav-1');
  const release = adapter.holdNext();
  const inFlight = await session.submit(form, submitSpec(form, 'submit-held'));
  const queued = await session.submit(form, navigateSpec('queued'));
  await new Promise((resolve) => setImmediate(resolve));
  const handoff = await service.assignOwner({ workspaceId: WORKSPACE_ID, adminCredential, ownerId: 'agent-b' });
  assert.equal(handoff.ownerGeneration, 2);
  const byId = Object.fromEntries(handoff.outstanding.map((action) => [action.actionId, action]));
  assert.equal(byId['submit-held'].dispatchStatus, 'dispatched');
  assert.equal(byId['submit-held'].outcome, null);
  assert.equal(byId.queued.dispatchStatus, 'never-dispatched');
  assert.equal(byId.queued.neverDispatched.code, 'stale-owner-generation');
  assert.equal(handoff.boundary.isAtomic, false);
  assert.equal((await queued.result).neverDispatched.stage, 'handoff');
  release();
  const held = await inFlight.result;
  assert.equal(held.outcome, 'completed');
  assert.equal(held.ownerGeneration, 1);
  await rejects(session.observe(), 'stale-owner-generation');
  await rejects(session.submit(form, navigateSpec('late')), 'stale-owner-generation');
  const next = createOwnerSession(service, { workspaceId: WORKSPACE_ID, ...handoff });
  const fresh = await next.observe();
  await rejects(next.submit(fresh, navigateSpec('ungranted')), 'unauthorized-intent');
  await service.grantAuthorization({
    workspaceId: WORKSPACE_ID,
    adminCredential,
    grantId: 'grant-agent-b',
    ownerId: 'agent-b',
    intents: [FORM_INTENT],
    actionKinds: ['navigate'],
    targetOrigins: [ORIGIN],
  });
  assert.equal((await next.act(fresh, navigateSpec('granted'))).outcome, 'completed');
  assert.deepEqual(adapter.executions, ['nav-1', 'submit-held', 'granted']);
  await service.close();
}

// Unknown outcomes: no implicit resubmission; reconciliation records its basis.
{
  const { service, session, adapter, adminCredential } = await setupWorkspace();
  let form = await openForm(session, 'nav-1');
  adapter.failNext('browser connection lost');
  const lost = await session.act(form, submitSpec(form, 'submit-lost'));
  assert.equal(lost.outcome, 'unknown');
  assert.equal(lost.outcomeBasis, 'effect-exception');
  assert.equal(lost.isUncertain, true);
  form = await session.observe();
  await rejects(session.submit(form, submitSpec(form, 'retry')), 'effect-unresolved');
  await rejects(session.submit(form, submitSpec(form, 'retry', { spec: { resubmissionOf: 'submit-lost' } })),
    'effect-unresolved');
  const absent = await session.reconcile({
    actionId: 'submit-lost',
    method: 'application-state',
    effectPresentWhen: [{ kind: 'element-present', selector: '#receipt' }],
    effectAbsentWhen: [{ kind: 'url-equals', value: FORM_URL }],
  });
  assert.equal(absent.reconciliation.result, 'effect-absent');
  assert.equal(absent.outcome, 'unknown');
  assert.equal(absent.isUncertain, false);
  await rejects(session.submit(form, submitSpec(form, 'implicit')), 'resubmission-not-permitted');
  const resubmitted = await session.act(form, submitSpec(form, 'resubmit', { spec: { resubmissionOf: 'submit-lost' } }));
  assert.equal(resubmitted.outcome, 'completed');
  form = await openForm(session, 'nav-2');
  await rejects(session.submit(form, submitSpec(form, 'duplicate', { spec: { resubmissionOf: 'resubmit' } })),
    'effect-already-completed');
  assert.equal(adapter.receipts().length, 1);

  adapter.failNext('renderer crashed');
  const reviewed = await session.act(form, submitSpec(form, 'submit-review', { effect: { effectKey: 'second-form' } }));
  assert.equal(reviewed.outcome, 'unknown');
  assert.equal((await session.reconcile({ actionId: 'submit-review', method: 'human-review' })).reconciliation.result,
    'human-review-requested');
  form = await session.observe();
  await rejects(session.submit(form, submitSpec(form, 'too-soon', {
    effect: { effectKey: 'second-form' },
    spec: { resubmissionOf: 'submit-review' },
  })), 'effect-unresolved');
  await service.decideHumanReview({ workspaceId: WORKSPACE_ID, adminCredential, actionId: 'submit-review', decision: 'effect-present' });
  await rejects(session.submit(form, submitSpec(form, 'after-review', {
    effect: { effectKey: 'second-form' },
    spec: { resubmissionOf: 'submit-review' },
  })), 'effect-already-completed');

  adapter.failNext('timeout waiting for response');
  const keyed = await session.act(form, submitSpec(form, 'submit-keyed', {
    effect: { effectKey: 'third-form', externalIdempotencyKey: 'order-7781' },
  }));
  assert.equal(keyed.outcome, 'unknown');
  const permitted = await session.reconcile({ actionId: 'submit-keyed', method: 'external-idempotency' });
  assert.equal(permitted.isUncertain, true);
  form = await session.observe();
  await rejects(session.submit(form, submitSpec(form, 'keyless', {
    effect: { effectKey: 'third-form' },
    spec: { resubmissionOf: 'submit-keyed' },
  })), 'resubmission-not-permitted');
  const keyedRetry = await session.act(form, submitSpec(form, 'keyed-retry', {
    effect: { effectKey: 'third-form', externalIdempotencyKey: 'order-7781' },
    spec: { resubmissionOf: 'submit-keyed' },
  }));
  assert.equal(keyedRetry.outcome, 'completed');
  const outstanding = (await session.outstanding()).map((action) => action.actionId);
  assert.ok(outstanding.includes('submit-keyed'));
  await service.close();
}

// Timeouts are unknown, never failed.
{
  const shortTimeout = { ...config, dispatch: { ...config.dispatch, actionTimeoutMs: 100 } };
  const { service, session, adapter } = await setupWorkspace({ config: shortTimeout });
  const form = await openForm(session, 'nav-1');
  adapter.holdNext();
  const timed = await session.act(form, submitSpec(form, 'submit-timeout'));
  assert.equal(timed.outcome, 'unknown');
  assert.equal(timed.outcomeBasis, 'effect-timeout');
  await service.close();
}

// Workflow code reaches the browser only through the service API.
{
  const { service, session } = await setupWorkspace();
  assert.deepEqual(Object.keys(service), []);
  assert.equal('adapter' in service, false);
  assert.deepEqual(Object.keys(session).sort(),
    ['acknowledge', 'act', 'action', 'identity', 'observe', 'outstanding', 'reconcile', 'submit']);
  await service.close();
}

console.log('ok: service');
