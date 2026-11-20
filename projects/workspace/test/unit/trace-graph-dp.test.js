import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { TraceDag } from '../../src/client/trace-dag.js';
import { compressTraceRecords } from '../../src/client/trace-graph-dp.js';
import { InvestigationStore } from '../../src/client/investigation.js';
import { runWorkflow } from '../../src/client/workflow-agent.js';
import { structuralLocator } from '../../src/adapters/page-query.js';

const limits = { maxNodes: 64, maxEdges: 64, maxSteps: 12 };
const textbox = (label, handle = label.toLowerCase().replace(/\s+/g, '-')) => ({
  handle, selector: `#${handle}`, digest: `d-${handle}`,
  role: 'textbox', label, tag: 'input', inputType: 'text', value: '',
});
const selectBox = (label, handle = label.toLowerCase().replace(/\s+/g, '-')) => ({
  handle, selector: `#${handle}`, digest: `d-${handle}`,
  role: 'combobox', label, tag: 'select', inputType: 'select-one', value: '',
});
const btn = (label, handle = label.toLowerCase().replace(/\s+/g, '-')) => ({
  handle, selector: `#${handle}`, digest: `d-${handle}`,
  role: 'button', label, tag: 'button', inputType: '', value: '',
});

// 1. Intra-trace loop contraction (wandering modal detour + duplicate fill).
{
  const rawRecords = [
    { id: 's0', depth: 0, step: { kind: 'click', locator: 'l-help', slot: null }, next: 's-modal' },
    { id: 's-modal', depth: 1, step: { kind: 'click', locator: 'l-close', slot: null }, next: 's0' },
    { id: 's0', depth: 2, step: { kind: 'fill', locator: 'l-q', slot: 'slot-q' }, next: 's1' },
    { id: 's1', depth: 3, step: { kind: 'fill', locator: 'l-q', slot: 'slot-q' }, next: 's1' },
  ];
  const contracted = compressTraceRecords(rawRecords, { id: 's1', depth: 4 });
  assert.equal(contracted.contractedSteps, 3);
  assert.equal(contracted.records.length, 1);
  assert.equal(contracted.records[0].id, 's0');
  assert.equal(contracted.records[0].next, 's1');
  assert.equal(contracted.terminal.depth, 1);
}

