import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { after, before, test } from 'node:test';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { blind, discovery, hashDirectory, maintenance, regress } from '../../qualification/workflow-generalization/three-arm-erpnext/erp-runner.mjs';
import { frozenFileSet as openProjectFrozenSet } from '../../qualification/workflow-generalization/three-arm/runner.mjs';

// A stand-in ERPNext: supplier quotations and purchase orders, submit, and the two accounts.
const store = new Map();
const counters = { quotation: 0, order: 0 };
// A later release that breaks what an arm learned: the order line no longer carries the quotation's name under that field.
const upgrade = { moveQuotationField: false };
let instances = -1;
const view = doc => {
  const data = structuredClone(doc);
  if (upgrade.moveQuotationField && data.doctype === 'Purchase Order') for (const item of data.items) { item.against_quotation = item.supplier_quotation; delete item.supplier_quotation; }
  return data;
};
const http = createServer(async (req, res) => {
  let text = '';
  for await (const chunk of req) text += chunk;
  const body = text ? JSON.parse(text) : {};
  const send = (status, value) => { res.statusCode = status; res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(value)); };
  const url = decodeURIComponent(req.url.split('?')[0]);
  const made = url.match(/^\/api\/resource\/(Supplier Quotation|Purchase Order)$/);
  if (req.method === 'POST' && made) {
    const kind = made[1] === 'Purchase Order' ? 'order' : 'quotation';
    counters[kind] += 1;
    const name = `${kind === 'order' ? 'PUR-ORD' : 'PUR-SQTN'}-2026-${String(counters[kind]).padStart(5, '0')}`;
    const doc = { doctype: made[1], name, docstatus: 0, company: body.company, items: body.items, total_qty: body.items.reduce((n, i) => n + i.qty, 0),
      terms: '', modified: `2026-02-01 00:00:${String(store.size).padStart(2, '0')}.000000`, versions: 0 };
    store.set(name, doc);
    return send(200, { data: view(doc) });
  }
  if (req.method === 'POST' && url === '/api/method/frappe.client.submit') {
    const doc = store.get(body.doc?.name);
    if (!doc) return send(404, { exception: 'DoesNotExistError' });
    doc.docstatus = 1;
    return send(200, { message: view(doc) });
  }
  const one = url.match(/^\/api\/resource\/(Supplier Quotation|Purchase Order)\/(.+)$/);
  if (req.method === 'GET' && one && store.has(one[2])) return send(200, { data: view(store.get(one[2])) });
  return send(404, { exception: 'DoesNotExistError' });
});

let dir;
let deps;
const recipe = (routeId, quotationQty, submit, orderQty, entryBranch, reference) => ({
  routeId, familyId: 'fam', entryBranch,
  setup: [
    { as: 'approver', method: 'POST', path: '/api/resource/Supplier%20Quotation', body: { company: 'Stage2 Qual Corp', items: [{ item_code: 'STAGE2-UNIT', qty: quotationQty, rate: 100 }] }, save: { quotation: 'data.name', quotationDoc: 'data' } },
    ...(submit ? [{ as: 'approver', method: 'POST', path: '/api/method/frappe.client.submit', body: { doc: '{quotationDoc}' } }] : []),
    { as: 'author', method: 'POST', path: '/api/resource/Purchase%20Order', body: { company: 'Stage2 Qual Corp', items: [{ item_code: 'STAGE2-UNIT', qty: orderQty, rate: 100, supplier_quotation: '{quotation}' }] }, save: { order: 'data.name' } },
  ],
  target: { doctype: 'Purchase Order', name: '{order}' }, write: { reference },
});

before(async () => {
  await new Promise(done => http.listen(0, '127.0.0.1', done));
  dir = mkdtempSync(join(tmpdir(), 'three-arm-erp-'));
  writeFileSync(join(dir, 'state.json'), JSON.stringify({ username: 'u', password: 'p', mariadbContainer: 'none',
    new: { url: `http://127.0.0.1:${http.address().port}`, database: 'none', tag: 'stand-in', seed: { authorToken: 'k:a', approverToken: 'k:b' } } }));
  writeFileSync(join(dir, 'families.json'), JSON.stringify({ families: [{ familyId: 'fam',
    policy: 'Confirm an order only while the supplier quotation it was raised from is submitted and is for the same total quantity.',
    disclosedExample: recipe('disclosed', 10, true, 10, 'direct', 'CONF-0001') }] }));
  writeFileSync(join(dir, 'blind.json'), JSON.stringify({ recipes: [
    recipe('r-1', 12, true, 12, 'order-list', 'CONF-1001'),
    recipe('r-2', 12, false, 12, 'direct', 'CONF-1002'),
    recipe('r-3', 5, true, 12, 'more-info-tab', 'CONF-1003'),
  ] }));
  const row = name => { const d = store.get(name); return { modified: d.modified, docstatus: d.docstatus, totalQty: d.total_qty, termsLength: d.terms.length, versionCount: d.versions }; };
  deps = {
    executable: fileURLToPath(new URL('../support/fake-claude-erpnext.mjs', import.meta.url)),
    stateFile: join(dir, 'state.json'),
    // A new database does not hand out the same names again.
    freshInstance() { store.clear(); instances += 1; counters.quotation = 100 * instances; counters.order = 100 * instances; },
    stopInstance() {},
    async openWriter() {
      return { readRow: row, close: async () => {}, holdsReference: (name, reference) => store.get(name).terms.includes(reference),
        async write(route) {
          const before = row(route.name);
          const d = store.get(route.name);
          d.terms += route.reference; d.versions += 1; d.modified = `${d.modified}+`;
          return { httpStatus: 200, before, after: row(route.name), committed: true, effectMatches: true, wallMs: 1, error: null };
        } };
    },
    async guardRunner({ guardDir, route, get }) {
      const guard = await import(`${pathToFileURL(join(guardDir, 'guard.mjs')).href}?t=${Date.now()}`);
      let reads = 0;
      const answer = await guard.decide({ ...route, get: path => { reads += 1; return get(path); } });
      return { decision: answer.decision, reason: answer.reason, error: null, reads };
    },
  };
});
after(() => { http.close(); rmSync(dir, { recursive: true, force: true }); });

