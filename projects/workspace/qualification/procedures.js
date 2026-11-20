// Fawn workspace qualification — case procedures.
//
// Each frozen case names one procedure. A procedure drives the real service host through the
// declared failure location and records what callers saw. It asserts nothing: the validator
// compares these records, the replayed journal and the fixture's own logs with the frozen
// expectations.

import { copyFileSync, readFileSync, writeFileSync } from 'node:fs';
import { summarizeAction } from './summaries.js';

const OWNER_B = 'agent-b';
// Recovery workflows rerun under a derived run identity; action ids are never reused.
const RECOVERY_RUN_SUFFIX = Object.freeze({ form: '-resubmit', export: '-resume' });
const CORRUPTED_OWNER = 'agent-z';

/** Hold the workflow's effect at the fixture, kill the host while it is held, then release it. */
async function crashWhileEffectHeld(ctx, owner, runId, taskOptions = {}) {
  const held = ctx.site.hold(ctx.wf.effectRequest);
  const running = ctx.startWorkflow(owner, runId, { task: taskOptions });
  await held.reached;
  const crash = await ctx.kill(running);
  held.release();
  return crash;
}

async function openSubmissionsAndReconcile(ctx, owner, runId, effectId) {
  const observed = await ctx.host.call('observe', ctx.identity(owner));
  await ctx.host.submitAndWait({
    ...ctx.identity(owner),
    actionId: `${runId}-open-submissions`,
    authorizedIntent: ctx.wf.intent,
    kind: 'navigate',
    target: { url: `${ctx.origin}/submissions` },
    observationVersion: observed.observationVersion,
  });
  const task = ctx.task(runId);
  return summarizeAction(await ctx.host.call('reconcile', {
    ...ctx.identity(owner),
    actionId: effectId,
    method: 'application-state',
    effectPresentWhen: [{
      kind: 'element-text-includes',
      selector: '#submissions',
      value: `${task.fields.name} ${task.fields.email}`,
    }],
  }));
}

