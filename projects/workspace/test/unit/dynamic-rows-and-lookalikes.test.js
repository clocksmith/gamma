import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { structuralLocator, structuralOutlineHash } from '../../src/adapters/page-query.js';
import { createFieldGroupScope } from '../../src/client/field-group-scope.js';
import { InvestigationStore } from '../../src/client/investigation.js';
import { TraceDag } from '../../src/client/trace-dag.js';
import { runWorkflow, scopeWorkflowObservation } from '../../src/client/workflow-agent.js';

const limits = { maxNodes: 64, maxEdges: 64, maxSteps: 16 };

function makeControl([role, label, tag, inputType], handle, { value = '', disabled = false, inert = false, visible = true } = {}) {
  return {
    role,
    label,
    tag,
    inputType,
    handle,
    selector: `#${handle}`,
    digest: `digest-${handle}-${label}-${disabled ? 'off' : 'on'}`,
    value,
    text: label,
    actionability: { visible, inert, disabled },
  };
}

// Intent-establishing controls across Screens A (Search), B (Item Brief), and C (Review Leaf)
const LOC_QUERY = ['textbox', 'Search inventory', 'input', 'search'];
const LOC_STATUS = ['combobox', 'Availability filter', 'select', ''];
const LOC_APPLY = ['button', 'Run inventory search', 'button', ''];
const LOC_OPEN_TOP = ['button', 'Open matched item brief', 'button', ''];
const LOC_GATE_OK = ['button', 'Confirm standard transfer terms', 'button', ''];
const LOC_GATE_LOOKALIKE = ['button', 'Accept uncapped liability waiver', 'button', ''];
const LOC_QTY = ['textbox', 'Transfer quantity', 'input', 'text'];
const LOC_PREPARE = ['button', 'Prepare transfer review', 'button', ''];

const ALLOWED_LOCATORS = [
  LOC_QUERY,
  LOC_STATUS,
  LOC_APPLY,
  LOC_OPEN_TOP,
  LOC_GATE_OK,
  LOC_QTY,
  LOC_PREPARE,
];

function dynamicRowElements(visitRows) {
  return visitRows.flatMap((row, idx) => [
    makeControl(['link', `${row.sku} - ${row.title} (${row.stock} in bin)`, 'a', ''], `row-link-${idx}`),
    makeControl(['link', `Page ${idx + 1} audit log`, 'a', ''], `page-link-${idx}`),
  ]);
}

const VISIT_1_ROWS = [
  { sku: 'LOT-104', title: 'Optic Transceiver 25G', stock: 18 },
  { sku: 'LOT-209', title: 'Patch Panel 48-Port', stock: 4 },
];
const VISIT_2_ROWS = [
  { sku: 'LOT-881', title: 'Thermal Sensor Array', stock: 42 },
  { sku: 'LOT-902', title: 'Redundant PSU Module', stock: 7 },
  { sku: 'LOT-944', title: 'DIN Rail Controller', stock: 11 },
  { sku: 'LOT-977', title: 'Fiber Splice Tray', stock: 29 },
];
const VISIT_3_ROWS = [
  { sku: 'LOT-512', title: 'Cold-Aisle Baffle Kit', stock: 3 },
];

// 1. Audit baseline: unscoped structuralOutlineHash ignores static prose changes,
//    but changes when interactive search/list result links vary across visits.
{
  const controlsV1 = [
    makeControl(LOC_QUERY, 'q'),
    makeControl(LOC_STATUS, 'status'),
    makeControl(LOC_APPLY, 'apply'),
    ...dynamicRowElements(VISIT_1_ROWS),
  ];
  const controlsV2 = [
    makeControl(LOC_QUERY, 'q'),
    makeControl(LOC_STATUS, 'status'),
    makeControl(LOC_APPLY, 'apply'),
    ...dynamicRowElements(VISIT_2_ROWS),
  ];
  assert.notEqual(
    structuralOutlineHash(controlsV1),
    structuralOutlineHash(controlsV2),
    'Unscoped outline includes interactive result-row link labels and therefore changes across dynamic list visits',
  );
}

