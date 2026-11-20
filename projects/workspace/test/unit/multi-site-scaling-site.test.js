import assert from 'node:assert/strict';
import {
  SCALING_SITES,
  allowedSiteLocators,
  buildDynamicVisitRows,
  buildMultiSiteScalingSpec,
  createControlledScalingPlanner,
  startMultiSiteScalingServer,
} from '../../qualification/multi-site-scaling-site.js';

const spec = buildMultiSiteScalingSpec();
assert.equal(spec.sites.length, 4);
assert.equal(spec.taskCount, 28, 'Scaling suite must contain 28 tasks (inside 24..30)');
assert.equal(spec.safetyCount, 4, 'One distinct lookalike/ambiguity safety case per site');
assert.equal(spec.orders.forward.tasks.length, 28);
assert.equal(spec.orders.mirrored.tasks.length, 28);

// Verify all 4 sites have genuinely distinct architectures, tag sets, and step counts
const architectures = new Set(SCALING_SITES.map(s => s.architecture));
assert.equal(architectures.size, 4, 'Each site must have a distinct DOM/control architecture');
const entryShapes = new Set(SCALING_SITES.map(s => s.entryFields.map(f => `${f.tag}:${f.inputType}`).join(',')));
assert.equal(entryShapes.size, 4, 'Entry form schemas must not be 4 copies of one template');
const primaryShapes = new Set(SCALING_SITES.map(s => s.primaryFields.map(f => `${f.tag}:${f.inputType}`).join(',')));
assert.equal(primaryShapes.size, 4, 'Primary form schemas must differ across all 4 sites');

// Forward and mirrored orders contain the exact same 28 taskIds while reversing per-round site order
const fwdIds = spec.orders.forward.tasks.map(t => t.taskId);
const mirIds = spec.orders.mirrored.tasks.map(t => t.taskId);
assert.deepEqual([...fwdIds].sort(), [...mirIds].sort());
assert.notDeepEqual(fwdIds.slice(0, 4), mirIds.slice(0, 4));
assert.deepEqual(fwdIds.slice(0, 4).reverse(), mirIds.slice(0, 4));

// Dynamic list rows rotate count and labels on every single visit
for (const site of SCALING_SITES) {
  const v1 = buildDynamicVisitRows(site, 1);
  const v2 = buildDynamicVisitRows(site, 2);
  const v3 = buildDynamicVisitRows(site, 3);
  assert.notDeepEqual(v1.map(r => r.label), v2.map(r => r.label));
  assert.notDeepEqual(v2.map(r => r.label), v3.map(r => r.label));
  assert.ok(allowedSiteLocators(site).fields.length >= 6);
}

// Verify Stock planner does NOT skip saved hAB helper on T3 (compose_ac)
for (const site of SCALING_SITES) {
  const t3 = spec.orders.forward.tasks.find(t => t.siteId === site.siteId && t.stageIndex === 3);
  const stockPlanner = createControlledScalingPlanner(site, t3, { isStock: true });
  const entryElements = [
    ...site.entryFields.map((f, idx) => ({
      handle: `h-${idx}`,
      label: f.label,
      tag: f.tag,
      inputType: f.inputType,
      value: f.kind === 'select' ? 'Choose' : '',
    })),
    { handle: 'h-search', label: site.labels.searchButton, tag: 'button', inputType: '', value: '' },
  ];
  const decision = await stockPlanner.next({
    inputs: t3.inputs,
    reusableHelpers: [
      { helperId: `${site.siteId}__search__record-brief`, siteId: site.siteId, startScreen: 'search', goal: 'record-brief', stepCount: site.entryFormSteps },
      { helperId: `${site.siteId}__brief__primary-review`, siteId: site.siteId, startScreen: 'brief', goal: 'primary-review', stepCount: site.primaryFormSteps + 2 },
    ],
    observation: { text: site.title, elements: entryElements },
  });
  assert.equal(decision.tool, 'call_helper', `Stock must invoke saved hAB helper on ${site.siteId} T3 instead of skipping it`);
  assert.equal(decision.input.helperId, `${site.siteId}__search__record-brief`);
}

// Verify live loopback HTTP server renders distinct DOM structures and rotates list items
const server = await startMultiSiteScalingServer();
try {
  const site = SCALING_SITES[0];
  const url = server.createSession('scale-s1', {
    siteId: site.siteId,
    startScreen: 'search',
    gateMode: 'v1',
    accountScope: site.accountScope,
    expectedAccountScope: site.accountScope,
    expectedGoal: 'primary-review',
  });
  const htmlVisit1 = await (await fetch(url)).text();
  const htmlVisit2 = await (await fetch(url)).text();
  assert.match(htmlVisit1, /Visit #1/);
  assert.match(htmlVisit2, /Visit #2/);
  assert.notEqual(htmlVisit1, htmlVisit2, 'Every visit renders changing list rows');

  // Verify distinct review tags across sites (<dl>, <section>, <table>, <article>)
  const briefTags = [];
  for (const s of SCALING_SITES) {
    const bUrl = server.createSession(`brief-${s.siteId}`, {
      siteId: s.siteId,
      startScreen: 'brief',
      query: { rec: s.records[0].id },
      gateMode: 'v1',
      accountScope: s.accountScope,
      expectedAccountScope: s.accountScope,
      expectedGoal: 'record-brief',
    });
    briefTags.push(await (await fetch(bUrl)).text());
  }
  assert.match(briefTags[0], /<dl>/);
  assert.match(briefTags[1], /<section class="incident-dossier">/);
  assert.match(briefTags[2], /<table>/);
  assert.match(briefTags[3], /<article class="vendor-profile">/);

  // Duplicate gate fault renders 2 identical buttons
  const helpdesk = SCALING_SITES[1];
  const dupUrl = server.createSession('scale-dup', {
    siteId: helpdesk.siteId,
    startScreen: 'gate',
    gateMode: 'duplicate-gate',
    accountScope: helpdesk.accountScope,
    expectedAccountScope: helpdesk.accountScope,
    expectedGoal: 'primary-review',
  });
  const dupHtml = await (await fetch(dupUrl)).text();
  const btnMatches = [...dupHtml.matchAll(new RegExp(helpdesk.labels.gateV1Button, 'g'))];
  assert.equal(btnMatches.length, 2);
} finally {
  await server.close();
}

console.log('ok: 28-task 4-distinct-site mirrored scaling spec, Stock helper reuse on T3, and immediate verifiers');
