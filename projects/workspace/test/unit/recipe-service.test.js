import assert from 'node:assert/strict';
import { createHash, randomBytes, randomUUID } from 'node:crypto';
import { mkdtempSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { createNodeRecipeServer } from '../../src/recipe-service/server-main.js';
import { ManagedRecipeClient } from '../../src/client/recipe-client.js';
import { InvestigationStore } from '../../src/client/investigation.js';
import { structuralLocator, structuralOutlineHash } from '../../src/adapters/page-query.js';

const sha256 = text => createHash('sha256').update(text).digest('hex');
const tokenAlpha = randomBytes(32).toString('hex');
const tokenBeta = randomBytes(32).toString('hex');
const tokenPublisher = randomBytes(32).toString('hex');
const secret = randomBytes(32).toString('hex');

const root = mkdtempSync(join(tmpdir(), 'fawn-recipe-service-'));
const { server, store: dbStore } = createNodeRecipeServer({
  dbPath: join(root, 'recipes.sqlite'),
  secret,
  catalogQuorum: 2,
  clients: [
    { clientId: 'alpha-1', workspaceId: 'ws-alpha', tokenHash: sha256(tokenAlpha), role: 'member' },
    { clientId: 'beta-1', workspaceId: 'ws-beta', tokenHash: sha256(tokenBeta), role: 'member' },
    { clientId: 'pub-1', workspaceId: 'ws-curated', tokenHash: sha256(tokenPublisher), role: 'publisher' },
  ],
});

await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const baseUrl = `http://127.0.0.1:${server.address().port}`;
const limits = { maxNodes: 64, maxEdges: 64, maxSteps: 12 };

const alphaClient = new ManagedRecipeClient({ url: baseUrl, token: tokenAlpha });
const betaClient = new ManagedRecipeClient({ url: baseUrl, token: tokenBeta });
const publisherClient = new ManagedRecipeClient({ url: baseUrl, token: tokenPublisher });

const el = (role, label, tag, inputType, handle, value = '') => ({
  role, label, tag, inputType, handle, selector: `#${handle}`, digest: `d-${handle}`, value,
});

try {
  // 1. Auth, Origin header rejection, and PII / forbidden-field rejection.
  assert.equal((await fetch(`${baseUrl}/health`)).status, 401);
  assert.equal((await fetch(`${baseUrl}/health`, {
    headers: { authorization: `Bearer ${tokenAlpha}`, origin: 'https://evil.example' },
  })).status, 403);
  assert.equal((await alphaClient.health()).ready, true);

  const outlineA = 'a'.repeat(64);
  const outlineB = 'b'.repeat(64);
  await assert.rejects(
    alphaClient.submitVerifiedTrace({
      submissionId: randomUUID(),
      scope: 'workspace',
      origin: 'https://app.example.com/private-path?token=secret',
      template: 't1',
      verificationId: 'v1',
      reviewVerified: true,
      steps: [{ beforeOutline: outlineA, afterOutline: outlineB, kind: 'fill', locator: ['textbox', 'Name', 'input', 'text'], slot: 'name' }],
    }),
    err => err.code === 'non-origin-url-rejected',
  );
  await assert.rejects(
    alphaClient.submitVerifiedTrace({
      submissionId: randomUUID(),
      scope: 'workspace',
      origin: 'https://app.example.com',
      template: 't1',
      verificationId: 'v1',
      reviewVerified: true,
      steps: [{
        beforeOutline: outlineA, afterOutline: outlineB, kind: 'fill',
        locator: ['textbox', 'Name', 'input', 'text'], slot: 'name', value: 'LEAKED_PII',
      }],
    }),
    err => err.code === 'pii-or-unknown-field-rejected',
  );
  await assert.rejects(
    alphaClient.submitVerifiedTrace({
      submissionId: randomUUID(),
      scope: 'workspace',
      origin: 'https://app.example.com',
      template: 't1',
      verificationId: 'v1',
      reviewVerified: true,
      steps: [{
        beforeOutline: outlineA, afterOutline: outlineB, kind: 'fill',
        locator: ['textbox', 'Password', 'input', 'password'], slot: 'pw',
      }],
    }),
    err => err.code === 'forbidden-target-rejected',
  );

  // 2. Sub-recipe authoring + cross-template server composition + zero-call & mid-recipe replay.
  const openBtn = el('button', 'Open drawer', 'button', '', 'open');
  const searchInput = el('textbox', 'Search catalog', 'input', 'search', 'search');
  const detailBtn = el('button', 'View details', 'button', '', 'detail');
  const formatSelect = el('combobox', 'Export format', 'select', 'select-one', 'format');

  const closedOutline = structuralOutlineHash([openBtn]);
  const drawerOutline = structuralOutlineHash([searchInput, detailBtn]);
  const detailOutline = structuralOutlineHash([formatSelect]);

  await publisherClient.registerSubrecipe({
    scope: 'catalog',
    origin: 'https://app.example.com',
    name: 'open-drawer',
    steps: [{
      beforeOutline: closedOutline,
      afterOutline: drawerOutline,
      kind: 'click',
      locator: structuralLocator(openBtn),
    }],
  });
  await publisherClient.registerSubrecipe({
    scope: 'catalog',
    origin: 'https://app.example.com',
    name: 'search-and-inspect',
    steps: [
      {
        beforeOutline: drawerOutline,
        afterOutline: drawerOutline,
        kind: 'fill',
        locator: structuralLocator(searchInput),
        slot: 'query',
      },
      {
        beforeOutline: drawerOutline,
        afterOutline: detailOutline,
        kind: 'click',
        locator: structuralLocator(detailBtn),
      },
    ],
  });
  await publisherClient.registerSubrecipe({
    scope: 'catalog',
    origin: 'https://app.example.com',
    name: 'choose-export-format',
    steps: [{
      beforeOutline: detailOutline,
      afterOutline: detailOutline,
      kind: 'select',
      locator: structuralLocator(formatSelect),
      slot: 'format',
    }],
  });

  const listed = await alphaClient.listSubrecipes({ scope: 'catalog', origin: 'https://app.example.com' });
  assert.equal(listed.subrecipes.length, 3);

  // Workspace alpha composes those shared catalog sub-recipes into TWO different templates!
  const composedA = await alphaClient.composeRecipe({
    scope: 'workspace',
    origin: 'https://app.example.com',
    targetTemplate: 'audit-export-v1',
    subrecipes: ['open-drawer', 'search-and-inspect', 'choose-export-format'],
    limits,
  });
  assert.equal(composedA.compressionStats.terminalCount, 1);
  assert.equal(composedA.compressionStats.nodeCount, 5);

  function appService(startStage = 'closed') {
    let stage = startStage, version = 0, query = '', format = '';
    const calls = [];
    return {
      calls,
      done: () => stage === 'detail' && query === 'kernel' && format === 'csv',
      outstanding: async () => [],
      observe: async () => ({
        url: 'https://app.example.com/items/99',
        text: stage,
        observationVersion: ++version,
        isTruncated: false,
        elements: stage === 'closed' ? [openBtn]
          : stage === 'drawer' ? [{ ...searchInput, value: query }, detailBtn]
            : [{ ...formatSelect, value: format }],
      }),
      submitAction: async req => {
        calls.push(req.target.handle);
        if (req.target.handle === 'open') stage = 'drawer';
        else if (req.target.handle === 'search') query = req.params.value;
        else if (req.target.handle === 'detail') stage = 'detail';
        else if (req.target.handle === 'format') format = req.params.value;
        return { result: Promise.resolve({ outcome: 'completed', isUncertain: false }) };
      },
    };
  }

  const resolvedComposed = await alphaClient.resolveDag({
    scope: 'workspace',
    origin: 'https://app.example.com',
    template: 'audit-export-v1',
    currentOutline: drawerOutline,
    limits,
  });
  assert.equal(resolvedComposed.entryLookup.entryOptimalCost, 3, 'On-demand mid-page lookup reports exact remaining DP cost');

  const fullSvc = appService('closed');
  const fullReplay = await resolvedComposed.restoredDag.session({
    service: fullSvc, owner: {}, pageId: 'main', intent: 'export', template: 'audit-export-v1',
    inputs: { query: 'kernel', format: 'csv' },
    intermediateClicks: [openBtn, detailBtn].map(structuralLocator),
  }).replay();
  assert.equal(fullReplay.reason, 'submit-boundary');
  assert.equal(fullReplay.steps, 4);
  assert.deepEqual(fullSvc.calls, ['open', 'search', 'detail', 'format']);

  const midSvc = appService('drawer');
  const midReplay = await resolvedComposed.restoredDag.session({
    service: midSvc, owner: {}, pageId: 'main', intent: 'export', template: 'audit-export-v1',
    inputs: { query: 'kernel', format: 'csv' },
    intermediateClicks: [openBtn, detailBtn].map(structuralLocator),
  }).replay();
  assert.equal(midReplay.reason, 'submit-boundary');
  assert.equal(midReplay.steps, 3);
  assert.deepEqual(midSvc.calls, ['search', 'detail', 'format']);

  // 3. Server-side loop contraction & dominated detour compression across traces.
  const menuBtn = el('button', 'Menu', 'button', '', 'menu');
  const subBtn = el('button', 'Submenu', 'button', '', 'sub');
  const quickBtn = el('button', 'Quick search', 'button', '', 'quick');
  const homeOut = structuralOutlineHash([menuBtn, quickBtn]);
  const menuOut = structuralOutlineHash([subBtn]);
  const searchOut = structuralOutlineHash([searchInput]);

  // Trace 1 has BOTH a modal loop (home -> menu -> home) AND a 2-click path (home -> menu -> search -> fill).
  const firstIngest = await alphaClient.submitVerifiedTrace({
    submissionId: 'trace-detour-1',
    scope: 'workspace',
    origin: 'https://app.example.com',
    template: 'detour-demo',
    verificationId: 'ver-1',
    reviewVerified: true,
    limits,
    steps: [
      { beforeOutline: homeOut, afterOutline: menuOut, kind: 'click', locator: structuralLocator(menuBtn), elapsedMs: 50 },
      { beforeOutline: menuOut, afterOutline: homeOut, kind: 'click', locator: ['button', 'Back', 'button', ''], elapsedMs: 50 },
      { beforeOutline: homeOut, afterOutline: menuOut, kind: 'click', locator: structuralLocator(menuBtn), elapsedMs: 50 },
      { beforeOutline: menuOut, afterOutline: searchOut, kind: 'click', locator: structuralLocator(subBtn), elapsedMs: 50 },
      { beforeOutline: searchOut, afterOutline: searchOut, kind: 'fill', locator: structuralLocator(searchInput), slot: 'query', elapsedMs: 40 },
    ],
  });
  assert.equal(firstIngest.contractedSteps, 2, 'Server contracts home -> menu -> home loop');
  assert.equal(firstIngest.compressionStats.nodeCount, 4);

  // Idempotent retry of same submissionId returns exact same receipt without double-counting.
  const retryIngest = await alphaClient.submitVerifiedTrace({
    submissionId: 'trace-detour-1',
    scope: 'workspace',
    origin: 'https://app.example.com',
    template: 'detour-demo',
    verificationId: 'ver-1',
    reviewVerified: true,
    limits,
    steps: [],
  });
  assert.equal(retryIngest.revision, firstIngest.revision);

  // Trace 2 discovers 1-click shortcut (home -> search -> fill): server prunes menu detour & garbage-collects menu node!
  const shortcutIngest = await alphaClient.submitVerifiedTrace({
    submissionId: 'trace-shortcut-2',
    scope: 'workspace',
    origin: 'https://app.example.com',
    template: 'detour-demo',
    verificationId: 'ver-1',
    reviewVerified: true,
    limits,
    steps: [
      { beforeOutline: homeOut, afterOutline: searchOut, kind: 'click', locator: structuralLocator(quickBtn), elapsedMs: 25 },
      { beforeOutline: searchOut, afterOutline: searchOut, kind: 'fill', locator: structuralLocator(searchInput), slot: 'query', elapsedMs: 30 },
    ],
  });
  assert.equal(shortcutIngest.reduction.detourEdgesRemoved, 1);
  assert.equal(shortcutIngest.reduction.detourNodesRemoved, 1);
  assert.equal(shortcutIngest.compressionStats.nodeCount, 3);
  assert.equal(shortcutIngest.compressionStats.edgeCount, 2);

  // 4. Quorum-gated shared catalog promotion + empirical Bellman DP latency selection.
  const fastField = el('textbox', 'Fast token', 'input', 'text', 'fast');
  const slowField = el('textbox', 'Slow token', 'input', 'text', 'slow');
  const dualOut = structuralOutlineHash([fastField, slowField]);

  await alphaClient.submitVerifiedTrace({
    submissionId: 'cat-alpha-fast',
    scope: 'catalog',
    origin: 'https://shared.example.com',
    template: 'dual-entry',
    verificationId: 'ver-dual',
    reviewVerified: true,
    limits,
    steps: [{
      beforeOutline: dualOut, afterOutline: dualOut, kind: 'fill',
      locator: structuralLocator(fastField), slot: 'fast', elapsedMs: 20,
    }],
  });
  // Quorum is 2: single-workspace contribution is NOT yet served in shared catalog!
  const beforeQuorum = await betaClient.resolveDag({
    scope: 'catalog',
    origin: 'https://shared.example.com',
    template: 'dual-entry',
    limits,
  });
  assert.equal(beforeQuorum.restoredDag.nodes.size, 0, 'Unconfirmed single-client edge stays unpromoted in catalog');

  // Second independent workspace (beta) confirms 'fast', AND both workspaces also submit slower 'slow' (5000 ms).
  await betaClient.submitVerifiedTrace({
    submissionId: 'cat-beta-fast',
    scope: 'catalog',
    origin: 'https://shared.example.com',
    template: 'dual-entry',
    verificationId: 'ver-dual',
    reviewVerified: true,
    limits,
    steps: [{
      beforeOutline: dualOut, afterOutline: dualOut, kind: 'fill',
      locator: structuralLocator(fastField), slot: 'fast', elapsedMs: 30,
    }],
  });
  for (const [client, id] of [[alphaClient, 'cat-alpha-slow'], [betaClient, 'cat-beta-slow']]) {
    await client.submitVerifiedTrace({
      submissionId: id,
      scope: 'catalog',
      origin: 'https://shared.example.com',
      template: 'dual-entry',
      verificationId: 'ver-dual',
      reviewVerified: true,
      limits,
      steps: [{
        beforeOutline: dualOut, afterOutline: dualOut, kind: 'fill',
        locator: structuralLocator(slowField), slot: 'slow', elapsedMs: 8000,
      }],
    });
  }

  const afterQuorum = await betaClient.resolveDag({
    scope: 'catalog',
    origin: 'https://shared.example.com',
    template: 'dual-entry',
    limits,
  });
  assert.equal(afterQuorum.restoredDag.nodes.size, 3);
  const picked = [];
  const dualReplay = await afterQuorum.restoredDag.session({
    service: {
      outstanding: async () => [],
      observe: async () => ({
        url: 'https://shared.example.com/form',
        observationVersion: 1,
        isTruncated: false,
        elements: [fastField, slowField],
      }),
      submitAction: async req => {
        picked.push(req.target.handle);
        return { result: Promise.resolve({ outcome: 'completed' }) };
      },
    },
    owner: {}, pageId: 'main', intent: 'form', template: 'dual-entry',
    inputs: { fast: 'F-1', slow: 'S-1' },
  }).replay();
  assert.equal(dualReplay.reason, 'submit-boundary');
  assert.deepEqual(picked, ['fast'], 'Empirical Bellman DP selects lower-latency promoted route');

  // 5. End-to-end ManagedRecipeClient.runWorkflow + Zero-trust local disclosure defense.
  const invStore = new InvestigationStore(join(root, 'inv'));
  try {
    let enteredName = '', obsVer = 0;
    const mkFormSvc = () => ({
      calls: 0,
      outstanding: async () => [],
      observe: async () => ({
        url: 'https://portal.example.com/apply',
        text: 'Apply',
        observationVersion: ++obsVer,
        isTruncated: false,
        elements: [el('textbox', 'Applicant name', 'input', 'text', 'applicant', enteredName)],
      }),
      async submitAction(req) {
        this.calls++;
        enteredName = req.params.value;
        return { result: Promise.resolve({ outcome: 'completed', isUncertain: false }) };
      },
    });
    const disclosurePolicy = {
      origin: 'https://portal.example.com',
      intermediateClicks: [],
      fields: [{ kind: 'fill', slot: 'name', locator: ['textbox', 'Applicant name', 'input', 'text'] }],
    };

    invStore.create({ id: 'p1', goal: 'Apply' });
    const learnRes = await alphaClient.runWorkflow({
      scope: 'workspace',
      mode: 'learn',
      limits,
      service: mkFormSvc(),
      owner: {}, pageId: 'main', intent: 'form', template: 'portal-apply',
      inputs: { name: 'SECRET_APPLICANT_NAME', ssn: '999-00-1111' },
      disclosurePolicy,
      accountScope: 'acct-1',
      verifyAccount: async () => 'acct-1',
      verificationId: 'portal-v1',
      task: 'Fill applicant name',
      planner: {
        identity: { model: 'controlled' },
        next: async ({ observation }) => observation.elements[0].value
          ? { tool: 'finish', input: { summary: 'Done' } }
          : { tool: 'act', input: { kind: 'fill', handle: 'applicant', slot: 'name' } },
      },
      config: { maxTurns: 4, maxInputBytes: 20000 },
      store: invStore,
      projectId: 'p1',
      verifyReview: async () => ({ completed: enteredName === 'SECRET_APPLICANT_NAME' }),
      signal: new AbortController().signal,
    });
    assert.equal(learnRes.completed, true);
    assert.equal(learnRes.remotePublication.status, 'published');

    // Verify SQLite DB on server contains ZERO private applicant values!
    const dbDump = JSON.stringify(await dbStore.all('SELECT * FROM recipe_edges'));
    assert.ok(!dbDump.includes('SECRET_APPLICANT_NAME'));
    assert.ok(!dbDump.includes('999-00-1111'));

    // Second session reuses the server-managed recipe with 0 planner calls!
    enteredName = '';
    invStore.create({ id: 'p2', goal: 'Apply reuse' });
    const reuseRes = await alphaClient.runWorkflow({
      scope: 'workspace',
      mode: 'reuse',
      limits,
      service: mkFormSvc(),
      owner: {}, pageId: 'main', intent: 'form', template: 'portal-apply',
      inputs: { name: 'SECOND_APPLICANT', ssn: '999-00-2222' },
      disclosurePolicy,
      accountScope: 'acct-1',
      verifyAccount: async () => 'acct-1',
      verificationId: 'portal-v1',
      task: 'Fill applicant name',
      planner: { next: () => { throw Error('Planner must not be called on managed recipe hit'); } },
      config: { maxTurns: 4, maxInputBytes: 20000 },
      store: invStore,
      projectId: 'p2',
      verifyReview: async () => ({ completed: enteredName === 'SECOND_APPLICANT' }),
      signal: new AbortController().signal,
    });
    assert.equal(reuseRes.completed, true);
    assert.equal(reuseRes.modelCalls, 0);

    // Zero-trust test: poison the server DB edge to request 'ssn' instead of 'name' -> client refuses locally!
    await dbStore.run("UPDATE recipe_edges SET slot_name = 'ssn' WHERE slot_name = 'name'");
    enteredName = '';
    const victimSvc = mkFormSvc();
    invStore.create({ id: 'p3', goal: 'Poisoned check' });
    const poisonedRes = await alphaClient.runWorkflow({
      scope: 'workspace',
      mode: 'reuse',
      publishLearned: false,
      limits,
      service: victimSvc,
      owner: {}, pageId: 'main', intent: 'form', template: 'portal-apply',
      inputs: { name: 'THIRD_APPLICANT', ssn: '999-00-3333' },
      disclosurePolicy,
      accountScope: 'acct-1',
      verifyAccount: async () => 'acct-1',
      verificationId: 'portal-v1',
      task: 'Fill applicant name',
      planner: { next: () => { throw Error('Must stop immediately on disclosure violation'); } },
      config: { maxTurns: 4, maxInputBytes: 20000 },
      store: invStore,
      projectId: 'p3',
      verifyReview: async () => ({ completed: false }),
      signal: new AbortController().signal,
    });
    assert.equal(poisonedRes.completed, false);
    assert.match(poisonedRes.detail, /violates local slot disclosure/);
    assert.equal(victimSvc.calls, 0, 'Poisoned remote recipe never reaches browser dispatch');
  } finally {
    invStore.close();
  }

  console.log('ok: managed recipe service sub-recipe authoring, cross-template composition, loop/detour compression, quorum promotion, empirical Bellman DP and zero-trust client fence');
} finally {
  await new Promise(resolve => server.close(resolve));
  dbStore.close();
  rmSync(root, { recursive: true, force: true });
}
