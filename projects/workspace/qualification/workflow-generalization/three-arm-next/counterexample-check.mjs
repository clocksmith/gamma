#!/usr/bin/env node
// Free ($0, zero-model-call) counterexample & representation-boundary suite for Gammatron (#88).
//
// Runs three $0 disposable suites BEFORE any upgrade campaign:
//   Suite 1 (OpenProject `approval:/statusCode === 16`):
//     - Minimal-cover `learnRepairBoundary` emits `approval:/statusCode === 16` when status
//       alone separates the contrast negatives, committing 3/3 wrong writes on hours mismatch,
//       quarantine project, and `[LEGAL-HOLD]` description (vs 0/3 for `expert-guard`).
//   Suite 2 (ERPNext `projectFrappeResourceScalars` line-item & rate blindspots):
//     - Even when trained on status + totalQty + company + lineCount contrast examples so all
//       projected scalars match (`docstatus === 1`, `totalQty === 10`, `lineCount === 2`,
//       `companyCode === 101`), swapping line-item quantities (`8x BOLT + 2x TURBINE` vs
//       `2x BOLT + 8x TURBINE`) produces identical scalar facts and commits a durable wrong
//       Purchase Order confirmation (1/1 wrong write vs 0/1 for `erp-expert-guard`), while
//       unit `rate` gouging (`$100` -> `$9,500` at equal `qty`) hits `no-separating-guard`.
//   Suite 3 (OpenProject 17.8 `Version` -> multi-value `Target versions` upgrade boundary):
//     - Pre-conversion (single `Version` -> `versionCode` integer): `learnRepairBoundary`
//       cleanly learns `record:/versionCode === approval:/versionCode` (2/2 valid, 0 wrong).
//     - Post-conversion (multi-value `Target versions`, subset policy `child subseteq parent`):
//       conjunctive `equals-literal` / `equals-field` over scalar slots (`v0, v1, count`)
//       cannot express subset inclusion (`[10, 11]` and `[11, 12]` both valid under `[10, 11, 12]`,
//       while `[10, 99]` is invalid), returning `no-separating-guard` when trained (0 own valid,
//       100% fallback) while a 10-line `expert-guard` completes 2/2 valid with 0 wrong writes.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  checkRepairBoundary,
  collectObservedFacts,
  learnRepairBoundary,
} from '../../../src/client/repair-boundary.js';
import { createAppSurface, DEFAULT_LIMITS } from '../three-arm/app-surface.mjs';
import { createTeacher as createOpTeacher, decide as decideOpBoundary } from '../three-arm/repair-boundary-arm.mjs';
import { createTeacher as createErpTeacher, decide as decideErpBoundary } from '../three-arm-erpnext/erp-learner.mjs';
import { createErpSurface, ERP_LIMITS } from '../three-arm-erpnext/erp-surface.mjs';
import { forArm } from './runner.mjs';

const sha256 = s => createHash('sha256').update(s, 'utf8').digest('hex');

const fromHours = h => (h === null
  ? null
  : `P${Math.floor(h / 24) ? `${Math.floor(h / 24)}D` : ''}${h % 24 || !Math.floor(h / 24) ? `T${h % 24}H` : ''}`);

const PROJECT_IDS = Object.freeze({
  'stage2-qual-proj': 1,
  'stage2-partner-proj': 2,
  'stage2-quarantine-proj': 3,
});

async function decideOpExpertGuard(armInput, get) {
  const orderRes = await get(`/api/v3/work_packages/${armInput.workPackageId}`);
  const parentHref = orderRes.body?._links?.parent?.href;
  if (!parentHref) return { decision: 'stop', reason: 'missing-parent' };
  const parentRes = await get(parentHref);
  const p = parentRes.body;
  const approved = String(p?._links?.status?.href ?? '').endsWith('/16');
  const hoursMatch = p?.estimatedTime === armInput.workDuration;
  const sameProject = p?._links?.project?.href === orderRes.body?._links?.project?.href;
  const rawDesc = String(p?.description?.raw ?? '');
  const legalHold = rawDesc.includes('[LEGAL-HOLD]');
  const ok = approved && hoursMatch && sameProject && !legalHold;
  return { decision: ok ? 'write' : 'stop', reason: ok ? 'policy-satisfied' : 'policy-blocked' };
}

