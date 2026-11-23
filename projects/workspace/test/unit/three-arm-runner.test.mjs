import assert from 'node:assert/strict';
import { cpSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { after, before, test } from 'node:test';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { blind, CONFIG, discovery, frozenFileSet, hashDirectory, maintenance, regress } from '../../qualification/workflow-generalization/three-arm/runner.mjs';

// A stand-in OpenProject: work packages with hours, a status and a parent, and the two accounts.
const store = new Map();
let nextId = 1;
// Two ways a later release could break what an arm learned: statuses renumbered, or a call refused.
const upgrade = { statusShift: 0, refuseParents: false };
// Durations come back the way OpenProject writes them: 24 hours is P1D, 56 hours is P2DT8H.
const toHours = d => { const m = String(d ?? '').match(/^P(?:(\d+)D)?(?:T(?:(\d+)H)?)?$/); return m ? Number(m[1] ?? 0) * 24 + Number(m[2] ?? 0) : null; };
const fromHours = h => (h === null ? null : `P${Math.floor(h / 24) ? `${Math.floor(h / 24)}D` : ''}${h % 24 || !Math.floor(h / 24) ? `T${h % 24}H` : ''}`);
const view = r => ({ id: r.id, lockVersion: r.lockVersion, estimatedTime: fromHours(toHours(r.estimatedTime)), subject: r.subject,
  _links: { status: { href: `/api/v3/statuses/${r.status}` }, project: { href: '/api/v3/projects/1' }, ...(r.parent ? { parent: { href: r.parent } } : {}) } });
const http = createServer(async (req, res) => {
  let text = '';
  for await (const chunk of req) text += chunk;
  const body = text ? JSON.parse(text) : {};
  const account = Buffer.from(req.headers.authorization.split(' ')[1], 'base64').toString() === 'apikey:A' ? 'author' : 'approver';
  const send = (status, value) => { res.statusCode = status; res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(value)); };
  const one = req.url.match(/^\/api\/v3\/work_packages\/(\d+)$/);
  if (req.method === 'POST' && /^\/api\/v3\/projects\/[^/]+\/work_packages$/.test(req.url)) {
    if (upgrade.refuseParents && body._links?.parent) return send(422, { message: 'Parent is invalid' });
    const record = { id: nextId++, lockVersion: 0, estimatedTime: body.estimatedTime ?? null, subject: body.subject, status: 15,
      parent: body._links?.parent?.href ?? null };
    store.set(record.id, record);
    return send(201, view(record));
  }
  if (one && store.has(Number(one[1]))) {
    const record = store.get(Number(one[1]));
    if (req.method === 'GET') return send(200, view(record));
    if (req.method === 'PATCH') {
      if (body._links?.status && account !== 'approver') return send(422, { message: 'Status is invalid' });
      if (body._links?.status) record.status = Number(body._links.status.href.split('/').pop()) + upgrade.statusShift;
      if (body.estimatedTime) record.estimatedTime = body.estimatedTime;
      record.lockVersion += 1;
      return send(200, view(record));
    }
  }
  if (req.url === '/api/v3/statuses') return send(200, { _embedded: { elements: [] } });
  return send(404, { message: 'not found' });
});

let dir;
let deps;
let instances = -1;
const recipe = (routeId, approvalHours, status, workHours, entryBranch) => ({
  routeId, familyId: 'fam', entryBranch,
  setup: [
    { as: 'approver', method: 'POST', path: '/api/v3/projects/stage2-qual-proj/work_packages', body: { subject: 'Approval {tag}', estimatedTime: `PT${approvalHours}H` }, save: { approval: 'id' } },
    { as: 'approver', method: 'PATCH', path: '/api/v3/work_packages/{approval}', body: { _links: { status: { href: status } } } },
    { as: 'author', method: 'POST', path: '/api/v3/projects/stage2-qual-proj/work_packages', body: { subject: 'Order {tag}', estimatedTime: 'PT8H', _links: { parent: { href: '/api/v3/work_packages/{approval}' } } }, save: { order: 'id' } },
  ],
  target: { workPackage: '{order}', project: 'stage2-qual-proj' }, write: { workHours },
});

