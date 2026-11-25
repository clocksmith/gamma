import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { after, before, test } from 'node:test';
import { fileURLToPath, pathToFileURL } from 'node:url';
import {
  assertFreeDiskForDockerScreen,
  checkRelease as checkErpReleaseWithRefusal,
  freezeLearned as freezeErpScreenLearned,
} from '../../qualification/workflow-generalization/second-upgrade-read-check-erpnext.mjs';
import { selftest as op178ScreenSelftest } from '../../qualification/workflow-generalization/op178-target-versions-screen.mjs';
import { runFreeCounterexampleCheck } from '../../qualification/workflow-generalization/three-arm-next/counterexample-check.mjs';
import { selftest as prelearnRuleSelftest } from '../../qualification/workflow-generalization/three-arm-next/prelearn-decision-rule.mjs';
import {
  forArm,
  freezeDeterministicArm,
  frozenNextFileSet,
  loadEqualTrainingRelease,
  measureAdapterLoc,
  recordAuditedAdapterPhase,
  registerAlwaysReplanPhase,
  runBlindArm,
} from '../../qualification/workflow-generalization/three-arm-next/runner.mjs';

const SCORER = fileURLToPath(
  new URL('../../qualification/workflow-generalization/three-arm-next/scorer/score_after_fallback.py', import.meta.url),
);
const COST_REPORT = fileURLToPath(
  new URL('../../qualification/workflow-generalization/three-arm-next/scorer/cost_report.py', import.meta.url),
);

// Stand-in dual server for OpenProject (/api/v3/...) and ERPNext (/api/resource/... & /api/method/...)
const opStore = new Map();
const erpQuotes = new Map();
const erpOrders = new Map();
let opId = 1;
let erpSeq = 1;
let refuseErpApproverSetup403 = false;

const toHours = d => {
  const m = String(d ?? '').match(/^P(?:(\d+)D)?(?:T(?:(\d+)H)?)?$/);
  return m ? Number(m[1] ?? 0) * 24 + Number(m[2] ?? 0) : null;
};
const fromHours = h => (h === null ? null : `P${Math.floor(h / 24) ? `${Math.floor(h / 24)}D` : ''}${h % 24 || !Math.floor(h / 24) ? `T${h % 24}H` : ''}`);
const opView = r => ({
  id: r.id,
  lockVersion: r.lockVersion,
  estimatedTime: fromHours(toHours(r.estimatedTime)),
  subject: r.subject,
  _links: {
    status: { href: `/api/v3/statuses/${r.status}` },
    project: { href: '/api/v3/projects/1' },
    ...(r.parent ? { parent: { href: r.parent } } : {}),
  },
});