// Deterministic multi-screen sandbox with visit-varying list rows and lookalike fault modes.
function createSandboxService({
  startScreen = 'A',
  visitRows = VISIT_1_ROWS,
  gateVariant = 'standard', // 'standard' | 'waiver-lookalike' | 'duplicate-ambiguous' | 'disabled-gate'
  proseBanner = 'Updated 09:00 UTC',
} = {}) {
  let screen = startScreen;
  let version = 0;
  let searched = false;
  const state = { query: '', status: '', qty: '' };
  const dispatched = [];

  return {
    dispatched,
    screen: () => screen,
    state: () => ({ ...state }),
    outstanding: async () => [],
    observe: async () => {
      let elements = [];
      if (screen === 'A') {
        elements = [
          makeControl(LOC_QUERY, 'query', { value: state.query }),
          makeControl(LOC_STATUS, 'status', { value: state.status }),
          makeControl(LOC_APPLY, 'apply'),
          ...(searched ? [makeControl(LOC_OPEN_TOP, 'open-top')] : []),
          ...dynamicRowElements(visitRows),
        ];
      } else if (screen === 'B') {
        const gateControls = gateVariant === 'waiver-lookalike'
          ? [makeControl(LOC_GATE_LOOKALIKE, 'gate-waiver')]
          : gateVariant === 'duplicate-ambiguous'
            ? [
                makeControl(LOC_GATE_OK, 'gate-ok-1'),
                makeControl(LOC_GATE_OK, 'gate-ok-2'),
              ]
            : gateVariant === 'disabled-gate'
              ? [makeControl(LOC_GATE_OK, 'gate-disabled', { disabled: true })]
              : [makeControl(LOC_GATE_OK, 'gate-ok')];
        elements = [...gateControls, ...dynamicRowElements(visitRows)];
      } else if (screen === 'C_FORM') {
        elements = [
          makeControl(LOC_QTY, 'qty', { value: state.qty }),
          makeControl(LOC_PREPARE, 'prepare'),
          ...dynamicRowElements(visitRows),
        ];
      } else if (screen === 'B_LEAF' || screen === 'C_LEAF' || screen === 'ALT_LEAF') {
        // Zero-control review leaf accompanied only by incidental dynamic audit links outside scope
        elements = [...dynamicRowElements(visitRows)];
      }
      return {
        url: `https://inventory.invalid/${screen.toLowerCase()}`,
        text: `${proseBanner} | screen=${screen} | rows=${visitRows.map(r => r.sku).join(',')}`,
        observationVersion: ++version,
        isTruncated: false,
        elements,
      };
    },
    submitAction: async command => {
      assert.equal(command.observationVersion, version);
      dispatched.push(command);
      if (command.kind === 'fill' || command.kind === 'select') {
        state[command.target.handle] = command.params.value;
      } else if (command.kind === 'click') {
        if (command.target.handle === 'apply') searched = true;
        else if (command.target.handle === 'open-top') screen = 'B';
        else if (command.target.handle.startsWith('gate-ok')) screen = 'C_FORM';
        else if (command.target.handle === 'prepare') screen = 'C_LEAF';
      }
      return { result: Promise.resolve({ outcome: 'completed', isUncertain: false }) };
    },
  };
}

