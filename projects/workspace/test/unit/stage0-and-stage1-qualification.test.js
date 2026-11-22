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
import { runWorkflow } from '../../src/client/workflow-agent.js';
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