// 2. Graph compression: dominated pure-click detour pruning and orphan node collection.
{
  const openMenu = btn('Open menu', 'menu');
  const openSubmenu = btn('Catalog submenu', 'submenu');
  const quickSearch = btn('Quick search', 'quick');
  const queryInput = textbox('Query', 'query');
  const allClicks = [openMenu, openSubmenu, quickSearch].map(structuralLocator);

  function navService(startStage = 'home') {
    let stage = startStage, version = 0, queryValue = '';
    const executed = [];
    const screens = {
      home: [openMenu, quickSearch],
      menu: [openSubmenu],
      search: [{ ...queryInput, value: queryValue }],
    };
    return {
      executed,
      queryValue: () => queryValue,
      outstanding: async () => [],
      observe: async () => ({
        url: 'https://fixture.invalid/catalog',
        observationVersion: ++version,
        isTruncated: false,
        elements: (stage === 'search' ? [{ ...queryInput, value: queryValue }] : screens[stage]),
      }),
      submitAction: async command => {
        executed.push(command.target.handle);
        if (command.target.handle === 'menu') stage = 'menu';
        else if (command.target.handle === 'submenu' || command.target.handle === 'quick') stage = 'search';
        else if (command.target.handle === 'query') queryValue = command.params.value;
        return { result: Promise.resolve({ outcome: 'completed' }) };
      },
    };
  }

  const baseOpts = service => ({
    service, owner: {}, pageId: 'main', intent: 'lookup', template: 'detour-compression',
    inputs: { query: 'bellman' }, intermediateClicks: allClicks,
  });

  const dag = new TraceDag(limits);
  // First learn clumsy 3-step route: Home -> Menu -> Search -> Fill(Query) (4 nodes, 3 edges).
  const detourSession = dag.session(baseOpts(navService('home')));
  assert.equal((await detourSession.record({ kind: 'click', locator: structuralLocator(openMenu) })).status, 'completed');
  assert.equal((await detourSession.record({ kind: 'click', locator: structuralLocator(openSubmenu) })).status, 'completed');
  assert.equal((await detourSession.record({ kind: 'fill', locator: structuralLocator(queryInput), slot: 'query' })).status, 'completed');
  assert.equal((await detourSession.finish()).reason, 'recorded-submit-boundary');
  assert.equal(dag.nodes.size, 4);

  // Now learn 2-step direct route: Home -> Search -> Fill(Query).
  // Search reconverges onto the existing Search node, and reduction prunes Home->Menu->Search!
  const directSession = dag.session(baseOpts(navService('home')));
  assert.equal((await directSession.record({ kind: 'click', locator: structuralLocator(quickSearch) })).status, 'completed');
  assert.equal((await directSession.record({ kind: 'fill', locator: structuralLocator(queryInput), slot: 'query' })).status, 'completed');
  assert.equal((await directSession.finish()).reason, 'recorded-submit-boundary');

  const stats = dag.compressionStats();
  assert.equal(stats.nodeCount, 3, 'Orphaned menu detour node is compressed out');
  assert.equal(stats.edgeCount, 2, 'Dominated detour edges are pruned');

  const replaySvc = navService('home');
  const replay = await dag.session(baseOpts(replaySvc)).replay();
  assert.equal(replay.reason, 'submit-boundary');
  assert.equal(replay.steps, 2);
  assert.deepEqual(replaySvc.executed, ['quick', 'query']);
}

// 3. Commuting fill diamond reconvergence, confluent DP tie-breaking, and mid-form entry.
{
  const nameField = textbox('Full name', 'name');
  const cityField = textbox('City', 'city');
  const nextBtn = btn('Review', 'review');
  const submitBtn = { ...btn('Submit', 'submit'), inputType: 'submit', formAction: true };

  function formService(prefilled = {}) {
    let stage = 0, version = 0;
    const values = { ...prefilled };
    const calls = [];
    return {
      calls,
      values,
      outstanding: async () => [],
      observe: async () => ({
        url: 'https://fixture.invalid/apply',
        observationVersion: ++version,
        isTruncated: false,
        elements: stage === 0
          ? [{ ...nameField, value: values.name ?? '' }, { ...cityField, value: values.city ?? '' }, nextBtn]
          : [submitBtn],
      }),
      submitAction: async command => {
        calls.push(command.target.handle);
        if (command.kind === 'click') stage = 1;
        else values[command.target.handle] = command.params.value;
        return { result: Promise.resolve({ outcome: 'completed' }) };
      },
    };
  }

  const opts = service => ({
    service, owner: {}, pageId: 'main', intent: 'form', template: 'diamond-form',
    inputs: { name: 'Ada Lovelace', city: 'London' },
    intermediateClicks: [structuralLocator(nextBtn)],
  });

  const dag = new TraceDag(limits);
  // Path A: Name -> City -> Review
  const s1 = dag.session(opts(formService()));
  await s1.record({ kind: 'fill', locator: structuralLocator(nameField), slot: 'name' });
  await s1.record({ kind: 'fill', locator: structuralLocator(cityField), slot: 'city' });
  await s1.record({ kind: 'click', locator: structuralLocator(nextBtn) });
  await s1.finish();

  // Path B: City -> Name -> Review (reconverges at {city, name} before Review!)
  const s2 = dag.session(opts(formService()));
  await s2.record({ kind: 'fill', locator: structuralLocator(cityField), slot: 'city' });
  await s2.record({ kind: 'fill', locator: structuralLocator(nameField), slot: 'name' });
  await s2.record({ kind: 'click', locator: structuralLocator(nextBtn) });
  await s2.finish();

  const stats = dag.compressionStats();
  // Nodes: Start([]), [name], [city], [city,name], Terminal = 5 nodes (instead of 7 unmerged!).
  assert.equal(stats.nodeCount, 5);
  assert.equal(stats.sharedMergeNodes, 1);
  assert.equal(stats.confluentDiamonds, 1);

  // Confluent diamond replays deterministically without 'ambiguous-branch'.
  const fullSvc = formService();
  const fullReplay = await dag.session(opts(fullSvc)).replay();
  assert.equal(fullReplay.reason, 'submit-boundary');
  assert.equal(fullReplay.steps, 3);
  assert.equal(fullSvc.values.name, 'Ada Lovelace');
  assert.equal(fullSvc.values.city, 'London');

  // Pre-filled mid-form entry: Name is already filled on load -> skips Name and only fills City + Review!
  const midSvc = formService({ name: 'Ada Lovelace' });
  const midReplay = await dag.session(opts(midSvc)).replay();
  assert.equal(midReplay.reason, 'submit-boundary');
  assert.equal(midReplay.steps, 2);
  assert.deepEqual(midSvc.calls, ['city', 'review']);
}

