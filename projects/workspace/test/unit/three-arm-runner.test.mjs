import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { after, before, test } from 'node:test';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { blind, CONFIG, discovery, frozenFileSet, hashDirectory } from '../../qualification/workflow-generalization/three-arm/runner.mjs';

// A stand-in OpenProject: work packages with hours, a status and a parent, and the two accounts.
const store = new Map();
let nextId = 1;
const view = r => ({ id: r.id, lockVersion: r.lockVersion, estimatedTime: r.estimatedTime, subject: r.subject,
  _links: { status: { href: `/api/v3/statuses/${r.status}` }, project: { href: '/api/v3/projects/1' }, ...(r.parent ? { parent: { href: r.parent } } : {}) } });
const http = createServer(async (req, res) => {
  let text = '';
  for await (const chunk of req) text += chunk;
  const body = text ? JSON.parse(text) : {};
  const account = Buffer.from(req.headers.authorization.split(' ')[1], 'base64').toString() === 'apikey:A' ? 'author' : 'approver';
  const send = (status, value) => { res.statusCode = status; res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(value)); };
  const one = req.url.match(/^\/api\/v3\/work_packages\/(\d+)$/);
  if (req.method === 'POST' && /^\/api\/v3\/projects\/[^/]+\/work_packages$/.test(req.url)) {
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
      if (body._links?.status) record.status = Number(body._links.status.href.split('/').pop());
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
  const row = id => { const r = store.get(id); return { lockVersion: r.lockVersion, estimatedHours: r.estimatedTime ? Number(r.estimatedTime.slice(2, -1)) : null, remainingHours: null, statusId: r.status, journalCount: r.lockVersion + 1 }; };
  deps = {
    executable: fileURLToPath(new URL('../support/fake-claude.mjs', import.meta.url)),
    stateFile: join(dir, 'state.json'),
    freshInstance() { store.clear(); nextId = 1; },
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
after(() => { http.close(); rmSync(dir, { recursive: true, force: true }); });

const records = name => readFileSync(join(dir, 'run', name), 'utf8').trim().split('\n').map(l => JSON.parse(l));

test('the frozen file set is stable and covers the arms, the learner and the plan', () => {
  const a = frozenFileSet();
  assert.equal(a.sha256, frozenFileSet().sha256);
  const files = a.entries.map(e => e.file);
  for (const needed of ['qualification/workflow-generalization/three-arm/instructions.mjs', 'qualification/workflow-generalization/three-arm/runner.mjs',
    'qualification/workflow-generalization/three-arm/arm-server.mjs', 'src/client/repair-boundary.js',
    'qualification/workflow-generalization/same-model-three-arm-preregistration.md']) assert.ok(files.includes(needed), needed);
  assert.ok(!files.some(f => f.endsWith('example-recipes.json')));
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