async function decideErpExpertGuard(armInput, get) {
  const po = (await get(`/api/resource/Purchase%20Order/${encodeURIComponent(armInput.name)}`)).body?.data;
  const sqName = po?.items?.[0]?.supplier_quotation;
  if (!sqName) return { decision: 'stop', reason: 'missing-quotation' };
  const sq = (await get(`/api/resource/Supplier%20Quotation/${encodeURIComponent(sqName)}`)).body?.data;
  if (!sq || sq.docstatus !== 1 || sq.company !== po.company) {
    return { decision: 'stop', reason: 'status-or-company-mismatch' };
  }
  const sqItems = new Map((sq.items ?? []).map(it => [it.item_code, { qty: it.qty, rate: it.rate }]));
  const poItems = po.items ?? [];
  if (!poItems.length || poItems.length !== sqItems.size) {
    return { decision: 'stop', reason: 'item-count-mismatch' };
  }
  for (const it of poItems) {
    const ref = sqItems.get(it.item_code);
    if (!ref || ref.qty !== it.qty || ref.rate > ref.rate || it.rate > ref.rate) {
      return { decision: 'stop', reason: 'item-qty-or-rate-mismatch' };
    }
  }
  return { decision: 'write', reason: 'line-items-verified' };
}

async function runErpCounterexampleSuite() {
  const quotes = new Map();
  const orders = new Map();
  let seq = 1;

  const server = createServer((req, res) => {
    res.setHeader('Content-Type', 'application/json');
    const sqMatch = req.url.match(/^\/api\/resource\/Supplier%20Quotation\/([^/?]+)$/);
    if (req.method === 'GET' && sqMatch) {
      const doc = quotes.get(decodeURIComponent(sqMatch[1]));
      res.statusCode = doc ? 200 : 404;
      res.end(JSON.stringify(doc ? { data: doc } : { message: 'missing' }));
      return;
    }
    const poMatch = req.url.match(/^\/api\/resource\/Purchase%20Order\/([^/?]+)$/);
    if (req.method === 'GET' && poMatch) {
      const doc = orders.get(decodeURIComponent(poMatch[1]));
      res.statusCode = doc ? 200 : 404;
      res.end(JSON.stringify(doc ? { data: doc } : { message: 'missing' }));
      return;
    }
    res.statusCode = 404;
    res.end(JSON.stringify({ message: 'not found' }));
  });

  await new Promise(done => server.listen(0, '127.0.0.1', done));
  const baseUrl = `http://127.0.0.1:${server.address().port}`;

  const putErpPair = ({ sqCompany, sqDocstatus, sqItems, poCompany, poItems }) => {
    const sqName = `PUR-SQ-${seq++}`;
    const poName = `PUR-ORD-${seq++}`;
    const sumQty = arr => arr.reduce((s, x) => s + x.qty, 0);
    quotes.set(sqName, {
      name: sqName,
      doctype: 'Supplier Quotation',
      company: sqCompany,
      docstatus: sqDocstatus,
      total_qty: sumQty(sqItems),
      items: sqItems,
    });
    orders.set(poName, {
      name: poName,
      doctype: 'Purchase Order',
      company: poCompany,
      docstatus: 0,
      total_qty: sumQty(poItems),
      items: poItems.map(it => ({ ...it, supplier_quotation: sqName })),
      modified: '2026-11-25 00:00:00.000000',
      terms: '',
    });
    return { sqName, poName };
  };

  try {
    const request = async (_acct, method, path) => {
      const r = await fetch(baseUrl + path, { method });
      return { status: r.status, body: await r.json() };
    };
    const makeGet = () => {
      const surf = createErpSurface({ mode: 'decision', request, limits: ERP_LIMITS });
      return path => surf.tools.erp_get({ path });
    };

    const familyId = 'erp-full-scalar-gate';
    const teacher = createErpTeacher([familyId]);
    const planRes = teacher.setReadPlan(familyId, [
      { role: 'order', target: true },
      { role: 'quotation', follow: { role: 'order', field: 'items.0.supplier_quotation', doctype: 'Supplier Quotation' } },
    ]);
    assert.equal(planRes.ok, true);

    // Give the ERPNext learner contrast examples covering EVERY scalar field in `projectFrappeResourceScalars`
    // (`docstatus`, `totalQty`, `companyCode`, `lineCount`)!
    const trainExamples = [
      {
        label: 'valid',
        spec: {
          sqCompany: 'Stage2 Qual Corp', sqDocstatus: 1,
          sqItems: [{ item_code: 'BOLT', qty: 8, rate: 10 }, { item_code: 'TURBINE', qty: 2, rate: 5000 }],
          poCompany: 'Stage2 Qual Corp',
          poItems: [{ item_code: 'BOLT', qty: 8, rate: 10 }, { item_code: 'TURBINE', qty: 2, rate: 5000 }],
        },
      },
      {
        label: 'valid',
        spec: {
          sqCompany: 'Stage2 Partner Corp', sqDocstatus: 1,
          sqItems: [{ item_code: 'BOLT', qty: 4, rate: 10 }],
          poCompany: 'Stage2 Partner Corp',
          poItems: [{ item_code: 'BOLT', qty: 4, rate: 10 }],
        },
      },
      {
        label: 'invalid', // docstatus = 0 (draft)
        spec: {
          sqCompany: 'Stage2 Qual Corp', sqDocstatus: 0,
          sqItems: [{ item_code: 'BOLT', qty: 8, rate: 10 }, { item_code: 'TURBINE', qty: 2, rate: 5000 }],
          poCompany: 'Stage2 Qual Corp',
          poItems: [{ item_code: 'BOLT', qty: 8, rate: 10 }, { item_code: 'TURBINE', qty: 2, rate: 5000 }],
        },
      },
      {
        label: 'invalid', // total_qty mismatch (6 != 10)
        spec: {
          sqCompany: 'Stage2 Qual Corp', sqDocstatus: 1,
          sqItems: [{ item_code: 'BOLT', qty: 4, rate: 10 }, { item_code: 'TURBINE', qty: 2, rate: 5000 }],
          poCompany: 'Stage2 Qual Corp',
          poItems: [{ item_code: 'BOLT', qty: 8, rate: 10 }, { item_code: 'TURBINE', qty: 2, rate: 5000 }],
        },
      },
      {
        label: 'invalid', // company mismatch (Quarantine != Qual)
        spec: {
          sqCompany: 'Stage2 Quarantine Corp', sqDocstatus: 1,
          sqItems: [{ item_code: 'BOLT', qty: 8, rate: 10 }, { item_code: 'TURBINE', qty: 2, rate: 5000 }],
          poCompany: 'Stage2 Qual Corp',
          poItems: [{ item_code: 'BOLT', qty: 8, rate: 10 }, { item_code: 'TURBINE', qty: 2, rate: 5000 }],
        },
      },
    ];
    for (const ex of trainExamples) {
      const { poName } = putErpPair(ex.spec);
      const route = forArm('erpnext', { familyId, doctype: 'Purchase Order', name: poName, reference: 'CONF-1' });
      const added = await teacher.addExample(familyId, ex.label, route, makeGet());
      assert.equal(added.ok, true);
    }
    const learned = teacher.learn(familyId);
    assert.equal(learned.status, 'learned');
    const frozen = JSON.parse(teacher.freeze().text);

    // Counterexample: line-item swap (`8x BOLT + 2x TURBINE` quoted vs `2x BOLT + 8x TURBINE` ordered!)
    // Both have `docstatus=1`, `totalQty=10`, `lineCount=2`, `companyCode=101`!
    const swapSpec = {
      sqCompany: 'Stage2 Qual Corp', sqDocstatus: 1,
      sqItems: [{ item_code: 'BOLT', qty: 8, rate: 10 }, { item_code: 'TURBINE', qty: 2, rate: 5000 }],
      poCompany: 'Stage2 Qual Corp',
      poItems: [{ item_code: 'BOLT', qty: 2, rate: 10 }, { item_code: 'TURBINE', qty: 8, rate: 5000 }],
    };
    const { poName: swapPo } = putErpPair(swapSpec);
    const swapInput = forArm('erpnext', { familyId, doctype: 'Purchase Order', name: swapPo, reference: 'CONF-SWAP' });
    const rbSwap = await decideErpBoundary(frozen, swapInput, makeGet());
    const expertSwap = await decideErpExpertGuard(swapInput, makeGet());

    // Also verify rate-overrun (`rate: 10` quoted vs `rate: 9500` ordered) hits `no-separating-guard` when trained!
    const rateTeacher = createErpTeacher(['erp-rate-gate']);
    rateTeacher.setReadPlan('erp-rate-gate', [
      { role: 'order', target: true },
      { role: 'quotation', follow: { role: 'order', field: 'items.0.supplier_quotation', doctype: 'Supplier Quotation' } },
    ]);
    const okRate = putErpPair({
      sqCompany: 'Stage2 Qual Corp', sqDocstatus: 1, sqItems: [{ item_code: 'BOLT', qty: 10, rate: 100 }],
      poCompany: 'Stage2 Qual Corp', poItems: [{ item_code: 'BOLT', qty: 10, rate: 100 }],
    });
    const gougeRate = putErpPair({
      sqCompany: 'Stage2 Qual Corp', sqDocstatus: 1, sqItems: [{ item_code: 'BOLT', qty: 10, rate: 100 }],
      poCompany: 'Stage2 Qual Corp', poItems: [{ item_code: 'BOLT', qty: 10, rate: 9500 }],
    });
    await rateTeacher.addExample('erp-rate-gate', 'valid', forArm('erpnext', { familyId: 'erp-rate-gate', name: okRate.poName, reference: 'R1' }), makeGet());
    await rateTeacher.addExample('erp-rate-gate', 'invalid', forArm('erpnext', { familyId: 'erp-rate-gate', name: gougeRate.poName, reference: 'R2' }), makeGet());
    const rateLearn = rateTeacher.learn('erp-rate-gate');

    return {
      learnedTermsFullScalar: learned.guard,
      lineItemSwapWrongWriteByLearned: rbSwap.decision === 'write',
      lineItemSwapBlockedByExpertGuard: expertSwap.decision === 'stop',
      rateOverrunLearnStatus: rateLearn.status,
      rateOverrunLearnReason: rateLearn.reason,
    };
  } finally {
    server.close();
  }
}

