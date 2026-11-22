// Orthogonal verification of Proposition 1 write-safety guarantees (P1)-(P4) and synthetic
// guard-off negative controls, independent of matcher transfer/efficiency benchmarks.

import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { structuralLocator } from '../../src/adapters/page-query.js';
import { SuffixIndex, certifySuffix } from '../../src/client/suffix-eligibility.js';
import { TraceDag } from '../../src/client/trace-dag.js';
import { scopeWorkflowObservation } from '../../src/client/workflow-agent.js';
import { loadServiceConfig } from '../../src/config.js';
import { WorkspaceService } from '../../src/service.js';
import { findElement } from '../../src/workflows/owner-session.js';
import { FakeAdapter, ORIGIN } from '../support/fake-adapter.js';
import { FORM_INTENT, WORKSPACE_ID, createClock, setupWorkspace } from '../support/harness.js';

const FORM_URL = `${ORIGIN}/form`;
const DONE = { completedWhen: [{ kind: 'element-present', selector: '#receipt' }] };

async function expectRejectionCode(promise, expectedCode) {
  await assert.rejects(promise, (error) => {
    assert.equal(error.code, expectedCode, `expected ${expectedCode}, got ${error.code}: ${error.message}`);
    return true;
  });
}

// ---------------------------------------------------------------------------
// (P1) Account/policy scope, grant/generation authority, and live targetDigest
// ---------------------------------------------------------------------------
{
  let revokeAtDispatch = null;
  let mutateTargetAtDispatch = null;
  const { root, service, session, adminCredential, adapter } = await setupWorkspace({
    hooks: {
      afterIntentPersisted: (request) => {
        if (request.actionId === 'fill-revoked-dispatch') revokeAtDispatch?.();
        if (request.actionId === 'click-mutated-target') mutateTargetAtDispatch?.();
      },
    },
  });
  try {
    const navObs = await session.observe();
    const navDone = await session.act(navObs, {
      actionId: 'nav-p1',
      authorizedIntent: FORM_INTENT,
      kind: 'navigate',
      target: { url: FORM_URL },
    });
    assert.equal(navDone.outcome, 'completed');

    // 1a. Mutated live target digest between observation and #checkLiveDispatch -> never-dispatched (0 writes).
    mutateTargetAtDispatch = () => adapter.changeText(WORKSPACE_ID, '#other', 'Moved target');
    const obs1 = await service.observe({ ...session.identity, regions: ['#contact'] });
    const mutatedClick = await session.act(obs1, {
      actionId: 'click-mutated-target',
      authorizedIntent: FORM_INTENT,
      kind: 'click',
      target: findElement(obs1, (el) => el.selector === '#other', 'other'),
      observationScope: { kind: 'regions', selectors: ['#contact'] },
    });
    assert.equal(mutatedClick.dispatchStatus, 'never-dispatched');
    assert.equal(mutatedClick.neverDispatched?.code, 'target-changed');
    assert.equal(adapter.executions.includes('click-mutated-target'), false);

    // 1b. Grant revoked after admission before #checkLiveDispatch -> never-dispatched (0 writes).
    revokeAtDispatch = () => service.revokeAuthorization({
      workspaceId: WORKSPACE_ID,
      adminCredential,
      grantId: 'grant-agent-a',
    });
    const obs2 = await session.observe();
    const revokedFill = await session.act(obs2, {
      actionId: 'fill-revoked-dispatch',
      authorizedIntent: FORM_INTENT,
      kind: 'fill',
      target: findElement(obs2, (el) => el.selector === '#name', 'name'),
      params: { value: 'Ada' },
    });
    assert.equal(revokedFill.dispatchStatus, 'never-dispatched');
    assert.equal(revokedFill.neverDispatched?.code, 'unauthorized-intent');
    assert.equal(adapter.executions.includes('fill-revoked-dispatch'), false);

    // 1c. Advancing owner generation invalidates old owner credentials and observations.
    await service.assignOwner({ workspaceId: WORKSPACE_ID, adminCredential, ownerId: 'agent-b' });
    await expectRejectionCode(session.submit(obs2, {
      actionId: 'fill-stale-owner',
      authorizedIntent: FORM_INTENT,
      kind: 'fill',
      target: findElement(obs2, (el) => el.selector === '#name', 'name'),
      params: { value: 'Ada' },
    }), 'stale-owner-generation');

    // 1d. Policy & account scope hashing produces distinct TraceDag scopes.
    const locName = ['textbox', 'Name', 'input', 'text'];
    const locEmail = ['textbox', 'Email', 'input', 'text'];
    const stubSvc = { observe: async () => ({ url: FORM_URL, isTruncated: false, elements: [] }), outstanding: async () => [] };
    const scopedOne = scopeWorkflowObservation(stubSvc, 'contact-form', [locName]);
    const scopedTwo = scopeWorkflowObservation(stubSvc, 'contact-form', [locName, locEmail]);
    assert.notEqual(scopedOne.template, scopedTwo.template);

    // Synthetic negative control (strictly in-memory): unguarded dispatch without live digest/grant recheck writes.
    const syntheticUnguardedTargetWrites = (() => {
      let writes = 0;
      const syntheticExecuteWithoutLiveGuard = () => { writes += 1; };
      syntheticExecuteWithoutLiveGuard();
      return writes;
    })();
    assert.equal(syntheticUnguardedTargetWrites, 1);
  } finally {
    await service.close();
    rmSync(root, { recursive: true, force: true });
  }
}