const scriptedPlanner = targetGoal => ({
  identity: { model: 'controlled-unit' },
  next: async ({ observation, inputs }) => {
    const byHandle = h => observation.elements.find(e => e.handle === h);
    if (byHandle('query') && byHandle('query').value !== inputs.query) {
      return { tool: 'act', input: { kind: 'fill', handle: 'query', slot: 'query' } };
    }
    if (byHandle('status') && byHandle('status').value !== inputs.status) {
      return { tool: 'act', input: { kind: 'select', handle: 'status', slot: 'status' } };
    }
    if (byHandle('apply') && !byHandle('open-top')) {
      return { tool: 'act', input: { kind: 'click', handle: 'apply' } };
    }
    if (byHandle('open-top')) {
      return { tool: 'act', input: { kind: 'click', handle: 'open-top' } };
    }
    if (targetGoal === 'item-brief') {
      return { tool: 'finish', input: { summary: 'Item brief reached' } };
    }
    if (byHandle('gate-ok')) {
      return { tool: 'act', input: { kind: 'click', handle: 'gate-ok' } };
    }
    if (byHandle('qty') && byHandle('qty').value !== inputs.qty) {
      return { tool: 'act', input: { kind: 'fill', handle: 'qty', slot: 'qty' } };
    }
    if (byHandle('prepare')) {
      return { tool: 'act', input: { kind: 'click', handle: 'prepare' } };
    }
    if (observation.elements.length === 0) {
      return { tool: 'finish', input: { summary: 'Transfer review ready' } };
    }
    return { tool: 'ask_human', input: { reason: 'Unexpected or unsafe screen' } };
  },
});

const tempRoot = mkdtempSync(join(tmpdir(), 'fawn-dynamic-lookalike-'));
const invStore = new InvestigationStore(tempRoot);
let runSeq = 0;

async function execWorkflow({
  dag,
  service,
  mode,
  goal,
  accountScope = 'prod-ops',
  observationLocators = ALLOWED_LOCATORS,
  inputs = { query: 'optic', status: 'in-stock', qty: '5' },
  verifyReview,
  planner = scriptedPlanner(goal),
}) {
  const projectId = `dyn-${++runSeq}`;
  invStore.create({ id: projectId, goal: `Goal ${goal}` });
  return runWorkflow({
    dag,
    mode,
    goal,
    accountScope,
    service,
    owner: {},
    pageId: 'main',
    intent: 'inventory-transfer',
    template: 'inventory-workflow',
    inputs,
    intermediateClicks: [LOC_APPLY, LOC_OPEN_TOP, LOC_GATE_OK, LOC_PREPARE],
    observationLocators,
    learnRepairs: true,
    reconvergeMidRepair: true,
    task: `Complete ${goal}`,
    planner,
    config: { maxTurns: 14, maxInputBytes: 24000 },
    store: invStore,
    projectId,
    verifyReview,
    signal: new AbortController().signal,
  });
}