const PROCEDURES = Object.freeze({
  async 'run-workflow'(ctx) {
    const { owner } = await ctx.setup();
    const runId = ctx.runId(1);
    ctx.actionRefs.effect = ctx.effectId(runId);
    ctx.record('workflow', await ctx.workflow(owner, runId, { fault: ctx.caseFault() }));
    await ctx.inspect();
    await ctx.close();
  },

  async 'stale-observation'(ctx) {
    const { owner } = await ctx.setup();
    // A prior version exists, so the stale citation names a real, superseded observation.
    await ctx.host.call('observe', ctx.identity(owner));
    ctx.record('workflow', await ctx.workflow(owner, ctx.runId(1), { fault: { kind: 'stale-observation' } }));
    await ctx.inspect();
    await ctx.close();
  },

  async 'stale-owner-restart'(ctx) {
    const { owner: ownerA, adminCredential } = await ctx.setup();
    const ownerB = await ctx.assign(adminCredential, OWNER_B);
    ctx.record('staleWorkflow', await ctx.workflow(ownerB, ctx.runId(1), {
      fault: { kind: 'stale-owner', owner: ctx.identity(ownerA) },
    }));
    await ctx.close();
    await ctx.start();
    ctx.record('staleObserveAfterRestart', await ctx.settle(ctx.host.call('observe', ctx.identity(ownerA))));
    const runId = ctx.runId(2);
    ctx.actionRefs.effect = ctx.effectId(runId);
    ctx.record('restartedWorkflow', await ctx.workflow(ownerB, runId));
    await ctx.inspect();
    await ctx.close();
  },

  async 'failure-before-dispatch'(ctx) {
    const { owner } = await ctx.setup();
    await ctx.close();
    const runId = ctx.runId(1);
    const effectId = ctx.effectId(runId);
    ctx.actionRefs.effect = effectId;
    await ctx.start({ crash: { hook: 'afterIntentPersisted', actionIdSuffix: ctx.wf.effectActionSuffix } });
    ctx.record('crash', await ctx.kill(ctx.startWorkflow(owner, runId), { killedByHost: true }));
    await ctx.start();
    ctx.record('afterRestart', await ctx.action(owner, effectId));
    let retryRun = ctx.runId(2);
    if (ctx.workflowName === 'form') {
      ctx.record('implicitRetry', await ctx.workflow(owner, retryRun));
      retryRun = ctx.runId(3);
    }
    ctx.actionRefs.retryEffect = ctx.effectId(retryRun);
    ctx.record('retry', await ctx.workflow(owner, retryRun, {
      task: ctx.workflowName === 'form' ? { resubmissionOf: effectId } : {},
    }));
    await ctx.inspect();
    await ctx.close();
  },

  async 'failure-after-effect-started'(ctx) {
    const { owner, adminCredential } = await ctx.setup();
    const effectId = ctx.effectId(ctx.runId(1));
    ctx.actionRefs.effect = effectId;
    ctx.record('crash', await crashWhileEffectHeld(ctx, owner, ctx.runId(1)));
    await ctx.start();
    ctx.record('afterRestart', await ctx.action(owner, effectId));
    await ctx.kill();
    await ctx.start();
    ctx.record('afterSecondRestart', await ctx.action(owner, effectId));
    const ownerB = await ctx.assign(adminCredential, OWNER_B);
    ctx.record('handoff', ctx.outstandingSummary(ownerB.outstanding, { effect: effectId }));
    if (ctx.workflowName === 'form') {
      ctx.record('resubmitBeforeReconcile', await ctx.workflow(ownerB, ctx.runId(2), { task: { resubmissionOf: effectId } }));
      ctx.record('reconcile', await openSubmissionsAndReconcile(ctx, ownerB, ctx.runId(3), effectId));
      ctx.record('resubmitAfterReconcile', await ctx.workflow(ownerB, ctx.runId(4), { task: { resubmissionOf: effectId } }));
    } else {
      ctx.record('rerun', await ctx.workflow(ownerB, ctx.runId(2)));
    }
    await ctx.inspect();
    await ctx.close();
  },

  async 'failure-after-completion'(ctx) {
    const { owner } = await ctx.setup();
    await ctx.close();
    const effectId = ctx.effectId(ctx.runId(1));
    ctx.actionRefs.effect = effectId;
    await ctx.start({ crash: { hook: 'afterOutcome', actionIdSuffix: ctx.wf.effectActionSuffix } });
    ctx.record('crash', await ctx.kill(ctx.startWorkflow(owner, ctx.runId(1)), { killedByHost: true }));
    await ctx.start();
    ctx.record('afterRestart', await ctx.action(owner, effectId));
    const includesEffect = async () => ({
      includesEffect: (await ctx.host.call('outstanding', ctx.identity(owner))).some((entry) => entry.actionId === effectId),
    });
    ctx.record('outstandingBeforeAcknowledgment', await includesEffect());
    await ctx.host.call('acknowledge', { ...ctx.identity(owner), actionId: effectId });
    ctx.record('outstandingAfterAcknowledgment', await includesEffect());
    if (ctx.workflowName === 'form') {
      ctx.record('resubmit', await ctx.workflow(owner, ctx.runId(2), { task: { resubmissionOf: effectId } }));
    }
    // Journal-only recovery is deliberately lazy. Obtain a genuine read-only
    // observation before requiring live browser image/socket evidence.
    await ctx.host.call('observe', ctx.identity(owner));
    await ctx.inspect();
    await ctx.close();
  },

  async 'queue-behind-held-effect'(ctx) {
    const { owner, adminCredential } = await ctx.setup();
    const effectId = ctx.effectId(ctx.runId(1));
    ctx.actionRefs.effect = effectId;
    const queuedId = `${ctx.runId(2)}-marker`;
    ctx.actionRefs.queued = queuedId;
    await ctx.host.queueBehindEffect({
      actionIdSuffix: ctx.wf.effectActionSuffix,
      queued: {
        ...ctx.identity(owner),
        actionId: queuedId,
        authorizedIntent: ctx.wf.intent,
        kind: 'navigate',
        target: { url: `${ctx.origin}/marker/queued` },
      },
    });
    const held = ctx.site.hold(ctx.wf.effectRequest);
    const running = ctx.startWorkflow(owner, ctx.runId(1));
    await held.reached;
    ctx.record('queuedAdmission', await ctx.host.awaitAdmission(queuedId));
    if (ctx.caseSpec.interruption === 'handoff') {
      const ownerB = await ctx.assign(adminCredential, OWNER_B);
      ctx.record('interruption', {
        ...ctx.outstandingSummary(ownerB.outstanding, { effect: effectId, queued: queuedId }),
        isAtomic: ownerB.boundary.isAtomic,
      });
    } else {
      await ctx.host.call('revokeAuthorization', {
        workspaceId: owner.workspaceId,
        adminCredential,
        grantId: ctx.grantId(owner.ownerId),
      });
    }
    held.release();
    ctx.record('workflow', await running);
    ctx.record('queued', summarizeAction(await ctx.host.awaitAction(queuedId)));
    if (ctx.caseSpec.interruption === 'handoff') {
      ctx.record('oldOwnerObserve', await ctx.settle(ctx.host.call('observe', ctx.identity(owner))));
    }
    await ctx.inspect();
    await ctx.close();
  },

  async 'handoff-race'(ctx) {
    const { owner: first, adminCredential } = await ctx.setup();
    let owner = first;
    const iterations = [];
    for (const [index, iteration] of ctx.caseSpec.race.iterations.entries()) {
      const runId = ctx.runId(index + 1);
      ctx.actionRefs[`race-${index}`] = ctx.effectId(runId);
      const raced = await ctx.host.raceWorkflow({
        name: ctx.workflowName,
        owner: ctx.identity(owner),
        task: ctx.task(runId, { subjectSuffix: `race-${index}` }),
        race: {
          order: iteration.order,
          delayMs: iteration.delayMs,
          actionIdSuffix: ctx.wf.effectActionSuffix,
          adminCredential,
          nextOwnerId: owner.ownerId === OWNER_B ? ctx.owners[0] : OWNER_B,
        },
      });
      const handoff = raced.handoff.value;
      iterations.push({
        order: iteration.order,
        delayMs: iteration.delayMs,
        effectReached: raced.effectReached,
        handoffAfterWorkflow: raced.handoffAfterWorkflow,
        workflow: ctx.summarizeSettled(raced.outcome),
        handoffError: raced.handoff.error ?? null,
        handoffGeneration: handoff?.ownerGeneration ?? null,
        handoffDisclosed: handoff ? ctx.outstandingSummary(handoff.outstanding, { effect: ctx.effectId(runId) }).effect : null,
      });
      if (!handoff) break;
      owner = { workspaceId: owner.workspaceId, ...handoff };
    }
    ctx.record('race', iterations);
    await ctx.inspect();
    await ctx.close();
  },

  async 'mutation-surface'(ctx) {
    const { owner } = await ctx.setup();
    const runId = ctx.runId(1);
    ctx.actionRefs.effect = ctx.effectId(runId);
    ctx.record('workflow', await ctx.workflow(owner, runId));
    ctx.record('surface', await ctx.host.surface(ctx.identity(owner)));
    const inspection = await ctx.inspect();
    ctx.record('endpoints', {
      listeningTcpSockets: inspection.listeningTcpSockets,
      devToolsActivePortFiles: inspection.devToolsActivePortFiles,
    });
    ctx.record('unsupportedKind', await ctx.workflow(owner, ctx.runId(2), {
      fault: { kind: 'effect-kind', actionIdSuffix: ctx.wf.effectActionSuffix, actionKind: 'evaluate-script' },
    }));
    await ctx.close();
  },

  async 'external-idempotency'(ctx) {
    const { owner } = await ctx.setup();
    const localRun = ctx.runId(1);
    ctx.record('localActionIdKey', await ctx.workflow(owner, localRun, {
      task: { externalIdempotencyKey: ctx.effectId(localRun) },
    }));
    const key = `reference-${ctx.token}`;
    const keyed = { reference: key, externalIdempotencyKey: key };
    const effectId = ctx.effectId(ctx.runId(2));
    ctx.actionRefs.effect = effectId;
    ctx.record('crash', await crashWhileEffectHeld(ctx, owner, ctx.runId(2), keyed));
    await ctx.start();
    ctx.record('afterRestart', await ctx.action(owner, effectId));
    ctx.record('reconcile', summarizeAction(await ctx.host.call('reconcile', {
      ...ctx.identity(owner),
      actionId: effectId,
      method: 'external-idempotency',
    })));
    ctx.record('keylessResubmit', await ctx.workflow(owner, ctx.runId(3), {
      task: { reference: key, resubmissionOf: effectId },
    }));
    ctx.actionRefs.retryEffect = ctx.effectId(ctx.runId(4));
    ctx.record('keyedResubmit', await ctx.workflow(owner, ctx.runId(4), { task: { ...keyed, resubmissionOf: effectId } }));
    await ctx.inspect();
    await ctx.close();
  },

  async 'human-review'(ctx) {
    const { owner, adminCredential } = await ctx.setup();
    const effectId = ctx.effectId(ctx.runId(1));
    ctx.actionRefs.effect = effectId;
    ctx.record('crash', await crashWhileEffectHeld(ctx, owner, ctx.runId(1)));
    await ctx.start();
    const ownerB = await ctx.assign(adminCredential, OWNER_B);
    ctx.record('handoff', ctx.outstandingSummary(ownerB.outstanding, { effect: effectId }));
    ctx.record('review', summarizeAction(await ctx.host.call('reconcile', {
      ...ctx.identity(ownerB),
      actionId: effectId,
      method: 'human-review',
    })));
    ctx.record('resubmitDuringReview', await ctx.workflow(ownerB, ctx.runId(2), { task: { resubmissionOf: effectId } }));
    // The reviewer decides from the application's own receipts, not from the service's records.
    const subject = ctx.task(ctx.runId(1)).fields.name;
    const present = ctx.site.receipts.some((receipt) => receipt.fields.name === subject);
    ctx.record('decision', summarizeAction(await ctx.host.call('decideHumanReview', {
      workspaceId: owner.workspaceId,
      adminCredential,
      actionId: effectId,
      decision: present ? 'effect-present' : 'effect-absent',
      note: `fixture receipts ${present ? 'contain' : 'do not contain'} ${subject}`,
    })));
    ctx.record('resubmitAfterDecision', await ctx.workflow(ownerB, ctx.runId(3), { task: { resubmissionOf: effectId } }));
    await ctx.inspect();
    await ctx.close();
  },

  async 'recover-after-crash'(ctx) {
    const { owner } = await ctx.setup();
    if (ctx.caseSpec.seedReceipts) await fetch(`${ctx.origin}/control/seed?count=${ctx.caseSpec.seedReceipts}`);
    const runId = ctx.runId(1);
    const effectId = ctx.effectId(runId);
    ctx.actionRefs.effect = effectId;
    ctx.actionRefs.resubmission = ctx.effectId(`${runId}${RECOVERY_RUN_SUFFIX[ctx.workflowName]}`);
    if (ctx.caseSpec.crashAt === 'while-effect-held') {
      ctx.record('crash', await crashWhileEffectHeld(ctx, owner, runId));
    } else {
      await ctx.close();
      await ctx.start({ crash: { hook: ctx.caseSpec.crashAt, actionIdSuffix: ctx.wf.effectActionSuffix } });
      ctx.record('crash', await ctx.kill(ctx.startWorkflow(owner, runId), { killedByHost: true }));
    }
    await ctx.start();
    ctx.record('afterRestart', await ctx.action(owner, effectId));
    ctx.record('recovery', await ctx.recover(owner, runId));
    await ctx.inspect();
    await ctx.close();
  },

  async 'authority-unavailable'(ctx) {
    await ctx.setup();
    ctx.record('lockedOpen', await ctx.settle(ctx.startDetached()));
    await ctx.close();
    copyFileSync(ctx.journalPath, ctx.evidencePath('journal.jsonl'));
    writeFileSync(ctx.journalPath, readFileSync(ctx.journalPath, 'utf8').replace(ctx.owners[0], CORRUPTED_OWNER));
    copyFileSync(ctx.journalPath, ctx.evidencePath('corrupt-journal.jsonl'));
    ctx.evidence.journal = 'journal.jsonl';
    ctx.evidence.corruptJournal = 'corrupt-journal.jsonl';
    ctx.record('corruptOpen', await ctx.settle(ctx.startDetached()));
  },
});

export { PROCEDURES };