// 4. Bellman DP: weighted cost selection, slot feasibility filtering, and branch reliability.
{
  const fastField = textbox('Express code', 'fast');
  const slowField = textbox('Manual code', 'slow');
  function dualService(unreliableManual = false) {
    let version = 0, mode = 'entry';
    const calls = [];
    return {
      calls,
      outstanding: async () => [],
      observe: async () => ({
        url: 'https://fixture.invalid/dual',
        observationVersion: ++version,
        isTruncated: false,
        elements: mode === 'entry' ? [fastField, slowField]
          : mode === 'surprise' ? [textbox('Unexpected captcha-free notice', 'notice')]
            : [fastField, slowField],
      }),
      submitAction: async command => {
        calls.push(command.target.handle);
        if (unreliableManual && command.target.handle === 'slow') mode = 'surprise';
        return { result: Promise.resolve({ outcome: 'completed' }) };
      },
    };
  }

  const dag = new TraceDag(limits);
  const opts = (service, inputs = { fast: 'EXP-1', slow: 'MAN-1' }) => ({
    service, owner: {}, pageId: 'main', intent: 'form', template: 'dp-choice', inputs,
  });

  // Record weighted edges: fast has weight 0.5, slow has weight 2.0.
  const rFast = dag.session(opts(dualService()));
  await rFast.record({ kind: 'fill', locator: structuralLocator(fastField), slot: 'fast' }, null, { weight: 0.5 });
  await rFast.finish();

  const rSlow = dag.session(opts(dualService()));
  await rSlow.record({ kind: 'fill', locator: structuralLocator(slowField), slot: 'slow' }, null, { weight: 2.0 });
  await rSlow.finish();

  // Both slots supplied: Bellman DP picks 'fast' (Q = 0.5 < Q = 2.0).
  const bothSvc = dualService();
  const bestReplay = await dag.session(opts(bothSvc)).replay();
  assert.equal(bestReplay.reason, 'submit-boundary');
  assert.deepEqual(bothSvc.calls, ['fast']);

  // Only 'slow' slot supplied: 'fast' is infeasible, so Bellman DP selects 'slow' cleanly.
  const slowOnlySvc = dualService();
  const constrainedReplay = await dag.session(opts(slowOnlySvc, { slow: 'MAN-ONLY' })).replay();
  assert.equal(constrainedReplay.reason, 'submit-boundary');
  assert.deepEqual(slowOnlySvc.calls, ['slow']);

  // Branch reliability DP: equal step weight (1.0), but 'slow' also recorded a non-terminal outcome.
  const relDag = new TraceDag(limits);
  const sFast = relDag.session(opts(dualService()));
  await sFast.record({ kind: 'fill', locator: structuralLocator(fastField), slot: 'fast' });
  await sFast.finish();
  const sSlowOk = relDag.session(opts(dualService(false)));
  await sSlowOk.record({ kind: 'fill', locator: structuralLocator(slowField), slot: 'slow' });
  await sSlowOk.finish();
  // Inject a second non-terminal outcome on the 'slow' action (simulating 50% popup miss -> replan penalty).
  const exported = relDag.export();
  const rootEntry = exported.nodes.find(([, node]) => node.edges.length === 2);
  const slowEdge = rootEntry[1].edges.find(edge => edge.step.slot === relDag.hash(['slot', 'slow']));
  const missNodeId = relDag.hash(['miss-outcome']);
  exported.nodes.push([missNodeId, { depth: 1, edges: [], repairs: [], terminal: false }]);
  rootEntry[1].edges.push({ next: missNodeId, step: structuredClone(slowEdge.step) });
  const restoredRel = TraceDag.restore(exported, limits);
  const relSvc = dualService();
  const relReplay = await restoredRel.session(opts(relSvc)).replay();
  assert.equal(relReplay.reason, 'submit-boundary');
  assert.deepEqual(relSvc.calls, ['fast'], 'DP selects 100%-reliable branch over 50%-miss branch');
}