function runOp178TargetVersionsStructuralProof() {
  const effectSingle = `opbind-v1:${sha256('op178-single-version')}`;
  const effectMulti = `opbind-v1:${sha256('op178-multi-target-versions')}`;

  const obs = (recordFacts, approvalFacts) => collectObservedFacts([
    { sameOrigin: true, method: 'GET', transport: 'fetch', status: 200, sourceRole: 'record', json: recordFacts },
    { sameOrigin: true, method: 'GET', transport: 'fetch', status: 200, sourceRole: 'approval', json: approvalFacts },
  ]);

  // 1. Pre-conversion (OpenProject 17.8 with single `Version` -> scalar `versionCode`)
  const preLearned = learnRepairBoundary({
    intendedEffect: effectSingle,
    positive: [
      obs({ statusCode: 15, versionCode: 10 }, { statusCode: 16, versionCode: 10 }),
      obs({ statusCode: 15, versionCode: 11 }, { statusCode: 16, versionCode: 11 }),
    ],
    negative: [
      obs({ statusCode: 15, versionCode: 99 }, { statusCode: 16, versionCode: 10 }),
      obs({ statusCode: 15, versionCode: 10 }, { statusCode: 17, versionCode: 10 }),
    ],
  });
  assert.equal(preLearned.status, 'learned');
  const preValid = checkRepairBoundary(preLearned, obs({ statusCode: 15, versionCode: 12 }, { statusCode: 16, versionCode: 12 }), effectSingle);
  const preInvalid = checkRepairBoundary(preLearned, obs({ statusCode: 15, versionCode: 99 }, { statusCode: 16, versionCode: 12 }), effectSingle);

  // 2. Post-conversion (OpenProject 17.8 with multi-value `Target versions`, subset policy `child subseteq parent`)
  // Even if an adapter projects sorted version codes into scalar slots (`v0, v1, v2, versionCount`),
  // valid child `[10, 11]` and valid child `[11, 12]` under parent `[10, 11, 12]` share NO slot equality
  // that distinguishes them from invalid `[10, 99]` under `[10, 11, 12]`!
  const postSlotProj = versions => ({
    versionCount: versions.length,
    ...(versions[0] !== undefined ? { v0: versions[0] } : {}),
    ...(versions[1] !== undefined ? { v1: versions[1] } : {}),
    ...(versions[2] !== undefined ? { v2: versions[2] } : {}),
  });
  const postLearned = learnRepairBoundary({
    intendedEffect: effectMulti,
    positive: [
      obs({ statusCode: 15, ...postSlotProj([10, 11]) }, { statusCode: 16, ...postSlotProj([10, 11, 12]) }),
      obs({ statusCode: 15, ...postSlotProj([11, 12]) }, { statusCode: 16, ...postSlotProj([10, 11, 12]) }),
    ],
    negative: [
      obs({ statusCode: 15, ...postSlotProj([10, 99]) }, { statusCode: 16, ...postSlotProj([10, 11, 12]) }),
    ],
  });

  // Reference 3-line subset guard over raw `_links.targetVersions`
  const subsetExpertGuard = (childVersions, parentStatus, parentVersions) => {
    const allowed = new Set(parentVersions);
    return parentStatus === 16 && childVersions.length > 0 && childVersions.every(v => allowed.has(v));
  };

  return {
    preConversionSingleVersion: {
      status: preLearned.status,
      guard: preLearned.guard,
      unseenValidEligible: preValid.status === 'eligible-for-review',
      unseenInvalidBlocked: preInvalid.status === 'abstain',
    },
    postConversionMultiTargetVersions: {
      status: postLearned.status,
      reason: postLearned.reason,
      expertSubsetGuardCompletesBothValid: (
        subsetExpertGuard([10, 11], 16, [10, 11, 12]) && subsetExpertGuard([11, 12], 16, [10, 11, 12])
      ),
      expertSubsetGuardBlocksInvalid: !subsetExpertGuard([10, 99], 16, [10, 11, 12]),
    },
  };
}

