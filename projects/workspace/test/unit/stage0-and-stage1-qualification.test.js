import assert from 'node:assert/strict';
import test from 'node:test';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { structuralLocator } from '../../src/adapters/page-query.js';
import { TraceDag } from '../../src/client/trace-dag.js';
import { SuffixIndex } from '../../src/client/suffix-eligibility.js';
import { runWorkflow, scopeWorkflowObservation } from '../../src/client/workflow-agent.js';
import { FakeAdapter, ORIGIN } from '../support/fake-adapter.js';
import { runStage1SuffixAblation } from '../../qualification/stage1-suffix-ablation.js';

test('Stage 0 (#85): observe(ifCurrentVersion) reuses only while revision, owner generation, expiry and URL are current', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'gammatron-stage0-unit-'));
  const config = loadServiceConfig();
  let snapshotCalls = 0;
  const service = await WorkspaceService.open({
    stateDir: dir,
    config,
    createAdapter: () => {
      const inner = new FakeAdapter(join(dir, 'receipts.jsonl'));
      const origSnapshot = inner.snapshot.bind(inner);
      inner.snapshot = async (...args) => {
        snapshotCalls += 1;
        return origSnapshot(...args);
      };
      return inner;
    },
  });

  try {
    const workspaceId = 'stage0-rev';
    const admin = { workspaceId, ...await service.createWorkspace({ workspaceId }) };
    await service.grantAuthorization({
      ...admin,
      grantId: 'g1',
      ownerId: 'agent',
      intents: ['form:fill'],
      actionKinds: ['navigate', 'fill', 'click'],
      targetOrigins: [ORIGIN],
    });
    const owner = { workspaceId, ...await service.assignOwner({ ...admin, ownerId: 'agent' }) };

    const obs0 = await service.observe(owner);
    const navRes = await (await service.submitAction({
      ...owner,
      actionId: 'nav-1',
      authorizedIntent: 'form:fill',
      kind: 'navigate',
      target: { url: `${ORIGIN}/form` },
      observationVersion: obs0.observationVersion,
    })).result;
    assert.equal(navRes.outcome, 'completed');
    const snapsBeforeReuse = snapshotCalls;

    // 1. Reuse while current revision matches `postObservationVersion`: 0 extra adapter snapshots, version unchanged.
    const reused = await service.observe({ ...owner, ifCurrentVersion: navRes.postObservationVersion });
    assert.equal(reused.observationVersion, navRes.postObservationVersion);
    assert.equal(snapshotCalls, snapsBeforeReuse, 'Current revision reuse must not trigger a redundant browser snapshot');

    // 2. Stale `ifCurrentVersion` falls through and records a fresh observation snapshot.
    const fresh = await service.observe({ ...owner, ifCurrentVersion: navRes.postObservationVersion - 1 });
    assert.equal(fresh.observationVersion, navRes.postObservationVersion + 1);
    assert.equal(snapshotCalls, snapsBeforeReuse + 1);

    // 3. Owner handoff invalidates cached observations across generations.
    const nextOwner = { workspaceId, ...await service.assignOwner({ ...admin, ownerId: 'agent' }) };
    const afterHandoff = await service.observe({ ...nextOwner, ifCurrentVersion: fresh.observationVersion });
    assert.equal(afterHandoff.observationVersion, fresh.observationVersion + 1);
    assert.equal(snapshotCalls, snapsBeforeReuse + 2);
  } finally {
    await service.close();
    rmSync(dir, { recursive: true, force: true });
  }
});

test('Stage 1 (#88 / #85): offline snapshot ablation beats exact-hash with 0 unsafe certifications across 4 workflow families', async () => {
  const receipt = await runStage1SuffixAblation();
  assert.equal(receipt.allStage1GatesPassed, true);
  assert.equal(receipt.gates.zeroUnsafeCertifications, true);
  assert.equal(receipt.gates.zeroSkippedApprovals, true);
  assert.equal(receipt.gates.certifiedRejoinK2AtLeast60Pct, true);
  assert.equal(receipt.gates.certifiedRejoinK3AtLeast75Pct, true);
  assert.equal(receipt.gates.plannerCallRatioAtMost065x, true);
});