// 5. Modular Recipe Composition (TraceDag.composeAll) + Mid-Recipe Screen Entry.
{
  const openDrawer = btn('Open drawer', 'open-drawer');
  const searchBox = textbox('Search catalog', 'search');
  const openDetails = btn('Inspect item', 'inspect');
  const formatSelect = selectBox('Export format', 'format');
  const clicks = [openDrawer, openDetails].map(structuralLocator);

  function pipelineService(initialStage = 'closed') {
    let stage = initialStage, version = 0;
    const state = { query: '', format: '' };
    const calls = [];
    return {
      calls,
      state,
      stage: () => stage,
      outstanding: async () => [],
      observe: async () => ({
        url: 'https://fixture.invalid/workspace',
        observationVersion: ++version,
        isTruncated: false,
        elements: stage === 'closed' ? [openDrawer]
          : stage === 'drawer' ? [{ ...searchBox, value: state.query }, openDetails]
            : [{ ...formatSelect, value: state.format }],
      }),
      submitAction: async command => {
        calls.push(command.target.handle);
        if (command.target.handle === 'open-drawer') stage = 'drawer';
        else if (command.target.handle === 'search') state.query = command.params.value;
        else if (command.target.handle === 'inspect') stage = 'detail';
        else if (command.target.handle === 'format') state.format = command.params.value;
        return { result: Promise.resolve({ outcome: 'completed' }) };
      },
    };
  }

  const sharedKeyDag = () => {
    const g = new TraceDag(limits);
    g.key = 'a'.repeat(64);
    return g;
  };
  const opts = service => ({
    service, owner: {}, pageId: 'main', intent: 'export', template: 'modular-pipeline',
    inputs: { query: 'gpu-kernel', format: 'json' }, intermediateClicks: clicks,
  });

  // Sub-recipe 1: Closed -> Drawer
  const g1 = sharedKeyDag();
  const s1 = g1.session(opts(pipelineService('closed')));
  await s1.record({ kind: 'click', locator: structuralLocator(openDrawer) });
  await s1.finish();

  // Sub-recipe 2: Drawer -> Fill(query) -> Detail
  const g2 = sharedKeyDag();
  const s2 = g2.session(opts(pipelineService('drawer')));
  await s2.record({ kind: 'fill', locator: structuralLocator(searchBox), slot: 'query' });
  await s2.record({ kind: 'click', locator: structuralLocator(openDetails) });
  await s2.finish();

  // Sub-recipe 3: Detail -> Select(format)
  const g3 = sharedKeyDag();
  const s3 = g3.session(opts(pipelineService('detail')));
  await s3.record({ kind: 'select', locator: structuralLocator(formatSelect), slot: 'format' });
  await s3.finish();

  const composed = TraceDag.composeAll([g1.export(), g2.export(), g3.export()], limits);
  assert.equal(composed.compressionStats().terminalCount, 1, 'Intermediate sub-recipe terminals become interior bridges');
  assert.equal(composed.compressionStats().nodeCount, 5);

  // Full composed replay from stage 0 ('closed') runs all 4 steps!
  const e2eSvc = pipelineService('closed');
  const e2e = await composed.session(opts(e2eSvc)).replay();
  assert.equal(e2e.reason, 'submit-boundary');
  assert.equal(e2e.steps, 4);
  assert.deepEqual(e2eSvc.calls, ['open-drawer', 'search', 'inspect', 'format']);

  // Mid-recipe entry starting at 'drawer' runs remaining 3 steps!
  const midDrawerSvc = pipelineService('drawer');
  const midDrawer = await composed.session(opts(midDrawerSvc)).replay();
  assert.equal(midDrawer.reason, 'submit-boundary');
  assert.equal(midDrawer.steps, 3);
  assert.deepEqual(midDrawerSvc.calls, ['search', 'inspect', 'format']);

  // Mid-recipe entry starting at 'detail' runs remaining 1 step!
  const midDetailSvc = pipelineService('detail');
  const midDetail = await composed.session(opts(midDetailSvc)).replay();
  assert.equal(midDetail.reason, 'submit-boundary');
  assert.equal(midDetail.steps, 1);
  assert.deepEqual(midDetailSvc.calls, ['format']);
}