const http = createServer(async (req, res) => {
  let text = '';
  for await (const chunk of req) text += chunk;
  const body = text ? JSON.parse(text) : {};
  const send = (status, val) => {
    res.statusCode = status;
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify(val));
  };

  if (req.url.startsWith('/api/v3/')) {
    const auth = Buffer.from((req.headers.authorization ?? '').split(' ')[1] ?? '', 'base64').toString();
    const account = auth === 'apikey:A' ? 'author' : 'approver';
    if (req.method === 'POST' && /^\/api\/v3\/projects\/[^/]+\/work_packages$/.test(req.url)) {
      if (req.url.includes('refuse-403-proj')) return send(403, { message: 'Forbidden setup project' });
      const rec = {
        id: opId++,
        lockVersion: 0,
        estimatedTime: body.estimatedTime ?? null,
        subject: body.subject,
        status: 15,
        parent: body._links?.parent?.href ?? null,
      };
      opStore.set(rec.id, rec);
      return send(201, opView(rec));
    }
    const one = req.url.match(/^\/api\/v3\/work_packages\/(\d+)$/);
    if (one && opStore.has(Number(one[1]))) {
      const rec = opStore.get(Number(one[1]));
      if (req.method === 'GET') return send(200, opView(rec));
      if (req.method === 'PATCH') {
        if (body._links?.status && account !== 'approver') return send(422, { message: 'Status denied' });
        if (body._links?.status) rec.status = Number(body._links.status.href.split('/').pop());
        if (body.estimatedTime) rec.estimatedTime = body.estimatedTime;
        rec.lockVersion += 1;
        return send(200, opView(rec));
      }
    }
    return send(404, { message: 'not found' });
  }

  // ERPNext routes
  const token = (req.headers.authorization ?? '').replace(/^token\s+/, '');
  const erpAccount = token === 'AUTHOR:1' ? 'author' : 'approver';
  if (req.method === 'POST' && req.url === '/api/resource/Supplier%20Quotation') {
    if (refuseErpApproverSetup403 && erpAccount === 'approver') {
      return send(403, { exception: 'frappe.exceptions.PermissionError: User does not have doctype access via role permission for document Item' });
    }
    const name = `PUR-SQ-${erpSeq++}`;
    const qty = (body.items ?? []).reduce((s, it) => s + Number(it.qty ?? 0), 0);
    const doc = {
      name,
      doctype: 'Supplier Quotation',
      company: body.company,
      docstatus: 0,
      total_qty: qty,
      items: body.items ?? [],
    };
    erpQuotes.set(name, doc);
    return send(200, { data: doc });
  }
  if (req.method === 'POST' && req.url === '/api/method/frappe.client.submit') {
    const q = erpQuotes.get(body.doc?.name);
    if (!q) return send(404, { message: 'missing quotation' });
    q.docstatus = 1;
    return send(200, { message: q });
  }
  if (req.method === 'POST' && req.url === '/api/resource/Purchase%20Order') {
    const name = `PUR-ORD-${erpSeq++}`;
    const qty = (body.items ?? []).reduce((s, it) => s + Number(it.qty ?? 0), 0);
    const doc = {
      name,
      doctype: 'Purchase Order',
      company: body.company,
      docstatus: 0,
      total_qty: qty,
      items: body.items ?? [],
      modified: '2026-11-24 10:00:00.000000',
      terms: '',
    };
    erpOrders.set(name, doc);
    return send(200, { data: doc });
  }
  const sqGet = req.url.match(/^\/api\/resource\/Supplier%20Quotation\/([^/?]+)$/);
  if (sqGet && req.method === 'GET') {
    const q = erpQuotes.get(decodeURIComponent(sqGet[1]));
    return q ? send(200, { data: q }) : send(404, { message: 'missing' });
  }
  const poGet = req.url.match(/^\/api\/resource\/Purchase%20Order\/([^/?]+)$/);
  if (poGet && req.method === 'GET') {
    const o = erpOrders.get(decodeURIComponent(poGet[1]));
    return o ? send(200, { data: o }) : send(404, { message: 'missing' });
  }
  return send(404, { message: 'not found' });
});

let dir;
let baseUrl;

before(async () => {
  await new Promise(done => http.listen(0, '127.0.0.1', done));
  baseUrl = `http://127.0.0.1:${http.address().port}`;
  dir = mkdtempSync(join(tmpdir(), 'three-arm-next-'));
});

after(() => {
  http.close();
  rmSync(dir, { recursive: true, force: true });
});

const opRecipe = (routeId, approvalHours, status, workHours, project = 'stage2-qual-proj') => ({
  routeId,
  familyId: 'op-approval-hours',
  entryBranch: 'project-table',
  setup: [
    { as: 'approver', method: 'POST', path: `/api/v3/projects/${project}/work_packages`, body: { subject: 'Parent {tag}', estimatedTime: `PT${approvalHours}H` }, save: { parent: 'id' } },
    { as: 'approver', method: 'PATCH', path: '/api/v3/work_packages/{parent}', body: { _links: { status: { href: status } } } },
    { as: 'author', method: 'POST', path: `/api/v3/projects/${project}/work_packages`, body: { subject: 'Child {tag}', estimatedTime: 'PT4H', _links: { parent: { href: '/api/v3/work_packages/{parent}' } } }, save: { child: 'id' } },
  ],
  target: { workPackage: '{child}', project },
  write: { workHours },
});

