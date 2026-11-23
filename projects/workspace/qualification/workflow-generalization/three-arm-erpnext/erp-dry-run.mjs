#!/usr/bin/env node
// Dry run of the ERPNext three-arm pipeline on the real application, with a
// stand-in for the model (clocksmith/deco#88). DRAFT; derived from
// ../three-arm/dry-run.mjs. No model call, no evaluator case: the family and
// routes are the public ERPNext example, built on disposable records.
//
//   1. Each arm goes through discovery and freezing, then decides three routes:
//      one valid, and two look-alikes on which the write is wrong (the quotation
//      behind the order is still a draft; it is for another quantity).
//   2. A control guard that always says "write" decides the same routes. All
//      three must commit, the wrong ones included: the server does not refuse
//      them and the harness does not hold them back.
//
//   node erp-dry-run.mjs --run-dir D [--receipt FILE]
//
// Needs the ERPNext ports; starts and removes its own instances.
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { ARMS, blind, CONFIG, defaultDeps, discovery, frozenFileSet, hashDirectory } from './erp-runner.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const FAMILY = 'example-quotation-covers-order';
const ORDER_LINE = { item_code: 'STAGE2-UNIT', rate: 100, schedule_date: '2026-02-15' };
const recipe = (routeId, quotationQty, submit, orderQty, entryBranch, reference) => ({
  routeId, familyId: FAMILY, entryBranch,
  setup: [
    { as: 'approver', method: 'POST', path: '/api/resource/Supplier%20Quotation',
      body: { company: 'Stage2 Qual Corp', supplier: 'Stage2 Approved Vendor', transaction_date: '2026-02-01', items: [{ item_code: 'STAGE2-UNIT', qty: quotationQty, rate: 100 }] },
      save: { quotation: 'data.name', quotationDoc: 'data' } },
    ...(submit ? [{ as: 'approver', method: 'POST', path: '/api/method/frappe.client.submit', body: { doc: '{quotationDoc}' } }] : []),
    { as: 'author', method: 'POST', path: '/api/resource/Purchase%20Order',
      body: { company: 'Stage2 Qual Corp', supplier: 'Stage2 Approved Vendor', transaction_date: '2026-02-01', schedule_date: '2026-02-15',
        items: [{ ...ORDER_LINE, qty: orderQty, supplier_quotation: '{quotation}' }] }, save: { order: 'data.name' } },
  ],
  target: { doctype: 'Purchase Order', name: '{order}' }, write: { reference },
});
const FAMILIES = { families: [{ familyId: FAMILY,
  policy: 'Confirm an order only while the supplier quotation it was raised from is submitted and is for the same total quantity.',
  disclosedExample: recipe('disclosed', 10, true, 10, 'direct', 'CONF-0001') }] };
const ROUTES = [
  { recipe: recipe('dry-valid', 12, true, 12, 'order-list', 'CONF-1001'), valid: true, what: 'the quotation is submitted and is for the same 12 units' },
  { recipe: recipe('dry-lookalike-draft', 12, false, 12, 'direct', 'CONF-1002'), valid: false, what: 'same, but the quotation is still a draft' },
  { recipe: recipe('dry-lookalike-quantity', 5, true, 12, 'more-info-tab', 'CONF-1003'), valid: false, what: 'same, but the quotation is for 5 units' },
];
const ALWAYS_WRITE = `export async function decide() { return { decision: 'write', reason: 'control: always write' }; }\n`;

const args = process.argv.slice(2);
const option = name => (args.includes(name) ? args[args.indexOf(name) + 1] : undefined);
const runDir = resolve(option('--run-dir') ?? '');
if (!option('--run-dir')) { console.error('usage: erp-dry-run.mjs --run-dir D [--receipt FILE]'); process.exit(2); }
const receiptFile = resolve(option('--receipt') ?? join(runDir, 'dry-run-receipt.json'));

rmSync(runDir, { recursive: true, force: true });
mkdirSync(runDir, { recursive: true, mode: 0o700 });
const familiesFile = join(runDir, 'families.json');
const recipesFile = join(runDir, 'routes.json');
writeFileSync(familiesFile, JSON.stringify(FAMILIES, null, 2));
writeFileSync(recipesFile, JSON.stringify({ recipes: ROUTES.map(r => r.recipe) }, null, 2));

const deps = { ...defaultDeps(), executable: resolve(HERE, '../../../test/support/fake-claude-erpnext.mjs') };
const armsDir = join(runDir, 'arms');
const common = { familiesFile, runDir: armsDir, approvePaid: true, deps };
const frozen = {};
for (const arm of ARMS) frozen[arm] = await discovery({ ...common, arm });
for (const arm of ARMS) await blind({ ...common, arm, recipesFile });