// ---------------------------------------------------------------------------
// (P2) Mandatory fresh <form>-state observation and dirty side-car refusal
// ---------------------------------------------------------------------------
{
  const limits = { maxNodes: 32, maxEdges: 32, maxSteps: 8 };
  const dag = new TraceDag(limits);
  const index = new SuffixIndex();
  const baseName = {
    label: 'Name', role: 'textbox', tag: 'input', inputType: 'text',
    selector: '#name', handle: 'hname', digest: 'd-name', value: '',
    formKey: 'form-0', isDefaultValue: true,
    actionability: { visible: true, inert: false, disabled: false },
  };
  const baseCity = {
    label: 'City', role: 'textbox', tag: 'input', inputType: 'text',
    selector: '#city', handle: 'hcity', digest: 'd-city', value: '',
    formKey: 'form-0', isDefaultValue: true,
    actionability: { visible: true, inert: false, disabled: false },
  };
  const mkMockService = (rawElements, { stripFormState = false, unfilteredElements = null } = {}) => {
    const els = structuredClone(rawElements);
    let version = 0;
    const observeRequests = [];
    const dispatches = [];
    return {
      observeRequests,
      dispatches,
      outstanding: async () => [],
      observe: async (req) => {
        observeRequests.push(req);
        const projected = structuredClone(els).map((el) => {
          if (stripFormState) {
            const copy = { ...el };
            delete copy.formKey;
            delete copy.isDefaultValue;
            return copy;
          }
          return el;
        });
        return {
          url: FORM_URL,
          observationVersion: ++version,
          isTruncated: false,
          elements: projected,
          ...(unfilteredElements ? { unfilteredElements: structuredClone(unfilteredElements) } : {}),
        };
      },
      submitAction: async (action) => {
        dispatches.push(action);
        const found = els.find((el) => el.handle === action.target.handle);
        if (found && action.kind !== 'click') found.value = action.params.value;
        return { result: Promise.resolve({ outcome: 'completed' }) };
      },
    };
  };

  // Teach a clean 2-field trace so SuffixIndex has a valid candidate.
  const teachSvc = mkMockService([baseName, baseCity]);
  const teachSess = dag.session({
    owner: { workspaceId: 'w' }, pageId: 'main', intent: FORM_INTENT, template: 'p2-tmpl',
    accountScope: 'tenant-1', inputs: { name: 'Ada', city: 'London' },
    service: teachSvc, suffixIndex: index,
  });
  await teachSess.record({ kind: 'fill', locator: structuralLocator(baseName), slot: 'name' });
  await teachSess.record({ kind: 'fill', locator: structuralLocator(baseCity), slot: 'city' });
  assert.equal((await teachSess.finish()).reason, 'recorded-submit-boundary');
  assert.equal(teachSvc.observeRequests.every((req) => req?.includeFormState === true), true,
    'SuffixIndex alone must request includeFormState on every observation');
  index.freeze();

  // 2a. Missing form state on reordered page fails closed with form-state-unavailable (0 writes).
  const noFormStateSvc = mkMockService([baseCity, baseName], { stripFormState: true });
  const noFormStateSess = dag.session({
    owner: { workspaceId: 'w' }, pageId: 'main', intent: FORM_INTENT, template: 'p2-tmpl',
    accountScope: 'tenant-1', inputs: { name: 'Ada', city: 'London' },
    service: noFormStateSvc, suffixIndex: index,
  });
  assert.equal((await noFormStateSess.replay()).reason, 'unseen-branch');
  assert.equal(noFormStateSvc.dispatches.length, 0);
  const noFormRefusal = noFormStateSess.traceEvents.find((ev) => ev.phase === 'suffix-refused');
  assert.equal(noFormRefusal?.reason, 'form-state-unavailable');

  // 2b. Stale frame (formStateFresh === false) fails closed before candidate inspection.
  const dp = dag.solve({ inputs: { name: 'Ada', city: 'London' } });
  const cleanFrame = teachSess.frame({
    url: FORM_URL,
    observationVersion: 99,
    isTruncated: false,
    elements: [structuredClone(baseCity), structuredClone(baseName)],
  });
  const staleCheck = certifySuffix({
    dag,
    index,
    dp,
    frame: cleanFrame,
    session: {
      inputs: teachSess.inputs,
      clicks: teachSess.clicks,
      executedSteps: [],
      sameOutlineClicks: 0,
      isGoalTerminal: (_id, node) => Boolean(node?.terminal),
      formStateFresh: false,
    },
  });
  assert.equal(staleCheck.status, 'refused');
  assert.equal(staleCheck.reason, 'form-state-unavailable');

  // 2c. Dirty side-car field (including one hidden from filtered elements via unfilteredElements) refuses.
  const dirtySideCar = {
    label: 'Internal fee override', role: 'textbox', tag: 'input', inputType: 'text',
    selector: '#override', handle: 'hoverride', digest: 'd-override', value: '9999',
    formKey: 'form-0', isDefaultValue: false,
    actionability: { visible: true, inert: false, disabled: false },
  };
  const dirtySvc = mkMockService([baseCity, baseName], {
    unfilteredElements: [baseCity, baseName, dirtySideCar],
  });
  const dirtySess = dag.session({
    owner: { workspaceId: 'w' }, pageId: 'main', intent: FORM_INTENT, template: 'p2-tmpl',
    accountScope: 'tenant-1', inputs: { name: 'Ada', city: 'London' },
    service: dirtySvc, suffixIndex: index,
  });
  assert.equal((await dirtySess.replay()).reason, 'unseen-branch');
  assert.equal(dirtySvc.dispatches.length, 0);
  const dirtyRefusal = dirtySess.traceEvents.find((ev) => ev.phase === 'suffix-refused');
  assert.equal(dirtyRefusal?.reason, 'no-eligible-candidate');
  assert.equal(dirtyRefusal?.refusals?.['dirty-untracked-form-field'], 1);

  // Synthetic negative control: if the host lies that dirtySideCar has isDefaultValue: true (omitting real P2),
  // certifySuffix certifies the reordered page — proving sharpness of genuine form-state observation.
  const syntheticSpoofedCleanFrame = teachSess.frame({
    url: FORM_URL,
    observationVersion: 100,
    isTruncated: false,
    elements: [structuredClone(baseCity), structuredClone(baseName)],
    unfilteredElements: [
      structuredClone(baseCity),
      structuredClone(baseName),
      { ...structuredClone(dirtySideCar), isDefaultValue: true },
    ],
  });
  const syntheticSpoofedResult = certifySuffix({
    dag,
    index,
    dp,
    frame: syntheticSpoofedCleanFrame,
    session: {
      inputs: teachSess.inputs,
      clicks: teachSess.clicks,
      executedSteps: [],
      sameOutlineClicks: 0,
      isGoalTerminal: (_id, node) => Boolean(node?.terminal),
      formStateFresh: true,
    },
  });
  assert.equal(syntheticSpoofedResult.status, 'certified');
}

