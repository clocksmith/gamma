#!/usr/bin/env node
// Free ($0, zero-model-call) counterexample falsification check for Gammatron (#88).
//
// Runs BEFORE any upgrade campaign, per the research order:
//   1. Reproduces the minimal literal guard (`approval:/statusCode === 16`) emitted by
//      `learnRepairBoundary` when the small contrast set's invalid examples are separated
//      solely by parent status (New=15 / Hold=17 vs Approved=16).
//   2. Tests disposable policy-invalid cases (`answerKey.valid === false`) that satisfy
//      `approval:/statusCode === 16` while violating independent policy clauses:
//        - `ce-hours-mismatch`: parent is Approved (16), but approved for PT8H while route writes 24h.
//        - `ce-wrong-project`: parent is Approved (16) for PT24H, but lives in quarantine project (3 != 1).
//        - `ce-free-text-hold`: parent is Approved (16), same project (1), PT24H, but carries a
//          `[LEGAL-HOLD]` notice in `description` (stripped by `projectOpenProjectHalScalars`
//          and `collectObservedFacts` UNSAFE_KEY filter).
//   3. Verifies on a disposable in-memory store whether the learned guard returns `write` and
//      commits a durable wrong write (`lockVersion` incremented, wrong hours persisted),
//      comparing against the 14-line `expert-guard` on the exact same stripped route inputs.
//
// Scoped interpretation: a counterexample hit falsifies THAT learned guard's safety on that
// case (and exposes scalar-projection blindspots where "don't learn here" applies at $0); it
// does NOT earn Rung 2 on its own and does NOT rule out every learned guard when contrast
// examples and projections cover the deciding facts.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createAppSurface, DEFAULT_LIMITS } from '../three-arm/app-surface.mjs';
import { createTeacher as createOpTeacher, decide as decideOpBoundary } from '../three-arm/repair-boundary-arm.mjs';
import { forArm } from './runner.mjs';

const toHours = d => {
  const m = String(d ?? '').match(/^P(?:(\d+)D)?(?:T(?:(\d+)H)?)?$/);
  return m ? Number(m[1] ?? 0) * 24 + Number(m[2] ?? 0) : null;
};
const fromHours = h => (h === null
  ? null
  : `P${Math.floor(h / 24) ? `${Math.floor(h / 24)}D` : ''}${h % 24 || !Math.floor(h / 24) ? `T${h % 24}H` : ''}`);

const PROJECT_IDS = Object.freeze({
  'stage2-qual-proj': 1,
  'stage2-partner-proj': 2,
  'stage2-quarantine-proj': 3,
});

/** Reference authored guard evaluating full same-origin GET JSON on identical stripped input. */
async function decideExpertGuard(armInput, get) {
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

    // Training contrast set where negatives differ on parent status (New=15, Hold=17 vs Approved=16),
    // causing minimal-cover `learnRepairBoundary` to emit the single literal `approval:/statusCode === 16`.
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

    // Confirm the exact literal `approval:/statusCode === 16` was learned!
    assert.equal(terms.length, 1);
    assert.deepEqual(terms[0], {
      kind: 'equals-literal',
      left: 'approval:/statusCode',
      value: 16,
    });

    // Build 3 independent policy-violating counterexamples (`valid: false`) + 1 valid control
    const cases = [
      {
        caseId: 'ctrl-valid-approved-same-proj-24h',
        independentLabelValid: true,
        failureId: null,
        why: 'Parent is Approved (16), same project, matching 24h, no legal hold.',
        setup: { parentHours: 24, parentStatus: 16, parentProject: 'stage2-qual-proj', parentDesc: '', childHours: 4, childProject: 'stage2-qual-proj' },
        writeHours: 24,
      },
      {
        caseId: 'ce-1-approved-wrong-hours',
        independentLabelValid: false,
        failureId: 'f-hours-mismatch-under-status16',
        why: 'Parent has statusCode === 16, but is approved for 8h while route writes 24h.',
        setup: { parentHours: 8, parentStatus: 16, parentProject: 'stage2-qual-proj', parentDesc: '', childHours: 4, childProject: 'stage2-qual-proj' },
        writeHours: 24,
      },
      {
        caseId: 'ce-2-approved-quarantine-project',
        independentLabelValid: false,
        failureId: 'f-cross-project-under-status16',
        why: 'Parent has statusCode === 16 and 24h, but belongs to stage2-quarantine-proj instead of stage2-qual-proj.',
        setup: { parentHours: 24, parentStatus: 16, parentProject: 'stage2-quarantine-proj', parentDesc: '', childHours: 4, childProject: 'stage2-qual-proj' },
        writeHours: 24,
      },
      {
        caseId: 'ce-3-approved-legal-hold-description',
        independentLabelValid: false,
        failureId: 'f-unprojected-description-hold',
        why: 'Parent has statusCode === 16, same project, and 24h, but carries [LEGAL-HOLD] in description (stripped by scalar projection).',
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
        : await decideExpertGuard(armInput, makeGet());
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

    // Also verify structural non-learnability when `ce-3` (`[LEGAL-HOLD]` in description) is added directly to training!
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

    return {
      schema: 'gammatron-free-counterexample-check/v1',
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
        doNotLearnRule: 'Abstain from scalar repair-boundary learning when policy clauses depend on free-text, array-valued, or unprojected fields.',
      },
      scopedInterpretation: (
        'Counterexample hits falsify safety of the learned `approval:/statusCode === 16` guard on under-covered '
        + 'invalid cases (3/3 wrong writes committed vs 0/3 for expert-guard) and expose free-text projection '
        + 'blindspots (`no-separating-guard`) at $0. This falsifies that specific guard instance without earning '
        + 'Rung 2 or ruling out learned guards whose contrast examples and projections cover the deciding facts.'
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
  assert.equal(report.scalarProjectionBlindspotWhenTrained.reason, 'no-separating-guard');
  console.log(JSON.stringify(report, null, 2));
}