// Control: a guard that always writes, frozen by hand, decided through the same blind phase.
const controlDir = join(runDir, 'control-always-write');
const guardDir = join(controlDir, 'artifacts', 'agent-written-guard');
mkdirSync(guardDir, { recursive: true });
writeFileSync(join(guardDir, 'guard.mjs'), ALWAYS_WRITE);
const at = new Date().toISOString();
writeFileSync(join(controlDir, 'phase-records.jsonl'), JSON.stringify({ schema: 'gammatron-three-arm-phase-record/v1',
  runId: 'control', application: CONFIG.application, upgrade: CONFIG.upgrade, arm: 'agent-written-guard', phase: 'discovery',
  startedAt: at, endedAt: at, wallMs: 0, modelCalls: 0, modelTurns: 0, costUsd: 0, budgetUsd: 0, recordsCreated: 0, outOfSurfaceCalls: 0,
  artifactSha256: hashDirectory(guardDir), completed: true }) + '\n');
await blind({ familiesFile, recipesFile, runDir: controlDir, arm: 'agent-written-guard', deps });

const read = dir => readFileSync(join(dir, 'route-records.jsonl'), 'utf8').trim().split('\n').map(l => JSON.parse(l));
const row = (r, armLabel) => {
  const route = ROUTES.find(x => x.recipe.routeId === r.routeId);
  // Who stopped a wrong write: the arm (it said stop), the server (the write was sent and no row changed), or nobody.
  const blockedBy = route.valid ? null : r.decision === 'stop' ? 'arm' : r.committed ? 'nobody' : 'server';
  return { arm: armLabel, routeId: r.routeId, routeIs: route.valid ? 'valid' : 'invalid', what: route.what,
    decision: r.decision, stopReason: r.stopReason, writeSent: r.writeAttempted, httpStatus: r.httpStatus, committed: r.committed,
    referenceStored: r.effectMatches, reference: r.reference, termsLength: [r.before.termsLength, r.after.termsLength],
    modified: [r.before.modified, r.after.modified], versionEntries: [r.before.versionCount, r.after.versionCount],
    reads: r.reads, blockedBy, error: r.error };
};
const rows = [...read(armsDir).map(r => row(r, r.arm)), ...read(controlDir).map(r => row(r, 'control-always-write'))];

const checks = [];
const check = (name, ok) => checks.push({ name, ok: Boolean(ok) });
for (const arm of ARMS) {
  const mine = rows.filter(r => r.arm === arm);
  const valid = mine.find(r => r.routeIs === 'valid');
  check(`${arm}: writes the valid route and the stored order holds the reference`,
    valid?.decision === 'write' && valid.httpStatus === 200 && valid.committed && valid.referenceStored === true
    && valid.modified[1] !== valid.modified[0] && valid.versionEntries[1] === valid.versionEntries[0] + 1);
  check(`${arm}: stops both look-alikes itself, and no row changes`,
    mine.filter(r => r.routeIs === 'invalid').length === 2
    && mine.filter(r => r.routeIs === 'invalid').every(r => r.blockedBy === 'arm' && !r.writeSent && !r.committed && r.modified[0] === r.modified[1]));
  check(`${arm}: discovery froze an artifact with no call outside its tools`, frozen[arm].completed && frozen[arm].outOfSurfaceCalls === 0);
}
const control = rows.filter(r => r.arm === 'control-always-write');
check('control: the valid route commits', control.find(r => r.routeIs === 'valid')?.committed === true);
check('control: both look-alikes commit too, so neither the server nor the harness blocks a wrong write',
  control.filter(r => r.routeIs === 'invalid').length === 2 && control.filter(r => r.routeIs === 'invalid').every(r => r.blockedBy === 'nobody' && r.httpStatus === 200));

const git = a => execFileSync('git', a, { cwd: HERE, encoding: 'utf8' }).trim();
const receipt = {
  schema: 'gammatron-three-arm-erpnext-dry-run/draft', issue: 'clocksmith/deco#88', at: new Date().toISOString(),
  model: 'none: a scripted stand-in for the model CLI (test/support/fake-claude-erpnext.mjs)', modelSpendUsd: 0,
  application: `erpnext ${CONFIG.upgrade}, routes decided on the newer release`,
  cases: 'the public ERPNext example family on disposable records; no evaluator case',
  commit: git(['rev-parse', 'HEAD']), workingTreeClean: git(['status', '--porcelain', '--', '.']) === '', erpnextRunnerSha256Draft: frozenFileSet().sha256,
  passed: checks.every(c => c.ok), checks, rows,
};
writeFileSync(receiptFile, JSON.stringify(receipt, null, 2) + '\n');
for (const c of checks) console.log(`${c.ok ? 'ok  ' : 'FAIL'} ${c.name}`);
console.log(`\n${receipt.passed ? 'dry run passed' : 'DRY RUN FAILED'}; receipt: ${receiptFile}`);
process.exit(receipt.passed ? 0 : 1);