test('Stage 2 gate (#88 item #3): requirePrerequisiteCheck fails closed on unrendered server-side state unless assertPrerequisite passes', async () => {
  const limits = { maxNodes: 32, maxEdges: 32, maxSteps: 8 };
  const control = (label, id) => ({
    label, role: 'textbox', tag: 'input', inputType: 'text',
    selector: `#${id}`, handle: id, digest: `digest-${id}`, value: '',
  });
  // Like the page query, a host returns form state only when the observation asks for it.
  const withFormState = (els, command) => els.map(el => (command?.includeFormState
    ? { formKey: 'form:0', isDefaultValue: !el.value, ...structuredClone(el) }
    : structuredClone(el)));
  const makePage = rawElements => {
    const elements = structuredClone(rawElements);
    let version = 0;
    const calls = [];
    return {
      calls,
      outstanding: async () => [],
      observe: async command => ({
        url: 'https://fixture.invalid/draft',
        observationVersion: ++version,
        isTruncated: false,
        elements: withFormState(elements, command),
      }),
      submitAction: async action => {
        calls.push(action);
        const target = elements.find(el => el.handle === action.target.handle);
        if (target && action.kind !== 'click') target.value = action.params.value;
        return { result: Promise.resolve({ outcome: 'completed' }) };
      },
    };
  };
  const makeStore = () => {
    const runs = new Map();
    return {
      run: (id, state) => runs.set(id, state),
      get: id => ({ run: runs.get(id) ?? null }),
      activity: () => {},
    };
  };

  const dag = new TraceDag(limits);
  const index = new SuffixIndex();
  const nameEl = control('Name', 'name');
  const cityEl = control('City', 'city');
  const inputs = { name: 'Ada', city: 'London' };
  const learnPage = makePage([nameEl, cityEl]);
  const learnSession = dag.session({
    owner: { workspaceId: 'w1' }, pageId: 'main', intent: 'form', template: 'draft-form',
    inputs, service: learnPage, suffixIndex: index,
  });
  await learnSession.record({ kind: 'fill', locator: structuralLocator(nameEl), slot: 'name' });
  await learnSession.record({ kind: 'fill', locator: structuralLocator(cityEl), slot: 'city' });
  assert.equal((await learnSession.finish()).reason, 'recorded-submit-boundary');
  index.freeze();

  const common = {
    dag,
    mode: 'reuse',
    owner: { workspaceId: 'w1' },
    pageId: 'main',
    intent: 'form',
    template: 'draft-form',
    inputs,
    intermediateClicks: [],
    task: 'Fill draft',
    planner: null,
    config: { maxTurns: 4 },
    projectId: 'p1',
    verifyReview: async () => ({ completed: true }),
    signal: new AbortController().signal,
    suffixIndex: index,
    requirePrerequisiteCheck: true,
  };

  // 1. Omitting assertPrerequisite when requirePrerequisiteCheck=true fails closed across learn, fresh, AND reuse.
  const omittedPage = makePage([cityEl, nameEl]);
  for (const mode of ['learn', 'fresh', 'reuse']) {
    await assert.rejects(
      runWorkflow({ ...common, mode, service: omittedPage, store: makeStore() }),
      err => err?.code === 'missing-prerequisite-check',
    );
  }
  assert.equal(omittedPage.calls.length, 0);

  // 2. Direct TraceSession and WorkspaceService.open also fail closed without assertPrerequisite.
  assert.throws(
    () => dag.session({
      owner: { workspaceId: 'w1' }, pageId: 'main', intent: 'form', template: 'draft-form',
      inputs, service: omittedPage, suffixIndex: index, requirePrerequisiteCheck: true,
    }),
    err => err?.code === 'missing-prerequisite-check',
  );
  const svcGuardDir = mkdtempSync(join(tmpdir(), 'gammatron-svc-prereq-'));
  try {
    await assert.rejects(
      WorkspaceService.open({
        stateDir: svcGuardDir,
        config: loadServiceConfig(),
        createAdapter: () => new FakeAdapter(join(svcGuardDir, 'receipts.jsonl')),
        requirePrerequisiteCheck: true,
      }),
      err => err?.code === 'missing-prerequisite-check',
    );
    let adapterExecutions = 0;
    const svc = await WorkspaceService.open({
      stateDir: svcGuardDir,
      config: loadServiceConfig(),
      createAdapter: () => {
        const inner = new FakeAdapter(join(svcGuardDir, 'receipts.jsonl'));
        const origExec = inner.execute.bind(inner);
        inner.execute = async (...args) => {
          if (args[1]?.kind !== 'navigate') adapterExecutions += 1;
          return origExec(...args);
        };
        return inner;
      },
      requirePrerequisiteCheck: true,
      assertPrerequisite: async () => ({ ok: false, reason: 'Server draft locked at service write boundary' }),
    });
    try {
      const admin = { workspaceId: 'w-svc', ...await svc.createWorkspace({ workspaceId: 'w-svc' }) };
      await svc.grantAuthorization({
        ...admin, grantId: 'g-svc', ownerId: 'agent',
        intents: ['form:fill'], actionKinds: ['navigate', 'fill'], targetOrigins: [ORIGIN],
      });
      const owner = { workspaceId: 'w-svc', ...await svc.assignOwner({ ...admin, ownerId: 'agent' }) };
      const obs0 = await svc.observe(owner);
      const nav = await (await svc.submitAction({
        ...owner, actionId: 'nav-svc', authorizedIntent: 'form:fill',
        kind: 'navigate', target: { url: `${ORIGIN}/form` }, observationVersion: obs0.observationVersion,
      })).result;
      assert.equal(nav.outcome, 'completed');
      const obsForm = await svc.observe({ ...owner, ifCurrentVersion: nav.postObservationVersion });
      const targetEl = obsForm.elements.find(el => el.tag === 'input');
      const blockedWrite = await (await svc.submitAction({
        ...owner, actionId: 'fill-svc', authorizedIntent: 'form:fill',
        kind: 'fill',
        target: { handle: targetEl.handle, selector: targetEl.selector, digest: targetEl.digest },
        params: { value: 'Blocked' },
        observationVersion: obsForm.observationVersion,
      })).result;
      assert.equal(blockedWrite.dispatchStatus, 'never-dispatched');
      assert.equal(blockedWrite.neverDispatched?.code, 'precondition-unestablished');
      assert.equal(adapterExecutions, 0, 'Service write guard must refuse before adapter.execute');
    } finally {
      await svc.close();
    }
  } finally {
    rmSync(svcGuardDir, { recursive: true, force: true });
  }

  // 3. Both replay (reuse) AND planner (learn/fresh) actions are blocked with zero browser writes when locked.
  const lockedPage = makePage([cityEl, nameEl]);
  const lockedRes = await runWorkflow({
    ...common,
    service: lockedPage,
    store: makeStore(),
    assertPrerequisite: async () => { throw Error('Server draft is locked for approval'); },
  });
  assert.equal(lockedRes.completed, false);
  assert.match(lockedRes.detail, /locked for approval/);
  assert.equal(lockedPage.calls.length, 0);

  const lockedPlannerPage = makePage([cityEl, nameEl]);
  const lockedPlannerRes = await runWorkflow({
    ...common,
    mode: 'fresh',
    planner: {
      identity: { model: 'test-planner' },
      next: async ctx => ({
        tool: 'act',
        input: { kind: 'fill', handle: ctx.observation.elements[0].handle, slot: 'city' },
      }),
    },
    service: lockedPlannerPage,
    store: makeStore(),
    assertPrerequisite: async () => ({ ok: false, reason: 'Server draft is locked for planner too' }),
  });
  assert.equal(lockedPlannerRes.completed, false);
  assert.match(lockedPlannerRes.detail, /locked for planner too/);
  assert.equal(lockedPlannerPage.calls.length, 0, 'Planner write into locked draft must also dispatch zero actions');

  // 4. Unlocked draft passes assertPrerequisite and completes reuse cleanly.
  const unlockedPage = makePage([cityEl, nameEl]);
  const seenChecks = [];
  const unlockedRes = await runWorkflow({
    ...common,
    service: unlockedPage,
    store: makeStore(),
    assertPrerequisite: async check => { seenChecks.push(check); },
  });
  assert.equal(unlockedRes.completed, true);
  assert.equal(unlockedPage.calls.length, 2);
  assert.equal(seenChecks.length, 2);
  assert.equal(seenChecks[0].origin, 'https://fixture.invalid');

  // 5. SuffixIndex also refuses dirty untracked <form> fields when form state is observed (Guardrail 2).
  const dirtyFormElements = [
    { ...cityEl, formKey: 'form:0', isDefaultValue: true },
    { ...nameEl, formKey: 'form:0', isDefaultValue: true },
    {
      label: 'Expedited overnight fee', role: 'textbox', tag: 'input', inputType: 'text',
      selector: '#fee', handle: 'fee', digest: 'digest-fee', value: '$199',
      formKey: 'form:0', isDefaultValue: false,
    },
  ];
  const dirtyPage = makePage(dirtyFormElements);
  const dirtySession = dag.session({
    owner: { workspaceId: 'w1' }, pageId: 'main', intent: 'form', template: 'draft-form',
    inputs, service: dirtyPage, suffixIndex: index,
  });
  assert.equal((await dirtySession.replay()).reason, 'unseen-branch');
  assert.equal(dirtyPage.calls.length, 0, 'SuffixIndex must refuse dirty untracked <form> control');
  assert.ok(dirtySession.traceEvents.some(e => e.refusals?.['dirty-untracked-form-field'] > 0));

  // 6. Session replacement (learnRepairs: false) preserves initial traceEvents and certified rejoins.
  const nextBtn = {
    label: 'Continue', role: 'button', tag: 'button', inputType: '',
    selector: '#continue', handle: 'continue', digest: 'digest-continue', value: null,
  };
  const clickDag = new TraceDag(limits);
  const clickIndex = new SuffixIndex();
  let learnStage = 0;
  const learnTwoPage = {
    outstanding: async () => [],
    observe: async command => ({
      url: 'https://fixture.invalid/draft',
      observationVersion: Date.now() + Math.random(),
      isTruncated: false,
      elements: withFormState(learnStage ? [cityEl] : [nameEl, nextBtn], command),
    }),
    submitAction: async action => {
      if (action.kind === 'click') learnStage = 1;
      return { result: Promise.resolve({ outcome: 'completed' }) };
    },
  };
  const clickLearn = clickDag.session({
    owner: { workspaceId: 'w1' }, pageId: 'main', intent: 'form', template: 'draft-2p',
    inputs, service: learnTwoPage, suffixIndex: clickIndex,
    intermediateClicks: [structuralLocator(nextBtn)],
  });
  await clickLearn.record({ kind: 'fill', locator: structuralLocator(nameEl), slot: 'name' });
  await clickLearn.record({ kind: 'click', locator: structuralLocator(nextBtn) });
  await clickLearn.record({ kind: 'fill', locator: structuralLocator(cityEl), slot: 'city' });
  assert.equal((await clickLearn.finish()).reason, 'recorded-submit-boundary');
  clickIndex.freeze();

  let evalStage = 0;
  const evalP1 = [structuredClone(nameEl), structuredClone(nextBtn), control('Referral code', 'ref')];
  const evalP2 = [structuredClone(cityEl)];
  const evalTwoPage = {
    outstanding: async () => [],
    observe: async command => ({
      url: 'https://fixture.invalid/draft',
      observationVersion: Date.now() + Math.random(),
      isTruncated: false,
      elements: withFormState(evalStage ? evalP2 : evalP1, command),
    }),
    submitAction: async action => {
      const els = evalStage ? evalP2 : evalP1;
      if (action.kind === 'click') evalStage = 1;
      else {
        const t = els.find(el => el.handle === action.target.handle);
        if (t) t.value = action.params.value;
      }
      return { result: Promise.resolve({ outcome: 'completed' }) };
    },
  };
  let plannerTurns = 0;
  const partialRes = await runWorkflow({
    ...common,
    dag: clickDag,
    template: 'draft-2p',
    inputs: { ...inputs, ref: 'REF-1' },
    intermediateClicks: [structuralLocator(nextBtn)],
    suffixIndex: clickIndex,
    requirePrerequisiteCheck: false,
    assertPrerequisite: null,
    learnRepairs: false,
    reconvergeMidRepair: true,
    planner: {
      identity: { model: 'test-planner' },
      next: async () => {
        plannerTurns += 1;
        if (plannerTurns === 1) return { tool: 'act', input: { kind: 'fill', handle: 'ref', slot: 'ref' } };
        if (plannerTurns === 2) return { tool: 'act', input: { kind: 'click', handle: 'continue' } };
        return { tool: 'finish', input: { summary: 'Done' } };
      },
    },
    service: evalTwoPage,
    store: makeStore(),
  });
  assert.equal(partialRes.completed, true);
  assert.ok(partialRes.cacheSteps >= 2, 'Prefix fill and post-repair suffix fill both cached');
  assert.ok(partialRes.traceEvents.some(e => e.phase === 'suffix-certified'), 'traceEvents from replaced initial session must be retained');
});