// 6. Mid-repair reconvergence (reconvergeMidRepair: true) cuts LLM calls and compresses suffix nodes.
{
  const root = mkdtempSync(join(tmpdir(), 'trace-dp-reconverge-'));
  const store = new InvestigationStore(root);
  try {
    const expand = ['button', 'Open library', 'button', ''];
    const search = ['textbox', 'Search components', 'input', 'search'];
    const nextBtn = ['button', 'Open details', 'button', ''];
    const filter = ['textbox', 'Filter version', 'input', 'text'];

    function uiPage(collapsed = false) {
      let stage = collapsed ? 'collapsed' : 'open', queryVal = '', filterVal = '', version = 0;
      const mk = ([role, label, tag, inputType], handle, val = '') => ({
        role, label, tag, inputType, handle, selector: `#${handle}`, digest: handle, value: val,
      });
      return {
        done: () => stage === 'detail' && queryVal === 'cache' && filterVal === 'v3',
        outstanding: async () => [],
        observe: async () => ({
          url: 'https://product.invalid/catalog',
          text: stage,
          observationVersion: ++version,
          isTruncated: false,
          elements: stage === 'collapsed' ? [mk(expand, 'expand')]
            : stage === 'open' ? [mk(search, 'search', queryVal), mk(nextBtn, 'next')]
              : [mk(filter, 'filter', filterVal)],
        }),
        submitAction: async req => {
          if (req.target.handle === 'expand') stage = 'open';
          else if (req.target.handle === 'search') queryVal = req.params.value;
          else if (req.target.handle === 'next') stage = 'detail';
          else if (req.target.handle === 'filter') filterVal = req.params.value;
          return { result: Promise.resolve({ outcome: 'completed', isUncertain: false }) };
        },
      };
    }

    const planner = {
      identity: { model: 'controlled' },
      next: async ({ observation, inputs }) => {
        const exp = observation.elements.find(e => e.handle === 'expand');
        if (exp) return { tool: 'act', input: { kind: 'click', handle: 'expand' } };
        const s = observation.elements.find(e => e.handle === 'search');
        if (s && s.value !== inputs.query) return { tool: 'act', input: { kind: 'fill', handle: 'search', slot: 'query' } };
        const n = observation.elements.find(e => e.handle === 'next');
        if (n) return { tool: 'act', input: { kind: 'click', handle: 'next' } };
        const f = observation.elements.find(e => e.handle === 'filter');
        if (f && f.value !== inputs.version) return { tool: 'act', input: { kind: 'fill', handle: 'filter', slot: 'version' } };
        return { tool: 'finish', input: { summary: 'Done' } };
      },
    };

    const dag = new TraceDag(limits);
    let seq = 0;
    const runCase = (svc, mode) => {
      const projectId = `reconv-${++seq}`;
      store.create({ id: projectId, goal: 'Catalog lookup' });
      return runWorkflow({
        dag, service: svc, mode, owner: {}, pageId: 'main', intent: 'lookup', template: 'reconv-lookup',
        inputs: { query: 'cache', version: 'v3' },
        intermediateClicks: [expand, nextBtn],
        observationLocators: [expand, search, nextBtn, filter],
        task: 'Find v3 cache component', planner,
        config: { maxTurns: 10, maxInputBytes: 20000 }, store, projectId,
        learnRepairs: true, reconvergeMidRepair: true,
        verifyReview: async () => ({ completed: svc.done() }),
        signal: new AbortController().signal,
      });
    };

    // Learn 3-step open-drawer flow (4 planner calls: fill search, click next, fill filter, finish -> 4 nodes, 3 edges).
    const learned = await runCase(uiPage(false), 'learn');
    assert.equal(learned.completed, true);
    assert.equal(learned.modelCalls, 4);
    assert.equal(dag.nodes.size, 4);

    // UI moves behind a collapsed drawer: only 1 planner call ('expand') is needed!
    // The remaining 3 suffix steps replay from cache automatically and publish only +1 node/+1 edge (5 nodes, 4 edges).
    const repaired = await runCase(uiPage(true), 'reuse');
    assert.equal(repaired.completed, true);
    assert.equal(repaired.modelCalls, 1, 'Mid-repair reconvergence reuses the 3-step suffix with zero extra LLM calls');
    assert.equal(repaired.cacheSteps, 3);
    assert.equal(dag.nodes.size, 5, 'Suffix nodes are shared rather than duplicated');
    assert.equal(dag.compressionStats().edgeCount, 4);

    // Subsequent runs from EITHER collapsed (4 steps) OR open (3 steps) use 0 planner calls!
    const fromCollapsed = await runCase(uiPage(true), 'reuse');
    assert.equal(fromCollapsed.completed, true);
    assert.equal(fromCollapsed.modelCalls, 0);
    assert.equal(fromCollapsed.cacheSteps, 4);

    const fromOpen = await runCase(uiPage(false), 'reuse');
    assert.equal(fromOpen.completed, true);
    assert.equal(fromOpen.modelCalls, 0);
    assert.equal(fromOpen.cacheSteps, 3);
  } finally {
    store.close();
    rmSync(root, { recursive: true, force: true });
  }
}