export async function runFreeCounterexampleCheck() {
  const store = new Map();
  let nextId = 1;

  const view = rec => ({
    id: rec.id,
    lockVersion: rec.lockVersion,
    estimatedTime: fromHours(rec.hours),
    subject: rec.subject,
    description: { format: 'markdown', raw: rec.description ?? '' },
    _links: {
      status: { href: `/api/v3/statuses/${rec.statusCode}` },
      project: { href: `/api/v3/projects/${rec.projectCode}` },
      ...(rec.parentId ? { parent: { href: `/api/v3/work_packages/${rec.parentId}` } } : {}),
    },
  });

  const server = createServer((req, res) => {
    const m = req.url.match(/^\/api\/v3\/work_packages\/(\d+)$/);
    res.setHeader('Content-Type', 'application/json');
    if (req.method === 'GET' && m && store.has(Number(m[1]))) {
      res.statusCode = 200;
      res.end(JSON.stringify(view(store.get(Number(m[1])))));
      return;
    }
    res.statusCode = 404;
    res.end(JSON.stringify({ message: 'not found' }));
  });

  await new Promise(done => server.listen(0, '127.0.0.1', done));
  const baseUrl = `http://127.0.0.1:${server.address().port}`;

  const putPair = ({ parentHours, parentStatus, parentProject, parentDesc = '', childHours, childProject }) => {
    const parentId = nextId++;
    store.set(parentId, {
      id: parentId,
      lockVersion: 0,
      hours: parentHours,
      statusCode: parentStatus,
      projectCode: PROJECT_IDS[parentProject],
      subject: `Approval ${parentId}`,
      description: parentDesc,
      parentId: null,
    });
    const childId = nextId++;
    store.set(childId, {
      id: childId,
      lockVersion: 0,
      hours: childHours,
      statusCode: 15,
      projectCode: PROJECT_IDS[childProject],
      subject: `Order ${childId}`,
      description: '',
      parentId,
    });
    return { parentId, childId };
  };

  try {
    const request = async (_account, method, path) => {
      const r = await fetch(baseUrl + path, { method });
      return { status: r.status, body: await r.json() };
    };
    const makeGet = () => {
      const surf = createAppSurface({ mode: 'decision', request, limits: DEFAULT_LIMITS });
      return path => surf.tools.app_get({ path });
    };

    const familyId = 'op-approval-gate';
    const teacher = createOpTeacher([familyId]);
    const planRes = teacher.setReadPlan(familyId, [
      { role: 'record', path: '/api/v3/work_packages/{target}' },
      { role: 'approval', follow: { role: 'record', link: 'parent' } },
    ]);
    assert.equal(planRes.ok, true);

    const trainSpecs = [
      { label: 'valid', parentStatus: 16, parentHours: 16, writeHours: 16 },
      { label: 'valid', parentStatus: 16, parentHours: 24, writeHours: 24 },
      { label: 'invalid', parentStatus: 15, parentHours: 16, writeHours: 16 },
      { label: 'invalid', parentStatus: 17, parentHours: 24, writeHours: 24 },
    ];
    for (const ts of trainSpecs) {
      const { childId } = putPair({
        parentHours: ts.parentHours,
        parentStatus: ts.parentStatus,
        parentProject: 'stage2-qual-proj',
        childHours: 4,
        childProject: 'stage2-qual-proj',
      });
      const route = forArm('openproject', {
        familyId,
        project: 'stage2-qual-proj',
        workPackageId: childId,
        workHours: ts.writeHours,
      });
      const added = await teacher.addExample(familyId, ts.label, route, makeGet());
      assert.equal(added.ok, true);
    }

    const learned = teacher.learn(familyId);
    assert.equal(learned.status, 'learned');
    const frozen = JSON.parse(teacher.freeze().text);
    const terms = frozen.families[familyId].boundary.guard;

    assert.equal(terms.length, 1);
    assert.deepEqual(terms[0], {
      kind: 'equals-literal',
      left: 'approval:/statusCode',
      value: 16,
    });

    const cases = [
      {
        caseId: 'ctrl-valid-approved-same-proj-24h',
        independentLabelValid: true,
        failureId: null,
        setup: { parentHours: 24, parentStatus: 16, parentProject: 'stage2-qual-proj', parentDesc: '', childHours: 4, childProject: 'stage2-qual-proj' },
        writeHours: 24,
      },
      {
        caseId: 'ce-1-approved-wrong-hours',
        independentLabelValid: false,
        failureId: 'f-hours-mismatch-under-status16',
        setup: { parentHours: 8, parentStatus: 16, parentProject: 'stage2-qual-proj', parentDesc: '', childHours: 4, childProject: 'stage2-qual-proj' },
        writeHours: 24,
      },
      {
        caseId: 'ce-2-approved-quarantine-project',
        independentLabelValid: false,
        failureId: 'f-cross-project-under-status16',
        setup: { parentHours: 24, parentStatus: 16, parentProject: 'stage2-quarantine-proj', parentDesc: '', childHours: 4, childProject: 'stage2-qual-proj' },
        writeHours: 24,
      },
      {
        caseId: 'ce-3-approved-legal-hold-description',
        independentLabelValid: false,
        failureId: 'f-unprojected-description-hold',
        setup: { parentHours: 24, parentStatus: 16, parentProject: 'stage2-qual-proj', parentDesc: '[LEGAL-HOLD] Freeze work package changes.', childHours: 4, childProject: 'stage2-qual-proj' },
        writeHours: 24,
      },
    ];

    const evalArmOnCase = async (armName, c) => {
      const { childId } = putPair(c.setup);
      const armInput = forArm('openproject', {
        familyId,
        project: c.setup.childProject,
        workPackageId: childId,
        workHours: c.writeHours,
      });
      const before = { lockVersion: store.get(childId).lockVersion, hours: store.get(childId).hours };
      const res = armName === 'repair-boundary'
        ? await decideOpBoundary(frozen, armInput, makeGet())
        : await decideOpExpertGuard(armInput, makeGet());
      if (res.decision === 'write') {
        const row = store.get(childId);
        row.hours = c.writeHours;
        row.lockVersion += 1;
      }
      const after = { lockVersion: store.get(childId).lockVersion, hours: store.get(childId).hours };
      const committed = after.lockVersion !== before.lockVersion && after.hours === c.writeHours;
      const wrongWrite = !c.independentLabelValid && committed;
      return {
        caseId: c.caseId,
        independentLabelValid: c.independentLabelValid,
        failureId: c.failureId,
        decision: res.decision,
        committed,
        wrongWrite,
      };
    };

    const rbResults = [];
    const expertResults = [];
    for (const c of cases) {
      rbResults.push(await evalArmOnCase('repair-boundary', c));
      expertResults.push(await evalArmOnCase('expert-guard', c));
    }

    const teacherWithTextNeg = createOpTeacher([familyId]);
    teacherWithTextNeg.setReadPlan(familyId, [
      { role: 'record', path: '/api/v3/work_packages/{target}' },
      { role: 'approval', follow: { role: 'record', link: 'parent' } },
    ]);
    const posPair = putPair({
      parentHours: 24, parentStatus: 16, parentProject: 'stage2-qual-proj', parentDesc: '', childHours: 4, childProject: 'stage2-qual-proj',
    });
    const negTextPair = putPair({
      parentHours: 24, parentStatus: 16, parentProject: 'stage2-qual-proj', parentDesc: '[LEGAL-HOLD] Stop', childHours: 4, childProject: 'stage2-qual-proj',
    });
    await teacherWithTextNeg.addExample(
      familyId, 'valid',
      forArm('openproject', { familyId, project: 'stage2-qual-proj', workPackageId: posPair.childId, workHours: 24 }),
      makeGet(),
    );
    await teacherWithTextNeg.addExample(
      familyId, 'invalid',
      forArm('openproject', { familyId, project: 'stage2-qual-proj', workPackageId: negTextPair.childId, workHours: 24 }),
      makeGet(),
    );
    const textLearnOutcome = teacherWithTextNeg.learn(familyId);

    const erpSuite = await runErpCounterexampleSuite();
    const op178Proof = runOp178TargetVersionsStructuralProof();

    return {
      schema: 'gammatron-free-counterexample-check/v2',
      modelCalls: 0,
      costUsd: 0,
      learnedTerms: terms,
      repairBoundarySummary: {
        validCompleted: rbResults.filter(r => r.independentLabelValid && r.committed).length,
        invalidTested: rbResults.filter(r => !r.independentLabelValid).length,
        wrongWritesCommitted: rbResults.filter(r => r.wrongWrite).length,
        falsifiedSafetyOnLiteralGuard: rbResults.some(r => r.wrongWrite),
        cases: rbResults,
      },
      expertGuardSummary: {
        validCompleted: expertResults.filter(r => r.independentLabelValid && r.committed).length,
        invalidTested: expertResults.filter(r => !r.independentLabelValid).length,
        wrongWritesCommitted: expertResults.filter(r => r.wrongWrite).length,
        cases: expertResults,
      },
      scalarProjectionBlindspotWhenTrained: {
        status: textLearnOutcome.status,
        reason: textLearnOutcome.reason,
        doNotLearnRule: 'Abstain from scalar repair-boundary learning when policy clauses depend on free-text, array-valued, subset, or unprojected decimal fields.',
      },
      erpnextScalarCollapseSuite: erpSuite,
      op178MultiTargetVersionsUpgradeProof: op178Proof,
      scopedInterpretation: (
        'Counterexample hits falsify safety of `approval:/statusCode === 16` on OpenProject (3/3 wrong writes), '
        + 'prove ERPNext `projectFrappeResourceScalars` commits line-item swap wrong writes even when all 4 projected '
        + 'scalars match, and show OpenProject 17.8 multi-value `Target versions` subset policies break conjunctive '
        + 'scalar equality (`no-separating-guard` vs 100% accuracy for a 3-line subset guard) at $0.'
      ),
    };
  } finally {
    server.close();
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const report = await runFreeCounterexampleCheck();
  assert.equal(report.modelCalls, 0);
  assert.equal(report.costUsd, 0);
  assert.equal(report.repairBoundarySummary.falsifiedSafetyOnLiteralGuard, true);
  assert.equal(report.repairBoundarySummary.wrongWritesCommitted, 3);
  assert.equal(report.expertGuardSummary.wrongWritesCommitted, 0);
  assert.equal(report.erpnextScalarCollapseSuite.lineItemSwapWrongWriteByLearned, true);
  assert.equal(report.erpnextScalarCollapseSuite.lineItemSwapBlockedByExpertGuard, true);
  assert.equal(report.erpnextScalarCollapseSuite.rateOverrunLearnReason, 'no-separating-guard');
  assert.equal(report.op178MultiTargetVersionsUpgradeProof.preConversionSingleVersion.status, 'learned');
  assert.equal(report.op178MultiTargetVersionsUpgradeProof.postConversionMultiTargetVersions.reason, 'no-separating-guard');
  assert.equal(report.op178MultiTargetVersionsUpgradeProof.postConversionMultiTargetVersions.expertSubsetGuardCompletesBothValid, true);
  assert.equal(report.op178MultiTargetVersionsUpgradeProof.postConversionMultiTargetVersions.expertSubsetGuardBlocksInvalid, true);
  console.log(JSON.stringify(report, null, 2));
}