const erpRecipe = (routeId, qQty, submit, oQty, ref = 'CONF-7001') => ({
  routeId,
  familyId: 'erp-quote-covers',
  entryBranch: 'order-list',
  setup: [
    { as: 'approver', method: 'POST', path: '/api/resource/Supplier%20Quotation', body: { company: 'Stage2 Qual Corp', supplier: 'Stage2 Approved Vendor', transaction_date: '2026-02-01', items: [{ item_code: 'STAGE2-UNIT', qty: qQty, rate: 100 }] }, save: { q: 'data.name', qdoc: 'data' } },
    ...(submit ? [{ as: 'approver', method: 'POST', path: '/api/method/frappe.client.submit', body: { doc: '{qdoc}' } }] : []),
    { as: 'author', method: 'POST', path: '/api/resource/Purchase%20Order', body: { company: 'Stage2 Qual Corp', supplier: 'Stage2 Approved Vendor', transaction_date: '2026-02-01', schedule_date: '2026-02-15', items: [{ item_code: 'STAGE2-UNIT', qty: oQty, rate: 100, schedule_date: '2026-02-15', supplier_quotation: '{q}' }] }, save: { o: 'data.name' } },
  ],
  target: { doctype: 'Purchase Order', name: '{o}' },
  write: { reference: ref },
});

test('forArm strips routeId, entryBranch, and setup steps on both OpenProject and ERPNext', () => {
  const op = forArm('openproject', {
    routeId: 'secret-route-id',
    familyId: 'op-approval-hours',
    entryBranch: 'relations-tab',
    project: 'stage2-qual-proj',
    workPackageId: 42,
    workHours: 40,
    steps: [{ index: 0 }],
  });
  assert.deepEqual(Object.keys(op).sort(), ['familyId', 'project', 'workDuration', 'workHours', 'workPackageId']);
  assert.equal(op.workDuration, 'P1DT16H');
  assert.equal('routeId' in op, false);
  assert.equal('entryBranch' in op, false);
  assert.equal('steps' in op, false);

  const erp = forArm('erpnext', {
    routeId: 'secret-erp-id',
    familyId: 'erp-quote-covers',
    entryBranch: 'buying-workspace',
    doctype: 'Purchase Order',
    name: 'PUR-ORD-9',
    reference: 'CONF-9001',
    steps: [{ index: 0 }],
  });
  assert.deepEqual(Object.keys(erp).sort(), ['doctype', 'familyId', 'name', 'reference']);
  assert.equal('routeId' in erp, false);
  assert.equal('entryBranch' in erp, false);
  assert.equal('steps' in erp, false);
});

test('measureAdapterLoc counts actual non-comment adapter lines and frozenNextFileSet hashes deterministically', () => {
  const opLoc = measureAdapterLoc('openproject');
  const erpLoc = measureAdapterLoc('erpnext');
  assert.ok(opLoc >= 20 && opLoc <= 30, `unexpected OpenProject adapter LOC: ${opLoc}`);
  assert.ok(erpLoc >= 18 && erpLoc <= 28, `unexpected ERPNext adapter LOC: ${erpLoc}`);
  assert.equal(frozenNextFileSet().sha256, frozenNextFileSet().sha256);
});