// 7. Multi-goal shared DAG: diverging click branches and intermediate goal pass-through with zero wrong actions.
{
  const filterBtn = btn('Filter catalog', 'filter-cat');
  const openProduct = btn('Open product', 'open-prod');
  const openCompliance = btn('Open compliance review', 'open-comp');
  const openQuote = btn('Open quote builder', 'open-quote');
  const fillQty = textbox('Quantity', 'qty');
  const calcQuote = btn('Calculate quote', 'calc');
  const clicks = [filterBtn, openProduct, openCompliance, openQuote, calcQuote].map(structuralLocator);

  function forkedPortal(startStage = 'home') {
    let stage = startStage, qty = '', version = 0;
    const actions = [];
    return {
      actions,
      stage: () => stage,
      qty: () => qty,
      outstanding: async () => [],
      observe: async () => ({
        url: 'https://portal.invalid/app',
        observationVersion: ++version,
        isTruncated: false,
        elements: stage === 'home' ? [filterBtn]
          : stage === 'filtered' ? [openProduct]
            : stage === 'overview' ? [openCompliance, openQuote]
              : stage === 'compliance' ? []
                : stage === 'quote-form' ? [{ ...fillQty, value: qty }, calcQuote]
                  : [],
      }),
      submitAction: async req => {
        actions.push(req.target.handle);
        if (req.target.handle === 'filter-cat') stage = 'filtered';
        else if (req.target.handle === 'open-prod') stage = 'overview';
        else if (req.target.handle === 'open-comp') stage = 'compliance';
        else if (req.target.handle === 'open-quote') stage = 'quote-form';
        else if (req.target.handle === 'qty') qty = req.params.value;
        else if (req.target.handle === 'calc') stage = 'quote-summary';
        return { result: Promise.resolve({ outcome: 'completed' }) };
      },
    };
  }

  const dag = new TraceDag(limits);
  const opts = (service, goal, inputs = {}) => ({
    service, owner: {}, pageId: 'main', intent: 'portal', template: 'shared-portal-v1',
    inputs, intermediateClicks: clicks, goal,
  });

  // Teach T1: home -> filtered -> overview -> compliance (shorter 1-step branch from overview!)
  const s1 = dag.session(opts(forkedPortal('home'), 'compliance-packet'));
  await s1.record({ kind: 'click', locator: structuralLocator(filterBtn) });
  await s1.record({ kind: 'click', locator: structuralLocator(openProduct) });
  await s1.record({ kind: 'click', locator: structuralLocator(openCompliance) });
  assert.equal((await s1.finish()).reason, 'recorded-submit-boundary');

  // Teach T2 starting at 'overview': overview -> quote-form -> qty -> calc (longer 3-step branch from overview!)
  const s2 = dag.session(opts(forkedPortal('overview'), 'shipping-quote', { quantity: '4' }));
  await s2.record({ kind: 'click', locator: structuralLocator(openQuote) });
  await s2.record({ kind: 'fill', locator: structuralLocator(fillQty), slot: 'quantity' });
  await s2.record({ kind: 'click', locator: structuralLocator(calcQuote) });
  assert.equal((await s2.finish()).reason, 'recorded-submit-boundary');

  // Confirm separate top-level goalTerminals table and restore validation.
  const exported = dag.export();
  assert.equal(Array.isArray(exported.goalTerminals), true);
  assert.equal(exported.goalTerminals.length, 2);
  const restored = TraceDag.restore(exported, limits);
  assert.equal(restored.compressionStats().terminalCount, 2);

  // Replay held-out composite: start at 'home' requesting 'shipping-quote' -> must take T1 prefix + T2 branch (zero wrong actions!).
  const compositeSvc = forkedPortal('home');
  const compositeReplay = await restored.session(opts(compositeSvc, 'shipping-quote', { quantity: '9' })).replay();
  assert.equal(compositeReplay.reason, 'submit-boundary');
  assert.deepEqual(compositeSvc.actions, ['filter-cat', 'open-prod', 'open-quote', 'qty', 'calc']);
  assert.equal(compositeSvc.qty(), '9');

  // Replay T1 goal from 'home' -> must still route to 'compliance-packet' cleanly.
  const compSvc = forkedPortal('home');
  const compReplay = await restored.session(opts(compSvc, 'compliance-packet')).replay();
  assert.equal(compReplay.reason, 'submit-boundary');
  assert.deepEqual(compSvc.actions, ['filter-cat', 'open-prod', 'open-comp']);

  // Invalid goalTerminals pointing at a non-terminal node must be rejected on restore.
  const bad = structuredClone(exported);
  const nonTerm = bad.nodes.find(([, n]) => !n.terminal);
  bad.goalTerminals.push([dag.hash(['goal', 'illegal']), [nonTerm[0]]]);
  assert.throws(() => TraceDag.restore(bad, limits), /Invalid trace goalTerminals/);
}

console.log('ok: loop contraction, detour graph compression, diamond reconvergence, Bellman DP routing, modular recipe composition, mid-entry and mid-repair suffix takeover');
