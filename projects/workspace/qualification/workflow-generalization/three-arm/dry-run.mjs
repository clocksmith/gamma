#!/usr/bin/env node
// Dry run of the three-arm pipeline on the real application, with a stand-in for
// the model (clocksmith/deco#88). No model call, no evaluator case: the family
// and routes are the public example, built on disposable records.
//
// It answers one question before any paid stage: can the harness let a write
// through, and when a write is stopped, who stopped it?
//
//   1. Each arm goes through discovery and freezing, then decides three routes:
//      one valid, and two look-alikes on which the write is wrong.
//      Expected: every arm writes the valid one and the row changes in
//      PostgreSQL; every arm stops both look-alikes itself.
//   2. A control guard that always says "write" decides the same routes.
//      Expected: all three commit, the wrong ones included. That shows the
//      server does not refuse them and the harness does not hold them back, so
//      a count of zero wrong commits for an arm is the arm's doing.
//
//   node dry-run.mjs --run-dir D [--receipt FILE]
//
// Needs the OpenProject ports; starts and removes its own instances.
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { ARMS, blind, CONFIG, defaultDeps, discovery, frozenFileSet, hashDirectory } from './runner.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const FAMILY = 'example-approval-hours-match';
const recipe = (routeId, approvalHours, status, workHours, entryBranch) => ({
  routeId, familyId: FAMILY, entryBranch,
  setup: [
    { as: 'approver', method: 'POST', path: '/api/v3/projects/stage2-qual-proj/work_packages',
      body: { subject: 'Approval {tag}', estimatedTime: `PT${approvalHours}H` }, save: { approval: 'id' } },
    { as: 'approver', method: 'PATCH', path: '/api/v3/work_packages/{approval}', body: { _links: { status: { href: status } } } },
    { as: 'author', method: 'POST', path: '/api/v3/projects/stage2-qual-proj/work_packages',
      body: { subject: 'Order {tag}', estimatedTime: 'PT8H', _links: { parent: { href: '/api/v3/work_packages/{approval}' } } }, save: { order: 'id' } },
  ],
  target: { workPackage: '{order}', project: 'stage2-qual-proj' }, write: { workHours },
});
const FAMILIES = { families: [{ familyId: FAMILY,
  policy: 'Save the hours only while the approval above the order is approved for those same hours.',
  disclosedExample: recipe('disclosed', 24, '{status.approved}', 24, 'direct') }] };
// Hours of a day or more on purpose: the application writes those as P2DT8H, not PT56H.
const ROUTES = [
  { recipe: recipe('dry-valid', 56, '{status.approved}', 56, 'project-table'), valid: true, what: 'approval is approved for the same 56 hours' },
  { recipe: recipe('dry-lookalike-hold', 56, '{status.hold}', 56, 'direct'), valid: false, what: 'same, but the approval is on hold' },
  { recipe: recipe('dry-lookalike-hours', 32, '{status.approved}', 56, 'relations-tab'), valid: false, what: 'same, but the approval is for 32 hours' },
];
const ALWAYS_WRITE = `export async function decide() { return { decision: 'write', reason: 'control: always write' }; }\n`;

const args = process.argv.slice(2);
const option = name => (args.includes(name) ? args[args.indexOf(name) + 1] : undefined);
const runDir = resolve(option('--run-dir') ?? '');
if (!option('--run-dir')) { console.error('usage: dry-run.mjs --run-dir D [--receipt FILE]'); process.exit(2); }
const receiptFile = resolve(option('--receipt') ?? join(runDir, 'dry-run-receipt.json'));

rmSync(runDir, { recursive: true, force: true });
mkdirSync(runDir, { recursive: true, mode: 0o700 });
const familiesFile = join(runDir, 'families.json');
const recipesFile = join(runDir, 'routes.json');
writeFileSync(familiesFile, JSON.stringify(FAMILIES, null, 2));
writeFileSync(recipesFile, JSON.stringify({ recipes: ROUTES.map(r => r.recipe) }, null, 2));

const deps = { ...defaultDeps(), executable: resolve(HERE, '../../../test/support/fake-claude.mjs') };
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
    hoursBefore: r.before.estimatedHours, hoursAfter: r.after.estimatedHours, hoursAsked: r.workHours,
    rowVersion: [r.before.lockVersion, r.after.lockVersion], journalEntries: [r.before.journalCount, r.after.journalCount],
    reads: r.reads, blockedBy, error: r.error };
};
const rows = [...read(armsDir).map(r => row(r, r.arm)), ...read(controlDir).map(r => row(r, 'control-always-write'))];

const checks = [];
const check = (name, ok) => checks.push({ name, ok: Boolean(ok) });
for (const arm of ARMS) {
  const mine = rows.filter(r => r.arm === arm);
  const valid = mine.find(r => r.routeIs === 'valid');
  check(`${arm}: writes the valid route and the row changes to the hours asked`,
    valid?.decision === 'write' && valid.httpStatus === 200 && valid.committed && Number(valid.hoursAfter) === valid.hoursAsked
    && valid.rowVersion[1] === valid.rowVersion[0] + 1 && valid.journalEntries[1] === valid.journalEntries[0] + 1);
  check(`${arm}: stops both look-alikes itself, and no row changes`,
    mine.filter(r => r.routeIs === 'invalid').length === 2
    && mine.filter(r => r.routeIs === 'invalid').every(r => r.blockedBy === 'arm' && !r.writeSent && !r.committed && r.hoursBefore === r.hoursAfter));
  check(`${arm}: discovery froze an artifact with no call outside its tools`, frozen[arm].completed && frozen[arm].outOfSurfaceCalls === 0);
}
const control = rows.filter(r => r.arm === 'control-always-write');
check('control: the valid route commits', control.find(r => r.routeIs === 'valid')?.committed === true);
check('control: both look-alikes commit too, so neither the server nor the harness blocks a wrong write',
  control.filter(r => r.routeIs === 'invalid').length === 2 && control.filter(r => r.routeIs === 'invalid').every(r => r.blockedBy === 'nobody' && r.httpStatus === 200));

const git = a => execFileSync('git', a, { cwd: HERE, encoding: 'utf8' }).trim();
const receipt = {
  schema: 'gammatron-three-arm-dry-run/v1', issue: 'clocksmith/deco#88', at: new Date().toISOString(),
  model: 'none: a scripted stand-in for the model CLI (test/support/fake-claude.mjs)', modelSpendUsd: 0,
  application: `openproject ${CONFIG.upgrade}, routes decided on the newer release`,
  cases: 'the public example family on disposable records; no evaluator case',
  commit: git(['rev-parse', 'HEAD']), workingTreeClean: git(['status', '--porcelain', '--', '.']) === '', runnerSha256: frozenFileSet().sha256,
  passed: checks.every(c => c.ok), checks, rows,
};
writeFileSync(receiptFile, JSON.stringify(receipt, null, 2) + '\n');
for (const c of checks) console.log(`${c.ok ? 'ok  ' : 'FAIL'} ${c.name}`);
console.log(`\n${receipt.passed ? 'dry run passed' : 'DRY RUN FAILED'}; receipt: ${receiptFile}`);
process.exit(receipt.passed ? 0 : 1);