test('equal-arms runner runs OpenProject + ERPNext with identical contrast sets, blocks leaks, records 403 as notTestable, and scores after fallback', async () => {
  const familiesFile = join(dir, 'families.json');
  const trainingFile = join(dir, 'training-examples.json');
  const opBlindFile = join(dir, 'blind-op.json');
  const erpBlindFile = join(dir, 'blind-erp.json');
  const keyFile = join(dir, 'answer-key.json');
  const opGuardFile = join(dir, 'op-guard.mjs');
  const erpGuardFile = join(dir, 'erp-guard.mjs');

  writeFileSync(familiesFile, JSON.stringify({
    about: ['gammatron-batch-canary-00000000-1111-4222-8333-444444444444'],
    families: [
      {
        familyId: 'op-approval-hours',
        application: 'openproject',
        policy: 'Save Work only when parent item is approved for the same hours.',
        disclosedExample: opRecipe('op-disc', 24, '{status.approved}', 24),
      },
      {
        familyId: 'erp-quote-covers',
        application: 'erpnext',
        policy: 'Confirm only when supplier quotation is submitted for the same total quantity.',
        disclosedExample: erpRecipe('erp-disc', 10, true, 10),
      },
    ],
  }));

  writeFileSync(trainingFile, JSON.stringify({
    about: ['gammatron-batch-canary-00000000-1111-4222-8333-444444444444'],
    families: [
      {
        familyId: 'op-approval-hours',
        examples: [
          { valid: true, why: 'approved 16h', recipe: opRecipe('op-tr-1', 16, '{status.approved}', 16) },
          { valid: true, why: 'approved 32h', recipe: opRecipe('op-tr-2', 32, '{status.approved}', 32) },
          { valid: false, why: 'on hold', failureId: 'tr-op-1', recipe: opRecipe('op-tr-3', 16, '{status.hold}', 16) },
          { valid: false, why: 'hours mismatch', failureId: 'tr-op-2', recipe: opRecipe('op-tr-4', 8, '{status.approved}', 16) },
        ],
      },
      {
        familyId: 'erp-quote-covers',
        examples: [
          { valid: true, why: 'submitted 12', recipe: erpRecipe('erp-tr-1', 12, true, 12) },
          { valid: true, why: 'submitted 6', recipe: erpRecipe('erp-tr-2', 6, true, 6) },
          { valid: false, why: 'draft quote', failureId: 'tr-erp-1', recipe: erpRecipe('erp-tr-3', 12, false, 12) },
          { valid: false, why: 'qty mismatch', failureId: 'tr-erp-2', recipe: erpRecipe('erp-tr-4', 4, true, 12) },
        ],
      },
    ],
  }));

  // Guard explicitly asserts no routeId/entryBranch/steps leaked!
  writeFileSync(opGuardFile, `
    export async function decide(input) {
      if ('routeId' in input || 'entryBranch' in input || 'steps' in input) {
        throw new Error('METADATA_LEAKED_TO_GUARD');
      }
      const rec = await input.get('/api/v3/work_packages/' + input.workPackageId);
      const pHref = rec.body?._links?.parent?.href;
      if (!pHref) return { decision: 'stop', reason: 'missing parent' };
      const parent = await input.get(pHref);
      const ok = String(parent.body?._links?.status?.href ?? '').endsWith('/16')
        && parent.body?.estimatedTime === input.workDuration;
      return { decision: ok ? 'write' : 'stop', reason: ok ? 'ok' : 'blocked' };
    }
  `);

  writeFileSync(erpGuardFile, `
    export async function decide(input) {
      if ('routeId' in input || 'entryBranch' in input || 'steps' in input) {
        throw new Error('METADATA_LEAKED_TO_GUARD');
      }
      const po = (await input.get('/api/resource/Purchase%20Order/' + encodeURIComponent(input.name))).body?.data;
      const sqName = po?.items?.[0]?.supplier_quotation;
      if (!sqName) return { decision: 'stop', reason: 'missing sq' };
      const sq = (await input.get('/api/resource/Supplier%20Quotation/' + encodeURIComponent(sqName))).body?.data;
      const ok = sq?.docstatus === 1 && sq?.total_qty === po?.total_qty;
      return { decision: ok ? 'write' : 'stop', reason: ok ? 'ok' : 'blocked' };
    }
  `);

  writeFileSync(opBlindFile, JSON.stringify({
    recipes: [
      opRecipe('op-b1', 40, '{status.approved}', 40),
      opRecipe('op-b2', 40, '{status.hold}', 40),
      opRecipe('op-b3', 40, '{status.approved}', 40, 'refuse-403-proj'), // 403 setup refusal -> notTestable!
    ],
  }));
  writeFileSync(erpBlindFile, JSON.stringify({
    recipes: [
      erpRecipe('erp-b1', 15, true, 15, 'CONF-8001'),
      erpRecipe('erp-b2', 15, false, 15, 'CONF-8002'),
    ],
  }));
  writeFileSync(keyFile, JSON.stringify({
    routes: {
      'op-b1': { valid: true, why: 'ok', application: 'openproject', familyId: 'op-approval-hours', confidence: 'sure' },
      'op-b2': { valid: false, why: 'hold', application: 'openproject', familyId: 'op-approval-hours', failureId: 'f-op-hold', failureReason: 'Parent item on hold.', confidence: 'sure' },
      'op-b3': { valid: true, why: '403 blocked', application: 'openproject', familyId: 'op-approval-hours', confidence: 'sure' },
      'erp-b1': { valid: true, why: 'ok', application: 'erpnext', familyId: 'erp-quote-covers', confidence: 'sure' },
      'erp-b2': { valid: false, why: 'draft', application: 'erpnext', familyId: 'erp-quote-covers', failureId: 'f-erp-draft', failureReason: 'Quotation still draft.', confidence: 'sure' },
    },
  }));

  const inProcessGuardRunner = async ({ guardDir, route, get }) => {
    const mod = await import(`${pathToFileURL(join(guardDir, 'guard.mjs')).href}?t=${Date.now()}-${Math.random()}`);
    let reads = 0;
    const ans = await mod.decide({ ...route, get: p => { reads += 1; return get(p); } });
    return { decision: ans.decision, reason: ans.reason, reads, error: null };
  };

  const opState = {
    new: {
      tag: '14.0.0',
      url: baseUrl,
      seed: {
        authorToken: 'A', approverToken: 'B',
        newStatusHref: '/api/v3/statuses/15', approvedStatusHref: '/api/v3/statuses/16',
        holdStatusHref: '/api/v3/statuses/17', disallowedStatusHref: '/api/v3/statuses/18',
        authorUserId: 5, approverUserId: 6,
      },
    },
  };
  const opDeps = {
    freshInstance() { opStore.clear(); },
    stopInstance() {},
    readState: () => opState,
    requester: rel => async (account, method, path, body) => {
      const r = await fetch(rel.url + path, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Basic ${Buffer.from(`apikey:${account === 'author' ? 'A' : 'B'}`).toString('base64')}`,
        },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      return { status: r.status, body: await r.json() };
    },
    async openWriter() {
      const readRow = id => {
        const r = opStore.get(id);
        return { lockVersion: r.lockVersion, estimatedHours: toHours(r.estimatedTime) };
      };
      return {
        readRow,
        close: async () => {},
        async write(route) {
          const before = readRow(route.workPackageId);
          const r = opStore.get(route.workPackageId);
          r.estimatedTime = `PT${route.workHours}H`;
          r.lockVersion += 1;
          return { httpStatus: 200, before, after: readRow(route.workPackageId) };
        },
      };
    },
    guardRunner: inProcessGuardRunner,
    async replanDecider({ route, get }) {
      const rec = await get(`/api/v3/work_packages/${route.workPackageId}`);
      const parent = rec.body?._links?.parent?.href ? await get(rec.body._links.parent.href) : null;
      const ok = String(parent?.body?._links?.status?.href ?? '').endsWith('/16')
        && parent?.body?.estimatedTime === route.workDuration;
      return { decision: ok ? 'write' : 'stop', reason: 'replan', reads: 2, modelCalls: 1, costUsd: 0.05, error: null };
    },
  };

  const erpState = {
    new: {
      tag: 'v15.20.0',
      url: baseUrl,
      seed: { authorToken: 'AUTHOR:1', approverToken: 'APPROVER:2' },
    },
  };
  const erpDeps = {
    freshInstance() { erpQuotes.clear(); erpOrders.clear(); },
    stopInstance() {},
    readState: () => erpState,
    requester: rel => async (account, method, path, body) => {
      const r = await fetch(rel.url + path, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `token ${rel.seed[account === 'author' ? 'authorToken' : 'approverToken']}`,
        },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      return { status: r.status, body: await r.json() };
    },
    async openWriter() {
      const readRow = name => {
        const o = erpOrders.get(name);
        return { modified: o.modified, terms: o.terms };
      };
      return {
        readRow,
        holdsReference: (name, ref) => String(erpOrders.get(name)?.terms ?? '').includes(ref),
        close: async () => {},
        async write(route) {
          const before = readRow(route.name);
          const o = erpOrders.get(route.name);
          o.modified = '2026-11-24 10:00:05.000000';
          o.terms = `Confirmed ${route.reference}`;
          return { httpStatus: 200, before, after: readRow(route.name) };
        },
      };
    },
    guardRunner: inProcessGuardRunner,
    async replanDecider({ route, get }) {
      const po = (await get(`/api/resource/Purchase%20Order/${encodeURIComponent(route.name)}`)).body?.data;
      const sqName = po?.items?.[0]?.supplier_quotation;
      const sq = sqName ? (await get(`/api/resource/Supplier%20Quotation/${encodeURIComponent(sqName)}`)).body?.data : null;
      const ok = sq?.docstatus === 1 && sq?.total_qty === po?.total_qty;
      return { decision: ok ? 'write' : 'stop', reason: 'replan', reads: 2, modelCalls: 1, costUsd: 0.05, error: null };
    },
  };

  const runDir = join(dir, 'combined-run');

  // Verify uncharged human adapter is rejected (loophole closed)
  await assert.rejects(
    () => freezeDeterministicArm({
      application: 'openproject',
      upgrade: '13.4.0->14.0.0',
      arm: 'repair-boundary',
      familiesFile,
      trainingExamplesFile: trainingFile,
      runDir: join(runDir, 'op'),
      readPlansByFamily: {
        'op-approval-hours': [
          { role: 'record', path: '/api/v3/work_packages/{target}' },
          { role: 'approval', follow: { role: 'record', link: 'parent' } },
        ],
      },
      deps: opDeps,
    }),
    /requires positive finite adapterAuthoringMinutes/,
  );

  // Freeze both arms on OpenProject with measured adapter/guard minutes and verify identical trainingReleaseSha256
  const opRb = await freezeDeterministicArm({
    application: 'openproject',
    upgrade: '13.4.0->14.0.0',
    arm: 'repair-boundary',
    familiesFile,
    trainingExamplesFile: trainingFile,
    runDir: join(runDir, 'op'),
    readPlansByFamily: {
      'op-approval-hours': [
        { role: 'record', path: '/api/v3/work_packages/{target}' },
        { role: 'approval', follow: { role: 'record', link: 'parent' } },
      ],
    },
    adapterSource: 'human',
    adapterAuthoringMinutes: 4.25,
    deps: opDeps,
  });
  assert.equal(opRb.adapterSource, 'human');
  assert.equal(opRb.adapterAuthoringMinutes, 4.25);
  assert.ok(opRb.authoringMinutes >= 4.25);
  const opExpert = await freezeDeterministicArm({
    application: 'openproject',
    upgrade: '13.4.0->14.0.0',
    arm: 'expert-guard',
    familiesFile,
    trainingExamplesFile: trainingFile,
    runDir: join(runDir, 'op'),
    guardSourceFile: opGuardFile,
    measuredAuthoringMinutes: 6.5,
    deps: opDeps,
  });
  registerAlwaysReplanPhase({ application: 'openproject', upgrade: '13.4.0->14.0.0', runDir: join(runDir, 'op') });
  assert.equal(opRb.trainingReleaseSha256, opExpert.trainingReleaseSha256);

  for (const arm of ['repair-boundary', 'expert-guard', 'always-replan']) {
    await runBlindArm({
      application: 'openproject',
      upgrade: '13.4.0->14.0.0',
      arm,
      familiesFile,
      trainingExamplesFile: trainingFile,
      recipesFile: opBlindFile,
      runDir: join(runDir, 'op'),
      deps: opDeps,
    });
  }

  // Freeze & run ERPNext using audited model-phase adapter discovery ($0.32 charged automatically)
  recordAuditedAdapterPhase({
    application: 'erpnext',
    upgrade: '15.10.0->15.20.0',
    phase: 'adapter-discovery',
    runDir: join(runDir, 'erp'),
    startedAt: '2026-11-24T10:00:00Z',
    endedAt: '2026-11-24T10:01:30Z',
    costUsd: 0.32,
    budgetUsd: 0.60,
    modelCalls: 2,
    modelTurns: 4,
    adapterLoc: measureAdapterLoc('erpnext'),
    artifactSha256: 'c'.repeat(64),
  });
  await freezeDeterministicArm({
    application: 'erpnext',
    upgrade: '15.10.0->15.20.0',
    arm: 'repair-boundary',
    familiesFile,
    trainingExamplesFile: trainingFile,
    runDir: join(runDir, 'erp'),
    readPlansByFamily: {
      'erp-quote-covers': [
        { role: 'order', target: true },
        { role: 'quotation', follow: { role: 'order', field: 'items.0.supplier_quotation', doctype: 'Supplier Quotation' } },
      ],
    },
    adapterSource: 'model-phase',
    deps: erpDeps,
  });
  await freezeDeterministicArm({
    application: 'erpnext',
    upgrade: '15.10.0->15.20.0',
    arm: 'expert-guard',
    familiesFile,
    trainingExamplesFile: trainingFile,
    runDir: join(runDir, 'erp'),
    guardSourceFile: erpGuardFile,
    measuredAuthoringMinutes: 6.5,
    deps: erpDeps,
  });
  registerAlwaysReplanPhase({ application: 'erpnext', upgrade: '15.10.0->15.20.0', runDir: join(runDir, 'erp') });
  for (const arm of ['repair-boundary', 'expert-guard', 'always-replan']) {
    await runBlindArm({
      application: 'erpnext',
      upgrade: '15.10.0->15.20.0',
      arm,
      familiesFile,
      trainingExamplesFile: trainingFile,
      recipesFile: erpBlindFile,
      runDir: join(runDir, 'erp'),
      deps: erpDeps,
    });
  }

  // Merge JSONL records and score through score_after_fallback.py
  const mergedRoutes = join(dir, 'merged-routes.jsonl');
  const mergedPhases = join(dir, 'merged-phases.jsonl');
  execFileSync('sh', ['-c', `cat "${join(runDir, 'op/route-records.jsonl')}" "${join(runDir, 'erp/route-records.jsonl')}" > "${mergedRoutes}"`]);
  execFileSync('sh', ['-c', `cat "${join(runDir, 'op/phase-records.jsonl')}" "${join(runDir, 'erp/phase-records.jsonl')}" > "${mergedPhases}"`]);

  const rawScore = execFileSync('python3', [
    '-B', SCORER,
    '--routes', mergedRoutes,
    '--phases', mergedPhases,
    '--key', keyFile,
    '--blind', opBlindFile,
    '--blind', erpBlindFile,
    '--rate-per-minute', '0.50',
    '--require-measured-adapter',
  ], { encoding: 'utf8' });
  const report = JSON.parse(rawScore);
  assert.equal(report.valid, true, JSON.stringify(report.problems));
  assert.equal(report.independentInvalidCases, 2);
  assert.equal(report.verdict, 'Underpowered: 2 independent invalid cases, below 99. No verdict.');
  // op-b3 hit 403 and was cleanly isolated into notTestableReleases (3 arms)
  assert.equal(report.notTestableReleases.length, 3);
  assert.equal(report.notTestableReleases[0].refusal.status, 403);
  assert.equal(report.arms['repair-boundary'].voided, false);
  assert.equal(report.arms['repair-boundary'].wrongFailureIdsAfterFallback, 0);
  assert.equal(report.arms['repair-boundary'].validCompletedAfterFallback, 2);
  assert.equal(report.arms['repair-boundary'].spendOneOffUsd, '0.32');
  assert.equal(report.arms['repair-boundary'].adapterAuthoringMinutes, '4.25');
  assert.equal(report.arms['expert-guard'].guardAuthoringMinutes, '13.0');
  assert.equal(report.arms['expert-guard'].validCompletedAfterFallback, 2);

  // Run cost_report.py on the merged run and verify break-even & historical provenance audit
  const rawCostReport = execFileSync('python3', [
    '-B', COST_REPORT,
    '--routes', mergedRoutes,
    '--phases', mergedPhases,
    '--key', keyFile,
    '--blind', opBlindFile,
    '--blind', erpBlindFile,
    '--rate-per-minute', '0.50',
  ], { encoding: 'utf8' });
  const costReport = JSON.parse(rawCostReport);
  assert.equal(costReport.valid, true);
  assert.ok(costReport.legacyAdapterProvenance.length >= 4);
  assert.ok(costReport.legacyAdapterProvenance.every(e => e.usableForRung2EffortClaim === false));
  assert.equal(
    costReport.pairwiseBreakEven['always-replan'].byRate.r.regime,
    'break-even-above-V*',
  );
  assert.ok(costReport.pairwiseBreakEven['always-replan'].byRate.r.breakEvenVolumeRoutes > 0);
});

test('ERPNext drift screen preflight blocks below 25 GiB and records 403 setup refusals as notTestable under Owner Correction (d)', async () => {
  assert.throws(
    () => assertFreeDiskForDockerScreen(25, '/tmp', () => ({ bavail: 6n * 1024n, bsize: 1024n * 1024n })),
    /below the 25 GiB safety floor/,
  );
  assert.equal(
    assertFreeDiskForDockerScreen(25, '/tmp', () => ({ bavail: 30n * 1024n, bsize: 1024n * 1024n })),
    30,
  );

  const rel = { url: baseUrl, seed: { authorToken: 'AUTHOR:1', approverToken: 'APPROVER:2' } };
  const frozen = await freezeErpScreenLearned(rel);
  const clean = await checkErpReleaseWithRefusal(rel, frozen.artifact);
  assert.equal(clean.notTestable, false);
  assert.equal(clean.allCorrect, true);

  refuseErpApproverSetup403 = true;
  try {
    const blocked = await checkErpReleaseWithRefusal(rel, frozen.artifact);
    assert.equal(blocked.notTestable, true);
    assert.equal(blocked.refusal.status, 403);
    assert.match(String(blocked.refusal.response?.exception ?? ''), /PermissionError.*Item/);
  } finally {
    refuseErpApproverSetup403 = false;
  }
});

test('free ($0) counterexample check falsifies OpenProject statusCode===16, ERPNext line-item swap, and OP 17.8 multi-version subset boundary', async () => {
  const report = await runFreeCounterexampleCheck();
  assert.equal(report.modelCalls, 0);
  assert.equal(report.costUsd, 0);
  assert.deepEqual(report.learnedTerms, [
    { kind: 'equals-literal', left: 'approval:/statusCode', value: 16 },
  ]);
  assert.equal(report.repairBoundarySummary.falsifiedSafetyOnLiteralGuard, true);
  assert.equal(report.repairBoundarySummary.wrongWritesCommitted, 3);
  assert.equal(report.expertGuardSummary.wrongWritesCommitted, 0);
  assert.equal(report.scalarProjectionBlindspotWhenTrained.reason, 'no-separating-guard');
  assert.equal(report.erpnextScalarCollapseSuite.lineItemSwapWrongWriteByLearned, true);
  assert.equal(report.erpnextScalarCollapseSuite.lineItemSwapBlockedByExpertGuard, true);
  assert.equal(report.erpnextScalarCollapseSuite.rateOverrunLearnReason, 'no-separating-guard');
  assert.equal(report.op178MultiTargetVersionsUpgradeProof.preConversionSingleVersion.status, 'learned');
  assert.equal(report.op178MultiTargetVersionsUpgradeProof.postConversionMultiTargetVersions.reason, 'no-separating-guard');
  assert.equal(report.op178MultiTargetVersionsUpgradeProof.postConversionMultiTargetVersions.expertSubsetGuardCompletesBothValid, true);
});

test('OpenProject 17.8 Target versions 3-repeat $0 candidate screen and prelearn decision rule enforce all gates', async () => {
  const res = await op178ScreenSelftest();
  assert.equal(res.ok, true);
  const preRes = prelearnRuleSelftest();
  assert.equal(preRes.ok, true);
});