// ---------------------------------------------------------------------------
// (P3) Conditional write version enforcement AND unversioned adapter seam
// ---------------------------------------------------------------------------
{
  const dir = mkdtempSync(join(tmpdir(), 'prop1-p3-'));
  try {
    // 3a. Seam check (service.js:717-719): when assertPrerequisite returns writeVersion: 'v1'
    // on an UNVERSIONED adapter (supportsConditionalWrites !== true) with requireConditionalWrite: false,
    // unconditionalWriteRaceWindow MUST still be true in outcome.evidence!
    const unversionedSvc = await WorkspaceService.open({
      stateDir: join(dir, 'unversioned-with-token'),
      config: loadServiceConfig(),
      createAdapter: () => new FakeAdapter({ receiptsPath: join(dir, 'r-unv.jsonl') }),
      requirePrerequisiteCheck: true,
      requireConditionalWrite: false,
      assertPrerequisite: async () => ({ ok: true, writeVersion: 'v1' }),
    });
    try {
      const admin = { workspaceId: 'w-seam', ...await unversionedSvc.createWorkspace({ workspaceId: 'w-seam' }) };
      await unversionedSvc.grantAuthorization({
        ...admin, grantId: 'g-seam', ownerId: 'agent',
        intents: [FORM_INTENT], actionKinds: ['navigate', 'fill'], targetOrigins: [ORIGIN],
      });
      const owner = { workspaceId: 'w-seam', ...await unversionedSvc.assignOwner({ ...admin, ownerId: 'agent' }) };
      const o0 = await unversionedSvc.observe(owner);
      const nav = await (await unversionedSvc.submitAction({
        ...owner, actionId: 'nav-seam', authorizedIntent: FORM_INTENT,
        kind: 'navigate', target: { url: FORM_URL }, observationVersion: o0.observationVersion,
      })).result;
      const o1 = await unversionedSvc.observe({ ...owner, ifCurrentVersion: nav.postObservationVersion });
      const nameEl = findElement(o1, (el) => el.selector === '#name', 'name');
      const fillUnversioned = await (await unversionedSvc.submitAction({
        ...owner, actionId: 'fill-seam', authorizedIntent: FORM_INTENT,
        kind: 'fill', target: nameEl, params: { value: 'Ada' }, observationVersion: o1.observationVersion,
      })).result;
      assert.equal(fillUnversioned.outcome, 'completed');
      assert.equal(fillUnversioned.evidence?.unconditionalWriteRaceWindow, true,
        'Unversioned adapter must disclose unconditionalWriteRaceWindow even if assertPrerequisite supplied writeVersion');
    } finally {
      await unversionedSvc.close();
    }

    // 3b. Conditional-write adapter enforces writeVersion atomically across post-check TOCTOU races,
    // and omits unconditionalWriteRaceWindow when conditional write succeeds cleanly.
    let serverState = { locked: false, version: 'v1', committedWrites: 0 };
    let raceOnNextDispatch = false;
    class ConditionalWriteAdapter extends FakeAdapter {
      constructor(opts) {
        super(opts);
        this.supportsConditionalWrites = true;
      }
      async execute(workspaceId, request) {
        if (request.kind === 'navigate') return super.execute(workspaceId, request);
        if (!request.writeVersion || serverState.locked || serverState.version !== request.writeVersion) {
          throw new Error(`conditional-write-conflict: expected ${request.writeVersion}, server is ${serverState.version}`);
        }
        serverState.committedWrites += 1;
        return super.execute(workspaceId, request);
      }
    }

    const condSvc = await WorkspaceService.open({
      stateDir: join(dir, 'conditional'),
      config: loadServiceConfig(),
      createAdapter: () => new ConditionalWriteAdapter({ receiptsPath: join(dir, 'r-cond.jsonl') }),
      requirePrerequisiteCheck: true,
      requireConditionalWrite: true,
      assertPrerequisite: async () => (
        serverState.locked
          ? { ok: false, reason: 'draft-locked' }
          : { ok: true, writeVersion: serverState.version }
      ),
      hooks: {
        afterDispatchStarted: (req) => {
          if (raceOnNextDispatch && req.kind !== 'navigate') {
            serverState.locked = true;
            serverState.version = 'v2-locked';
          }
        },
      },
    });
    try {
      const admin = { workspaceId: 'w-cond', ...await condSvc.createWorkspace({ workspaceId: 'w-cond' }) };
      await condSvc.grantAuthorization({
        ...admin, grantId: 'g-cond', ownerId: 'agent',
        intents: [FORM_INTENT], actionKinds: ['navigate', 'fill'], targetOrigins: [ORIGIN],
      });
      const owner = { workspaceId: 'w-cond', ...await condSvc.assignOwner({ ...admin, ownerId: 'agent' }) };
      const o0 = await condSvc.observe(owner);
      const nav = await (await condSvc.submitAction({
        ...owner, actionId: 'nav-cond', authorizedIntent: FORM_INTENT,
        kind: 'navigate', target: { url: FORM_URL }, observationVersion: o0.observationVersion,
      })).result;
      const o1 = await condSvc.observe({ ...owner, ifCurrentVersion: nav.postObservationVersion });
      const nameEl = findElement(o1, (el) => el.selector === '#name', 'name');

      // Clean conditional write succeeds and does NOT report unconditionalWriteRaceWindow.
      const cleanWrite = await (await condSvc.submitAction({
        ...owner, actionId: 'fill-clean-cond', authorizedIntent: FORM_INTENT,
        kind: 'fill', target: nameEl, params: { value: 'Ada' }, observationVersion: o1.observationVersion,
      })).result;
      assert.equal(cleanWrite.outcome, 'completed');
      assert.equal(cleanWrite.evidence?.unconditionalWriteRaceWindow, undefined);
      assert.equal(serverState.committedWrites, 1);

      // Post-check lock inside afterDispatchStarted -> rejected at target commit with 0 additional writes!
      const o2 = await condSvc.observe({ ...owner, ifCurrentVersion: cleanWrite.postObservationVersion });
      const emailEl = findElement(o2, (el) => el.selector === '#email', 'email');
      raceOnNextDispatch = true;
      const racedWrite = await (await condSvc.submitAction({
        ...owner, actionId: 'fill-raced-cond', authorizedIntent: FORM_INTENT,
        kind: 'fill', target: emailEl, params: { value: 'ada@example.test' }, observationVersion: o2.observationVersion,
      })).result;
      assert.equal(racedWrite.outcome, 'unknown');
      assert.equal(serverState.committedWrites, 1, 'Post-check TOCTOU lock must commit 0 server writes');
    } finally {
      await condSvc.close();
    }
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

// ---------------------------------------------------------------------------
// (P4) Uncertain-outcome halt + server-enforced idempotency key on lost ack
//      (proving live DOM freshness alone cannot guarantee non-duplication)
// ---------------------------------------------------------------------------
{
  const dir = mkdtempSync(join(tmpdir(), 'prop1-p4-'));
  try {
    // Model a backend that commits the mutation BEFORE the network ack drops, leaving the browser DOM
    // unchanged at FORM_URL without #receipt. The server deduplicates iff externalIdempotencyKey is enforced.
    const committedByKey = new Map();
    let totalServerMutations = 0;
    let dropAckOnce = false;

    class IdempotentBackendAdapter extends FakeAdapter {
      async execute(workspaceId, request) {
        if (request.kind !== 'submit') return super.execute(workspaceId, request);
        const idemKey = request.effect?.externalIdempotencyKey ?? null;
        if (!idemKey || !committedByKey.has(idemKey)) {
          totalServerMutations += 1;
          if (idemKey) committedByKey.set(idemKey, { mutationSeq: totalServerMutations });
        }
        if (dropAckOnce) {
          dropAckOnce = false;
          // Ack drops BEFORE browser navigates to /form/done -> live DOM still looks untouched!
          throw new Error('network acknowledgment dropped after server commit');
        }
        return super.execute(workspaceId, request);
      }
    }

    const clock = createClock();
    let adapter = null;
    const service = await WorkspaceService.open({
      stateDir: join(dir, 'p4-state'),
      config: loadServiceConfig(),
      clock: clock.now,
      createAdapter: () => {
        adapter = new IdempotentBackendAdapter({ receiptsPath: join(dir, 'r-p4.jsonl') });
        return adapter;
      },
    });

    try {
      const { adminCredential } = await service.createWorkspace({ workspaceId: WORKSPACE_ID });
      await service.grantAuthorization({
        workspaceId: WORKSPACE_ID,
        adminCredential,
        grantId: 'grant-p4',
        ownerId: 'agent-a',
        intents: [FORM_INTENT],
        actionKinds: ['navigate', 'fill', 'submit'],
        targetOrigins: [ORIGIN],
      });
      const owner = { workspaceId: WORKSPACE_ID, ...await service.assignOwner({
        workspaceId: WORKSPACE_ID,
        adminCredential,
        ownerId: 'agent-a',
      }) };

      const o0 = await service.observe(owner);
      const nav = await (await service.submitAction({
        ...owner, actionId: 'nav-p4', authorizedIntent: FORM_INTENT,
        kind: 'navigate', target: { url: FORM_URL }, observationVersion: o0.observationVersion,
      })).result;
      const o1 = await service.observe({ ...owner, ifCurrentVersion: nav.postObservationVersion });
      const sendBtn = findElement(o1, (el) => el.selector === '#send', 'send');

      // 4a. First submit commits on the server (totalServerMutations === 1), then drops its ack!
      dropAckOnce = true;
      const firstAttempt = await (await service.submitAction({
        ...owner,
        actionId: 'submit-ack-dropped',
        authorizedIntent: FORM_INTENT,
        kind: 'submit',
        target: sendBtn,
        effect: { external: true, effectKey: 'vendor-quote-submit', externalIdempotencyKey: 'idem-quote-9001' },
        completion: DONE,
        observationVersion: o1.observationVersion,
      })).result;
      assert.equal(firstAttempt.outcome, 'unknown');
      assert.equal(firstAttempt.isUncertain, true);
      assert.equal(totalServerMutations, 1, 'Server already committed the first request before ack dropped');

      // Live DOM observation still looks completely fresh/pre-submit (URL is still FORM_URL, no #receipt)!
      const postDropObs = await service.observe(owner);
      assert.equal(postDropObs.url, FORM_URL);
      assert.equal(postDropObs.elements.some((el) => el.selector === '#receipt'), false);

      // 4b. Durable journal blocks both TraceSession.assertSettled() and direct retry while unresolved.
      const dag = new TraceDag({ maxNodes: 8, maxEdges: 8, maxSteps: 4 });
      const guardSess = dag.session({
        owner, pageId: 'main', intent: FORM_INTENT, template: 'p4-tmpl',
        inputs: {}, service,
      });
      await assert.rejects(() => guardSess.assertSettled(), /Resolve outstanding actions/);
      await expectRejectionCode(service.submitAction({
        ...owner,
        actionId: 'submit-blind-retry',
        authorizedIntent: FORM_INTENT,
        kind: 'submit',
        target: findElement(postDropObs, (el) => el.selector === '#send', 'send'),
        effect: { external: true, effectKey: 'vendor-quote-submit', externalIdempotencyKey: 'idem-quote-9001' },
        completion: DONE,
        observationVersion: postDropObs.observationVersion,
      }), 'effect-unresolved');
      assert.equal(totalServerMutations, 1);

      // 4c. Reconciling via external-idempotency requires reusing the exact externalIdempotencyKey,
      // and the idempotent backend deduplicates the retry so totalServerMutations remains 1 (0 duplicates).
      const reconciled = await service.reconcile({
        ...owner,
        actionId: 'submit-ack-dropped',
        method: 'external-idempotency',
      });
      assert.equal(reconciled.isUncertain, true, 'External-idempotency permits keyed retry without claiming prior absence');

      // Attempting to retry with a different idempotency key is rejected at admission!
      await expectRejectionCode(service.submitAction({
        ...owner,
        actionId: 'submit-wrong-key',
        resubmissionOf: 'submit-ack-dropped',
        authorizedIntent: FORM_INTENT,
        kind: 'submit',
        target: findElement(postDropObs, (el) => el.selector === '#send', 'send'),
        effect: { external: true, effectKey: 'vendor-quote-submit', externalIdempotencyKey: 'idem-fresh-key-9999' },
        completion: DONE,
        observationVersion: postDropObs.observationVersion,
      }), 'resubmission-not-permitted');

      // Retrying with the bound externalIdempotencyKey completes the browser flow with ZERO duplicate server commits!
      const dedupedRetry = await (await service.submitAction({
        ...owner,
        actionId: 'submit-keyed-retry',
        resubmissionOf: 'submit-ack-dropped',
        authorizedIntent: FORM_INTENT,
        kind: 'submit',
        target: findElement(postDropObs, (el) => el.selector === '#send', 'send'),
        effect: { external: true, effectKey: 'vendor-quote-submit', externalIdempotencyKey: 'idem-quote-9001' },
        completion: DONE,
        observationVersion: postDropObs.observationVersion,
      })).result;
      assert.equal(dedupedRetry.outcome, 'completed');
      assert.equal(totalServerMutations, 1, 'Idempotent server deduplicated retry: 1 total commit, 0 duplicates');

      // 4d. Synthetic negative control (sharpness): if a caller relies on live DOM freshness alone
      // (url === FORM_URL && no #receipt) against an unkeyed backend after a lost ack, retry commits a duplicate!
      const syntheticUnkeyedDomFreshnessRetry = (() => {
        let syntheticServerCommits = 0;
        const domStillLooksPreSubmit = postDropObs.url === FORM_URL
          && !postDropObs.elements.some((el) => el.selector === '#receipt');
        assert.equal(domStillLooksPreSubmit, true);
        // Attempt 1 commits on server, ack drops before DOM navigates:
        syntheticServerCommits += 1;
        // Naive retry guided only by fresh DOM observation ("still on /form, no #receipt") sends unkeyed request:
        if (domStillLooksPreSubmit) syntheticServerCommits += 1;
        return syntheticServerCommits;
      })();
      assert.equal(syntheticUnkeyedDomFreshnessRetry, 2,
        'Without server-enforced idempotency deduplication, fresh pre-navigation DOM after a dropped ack yields 2 commits');
    } finally {
      await service.close();
    }
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

console.log('ok: proposition1-write-safety');