before(async () => {
  await new Promise(done => http.listen(0, '127.0.0.1', done));
  dir = mkdtempSync(join(tmpdir(), 'three-arm-run-'));
  const url = `http://127.0.0.1:${http.address().port}`;
  writeFileSync(join(dir, 'state.json'), JSON.stringify({ username: 'u', password: 'p', new: { url, pgUrl: 'postgres://x@y/z', seed: {
    authorToken: 'A', approverToken: 'B', newStatusHref: '/api/v3/statuses/15', approvedStatusHref: '/api/v3/statuses/16',
    holdStatusHref: '/api/v3/statuses/17', disallowedStatusHref: '/api/v3/statuses/18', authorUserId: 5, approverUserId: 6 } } }));
  writeFileSync(join(dir, 'families.json'), JSON.stringify({ families: [{ familyId: 'fam',
    policy: 'Save the hours only while the approval above the order is approved for those same hours.',
    disclosedExample: recipe('disclosed', 24, '{status.approved}', 24, 'direct') }] }));
  writeFileSync(join(dir, 'blind.json'), JSON.stringify({ recipes: [
    recipe('r-1', 56, '{status.approved}', 56, 'project-table'),
    recipe('r-2', 56, '{status.hold}', 56, 'direct'),
    recipe('r-3', 32, '{status.approved}', 56, 'relations-tab'),
  ] }));
  const row = id => { const r = store.get(id); return { lockVersion: r.lockVersion, estimatedHours: toHours(r.estimatedTime), remainingHours: null, statusId: r.status, journalCount: r.lockVersion + 1 }; };
  deps = {
    executable: fileURLToPath(new URL('../support/fake-claude.mjs', import.meta.url)),
    stateFile: join(dir, 'state.json'),
    // A new database does not hand out the same numbers again.
    freshInstance() { store.clear(); nextId = 1 + 100 * (instances += 1); },
    stopInstance() {},
    async openWriter() {
      return { readRow: row, close: async () => {},
        async write(route) {
          const before = row(route.workPackageId);
          const record = store.get(route.workPackageId);
          record.estimatedTime = `PT${route.workHours}H`;
          record.lockVersion += 1;
          return { httpStatus: 200, before, after: row(route.workPackageId), committed: true, effectMatches: true, wallMs: 1, error: null };
        } };
    },
    // The sandbox has its own test; here the frozen guard is loaded in-process so this test needs no container.
    async guardRunner({ guardDir, route, get }) {
      const guard = await import(`${pathToFileURL(join(guardDir, 'guard.mjs')).href}?t=${Date.now()}`);
      let reads = 0;
      const answer = await guard.decide({ ...route, get: path => { reads += 1; return get(path); } });
      return { decision: answer.decision, reason: answer.reason, error: null, reads };
    },
  };
});
after(() => {
  http.close();
  // Set THREE_ARM_KEEP to a directory to keep the stand-in run's records, for trying them against the scorer.
  if (process.env.THREE_ARM_KEEP) cpSync(dir, process.env.THREE_ARM_KEEP, { recursive: true });
  rmSync(dir, { recursive: true, force: true });
});

const records = name => readFileSync(join(dir, 'run', name), 'utf8').trim().split('\n').map(l => JSON.parse(l));