test('Write-boundary races & scope isolation (#88): post-validation lock/revocation, conditional write version, and suffixProfiles scope', async () => {
  // 1. Lock or grant revocation AFTER client-side validation (authorizeStep) BEFORE WorkspaceService.#checkLiveDispatch
  //    plus post-#checkLiveDispatch race window vs. conditional/versioned writes.
  const dir = mkdtempSync(join(tmpdir(), 'gammatron-race-unit-'));
  try {
    let serverDraft = { locked: false, version: 'v1', committedWrites: 0 };
    let unversionedExecutions = 0;

    // 1a. requireConditionalWrite=true refuses unversioned adapter before dispatch.
    const unversionedSvc = await WorkspaceService.open({
      stateDir: join(dir, 'unversioned-req'),
      config: loadServiceConfig(),
      createAdapter: () => new FakeAdapter(join(dir, 'r1.jsonl')),
      requirePrerequisiteCheck: true,
      requireConditionalWrite: true,
      assertPrerequisite: async () => ({ ok: !serverDraft.locked, writeVersion: serverDraft.version }),
    });
    try {
      const admin = { workspaceId: 'w1', ...await unversionedSvc.createWorkspace({ workspaceId: 'w1' }) };
      await unversionedSvc.grantAuthorization({
        ...admin, grantId: 'g1', ownerId: 'agent',
        intents: ['form:fill'], actionKinds: ['navigate', 'fill'], targetOrigins: [ORIGIN],
      });
      const owner = { workspaceId: 'w1', ...await unversionedSvc.assignOwner({ ...admin, ownerId: 'agent' }) };
      const o0 = await unversionedSvc.observe(owner);
      const nav = await (await unversionedSvc.submitAction({
        ...owner, actionId: 'nav-1', authorizedIntent: 'form:fill',
        kind: 'navigate', target: { url: `${ORIGIN}/form` }, observationVersion: o0.observationVersion,
      })).result;
      const o1 = await unversionedSvc.observe({ ...owner, ifCurrentVersion: nav.postObservationVersion });
      const inputEl = o1.elements.find(el => el.tag === 'input');
      const refused = await (await unversionedSvc.submitAction({
        ...owner, actionId: 'fill-unver', authorizedIntent: 'form:fill',
        kind: 'fill', target: { handle: inputEl.handle, selector: inputEl.selector, digest: inputEl.digest },
        params: { value: 'Ada' }, observationVersion: o1.observationVersion,
      })).result;
      assert.equal(refused.dispatchStatus, 'never-dispatched');
      assert.equal(refused.neverDispatched?.code, 'precondition-unestablished');
    } finally {
      await unversionedSvc.close();
    }

    // 1b. Post-client-validation lock AND grant revocation before #checkLiveDispatch dispatch zero effects;
    //     post-#checkLiveDispatch lock races on unversioned DOM (flagged unconditionalWriteRaceWindow=true),
    //     while conditional/versioned write rejects stale writeVersion with 0 committed server writes.
    let mutateAfterDispatchCheck = false;
    const versionedSvc = await WorkspaceService.open({
      stateDir: join(dir, 'versioned'),
      config: loadServiceConfig(),
      hooks: {
        afterDispatchStarted: req => {
          if (mutateAfterDispatchCheck && req.kind !== 'navigate') {
            serverDraft = { ...serverDraft, locked: true, version: 'v2' };
          }
        },
      },
      createAdapter: () => {
        const inner = new FakeAdapter(join(dir, 'r2.jsonl'));
        inner.supportsConditionalWrites = true;
        const origExec = inner.execute.bind(inner);
        inner.execute = async (wsId, req, files) => {
          if (req.kind !== 'navigate') {
            if (req.writeVersion !== undefined) {
              if (serverDraft.locked || req.writeVersion !== serverDraft.version) {
                throw Error(`Conditional write conflict: expected ${req.writeVersion}, server at ${serverDraft.version}`);
              }
              serverDraft.committedWrites += 1;
            } else {
              unversionedExecutions += 1;
            }
          }
          return origExec(wsId, req, files);
        };
        return inner;
      },
      requirePrerequisiteCheck: true,
      requireConditionalWrite: true,
      assertPrerequisite: async () => (
        serverDraft.locked
          ? { ok: false, reason: 'locked before #checkLiveDispatch' }
          : { ok: true, writeVersion: serverDraft.version }
      ),
    });
    try {
      const admin = { workspaceId: 'w2', ...await versionedSvc.createWorkspace({ workspaceId: 'w2' }) };
      await versionedSvc.grantAuthorization({
        ...admin, grantId: 'g2', ownerId: 'agent',
        intents: ['form:fill'], actionKinds: ['navigate', 'fill'], targetOrigins: [ORIGIN],
      });
      const owner = { workspaceId: 'w2', ...await versionedSvc.assignOwner({ ...admin, ownerId: 'agent' }) };
      const o0 = await versionedSvc.observe(owner);
      const nav = await (await versionedSvc.submitAction({
        ...owner, actionId: 'nav-2', authorizedIntent: 'form:fill',
        kind: 'navigate', target: { url: `${ORIGIN}/form` }, observationVersion: o0.observationVersion,
      })).result;
      const o1 = await versionedSvc.observe({ ...owner, ifCurrentVersion: nav.postObservationVersion });
      const inputEl = o1.elements.find(el => el.tag === 'input');

      // Lock engages AFTER client validation passes, BEFORE #checkLiveDispatch:
      const clientCheckPassed = !serverDraft.locked;
      assert.equal(clientCheckPassed, true);
      serverDraft.locked = true;
      const caughtPreDispatch = await (await versionedSvc.submitAction({
        ...owner, actionId: 'fill-prelock', authorizedIntent: 'form:fill',
        kind: 'fill', target: { handle: inputEl.handle, selector: inputEl.selector, digest: inputEl.digest },
        params: { value: 'Ada' }, observationVersion: o1.observationVersion,
      })).result;
      assert.equal(caughtPreDispatch.dispatchStatus, 'never-dispatched');
      assert.equal(serverDraft.committedWrites, 0);

      // Unlock, then lock AFTER #checkLiveDispatch (inside afterDispatchStarted) -> versioned write rejects!
      serverDraft = { locked: false, version: 'v1', committedWrites: 0 };
      mutateAfterDispatchCheck = true;
      const caughtAtCommit = await (await versionedSvc.submitAction({
        ...owner, actionId: 'fill-toctou', authorizedIntent: 'form:fill',
        kind: 'fill', target: { handle: inputEl.handle, selector: inputEl.selector, digest: inputEl.digest },
        params: { value: 'Ada' }, observationVersion: o1.observationVersion,
      })).result;
      assert.equal(caughtAtCommit.outcome, 'unknown');
      assert.equal(serverDraft.committedWrites, 0, 'Conditional write version rejected stale mutation');
      assert.equal(unversionedExecutions, 0);
    } finally {
      await versionedSvc.close();
    }

    // 1c. Unversioned write marks unconditionalWriteRaceWindow: true in evidence.
    const plainSvc = await WorkspaceService.open({
      stateDir: join(dir, 'plain'),
      config: loadServiceConfig(),
      createAdapter: () => new FakeAdapter(join(dir, 'r3.jsonl')),
    });
    try {
      const admin = { workspaceId: 'w3', ...await plainSvc.createWorkspace({ workspaceId: 'w3' }) };
      await plainSvc.grantAuthorization({
        ...admin, grantId: 'g3', ownerId: 'agent',
        intents: ['form:fill'], actionKinds: ['navigate', 'fill'], targetOrigins: [ORIGIN],
      });
      const owner = { workspaceId: 'w3', ...await plainSvc.assignOwner({ ...admin, ownerId: 'agent' }) };
      const o0 = await plainSvc.observe(owner);
      const nav = await (await plainSvc.submitAction({
        ...owner, actionId: 'nav-3', authorizedIntent: 'form:fill',
        kind: 'navigate', target: { url: `${ORIGIN}/form` }, observationVersion: o0.observationVersion,
      })).result;
      const o1 = await plainSvc.observe({ ...owner, ifCurrentVersion: nav.postObservationVersion });
      const inputEl = o1.elements.find(el => el.tag === 'input');
      const done = await (await plainSvc.submitAction({
        ...owner, actionId: 'fill-plain', authorizedIntent: 'form:fill',
        kind: 'fill', target: { handle: inputEl.handle, selector: inputEl.selector, digest: inputEl.digest },
        params: { value: 'Ada' }, observationVersion: o1.observationVersion,
      })).result;
      assert.equal(done.outcome, 'completed');
      assert.equal(done.evidence?.unconditionalWriteRaceWindow, true);
    } finally {
      await plainSvc.close();
    }
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }

  // 2. suffixProfiles binds to session scope (template + origin + readScope + accountScope).
  const limits = { maxNodes: 32, maxEdges: 32, maxSteps: 8 };
  const dag = new TraceDag(limits);
  const elA = {
    label: 'Name', role: 'textbox', tag: 'input', inputType: 'text',
    selector: '#name', handle: 'name', digest: 'd-name', value: '',
    actionability: { visible: true, inert: false, disabled: false },
  };
  const elB = {
    label: 'City', role: 'textbox', tag: 'input', inputType: 'text',
    selector: '#city', handle: 'city', digest: 'd-city', value: '',
    actionability: { visible: true, inert: false, disabled: false },
  };
  const mkPage = raw => {
    const els = structuredClone(raw);
    let v = 0;
    const calls = [];
    return {
      calls,
      outstanding: async () => [],
      observe: async () => ({
        url: 'https://fixture.invalid/edit/42',
        observationVersion: ++v,
        isTruncated: false,
        elements: structuredClone(els),
      }),
      submitAction: async a => {
        calls.push(a);
        const t = els.find(x => x.handle === a.target.handle);
        if (t && a.kind !== 'click') t.value = a.params.value;
        return { result: Promise.resolve({ outcome: 'completed' }) };
      },
    };
  };
  const learnSess = dag.session({
    owner: { workspaceId: 'w' }, pageId: 'main', intent: 'edit', template: 'tmpl-v1',
    accountScope: 'tenant-alpha', inputs: { name: 'Ada', city: 'London' },
    service: mkPage([elA, elB]), suffixEligibility: true,
  });
  await learnSess.record({ kind: 'fill', locator: structuralLocator(elA), slot: 'name' });
  await learnSess.record({ kind: 'fill', locator: structuralLocator(elB), slot: 'city' });
  assert.equal((await learnSess.finish()).reason, 'recorded-submit-boundary');

  // Reordered page under DIFFERENT accountScope must be refused by suffixProfiles (`scope-mismatch`).
  const wrongScopePage = mkPage([elB, elA]);
  const wrongScopeSess = dag.session({
    owner: { workspaceId: 'w' }, pageId: 'main', intent: 'edit', template: 'tmpl-v1',
    accountScope: 'tenant-beta', inputs: { name: 'Ada', city: 'London' },
    service: wrongScopePage, suffixEligibility: true,
  });
  assert.equal((await wrongScopeSess.replay()).reason, 'unseen-branch');
  assert.equal(wrongScopePage.calls.length, 0);
  assert.equal(wrongScopeSess.certifiedSuffixRejoins.length, 0);
  assert.equal(wrongScopeSess.lastSuffixRejection?.reason, 'scope-mismatch');

  // Legacy profile with no recorded scope also fails closed with scope-mismatch (Rule 2.3).
  const rawExport = dag.export();
  rawExport.suffixProfiles = rawExport.suffixProfiles.map(([id, prof]) => {
    const copy = structuredClone(prof);
    delete copy.scope;
    return [id, copy];
  });
  const legacyDag = TraceDag.restore(rawExport, limits);
  const legacyPage = mkPage([elB, elA]);
  const legacySess = legacyDag.session({
    owner: { workspaceId: 'w' }, pageId: 'main', intent: 'edit', template: 'tmpl-v1',
    accountScope: 'tenant-alpha', inputs: { name: 'Ada', city: 'London' },
    service: legacyPage, suffixEligibility: true,
  });
  assert.equal((await legacySess.replay()).reason, 'unseen-branch');
  assert.equal(legacyPage.calls.length, 0);
  assert.equal(legacySess.lastSuffixRejection?.reason, 'scope-mismatch');

  // A different observation policy is a different template, so the profile is refused the same way
  // (Rule 2.2). The control shows the same reordered page is rejoined under the taught policy.
  const taughtPolicy = [structuralLocator(elA), structuralLocator(elB)];
  const widerPolicy = [...taughtPolicy, ['textbox', 'Referral code', 'input', 'text']];
  const policyDag = new TraceDag(limits);
  const session = (policy, page) => {
    const scoped = scopeWorkflowObservation(page, 'tmpl-v1', policy);
    return policyDag.session({
      owner: { workspaceId: 'w' }, pageId: 'main', intent: 'edit', template: scoped.template,
      accountScope: 'tenant-alpha', inputs: { name: 'Ada', city: 'London' },
      service: scoped.service, suffixEligibility: true,
    });
  };
  const policyLearn = session(taughtPolicy, mkPage([elA, elB]));
  await policyLearn.record({ kind: 'fill', locator: structuralLocator(elA), slot: 'name' });
  await policyLearn.record({ kind: 'fill', locator: structuralLocator(elB), slot: 'city' });
  assert.equal((await policyLearn.finish()).reason, 'recorded-submit-boundary');

  const samePolicyPage = mkPage([elB, elA]);
  const samePolicySess = session(taughtPolicy, samePolicyPage);
  await samePolicySess.replay();
  assert.equal(samePolicySess.certifiedSuffixRejoins.length, 1, 'Under the taught policy the reordered page is rejoined');
  assert.ok(samePolicyPage.calls.length > 0);

  const otherPolicyPage = mkPage([elB, elA]);
  const otherPolicySess = session(widerPolicy, otherPolicyPage);
  assert.equal((await otherPolicySess.replay()).reason, 'unseen-branch');
  assert.equal(otherPolicyPage.calls.length, 0, 'A changed observation policy dispatches nothing');
  assert.equal(otherPolicySess.certifiedSuffixRejoins.length, 0);
  assert.equal(otherPolicySess.lastSuffixRejection?.reason, 'scope-mismatch');
});