try {
  // 2. Scoped dynamic-row invariance + held-out A->C graph composition across 3 changing row sets:
  //    Teach A->B on Visit 1 rows, teach B->C on Visit 2 rows, then compose held-out A->C on Visit 3 rows
  //    with 0 planner calls despite completely different list links and banners on every visit.
  const dag = new TraceDag(limits);

  const sTeachAB = createSandboxService({ startScreen: 'A', visitRows: VISIT_1_ROWS, proseBanner: 'Visit 1' });
  const rTeachAB = await execWorkflow({
    dag,
    service: sTeachAB,
    mode: 'learn',
    goal: 'item-brief',
    verifyReview: async () => ({ completed: sTeachAB.screen() === 'B' }),
  });
  assert.equal(rTeachAB.completed, true);
  assert.equal(rTeachAB.modelCalls, 5);

  const sTeachBC = createSandboxService({ startScreen: 'B', visitRows: VISIT_2_ROWS, proseBanner: 'Visit 2' });
  const rTeachBC = await execWorkflow({
    dag,
    service: sTeachBC,
    mode: 'learn',
    goal: 'transfer-review',
    verifyReview: async () => ({ completed: sTeachBC.screen() === 'C_LEAF' && sTeachBC.state().qty === '5' }),
  });
  assert.equal(rTeachBC.completed, true);
  assert.equal(rTeachBC.modelCalls, 4);

  // Exact A->B replay under Visit 2's 4-row list -> 0 model calls
  const sReplayAB = createSandboxService({
    startScreen: 'A',
    visitRows: VISIT_2_ROWS,
    proseBanner: 'Visit 2 replay',
  });
  const rReplayAB = await execWorkflow({
    dag,
    service: sReplayAB,
    mode: 'reuse',
    goal: 'item-brief',
    inputs: { query: 'thermal', status: 'all', qty: '2' },
    verifyReview: async () => ({ completed: sReplayAB.screen() === 'B' && sReplayAB.state().query === 'thermal' }),
  });
  assert.equal(rReplayAB.completed, true);
  assert.equal(rReplayAB.modelCalls, 0);
  assert.equal(rReplayAB.cacheSteps, 4);

  // Held-out A->C composition under Visit 3's single-row list -> 0 model calls, all 7 steps replayed
  const sComposeAC = createSandboxService({
    startScreen: 'A',
    visitRows: VISIT_3_ROWS,
    proseBanner: 'Visit 3 held-out',
  });
  const rComposeAC = await execWorkflow({
    dag,
    service: sComposeAC,
    mode: 'reuse',
    goal: 'transfer-review',
    inputs: { query: 'baffle', status: 'in-stock', qty: '9' },
    verifyReview: async () => ({ completed: sComposeAC.screen() === 'C_LEAF' && sComposeAC.state().qty === '9' }),
  });
  assert.equal(rComposeAC.completed, true);
  assert.equal(rComposeAC.modelCalls, 0);
  assert.equal(rComposeAC.cacheSteps, 7);

  // 3. Lookalike Refusal A: identical DOM and controls under a different accountScope must never merge.
  const sWrongAccount = createSandboxService({ startScreen: 'A', visitRows: VISIT_1_ROWS });
  const scopedWrongAccount = scopeWorkflowObservation(sWrongAccount, 'inventory-workflow', ALLOWED_LOCATORS);
  const wrongAcctReplay = await dag.session({
    service: scopedWrongAccount.service,
    owner: {},
    pageId: 'main',
    intent: 'inventory-transfer',
    template: scopedWrongAccount.template,
    goal: 'transfer-review',
    accountScope: 'sandbox-guest',
    inputs: { query: 'optic', status: 'in-stock', qty: '5' },
    intermediateClicks: [LOC_APPLY, LOC_OPEN_TOP, LOC_GATE_OK, LOC_PREPARE],
    assertContext: async () => {},
    authorizeStep: async () => {},
  }).replay();
  assert.equal(wrongAcctReplay.steps, 0);
  assert.equal(wrongAcctReplay.reason, 'unseen-branch');
  assert.equal(sWrongAccount.dispatched.length, 0);

  // 4. Lookalike Refusal B: altered intent/allowed-control policy changes bound template identity -> 0 reuse.
  const narrowedLocators = ALLOWED_LOCATORS.filter(loc => loc !== LOC_GATE_OK);
  const sNarrowedPolicy = createSandboxService({ startScreen: 'A', visitRows: VISIT_1_ROWS });
  const narrowedScoped = scopeWorkflowObservation(sNarrowedPolicy, 'inventory-workflow', narrowedLocators);
  const narrowedReplay = await dag.session({
    service: narrowedScoped.service,
    owner: {},
    pageId: 'main',
    intent: 'inventory-transfer',
    template: narrowedScoped.template,
    goal: 'item-brief',
    accountScope: 'prod-ops',
    inputs: { query: 'optic', status: 'in-stock', qty: '5' },
    intermediateClicks: [LOC_APPLY, LOC_OPEN_TOP],
    assertContext: async () => {},
    authorizeStep: async () => {},
  }).replay();
  assert.equal(narrowedReplay.steps, 0);
  assert.equal(sNarrowedPolicy.dispatched.length, 0);

  // 5. Lookalike Refusal C: altered gate control ('Accept uncapped liability waiver') stops at Screen B
  //    without clicking the lookalike waiver button.
  const sWaiverGate = createSandboxService({
    startScreen: 'B',
    visitRows: VISIT_3_ROWS,
    gateVariant: 'waiver-lookalike',
  });
  const waiverScoped = scopeWorkflowObservation(
    sWaiverGate,
    'inventory-workflow',
    [...ALLOWED_LOCATORS, LOC_GATE_LOOKALIKE],
  );
  const waiverReplay = await dag.session({
    service: waiverScoped.service,
    owner: {},
    pageId: 'main',
    intent: 'inventory-transfer',
    template: scopeWorkflowObservation(sWaiverGate, 'inventory-workflow', ALLOWED_LOCATORS).template,
    goal: 'transfer-review',
    accountScope: 'prod-ops',
    inputs: { query: 'optic', status: 'in-stock', qty: '5' },
    intermediateClicks: [LOC_APPLY, LOC_OPEN_TOP, LOC_GATE_OK, LOC_PREPARE],
    assertContext: async () => {},
    authorizeStep: async () => {},
  }).replay();
  assert.equal(waiverReplay.steps, 0);
  assert.equal(waiverReplay.reason, 'unseen-branch');
  assert.equal(sWaiverGate.dispatched.length, 0);

  // 6. Lookalike Refusal D: duplicate target uniqueness violation stops both outline replay
  //    ('unseen-branch') and direct step execution ('ambiguous-locator') with 0 dispatched actions.
  const sDuplicateGate = createSandboxService({
    startScreen: 'B',
    visitRows: VISIT_2_ROWS,
    gateVariant: 'duplicate-ambiguous',
  });
  const dupScoped = scopeWorkflowObservation(sDuplicateGate, 'inventory-workflow', ALLOWED_LOCATORS);
  const dupOpts = {
    service: dupScoped.service,
    owner: {},
    pageId: 'main',
    intent: 'inventory-transfer',
    template: dupScoped.template,
    goal: 'transfer-review',
    accountScope: 'prod-ops',
    inputs: { query: 'optic', status: 'in-stock', qty: '5' },
    intermediateClicks: [LOC_APPLY, LOC_OPEN_TOP, LOC_GATE_OK, LOC_PREPARE],
    assertContext: async () => {},
    authorizeStep: async () => {},
  };
  const dupReplay = await dag.session(dupOpts).replay();
  assert.equal(dupReplay.steps, 0);
  assert.equal(dupReplay.reason, 'unseen-branch');
  const dupDirect = await dag.session(dupOpts).record({ kind: 'click', locator: LOC_GATE_OK });
  assert.equal(dupDirect.status, 'stopped');
  assert.equal(dupDirect.reason, 'ambiguous-locator');
  assert.equal(sDuplicateGate.dispatched.length, 0);

  // 7. Lookalike Refusal E: disabled control is excluded by actionability filter -> 0 dispatched actions.
  const sDisabledGate = createSandboxService({
    startScreen: 'B',
    visitRows: VISIT_1_ROWS,
    gateVariant: 'disabled-gate',
  });
  const disScoped = scopeWorkflowObservation(sDisabledGate, 'inventory-workflow', ALLOWED_LOCATORS);
  const disReplay = await dag.session({
    ...dupOpts,
    service: disScoped.service,
    template: disScoped.template,
  }).replay();
  assert.equal(disReplay.steps, 0);
  assert.equal(sDisabledGate.dispatched.length, 0);

  // 8. Lookalike Refusal F: zero-control review leaf disambiguates distinct goals (never false-completes).
  const sWrongGoal = createSandboxService({ startScreen: 'B', visitRows: VISIT_1_ROWS });
  const wrongGoalScoped = scopeWorkflowObservation(sWrongGoal, 'inventory-workflow', ALLOWED_LOCATORS);
  const wrongGoalReplay = await dag.session({
    ...dupOpts,
    service: wrongGoalScoped.service,
    template: wrongGoalScoped.template,
    goal: 'audit-export-never-taught',
  }).replay();
  assert.equal(wrongGoalReplay.steps, 0);
  assert.equal(sWrongGoal.dispatched.length, 0);

  // 9. Field-group boundary check: dynamic row links are ignored during field fill, while an unreviewed
  //    new interactive control at the transition boundary halts before clicking through.
  const fgScope = createFieldGroupScope([{
    id: 'search-group',
    steps: [
      { kind: 'fill', slot: 'query', locators: [LOC_QUERY] },
      { kind: 'click', locators: [LOC_APPLY] },
    ],
  }], 8);
  const fgVisit1 = { elements: [makeControl(LOC_QUERY, 'q'), makeControl(LOC_APPLY, 'a'), ...dynamicRowElements(VISIT_1_ROWS)] };
  const fgVisit2 = { elements: [makeControl(LOC_QUERY, 'q'), makeControl(LOC_APPLY, 'a'), ...dynamicRowElements(VISIT_2_ROWS)] };
  assert.deepEqual(
    fgScope.outline(fgVisit1, { groupIndex: 0, filledSlots: [] }),
    fgScope.outline(fgVisit2, { groupIndex: 0, filledSlots: [] }),
    'Field-group fill stage ignores changing list rows',
  );
  assert.notDeepEqual(
    fgScope.outline(fgVisit1, { groupIndex: 0, filledSlots: ['query'] }),
    fgScope.outline(fgVisit2, { groupIndex: 0, filledSlots: ['query'] }),
    'At transition boundary, unscoped extra elements remain visible unless readRoots/observationLocators scope them out',
  );
  // Hidden duplicate control inside field group throws Ambiguous
  assert.throws(
    () => fgScope.outline({
      elements: [
        makeControl(LOC_QUERY, 'q1'),
        makeControl(LOC_QUERY, 'q2-hidden', { visible: false }),
        makeControl(LOC_APPLY, 'a'),
      ],
    }, { groupIndex: 0, filledSlots: [] }),
    /Ambiguous field-group meaning/,
  );

  // 10. Legitimate lookalike page MUST succeed (no false refusal): redesigned banner prose,
  //     extra promotional links/buttons outside authorized controls, and unseen row links under
  //     the verified accountScope complete in 0 calls.
  const LEGIT_REDESIGN_ROWS = [
    { id: 'promo-link-1', label: 'New Q4 Warehouse Rebates Guide' },
    { id: 'promo-link-2', label: 'Download Updated Carrier Schedule' },
    { id: 'lot-999', label: 'SKU-CHASSIS-99: 4U Rack Enclosure (New Arrival)' },
  ];
  const sLegitLookalike = createSandboxService({
    startScreen: 'A',
    visitRows: LEGIT_REDESIGN_ROWS,
    proseBanner: 'Redesigned Q4 Enterprise Warehouse Header — Theme v2',
  });
  const rLegitLookalike = await execWorkflow({
    dag,
    service: sLegitLookalike,
    mode: 'reuse',
    goal: 'transfer-review',
    inputs: { query: 'chassis', status: 'in-stock', qty: '11' },
    verifyReview: async () => ({
      completed: sLegitLookalike.screen() === 'C_LEAF' && sLegitLookalike.state().qty === '11',
    }),
  });
  assert.equal(rLegitLookalike.completed, true, 'Legitimate lookalike redesign under verified account must succeed');
  assert.equal(rLegitLookalike.modelCalls, 0);
  assert.equal(rLegitLookalike.cacheSteps, 7);

  console.log('ok: dynamic-row scoped invariance, A->C composition, legitimate lookalike completion, and 6 unsafe refusals');
} finally {
  invStore.close();
  rmSync(tempRoot, { recursive: true, force: true });
}