test('the frozen file set is stable and covers the arms, the learner and the plan', () => {
  const a = frozenFileSet();
  assert.equal(a.sha256, frozenFileSet().sha256);
  const files = a.entries.map(e => e.file);
  for (const needed of ['qualification/workflow-generalization/three-arm/instructions.mjs', 'qualification/workflow-generalization/three-arm/runner.mjs',
    'qualification/workflow-generalization/three-arm/arm-server.mjs', 'src/client/repair-boundary.js',
    'qualification/workflow-generalization/same-model-three-arm-preregistration.md']) assert.ok(files.includes(needed), needed);
  assert.ok(!files.some(f => /example-recipes\.json$|task-contract|three-arm\/README\.md$|\/scorer\//.test(f)));
});

test('a paid phase refuses to start without approval', async () => {
  const runDir = join(dir, 'refused');
  await assert.rejects(discovery({ arm: 'repair-boundary', familiesFile: join(dir, 'families.json'), runDir, deps }), /--approve-paid/);
});

test('discovery freezes each arm, then the unseen routes are decided, written and recorded without labels', async () => {
  const runDir = join(dir, 'run');
  const common = { familiesFile: join(dir, 'families.json'), runDir, approvePaid: true, deps };
  const guard = await discovery({ ...common, arm: 'agent-written-guard' });
  const boundary = await discovery({ ...common, arm: 'repair-boundary' });
  const replan = await discovery({ ...common, arm: 'always-replan' });
  for (const phase of [guard, boundary, replan]) {
    assert.equal(phase.completed, true);
    assert.match(phase.artifactSha256, /^[a-f0-9]{64}$/);
    assert.equal(phase.outOfSurfaceCalls, 0);
  }
  assert.equal(guard.costUsd, 0.01);
  assert.equal(guard.budgetUsd, CONFIG.discovery.budgetUsd);
  assert.equal(boundary.recordsCreated, 6);
  // Both arms keep labelled cases and the calls that built their records.
  const kept = arm => JSON.parse(readFileSync(join(runDir, 'artifacts', `${arm}.regression.json`), 'utf8'));
  assert.deepEqual(kept('agent-written-guard').cases.map(c => c.expect), ['write', 'stop']);
  assert.deepEqual(kept('repair-boundary').cases.map(c => c.expect), ['write', 'write', 'stop', 'stop']);
  assert.equal(kept('repair-boundary').trace.length, 9);
  assert.ok(kept('agent-written-guard').trace.every(call => call.method !== 'GET'));
  const summary = arm => JSON.parse(readFileSync(join(runDir, 'logs', `discovery-${arm}.summary.json`), 'utf8')).keptCases;
  assert.deepEqual([summary('agent-written-guard').cases, summary('agent-written-guard').passingAtFreeze], [2, 2]);
  assert.deepEqual([summary('repair-boundary').cases, summary('repair-boundary').passingAtFreeze], [4, 4]);
  assert.equal(replan.costUsd, 0);
  assert.equal(hashDirectory(join(runDir, 'artifacts', 'agent-written-guard')), guard.artifactSha256);
  const learned = JSON.parse(readFileSync(join(runDir, 'artifacts', 'repair-boundary.json'), 'utf8')).families.fam.boundary;
  assert.equal(learned.status, 'learned');

  for (const arm of ['agent-written-guard', 'repair-boundary', 'always-replan']) {
    const phase = await blind({ ...common, arm, recipesFile: join(dir, 'blind.json') });
    assert.equal(phase.phase, 'blind-routes');
    assert.equal(phase.outOfSurfaceCalls, 0);
  }
  const routes = records('route-records.jsonl');
  assert.equal(routes.length, 9);
  for (const arm of ['agent-written-guard', 'repair-boundary', 'always-replan']) {
    const mine = routes.filter(r => r.arm === arm);
    assert.deepEqual(mine.map(r => [r.routeId, r.decision, r.writeAttempted, r.committed]),
      [['r-1', 'write', true, true], ['r-2', 'stop', false, false], ['r-3', 'stop', false, false]], arm);
    assert.ok(mine.every(r => r.reads >= 1 && r.reads <= 8), arm);
    assert.equal(mine[0].after.estimatedHours, 56);
    assert.equal(mine[0].effectMatches, true);
  }
  assert.ok(routes.every(r => !('valid' in r) && !('label' in r)));
  assert.ok(routes.filter(r => r.arm !== 'always-replan').every(r => r.modelCalls === 0 && r.costUsd === 0));
  assert.ok(routes.filter(r => r.arm === 'always-replan').every(r => r.modelCalls >= 1 && r.costUsd === 0.01));
  const phases = records('phase-records.jsonl');
  assert.equal(phases.length, 6);
  assert.equal(phases.find(p => p.arm === 'always-replan' && p.phase === 'blind-routes').costUsd, 0.03);
  const spend = JSON.parse(readFileSync(join(runDir, 'spend.json'), 'utf8'));
  assert.equal(spend.spentUsd, 0.05);

  // Every record matches the published schema's required fields.
  const schema = JSON.parse(readFileSync(new URL('../../qualification/workflow-generalization/three-arm/route-record.schema.json', import.meta.url), 'utf8'));
  for (const r of routes) assert.deepEqual(Object.keys(r).sort(), [...schema.$defs.routeRecord.required].sort());
  for (const p of phases) assert.deepEqual(Object.keys(p).sort(), [...schema.$defs.phaseRecord.required].sort());
});

test('kept cases are rebuilt on a new database and rerun; a release that breaks them is caught', async () => {
  const runDir = join(dir, 'run');
  const common = { familiesFile: join(dir, 'families.json'), runDir, deps };
  for (const arm of ['agent-written-guard', 'repair-boundary']) {
    const same = await regress({ ...common, arm });
    assert.equal(same.rebuilt, true, arm);
    assert.equal(same.passed, same.total, arm);
    assert.deepEqual(same.failedFamilies, [], arm);
    assert.ok(same.results.every(r => r.workPackageId > 100), 'numbers differ on the new database');
  }
  upgrade.statusShift = 10;
  try {
    for (const arm of ['agent-written-guard', 'repair-boundary']) {
      const shifted = await regress({ ...common, arm });
      assert.equal(shifted.rebuilt, true, arm);
      assert.deepEqual(shifted.failedFamilies, ['fam'], arm);
      assert.ok(shifted.results.some(r => r.expect === 'write' && r.got === 'stop'), arm);
    }
  } finally { upgrade.statusShift = 0; }
  upgrade.refuseParents = true;
  try {
    const refused = await regress({ ...common, arm: 'repair-boundary' });
    assert.equal(refused.rebuilt, false);
    assert.match(refused.reason, /returned 422: Parent is invalid/);
    assert.deepEqual(refused.failedFamilies, ['fam']);
  } finally { upgrade.refuseParents = false; }
  await assert.rejects(regress({ ...common, arm: 'always-replan' }), /keep cases/);
});

test('after an upgrade that renumbers statuses, each arm repairs its frozen work and decides the new routes correctly', async () => {
  const fromRunDir = join(dir, 'run');
  const runDir = join(dir, 'run-upgrade-2');
  const common = { familiesFile: join(dir, 'families.json'), runDir, approvePaid: true, upgrade: '14.0.0->15.0.0', deps };
  upgrade.statusShift = 10;
  try {
    for (const arm of ['agent-written-guard', 'repair-boundary', 'always-replan']) {
      const phase = await maintenance({ ...common, arm, fromRunDir });
      assert.equal(phase.phase, 'maintenance');
      assert.equal(phase.upgrade, '14.0.0->15.0.0');
      assert.equal(phase.completed, true, arm);
      assert.equal(phase.outOfSurfaceCalls, 0, arm);
    }
    for (const arm of ['agent-written-guard', 'repair-boundary']) {
      const summary = JSON.parse(readFileSync(join(runDir, 'logs', `maintenance-${arm}.summary.json`), 'utf8'));
      assert.deepEqual(summary.keptCases.familiesCaught, ['fam'], arm);
      assert.ok(summary.keptCases.passedAfterUpgrade < summary.keptCases.total, arm);
      await blind({ ...common, arm, recipesFile: join(dir, 'blind.json') });
    }
    const routes = readFileSync(join(runDir, 'route-records.jsonl'), 'utf8').trim().split('\n').map(l => JSON.parse(l));
    for (const arm of ['agent-written-guard', 'repair-boundary']) {
      assert.deepEqual(routes.filter(r => r.arm === arm).map(r => [r.routeId, r.decision, r.committed]),
        [['r-1', 'write', true], ['r-2', 'stop', false], ['r-3', 'stop', false]], arm);
    }
    assert.ok(routes.every(r => r.upgrade === '14.0.0->15.0.0'));
    // The work frozen at the first upgrade is left as it was.
    const first = JSON.parse(readFileSync(join(fromRunDir, 'phase-records.jsonl'), 'utf8').split('\n')[0]);
    assert.equal(hashDirectory(join(fromRunDir, 'artifacts', 'agent-written-guard')), first.artifactSha256);
  } finally { upgrade.statusShift = 0; }
  await assert.rejects(maintenance({ ...common, arm: 'repair-boundary', fromRunDir, approvePaid: false }), /--approve-paid/);
});

test('a write that lands after its first reading is still recorded as committed', async () => {
  const runDir = join(dir, 'late');
  const common = { familiesFile: join(dir, 'families.json'), runDir, approvePaid: true, deps };
  await discovery({ ...common, arm: 'agent-written-guard' });
  // A writer whose save lands only after the write step has read the row.
  const late = { ...deps, async openWriter(state) {
    const writer = await deps.openWriter(state);
    return { ...writer, async write(route) {
      const before = writer.readRow(route.workPackageId);
      setTimeout(() => { const r = store.get(route.workPackageId); r.estimatedTime = `PT${route.workHours}H`; r.lockVersion += 1; }, 20);
      return { httpStatus: 200, before, after: before, committed: false, effectMatches: false, wallMs: 1, error: null };
    }, close: async () => { await new Promise(done => setTimeout(done, 60)); } };
  } };
  await new Promise(done => setTimeout(done, 0));
  const slowRead = { ...late, async openWriter(state) {
    const writer = await late.openWriter(state);
    let reads = 0;
    // The final pass happens after every route was decided; give the late saves time to land first.
    return { ...writer, readRow(id) { reads += 1; return writer.readRow(id); }, write: async route => { const r = await writer.write(route); await new Promise(done => setTimeout(done, 40)); return r; } };
  } };
  await blind({ ...common, deps: slowRead, arm: 'agent-written-guard', recipesFile: join(dir, 'blind.json') });
  const written = readFileSync(join(runDir, 'route-records.jsonl'), 'utf8').trim().split('\n').map(l => JSON.parse(l)).find(r => r.routeId === 'r-1');
  assert.equal(written.decision, 'write');
  assert.equal(written.committed, true);
  assert.equal(written.effectMatches, true);
  assert.equal(written.after.estimatedHours, 56);
  assert.match(written.error, /changed after its first reading/);
});

test('a session that calls a tool outside its surface is counted, and a changed artifact is refused', async () => {
  const runDir = join(dir, 'dirty');
  const common = { familiesFile: join(dir, 'families.json'), runDir, approvePaid: true, deps };
  process.env.FAKE_CLAUDE_MISBEHAVE = '1';
  try {
    const phase = await discovery({ ...common, arm: 'agent-written-guard' });
    assert.equal(phase.outOfSurfaceCalls, 1);
  } finally { delete process.env.FAKE_CLAUDE_MISBEHAVE; }
  writeFileSync(join(runDir, 'artifacts', 'agent-written-guard', 'guard.mjs'), 'export async function decide() { return { decision: "write" }; }');
  await assert.rejects(blind({ ...common, arm: 'agent-written-guard', recipesFile: join(dir, 'blind.json') }), /changed after it was frozen/);
});

test('rebuilding maps new record numbers through later calls and stops at the first call that answers differently', async () => {
  const { rebuildRecords, readGuardCases } = await import('../../qualification/workflow-generalization/three-arm/regression.mjs');
  const sent = [];
  let next = 500;
  const request = async (as, method, path, body) => {
    sent.push({ as, method, path, body });
    if (method === 'POST') return { status: path.includes('refuse') ? 422 : 201, body: { id: next++ } };
    return { status: 200, body: {} };
  };
  const trace = [
    { as: 'approver', method: 'POST', path: '/api/v3/projects/p/work_packages', body: { subject: 'a' }, status: 201, id: 7 },
    { as: 'approver', method: 'PATCH', path: '/api/v3/work_packages/7', body: { lockVersion: 0 }, status: 200, id: 7 },
    { as: 'author', method: 'POST', path: '/api/v3/projects/p/work_packages', body: { _links: { parent: { href: '/api/v3/work_packages/7' } } }, status: 201, id: 8 },
    { as: 'author', method: 'POST', path: '/api/v3/projects/p/work_packages', body: { _links: { parent: { href: '/api/v3/work_packages/3' } } }, status: 201, id: 9 },
  ];
  const done = await rebuildRecords({ trace, request, ids: new Map([[3, 303]]) });
  assert.equal(done.rebuilt, true);
  assert.deepEqual([...done.ids], [[3, 303], [7, 500], [8, 501], [9, 502]]);
  assert.equal(sent[1].path, '/api/v3/work_packages/500');
  assert.equal(sent[2].body._links.parent.href, '/api/v3/work_packages/500');
  assert.equal(sent[3].body._links.parent.href, '/api/v3/work_packages/303');
  const broken = await rebuildRecords({ trace: [{ as: 'author', method: 'POST', path: '/api/v3/projects/refuse/work_packages', body: null, status: 201, id: 1 }, ...trace], request });
  assert.equal(broken.rebuilt, false);
  assert.equal(broken.failedAt, 0);
  const read = readGuardCases([{ familyId: 'f', project: 'p', workPackageId: 1, workHours: 2, expect: 'write' }, { familyId: 'f', expect: 'maybe' }, 'x']);
  assert.equal(read.cases.length, 1);
  assert.equal(read.problems.length, 2);
  assert.equal(readGuardCases({}).problems.length, 1);
  const many = Array.from({ length: 30 }, (_, i) => ({ familyId: i < 26 ? 'f' : 'g', project: 'p', workPackageId: i + 1, workHours: 2, expect: 'stop' }));
  assert.equal(readGuardCases(many).cases.filter(c => c.familyId === 'f').length, 24);
  assert.equal(readGuardCases(many).cases.filter(c => c.familyId === 'g').length, 4);
});

test('the runner retries its own calls when the connection fails, and never when the application answers', async () => {
  const { steady } = await import('../../qualification/workflow-generalization/three-arm/runner.mjs');
  let calls = 0;
  const flaky = steady(async () => { calls += 1; if (calls < 3) throw new TypeError('fetch failed'); return { status: 201, body: {} }; }, { waitMs: 1 });
  assert.equal((await flaky('approver', 'POST', '/api/v3/x')).status, 201);
  assert.equal(calls, 3);
  calls = 0;
  const refused = steady(async () => { calls += 1; return { status: 422, body: {} }; }, { waitMs: 1 });
  assert.equal((await refused('approver', 'POST', '/api/v3/x')).status, 422);
  assert.equal(calls, 1);
  calls = 0;
  const dead = steady(async () => { calls += 1; throw new TypeError('fetch failed'); }, { attempts: 3, waitMs: 1 });
  await assert.rejects(dead('approver', 'GET', '/api/v3/x'), /fetch failed/);
  assert.equal(calls, 3);
});