const lines = (run, name) => readFileSync(join(dir, run, name), 'utf8').trim().split('\n').map(l => JSON.parse(l));
const ARMS = ['agent-written-guard', 'repair-boundary', 'always-replan'];

test('building the ERPNext runner left the frozen OpenProject runner untouched', () => {
  assert.equal(openProjectFrozenSet().sha256, '8e7361e2521fcd95d025e50646a33a412ff15dc75d512fa10fa4578d4583c890');
});

test('ERPNext: discovery freezes each arm, then three routes are decided, written and recorded without labels', async () => {
  const runDir = join(dir, 'run');
  const common = { familiesFile: join(dir, 'families.json'), runDir, approvePaid: true, deps };
  for (const arm of ARMS) {
    const phase = await discovery({ ...common, arm });
    assert.equal(phase.completed, true, arm);
    assert.equal(phase.outOfSurfaceCalls, 0, arm);
    assert.equal(phase.application, 'erpnext');
  }
  const learned = JSON.parse(readFileSync(join(runDir, 'artifacts', 'repair-boundary.json'), 'utf8')).families.fam.boundary;
  assert.equal(learned.status, 'learned');
  assert.deepEqual(learned.guard.map(t => t.kind).sort(), ['equals-field', 'equals-literal']);
  const kept = arm => JSON.parse(readFileSync(join(runDir, 'artifacts', `${arm}.regression.json`), 'utf8'));
  assert.deepEqual(kept('agent-written-guard').cases.map(c => c.expect), ['write', 'stop']);
  assert.deepEqual(kept('repair-boundary').cases.map(c => c.expect), ['write', 'write', 'stop', 'stop']);
  const summary = arm => JSON.parse(readFileSync(join(runDir, 'logs', `discovery-${arm}.summary.json`), 'utf8')).keptCases;
  assert.deepEqual([summary('agent-written-guard').passingAtFreeze, summary('repair-boundary').passingAtFreeze], [2, 4]);

  for (const arm of ARMS) await blind({ ...common, arm, recipesFile: join(dir, 'blind.json') });
  const routes = lines('run', 'route-records.jsonl');
  assert.equal(routes.length, 9);
  for (const arm of ARMS) {
    assert.deepEqual(routes.filter(r => r.arm === arm).map(r => [r.routeId, r.decision, r.writeAttempted, r.committed, r.effectMatches]),
      [['r-1', 'write', true, true, true], ['r-2', 'stop', false, false, false], ['r-3', 'stop', false, false, false]], arm);
  }
  assert.ok(routes.every(r => !('valid' in r) && !('label' in r) && r.application === 'erpnext' && typeof r.reference === 'string'));
  assert.ok(routes.every(r => r.reads >= 1 && r.reads <= 8));
});

test('ERPNext: kept cases are rebuilt under new names and rerun; a release that moves a field is caught', async () => {
  const common = { familiesFile: join(dir, 'families.json'), runDir: join(dir, 'run'), deps };
  for (const arm of ['agent-written-guard', 'repair-boundary']) {
    const same = await regress({ ...common, arm });
    assert.equal(same.rebuilt, true, arm);
    assert.equal(same.passed, same.total, arm);
    assert.ok(same.results.every(r => /-0(0[1-9]|[1-9])\d\d$/.test(r.name)), 'names differ on the new database');
  }
  upgrade.moveQuotationField = true;
  try {
    for (const arm of ['agent-written-guard', 'repair-boundary']) {
      const moved = await regress({ ...common, arm });
      assert.deepEqual(moved.failedFamilies, ['fam'], arm);
      assert.ok(moved.results.some(r => r.expect === 'write' && r.got === 'stop'), arm);
    }
  } finally { upgrade.moveQuotationField = false; }
});

test('ERPNext: maintenance starts from the frozen work and the routes are decided on the newer release', async () => {
  const fromRunDir = join(dir, 'run');
  const runDir = join(dir, 'run-2');
  const common = { familiesFile: join(dir, 'families.json'), runDir, approvePaid: true, upgrade: '15.20.0->15.30.0', deps };
  for (const arm of ARMS) {
    const phase = await maintenance({ ...common, arm, fromRunDir });
    assert.equal(phase.completed, true, arm);
    assert.equal(phase.phase, 'maintenance');
  }
  for (const arm of ['agent-written-guard', 'repair-boundary']) await blind({ ...common, arm, recipesFile: join(dir, 'blind.json') });
  const routes = lines('run-2', 'route-records.jsonl');
  for (const arm of ['agent-written-guard', 'repair-boundary']) {
    assert.deepEqual(routes.filter(r => r.arm === arm).map(r => [r.routeId, r.decision, r.committed]), [['r-1', 'write', true], ['r-2', 'stop', false], ['r-3', 'stop', false]], arm);
  }
  assert.equal(hashDirectory(join(fromRunDir, 'artifacts', 'agent-written-guard')), lines('run', 'phase-records.jsonl')[0].artifactSha256);
});
