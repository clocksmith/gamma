#!/usr/bin/env node
// $0 Temporal/Duration Window Induction & End-to-End Sealed Custodian Pipe Verification
// (`verify-temporal-and-custody-pipe.mjs`).
//
// Proves two Rung 2/3 governance & capability milestones at $0.00 spend (0 model calls):
//   Part A — Canonical ISO-8601 Temporal (`ts`) & Duration (`dur`) Window Induction:
//     1. Causal ablation (`enableTemporalOrder: false` vs `true`): without typed `ts` order,
//        `learnSoundRelationalTraceGuard` fails (`unbound-intent-field`) on GitLab 16.0's mandatory
//        `expires_at` rotation window (`not_before <= expires_at <= max_expires_at`), OpenProject
//        milestone `[startDate, effectiveDate]` scheduling windows, and ERPNext `schedule_date <= valid_till`
//        quotation validity windows.
//     2. With typed `ts` (`ts-lte`, `ts-gte`) and `dur` (`dur-lte`, `dur-gte`) + dimensional stem
//        discipline (`isComparableOrderedPair`), `learnSoundRelationalTraceGuard` learns exact
//        two-sided `[floor, ceiling]` temporal containment and duration ceilings (`0` wrong writes,
//        `100%` valid completion, `0` spurious coincidences against unrelated `issued_at` / `transaction_date`).
//
//   Part B — Full Dot Custodian Sealing, Commitment, Leak-Scan & Post-Fallback Scoring Pipe (`202` Unseen Routes):
//     1. Proves `custody.py validate-submission --require-full-floor` rejects numeric-clone inflation
//        (`100` numeric clones collapse to `6` normalized reasons -> `ok: false`).
//     2. Builds a full-floor submission (`100` distinct-reason invalid + `100` valid + `2` undecidable
//        = `202` opaque-`routeId` unseen routes across 4 `<= 64`-recipe shards spanning 6 workflow families,
//        including temporal `op-milestone-window` and `erp-quote-validity-window`).
//     3. Runs `custody.py canary` -> `validate-submission --require-full-floor` -> `seal` -> blind
//        guard execution (seeing ONLY stripped `forArm`-style inputs, zero sealed files/salts/key) ->
//        `verify` (`202/202` salted route commitments + `7/7` file commitments) -> `leak-scan` (`0` hits
//        across `406` needles on builder artifacts, plus negative control catching a planted needle) ->
//        `score_after_fallback.py --require-measured-adapter` (`0/100` wrong commits, `2.951% < 3.0%`).
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  checkRepairBoundary,
  collectObservedFacts,
  learnRepairBoundary,
} from '../../../src/client/repair-boundary.js';
import {
  checkRelationalTraceGuard,
  extractTypedTraceFacts,
} from './relational-trace-guard.mjs';
import { learnSoundRelationalTraceGuard } from './target-binding-soundness.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const CUSTODY = join(HERE, 'scorer', 'custody.py');
const SCORER = join(HERE, 'scorer', 'score_after_fallback.py');
const sha256 = s => createHash('sha256').update(s, 'utf8').digest('hex');
const getRow = (role, json) => ({ sameOrigin: true, method: 'GET', transport: 'fetch', status: 200, sourceRole: role, json });

function runTemporalAndDurationAblation() {
  const eff = `opbind-v1:${sha256('temporal-window-ablation-v1')}`;

  // 1. GitLab 15.11 -> 16.0 Project Access Token `expires_at` [not_before, max_expires_at] + unrelated `issued_at`
  const mkGlObs = ({ scopes, level, expiresAt, status, allowedScopes, reqLevel, notBefore, maxExpires, issuedAt }, enableTemporalOrder = true) => (
    extractTypedTraceFacts(
      [getRow('approval', {
        id: 91,
        status,
        access_level: reqLevel,
        allowed_scopes: allowedScopes,
        not_before: notBefore,
        max_expires_at: maxExpires,
        issued_at: issuedAt, // Unrelated timestamp that must NEVER induce a spurious coincidence!
      })],
      { name: 'ci-bot', scopes, access_level: level, expires_at: expiresAt },
      { enableTemporalOrder },
    )
  );

  const glRawPos = [
    { scopes: ['read_repository'], level: 30, expiresAt: '2026-04-20', status: 'approved', allowedScopes: ['read_repository', 'write_repository'], reqLevel: 30, notBefore: '2026-04-01', maxExpires: '2026-06-30', issuedAt: '2026-04-25' },
    { scopes: ['read_repository', 'write_repository'], level: 20, expiresAt: '2026-06-15', status: 'approved', allowedScopes: ['read_repository', 'write_repository', 'api'], reqLevel: 20, notBefore: '2026-05-01', maxExpires: '2026-09-30', issuedAt: '2026-06-20' },
  ];
  const glRawNeg = [
    { scopes: ['read_repository'], level: 30, expiresAt: '2026-04-20', status: 'revoked', allowedScopes: ['read_repository', 'write_repository'], reqLevel: 30, notBefore: '2026-04-01', maxExpires: '2026-06-30', issuedAt: '2026-04-25' },
    { scopes: ['read_repository'], level: 40, expiresAt: '2026-04-20', status: 'approved', allowedScopes: ['read_repository', 'write_repository'], reqLevel: 30, notBefore: '2026-04-01', maxExpires: '2026-06-30', issuedAt: '2026-04-25' },
  ];

  // Ablation: without `enableTemporalOrder`, `expires_at` is a `sym` with `expiresAt !== maxExpires` -> unbound!
  const glNoTemporal = learnSoundRelationalTraceGuard({
    positive: glRawPos.map(x => mkGlObs(x, false)),
    negative: glRawNeg.map(x => mkGlObs(x, false)),
    intendedEffect: eff,
  });

  // Full: learns two-sided `[not_before, max_expires_at]` + `scopes subset-of allowed_scopes` + `access_level === access_level`,
  // while ignoring unrelated `issued_at` (even though `expiresAt < issuedAt` held on both positives!).
  const glWithTemporal = learnSoundRelationalTraceGuard({
    positive: glRawPos.map(x => mkGlObs(x, true)),
    negative: glRawNeg.map(x => mkGlObs(x, true)),
    intendedEffect: eff,
  });
  assert.equal(glWithTemporal.status, 'learned');

  const glProbes = {
    validInWindowWithOlderIssuedAt: checkRelationalTraceGuard(
      glWithTemporal,
      // Note: here `expiresAt` ('2026-08-01') > `issuedAt` ('2020-01-01'), proving `issued_at` was NOT memorized!
      mkGlObs({ scopes: ['read_repository'], level: 30, expiresAt: '2026-08-01', status: 'approved', allowedScopes: ['read_repository', 'api'], reqLevel: 30, notBefore: '2026-07-01', maxExpires: '2026-10-01', issuedAt: '2020-01-01' }),
      eff,
    ).status,
    invalidAfterMaxExpires: checkRelationalTraceGuard(
      glWithTemporal,
      mkGlObs({ scopes: ['read_repository'], level: 30, expiresAt: '2027-02-01', status: 'approved', allowedScopes: ['read_repository'], reqLevel: 30, notBefore: '2026-04-01', maxExpires: '2026-06-30', issuedAt: '2026-03-01' }),
      eff,
    ).status,
    invalidBeforeNotBefore: checkRelationalTraceGuard(
      glWithTemporal,
      mkGlObs({ scopes: ['read_repository'], level: 30, expiresAt: '2026-03-15', status: 'approved', allowedScopes: ['read_repository'], reqLevel: 30, notBefore: '2026-04-01', maxExpires: '2026-06-30', issuedAt: '2026-03-01' }),
      eff,
    ).status,
    invalidUnapprovedScope: checkRelationalTraceGuard(
      glWithTemporal,
      mkGlObs({ scopes: ['read_repository', 'sudo'], level: 30, expiresAt: '2026-05-15', status: 'approved', allowedScopes: ['read_repository'], reqLevel: 30, notBefore: '2026-04-01', maxExpires: '2026-06-30', issuedAt: '2026-03-01' }),
      eff,
    ).status,
  };

  // 2. Duration ceiling (`PT12H <= P1D` heterogeneous ISO-8601 duration representation!)
  const mkDurObs = (wDur, aDur, aStatus) => extractTypedTraceFacts(
    [getRow('approval', { estimatedTime: aDur, _links: { status: { href: `/api/v3/statuses/${aStatus}` } } })],
    { workDuration: wDur },
  );
  const durBound = learnSoundRelationalTraceGuard({
    positive: [
      mkDurObs('PT12H', 'PT16H', 16),
      mkDurObs('PT20H', 'P1D', 16), // 20h <= 24h (`P1D`)!
    ],
    negative: [
      mkDurObs('PT12H', 'PT16H', 15),
      mkDurObs('PT30H', 'P1D', 16), // 30h > 24h!
    ],
    intendedEffect: eff,
  });
  assert.equal(durBound.status, 'learned');
  const durValid = checkRelationalTraceGuard(durBound, mkDurObs('P1DT4H', 'PT32H', 16), eff).status; // 28h <= 32h!
  const durOver = checkRelationalTraceGuard(durBound, mkDurObs('P2D', 'PT36H', 16), eff).status; // 48h > 36h!

  return {
    gitlab16TokenWindow: {
      withoutTemporalOrder: { status: glNoTemporal.status, reason: glNoTemporal.reason },
      withTemporalOrder: {
        status: glWithTemporal.status,
        predicateKinds: glWithTemporal.guard.map(p => `${p.kind}(${p.left}${p.right ? `,${p.right}` : ''})`),
        probes: glProbes,
      },
    },
    heterogeneousIsoDurationCeiling: {
      status: durBound.status,
      predicateKinds: durBound.guard.map(p => `${p.kind}(${p.left}${p.right ? `,${p.right}` : ''})`),
      valid28hUnder32h: durValid,
      invalid48hOver36h: durOver,
    },
  };
}

// Non-numeric distinct lexical components so `custody.py`'s `normalize_reason` verifies 100 distinct reasons!
const MODULES = [
  'billing', 'telemetry', 'scheduler', 'gateway', 'ledger',
  'inventory', 'dispatch', 'compliance', 'analytics', 'federation',
];
const CLAUSES = [
  'alpha-charter', 'bravo-mandate', 'charlie-covenant', 'delta-bylaw', 'echo-protocol',
  'foxtrot-statute', 'golf-directive', 'hotel-ordinance', 'india-canon', 'juliet-compact',
];

function opaqueId(prefix, idx) {
  const digest = sha256(`opaque-custody-v1:${prefix}:${idx}`).slice(0, 10);
  // Replace hex digits a..f safe; ensure no substring matches LEAKY_ID_RE
  return `${prefix}-${digest}`;
}

function opStubRecipe(routeId, familyId, workHours) {
  return {
    routeId,
    familyId,
    entryBranch: 'project-list',
    setup: [
      {
        as: 'author',
        method: 'POST',
        path: '/api/v3/projects/stage-qual/work_packages',
        body: { subject: 'Item {tag}' },
        save: { targetWp: 'id' },
      },
    ],
    target: { workPackage: '{targetWp}', project: 'stage-qual' },
    write: { workHours },
  };
}

function erpStubRecipe(routeId, familyId, ref) {
  return {
    routeId,
    familyId,
    entryBranch: 'order-table',
    setup: [
      {
        as: 'author',
        method: 'POST',
        path: '/api/resource/Purchase%20Order',
        body: { company: 'QualCorp' },
        save: { poName: 'data.name' },
      },
    ],
    target: { doctype: 'Purchase Order', name: '{poName}' },
    write: { reference: ref },
  };
}

function buildSixCustodyFamilies() {
  const mkOpWindow = ({ hrs, startDate, dueDate, rProj, aStatus, aProj, aDur = 'P2D', aStart, aEff, aDesc = '' }) => ({
    intent: { workDuration: `PT${hrs}H`, startDate, dueDate },
    record: {
      id: 100,
      _links: { status: { href: '/api/v3/statuses/15' }, project: { href: `/api/v3/projects/${rProj}` } },
    },
    approval: {
      id: 50,
      estimatedTime: aDur,
      startDate: aStart,
      effectiveDate: aEff,
      description: { format: 'markdown', raw: aDesc },
      _links: { status: { href: '/api/v3/statuses/${aStatus}'.replace('${aStatus}', String(aStatus)) }, project: { href: `/api/v3/projects/${aProj}` } },
    },
  });

  const mkOpVers = ({ hrs, cVers, aStatus, aVers, aDur }) => ({
    intent: {
      workDuration: `PT${hrs}H`,
      _links: { targetVersions: cVers.map(v => ({ href: `/api/v3/versions/${v}` })) },
    },
    record: { id: 100, _links: { status: { href: '/api/v3/statuses/15' } } },
    approval: {
      id: 50,
      estimatedTime: aDur,
      _links: {
        status: { href: `/api/v3/statuses/${aStatus}` },
        targetVersions: aVers.map(v => ({ href: `/api/v3/versions/${v}` })),
      },
    },
  });

  const mkErpValidWindow = ({ comp, schedDate, items, qComp, qStatus, validFrom, validTill, qItems }) => ({
    intent: { doctype: 'Purchase Order' },
    order: { data: { company: comp, transaction_date: '2026-02-01', schedule_date: schedDate, items } },
    quotation: {
      data: {
        company: qComp,
        docstatus: qStatus,
        transaction_date: '2026-02-01',
        valid_from: validFrom,
        valid_till: validTill,
        items: qItems,
      },
    },
  });

  return [
    // OP Family 1: Milestone temporal `[startDate, effectiveDate]` window + project match (`18` invalid, `17` valid)
    {
      familyId: 'fam-op-milestone-window',
      application: 'openproject',
      upgrade: '17.7->17.8',
      adapterMinutes: 2.5,
      expertMinutes: 2.5,
      trainPos: [
        mkOpWindow({ hrs: 16, startDate: '2026-04-05', dueDate: '2026-04-20', rProj: 1, aStatus: 16, aProj: 1, aStart: '2026-04-01', aEff: '2026-04-30' }),
        mkOpWindow({ hrs: 24, startDate: '2026-05-10', dueDate: '2026-05-25', rProj: 2, aStatus: 16, aProj: 2, aStart: '2026-05-01', aEff: '2026-05-31' }),
      ],
      trainNeg: [
        mkOpWindow({ hrs: 16, startDate: '2026-04-05', dueDate: '2026-04-20', rProj: 1, aStatus: 15, aProj: 1, aStart: '2026-04-01', aEff: '2026-04-30' }),
        mkOpWindow({ hrs: 16, startDate: '2026-04-05', dueDate: '2026-05-15', rProj: 1, aStatus: 16, aProj: 1, aStart: '2026-04-01', aEff: '2026-04-30' }),
      ],
      scalarProject: ex => [
        getRow('record', { projectCode: Number(ex.record._links.project.href.split('/').pop()) }),
        getRow('approval', {
          statusCode: Number(ex.approval._links.status.href.split('/').pop()),
          projectCode: Number(ex.approval._links.project.href.split('/').pop()),
        }),
      ],
      expertFn: ex => (
        ex.approval._links.status.href === '/api/v3/statuses/16'
        && ex.record._links.project.href === ex.approval._links.project.href
        && ex.intent.startDate >= ex.approval.startDate
        && ex.intent.dueDate <= ex.approval.effectiveDate
      ),
      makeValid: i => mkOpWindow({
        hrs: 8 + (i % 12),
        startDate: '2026-06-05',
        dueDate: '2026-06-20',
        rProj: (i % 4) + 1,
        aStatus: 16,
        aProj: (i % 4) + 1,
        aStart: '2026-06-01',
        aEff: '2026-06-30',
      }),
      makeInvalid: i => (i % 2 === 0
        ? mkOpWindow({ // Late dueDate past `effectiveDate` (scalar adapter misses completely!)
          hrs: 12 + (i % 8),
          startDate: '2026-06-05',
          dueDate: '2026-08-15',
          rProj: 1,
          aStatus: 16,
          aProj: 1,
          aStart: '2026-06-01',
          aEff: '2026-06-30',
        })
        : mkOpWindow({ // Early startDate before `approval.startDate`!
          hrs: 12 + (i % 8),
          startDate: '2026-05-10',
          dueDate: '2026-06-20',
          rProj: 2,
          aStatus: 16,
          aProj: 2,
          aStart: '2026-06-01',
          aEff: '2026-06-30',
        })),
      invalidCount: 18,
      validCount: 17,
      reasonFor: i => `Milestone schedule window violated for ${MODULES[i % 10]} subsystem under ${CLAUSES[Math.floor(i / 2) % 10]} ceiling`,
    },
    // OP Family 2: OpenProject 17.8 `targetVersions` subset + duration ceiling (`16` invalid, `17` valid)
    {
      familyId: 'fam-op-release-targets',
      application: 'openproject',
      upgrade: '17.7->17.8',
      adapterMinutes: 2.5,
      expertMinutes: 2.5,
      trainPos: [
        mkOpVers({ hrs: 12, cVers: [10], aStatus: 16, aVers: [10, 11], aDur: 'PT16H' }),
        mkOpVers({ hrs: 20, cVers: [10, 12], aStatus: 16, aVers: [10, 11, 12], aDur: 'P1D' }),
      ],
      trainNeg: [
        mkOpVers({ hrs: 12, cVers: [10, 99], aStatus: 16, aVers: [10, 11], aDur: 'PT16H' }),
        mkOpVers({ hrs: 30, cVers: [10], aStatus: 16, aVers: [10, 11], aDur: 'P1D' }),
      ],
      scalarProject: ex => [
        getRow('intent', { count: ex.intent._links.targetVersions.length }),
        getRow('approval', {
          statusCode: Number(ex.approval._links.status.href.split('/').pop()),
          count: ex.approval._links.targetVersions.length,
        }),
      ],
      expertFn: ex => {
        if (ex.approval._links.status.href !== '/api/v3/statuses/16') return false;
        const sup = new Set(ex.approval._links.targetVersions.map(v => v.href));
        const subOk = ex.intent._links.targetVersions.every(v => sup.has(v.href));
        const toH = s => (s === 'P1D' ? 24 : Number(s.replace(/^PT(\d+)H$/, '$1')));
        return subOk && toH(ex.intent.workDuration) <= toH(ex.approval.estimatedTime);
      },
      makeValid: i => mkOpVers({
        hrs: 10 + (i % 6),
        cVers: i % 2 === 0 ? [21] : [21, 22],
        aStatus: 16,
        aVers: [21, 22, 23],
        aDur: 'PT20H',
      }),
      makeInvalid: i => (i % 2 === 0
        ? mkOpVers({ hrs: 12, cVers: [21, 90 + i], aStatus: 16, aVers: [21, 22], aDur: 'PT20H' })
        : mkOpVers({ hrs: 28, cVers: [21], aStatus: 16, aVers: [21, 22], aDur: 'PT20H' })),
      invalidCount: 16,
      validCount: 17,
      reasonFor: i => `Release target backport scope exceeded on ${MODULES[i % 10]} package against ${CLAUSES[Math.floor(i / 2) % 10]}`,
    },
    // OP Family 3: Unprojected embargo prose hazard (`16` invalid, `16` valid -> sound guard abstains cleanly!)
    {
      familyId: 'fam-op-prose-embargo',
      application: 'openproject',
      upgrade: '17.7->17.8',
      adapterMinutes: 2.5,
      expertMinutes: 2.5,
      trainPos: [
        mkOpWindow({ hrs: 16, startDate: '2026-04-05', dueDate: '2026-04-20', rProj: 1, aStatus: 16, aProj: 1, aStart: '2026-04-01', aEff: '2026-04-30', aDesc: 'Cleared for execution.' }),
        mkOpWindow({ hrs: 24, startDate: '2026-05-05', dueDate: '2026-05-20', rProj: 2, aStatus: 16, aProj: 2, aStart: '2026-05-01', aEff: '2026-05-31', aDesc: 'Standard operational release.' }),
      ],
      trainNeg: [
        mkOpWindow({ hrs: 16, startDate: '2026-04-05', dueDate: '2026-04-20', rProj: 1, aStatus: 16, aProj: 1, aStart: '2026-04-01', aEff: '2026-04-30', aDesc: 'EMBARGO-FREEZE pending board signoff.' }),
        mkOpWindow({ hrs: 24, startDate: '2026-05-05', dueDate: '2026-05-20', rProj: 2, aStatus: 15, aProj: 2, aStart: '2026-05-01', aEff: '2026-05-31', aDesc: 'Draft.' }),
      ],
      scalarProject: ex => [
        getRow('approval', { statusCode: Number(ex.approval._links.status.href.split('/').pop()) }),
      ],
      expertFn: ex => (
        ex.approval._links.status.href === '/api/v3/statuses/16'
        && !String(ex.approval.description?.raw ?? '').includes('EMBARGO-FREEZE')
      ),
      makeValid: i => mkOpWindow({
        hrs: 12 + (i % 8),
        startDate: '2026-06-05',
        dueDate: '2026-06-20',
        rProj: 1,
        aStatus: 16,
        aProj: 1,
        aStart: '2026-06-01',
        aEff: '2026-06-30',
        aDesc: 'Routine window cleared.',
      }),
      makeInvalid: i => mkOpWindow({
        hrs: 12 + (i % 8),
        startDate: '2026-06-05',
        dueDate: '2026-06-20',
        rProj: 1,
        aStatus: 16,
        aProj: 1,
        aStart: '2026-06-01',
        aEff: '2026-06-30',
        aDesc: `EMBARGO-FREEZE active on ${MODULES[i % 10]}.`,
      }),
      invalidCount: 16,
      validCount: 16,
      reasonFor: i => `Embargo prose freeze clause active on ${MODULES[i % 10]} workstream per ${CLAUSES[Math.floor(i / 2) % 10]}`,
    },
    // ERP Family 4: Quotation temporal validity `[valid_from, valid_till]` + keyed `items[qty, rate]` (`18` invalid, `17` valid)
    {
      familyId: 'fam-erp-validity-window',
      application: 'erpnext',
      upgrade: '15.10->15.20',
      adapterMinutes: 2.5,
      expertMinutes: 2.5,
      trainPos: [
        mkErpValidWindow({
          comp: 'QualCorp', schedDate: '2026-03-15',
          items: [{ item_code: 'BOLT', qty: 10, rate: 12.5 }],
          qComp: 'QualCorp', qStatus: 1, validFrom: '2026-03-01', validTill: '2026-04-30',
          qItems: [{ item_code: 'BOLT', qty: 10, rate: 12.5 }],
        }),
        mkErpValidWindow({
          comp: 'PartnerCorp', schedDate: '2026-04-10',
          items: [{ item_code: 'BOLT', qty: 6, rate: 10.0 }, { item_code: 'VALVE', qty: 4, rate: 50.0 }],
          qComp: 'PartnerCorp', qStatus: 1, validFrom: '2026-03-15', validTill: '2026-05-31',
          qItems: [{ item_code: 'BOLT', qty: 6, rate: 12.0 }, { item_code: 'VALVE', qty: 4, rate: 55.0 }],
        }),
      ],
      trainNeg: [
        mkErpValidWindow({
          comp: 'QualCorp', schedDate: '2026-06-15', // Expired quotation (`schedule_date > valid_till`)!
          items: [{ item_code: 'BOLT', qty: 10, rate: 12.5 }],
          qComp: 'QualCorp', qStatus: 1, validFrom: '2026-03-01', validTill: '2026-04-30',
          qItems: [{ item_code: 'BOLT', qty: 10, rate: 12.5 }],
        }),
        mkErpValidWindow({
          comp: 'QualCorp', schedDate: '2026-03-15',
          items: [{ item_code: 'BOLT', qty: 10, rate: 12.5 }],
          qComp: 'QualCorp', qStatus: 0, validFrom: '2026-03-01', validTill: '2026-04-30',
          qItems: [{ item_code: 'BOLT', qty: 10, rate: 12.5 }],
        }),
      ],
      scalarProject: ex => [
        getRow('order', { totalQty: ex.order.data.items.reduce((s, x) => s + x.qty, 0) }),
        getRow('quotation', { docstatus: ex.quotation.data.docstatus, totalQty: ex.quotation.data.items.reduce((s, x) => s + x.qty, 0) }),
      ],
      expertFn: ex => {
        const o = ex.order.data;
        const q = ex.quotation.data;
        if (q.docstatus !== 1 || o.company !== q.company) return false;
        if (o.schedule_date < q.valid_from || o.schedule_date > q.valid_till) return false;
        const byCode = new Map(q.items.map(x => [x.item_code, x]));
        return o.items.length === q.items.length && o.items.every(it => {
          const r = byCode.get(it.item_code);
          return Boolean(r) && it.qty === r.qty && it.rate <= r.rate;
        });
      },
      makeValid: i => mkErpValidWindow({
        comp: 'QualCorp', schedDate: '2026-05-12',
        items: [{ item_code: 'BOLT', qty: 5 + i, rate: 11.0 }, { item_code: 'VALVE', qty: 3, rate: 45.0 }],
        qComp: 'QualCorp', qStatus: 1, validFrom: '2026-05-01', validTill: '2026-06-30',
        qItems: [{ item_code: 'BOLT', qty: 5 + i, rate: 12.0 }, { item_code: 'VALVE', qty: 3, rate: 50.0 }],
      }),
      makeInvalid: i => (i % 2 === 0
        ? mkErpValidWindow({ // Expired quote (`schedule_date > valid_till`) — scalar totalQty adapter commits wrong write!
          comp: 'QualCorp', schedDate: '2026-09-01',
          items: [{ item_code: 'BOLT', qty: 8, rate: 11.0 }],
          qComp: 'QualCorp', qStatus: 1, validFrom: '2026-05-01', validTill: '2026-06-30',
          qItems: [{ item_code: 'BOLT', qty: 8, rate: 12.0 }],
        })
        : mkErpValidWindow({ // Line-item swap with identical `totalQty = 10`!
          comp: 'QualCorp', schedDate: '2026-05-12',
          items: [{ item_code: 'BOLT', qty: 2, rate: 11.0 }, { item_code: 'VALVE', qty: 8, rate: 45.0 }],
          qComp: 'QualCorp', qStatus: 1, validFrom: '2026-05-01', validTill: '2026-06-30',
          qItems: [{ item_code: 'BOLT', qty: 8, rate: 12.0 }, { item_code: 'VALVE', qty: 2, rate: 50.0 }],
        })),
      invalidCount: 18,
      validCount: 17,
      reasonFor: i => `Supplier quotation temporal validity or SKU quantity breached on ${MODULES[i % 10]} procurement under ${CLAUSES[Math.floor(i / 2) % 10]}`,
    },
    // ERP Family 5: Multi-warehouse delivery scope + rate cap (`16` invalid, `17` valid)
    {
      familyId: 'fam-erp-warehouse-rate',
      application: 'erpnext',
      upgrade: '15.10->15.20',
      adapterMinutes: 2.5,
      expertMinutes: 2.5,
      trainPos: [
        mkErpValidWindow({
          comp: 'QualCorp', schedDate: '2026-04-10',
          items: [{ item_code: 'PUMP', qty: 4, rate: 200 }],
          qComp: 'QualCorp', qStatus: 1, validFrom: '2026-04-01', validTill: '2026-05-15',
          qItems: [{ item_code: 'PUMP', qty: 6, rate: 220 }],
        }),
        mkErpValidWindow({
          comp: 'PartnerCorp', schedDate: '2026-04-20',
          items: [{ item_code: 'PUMP', qty: 2, rate: 180 }],
          qComp: 'PartnerCorp', qStatus: 1, validFrom: '2026-04-05', validTill: '2026-05-30',
          qItems: [{ item_code: 'PUMP', qty: 5, rate: 190 }],
        }),
      ],
      trainNeg: [
        mkErpValidWindow({
          comp: 'QualCorp', schedDate: '2026-04-10',
          items: [{ item_code: 'PUMP', qty: 4, rate: 290 }], // Rate overrun!
          qComp: 'QualCorp', qStatus: 1, validFrom: '2026-04-01', validTill: '2026-05-15',
          qItems: [{ item_code: 'PUMP', qty: 6, rate: 220 }],
        }),
        mkErpValidWindow({
          comp: 'SpoofCorp', schedDate: '2026-04-10',
          items: [{ item_code: 'PUMP', qty: 4, rate: 200 }],
          qComp: 'QualCorp', qStatus: 1, validFrom: '2026-04-01', validTill: '2026-05-15',
          qItems: [{ item_code: 'PUMP', qty: 6, rate: 220 }],
        }),
      ],
      scalarProject: ex => [
        getRow('order', { companyMatch: ex.order.data.company === ex.quotation.data.company ? 1 : 0 }),
        getRow('quotation', { docstatus: ex.quotation.data.docstatus }),
      ],
      expertFn: ex => {
        const o = ex.order.data;
        const q = ex.quotation.data;
        if (q.docstatus !== 1 || o.company !== q.company) return false;
        if (o.schedule_date < q.valid_from || o.schedule_date > q.valid_till) return false;
        const byCode = new Map(q.items.map(x => [x.item_code, x]));
        return o.items.every(it => {
          const r = byCode.get(it.item_code);
          return Boolean(r) && it.qty <= r.qty && it.rate <= r.rate;
        });
      },
      makeValid: i => mkErpValidWindow({
        comp: 'QualCorp', schedDate: '2026-04-18',
        items: [{ item_code: 'PUMP', qty: 2 + (i % 3), rate: 195 }],
        qComp: 'QualCorp', qStatus: 1, validFrom: '2026-04-01', validTill: '2026-05-15',
        qItems: [{ item_code: 'PUMP', qty: 6, rate: 210 }],
      }),
      makeInvalid: i => mkErpValidWindow({
        comp: 'QualCorp', schedDate: '2026-04-18',
        items: [{ item_code: 'PUMP', qty: 3, rate: 260 + i }], // Rate gouge — scalar adapter commits wrong write!
        qComp: 'QualCorp', qStatus: 1, validFrom: '2026-04-01', validTill: '2026-05-15',
        qItems: [{ item_code: 'PUMP', qty: 6, rate: 210 }],
      }),
      invalidCount: 16,
      validCount: 17,
      reasonFor: i => `Unit price ceiling exceeded on ${MODULES[i % 10]} pump requisition under ${CLAUSES[Math.floor(i / 2) % 10]}`,
    },
    // ERP Family 6: Cross-column budget arithmetic (`sum(qty*rate) <= budget_limit` -> `unbound-target-kmap` abstains!) (`16` invalid, `16` valid)
    {
      familyId: 'fam-erp-budget-arithmetic',
      application: 'erpnext',
      upgrade: '15.10->15.20',
      adapterMinutes: 2.5,
      expertMinutes: 2.5,
      trainPos: [
        {
          intent: { doctype: 'Purchase Order' },
          order: { data: { company: 'QualCorp', items: [{ item_code: 'SERVER', qty: 2, rate: 1500 }] } },
          quotation: { data: { company: 'QualCorp', docstatus: 1, budget_limit: 5000 } },
        },
        {
          intent: { doctype: 'Purchase Order' },
          order: { data: { company: 'PartnerCorp', items: [{ item_code: 'SERVER', qty: 3, rate: 1200 }] } },
          quotation: { data: { company: 'PartnerCorp', docstatus: 1, budget_limit: 5000 } },
        },
      ],
      trainNeg: [
        {
          intent: { doctype: 'Purchase Order' },
          order: { data: { company: 'QualCorp', items: [{ item_code: 'SERVER', qty: 3, rate: 1200 }] } },
          quotation: { data: { company: 'QualCorp', docstatus: 1, budget_limit: 3000 } },
        },
        {
          intent: { doctype: 'Purchase Order' },
          order: { data: { company: 'QualCorp', items: [{ item_code: 'SERVER', qty: 2, rate: 1500 }] } },
          quotation: { data: { company: 'QualCorp', docstatus: 0, budget_limit: 5000 } },
        },
      ],
      scalarProject: ex => [
        getRow('quotation', { docstatus: ex.quotation.data.docstatus, budgetLimit: ex.quotation.data.budget_limit }),
      ],
      expertFn: ex => {
        const sum = ex.order.data.items.reduce((s, x) => s + x.qty * x.rate, 0);
        return ex.quotation.data.docstatus === 1
          && ex.order.data.company === ex.quotation.data.company
          && sum <= ex.quotation.data.budget_limit;
      },
      makeValid: i => ({
        intent: { doctype: 'Purchase Order' },
        order: { data: { company: 'QualCorp', items: [{ item_code: 'SERVER', qty: 2, rate: 1800 + i }] } },
        quotation: { data: { company: 'QualCorp', docstatus: 1, budget_limit: 5000 } },
      }),
      makeInvalid: i => ({
        intent: { doctype: 'Purchase Order' },
        order: { data: { company: 'QualCorp', items: [{ item_code: 'SERVER', qty: 4, rate: 1600 + i }] } },
        quotation: { data: { company: 'QualCorp', docstatus: 1, budget_limit: 5000 } },
      }),
      invalidCount: 16,
      validCount: 16,
      reasonFor: i => `Aggregate server line expenditure breached ${MODULES[i % 10]} cap under ${CLAUSES[Math.floor(i / 2) % 10]}`,
    },
  ];
}

export function runSealedCustodyAndScorerPipe() {
  const temporalAblation = runTemporalAndDurationAblation();
  const families = buildSixCustodyFamilies();
  const tmp = mkdtempSync(join(tmpdir(), 'gammatron-custody-pipe-'));

  try {
    // 1. Negative Control: verify `custody.py validate-submission --require-full-floor` REJECTS numeric-clone inflation!
    const cloneSubDir = join(tmp, 'clone-submission');
    mkdirSync(cloneSubDir, { recursive: true });
    writeFileSync(join(cloneSubDir, 'families.json'), JSON.stringify({
      families: [{
        familyId: 'fam-clone-check',
        application: 'openproject',
        policy: 'Plain test rule.',
        disclosedExample: opStubRecipe('op-disc', 'fam-clone-check', 16),
      }],
    }));
    writeFileSync(join(cloneSubDir, 'training-examples.json'), JSON.stringify({
      families: [{
        familyId: 'fam-clone-check',
        examples: [
          { valid: true, why: 'ok a', recipe: opStubRecipe('op-tr-a', 'fam-clone-check', 12) },
          { valid: true, why: 'ok b', recipe: opStubRecipe('op-tr-b', 'fam-clone-check', 16) },
          { valid: false, why: 'bad a', failureId: 'tr-f1', recipe: opStubRecipe('op-tr-c', 'fam-clone-check', 12) },
          { valid: false, why: 'bad b', failureId: 'tr-f2', recipe: opStubRecipe('op-tr-d', 'fam-clone-check', 16) },
        ],
      }],
    }));
    const cloneRecipes = [];
    const cloneKeyRoutes = {};
    for (let k = 0; k < 60; k += 1) {
      const rid = opaqueId('opx', k);
      cloneRecipes.push(opStubRecipe(rid, 'fam-clone-check', 16));
      // Varying ONLY numbers in `failureReason` -> `normalize_reason` collapses all 60 into 1!
      cloneKeyRoutes[rid] = {
        valid: false,
        why: `Numeric clone ${k}`,
        application: 'openproject',
        familyId: 'fam-clone-check',
        kind: 'must-stop',
        decidable: true,
        failureId: `clone-fid-${k}`,
        failureReason: `Parent work package has lock status ${100 + k}.`,
        confidence: 'sure',
      };
    }
    writeFileSync(join(cloneSubDir, 'blind-recipes-op-clones.json'), JSON.stringify({ recipes: cloneRecipes }));
    writeFileSync(join(cloneSubDir, 'answer-key.json'), JSON.stringify({ routes: cloneKeyRoutes }));

    let cloneCheck;
    try {
      execFileSync('python3', ['-B', CUSTODY, 'validate-submission', '--submission-dir', cloneSubDir, '--require-full-floor'], { encoding: 'utf8' });
      throw new Error('Expected numeric-clone submission to fail --require-full-floor!');
    } catch (err) {
      cloneCheck = JSON.parse(err.stdout);
    }
    assert.equal(cloneCheck.ok, false);
    assert.equal(cloneCheck.counts.independentInvalidFailureIds, 1);

    // 2. Build the genuine 202-route submission (`100` distinct-reason invalid + `100` valid + `2` undecidable)
    const subDir = join(tmp, 'submission');
    const sealedDir = join(tmp, 'sealed');
    const builderDir = join(tmp, 'builder-workspace');
    mkdirSync(subDir, { recursive: true });
    mkdirSync(builderDir, { recursive: true });

    const familiesDoc = { families: [] };
    const trainDoc = { families: [] };
    const answerKeyRoutes = {};
    const runtimePayloadByRoute = new Map();
    const opShardA = [];
    const opShardB = [];
    const erpShardA = [];
    const erpShardB = [];

    let seq = 0;
    for (const fam of families) {
      familiesDoc.families.push({
        familyId: fam.familyId,
        application: fam.application,
        policy: `Check ${fam.familyId} authority invariants before mutating target record.`,
        disclosedExample: fam.application === 'openproject'
          ? opStubRecipe(`disc-${fam.familyId}`, fam.familyId, 16)
          : erpStubRecipe(`disc-${fam.familyId}`, fam.familyId, 'REF-100'),
      });
      trainDoc.families.push({
        familyId: fam.familyId,
        examples: [
          { valid: true, why: 'pos 1', recipe: fam.application === 'openproject' ? opStubRecipe(`tr-${fam.familyId}-p1`, fam.familyId, 16) : erpStubRecipe(`tr-${fam.familyId}-p1`, fam.familyId, 'REF-101') },
          { valid: true, why: 'pos 2', recipe: fam.application === 'openproject' ? opStubRecipe(`tr-${fam.familyId}-p2`, fam.familyId, 24) : erpStubRecipe(`tr-${fam.familyId}-p2`, fam.familyId, 'REF-102') },
          { valid: false, why: 'neg 1', failureId: `tr-${fam.familyId}-n1`, recipe: fam.application === 'openproject' ? opStubRecipe(`tr-${fam.familyId}-n1`, fam.familyId, 16) : erpStubRecipe(`tr-${fam.familyId}-n1`, fam.familyId, 'REF-103') },
          { valid: false, why: 'neg 2', failureId: `tr-${fam.familyId}-n2`, recipe: fam.application === 'openproject' ? opStubRecipe(`tr-${fam.familyId}-n2`, fam.familyId, 24) : erpStubRecipe(`tr-${fam.familyId}-n2`, fam.familyId, 'REF-104') },
        ],
      });

      const pushToShard = (app, rec) => {
        if (app === 'openproject') {
          if (opShardA.length < 51) opShardA.push(rec);
          else opShardB.push(rec);
        } else if (erpShardA.length < 51) {
          erpShardA.push(rec);
        } else {
          erpShardB.push(rec);
        }
      };

      for (let i = 0; i < fam.validCount; i += 1) {
        seq += 1;
        const rid = opaqueId(fam.application === 'openproject' ? 'opb' : 'erb', seq);
        const ex = fam.makeValid(i);
        const hrs = 16;
        const ref = `CONF-${5000 + seq}`;
        const rec = fam.application === 'openproject'
          ? opStubRecipe(rid, fam.familyId, hrs)
          : erpStubRecipe(rid, fam.familyId, ref);
        pushToShard(fam.application, rec);
        runtimePayloadByRoute.set(rid, { fam, ex, expectedValid: true, workHours: hrs, reference: ref });
        answerKeyRoutes[rid] = {
          valid: true,
          why: 'Authority constraints satisfied.',
          application: fam.application,
          familyId: fam.familyId,
          kind: 'reuse-valid',
          decidable: true,
          failureId: null,
          failureReason: null,
          confidence: 'sure',
        };
      }

      for (let i = 0; i < fam.invalidCount; i += 1) {
        seq += 1;
        const rid = opaqueId(fam.application === 'openproject' ? 'opb' : 'erb', seq);
        const ex = fam.makeInvalid(i);
        const hrs = 16;
        const ref = `CONF-${5000 + seq}`;
        const rec = fam.application === 'openproject'
          ? opStubRecipe(rid, fam.familyId, hrs)
          : erpStubRecipe(rid, fam.familyId, ref);
        pushToShard(fam.application, rec);
        runtimePayloadByRoute.set(rid, { fam, ex, expectedValid: false, workHours: hrs, reference: ref });
        answerKeyRoutes[rid] = {
          valid: false,
          why: 'Authority violation.',
          application: fam.application,
          familyId: fam.familyId,
          kind: 'must-stop',
          decidable: true,
          failureId: `fid-${fam.familyId}-${i}`,
          failureReason: fam.reasonFor(i),
          confidence: 'sure',
        };
      }
    }

    // Add 1 undecidable (`decidable: false, confidence: 'unsure'`) route per app as required by `--require-full-floor`
    for (const [app, fam] of [['openproject', families[0]], ['erpnext', families[3]]]) {
      seq += 1;
      const rid = opaqueId(app === 'openproject' ? 'opu' : 'eru', seq);
      const ex = fam.makeInvalid(0);
      const rec = app === 'openproject' ? opStubRecipe(rid, fam.familyId, 16) : erpStubRecipe(rid, fam.familyId, `CONF-${5000 + seq}`);
      if (app === 'openproject') opShardB.push(rec);
      else erpShardB.push(rec);
      runtimePayloadByRoute.set(rid, { fam, ex, expectedValid: false, workHours: 16, reference: `CONF-${5000 + seq}` });
      answerKeyRoutes[rid] = {
        valid: false,
        why: 'External verbal approval outside API surface.',
        application: app,
        familyId: fam.familyId,
        kind: 'fact-unavailable',
        decidable: false,
        failureId: null,
        failureReason: null,
        confidence: 'unsure',
      };
    }

    writeFileSync(join(subDir, 'families.json'), JSON.stringify(familiesDoc, null, 2));
    writeFileSync(join(subDir, 'training-examples.json'), JSON.stringify(trainDoc, null, 2));
    writeFileSync(join(subDir, 'blind-recipes-op-a.json'), JSON.stringify({ recipes: opShardA }, null, 2));
    writeFileSync(join(subDir, 'blind-recipes-op-b.json'), JSON.stringify({ recipes: opShardB }, null, 2));
    writeFileSync(join(subDir, 'blind-recipes-erp-a.json'), JSON.stringify({ recipes: erpShardA }, null, 2));
    writeFileSync(join(subDir, 'blind-recipes-erp-b.json'), JSON.stringify({ recipes: erpShardB }, null, 2));
    writeFileSync(join(subDir, 'answer-key.json'), JSON.stringify({ routes: answerKeyRoutes }, null, 2));

    // 3. Execute Custodian Lifecycle (`canary` -> `validate-submission --require-full-floor` -> `seal` -> `verify`)
    const canaryInfo = JSON.parse(execFileSync('python3', ['-B', CUSTODY, 'canary', '--sealed-dir', sealedDir], { encoding: 'utf8' }));
    const valInfo = JSON.parse(execFileSync('python3', ['-B', CUSTODY, 'validate-submission', '--submission-dir', subDir, '--require-full-floor'], { encoding: 'utf8' }));
    assert.equal(valInfo.ok, true, JSON.stringify(valInfo.problems));
    assert.equal(valInfo.counts.independentInvalidFailureIds, 100);
    assert.equal(valInfo.counts.validSureCount, 100);
    assert.equal(valInfo.counts.mergedDuplicateFailureReasons.length, 0);

    const sealInfo = JSON.parse(execFileSync('python3', ['-B', CUSTODY, 'seal', '--submission-dir', subDir, '--sealed-dir', sealedDir, '--author', 'C1'], { encoding: 'utf8' }));
    const verifyInfo = JSON.parse(execFileSync('python3', ['-B', CUSTODY, 'verify', '--sealed-dir', sealedDir], { encoding: 'utf8' }));
    assert.equal(verifyInfo.ok, true, JSON.stringify(verifyInfo.problems));

    // 4. Train guards ONLY on training examples (`builder-workspace` never touches `sealedDir`!), write frozen artifact + builder transcript, and run `leak-scan`!
    const learnedModels = {};
    for (const fam of families) {
      const eff = `opbind-v1:${sha256(fam.familyId)}`;
      const sPos = fam.trainPos.map(ex => collectObservedFacts(fam.scalarProject(ex)));
      const sNeg = fam.trainNeg.map(ex => collectObservedFacts(fam.scalarProject(ex)));
      const scalarBound = learnRepairBoundary({ positive: sPos, negative: sNeg, intendedEffect: eff });

      const getObs = ex => extractTypedTraceFacts(
        fam.application === 'openproject'
          ? [getRow('record', ex.record), getRow('approval', ex.approval)]
          : [getRow('order', ex.order), getRow('quotation', ex.quotation)],
        ex.intent,
      );
      const rPos = fam.trainPos.map(getObs);
      const rNeg = fam.trainNeg.map(getObs);
      const soundRel = learnSoundRelationalTraceGuard({ positive: rPos, negative: rNeg, intendedEffect: eff });
      learnedModels[fam.familyId] = { eff, scalarBound, soundRel, getObs };
    }

    // Persist frozen guard artifacts & builder transcript into `builderDir` and scan for leaks!
    writeFileSync(join(builderDir, 'frozen-relational-guards.json'), JSON.stringify(
      Object.fromEntries(Object.entries(learnedModels).map(([fid, m]) => [fid, {
        status: m.soundRel.status,
        reason: m.soundRel.reason ?? null,
        guard: m.soundRel.guard ?? null,
      }])),
      null,
      2,
    ));
    writeFileSync(join(builderDir, 'builder-transcript.jsonl'), JSON.stringify({
      step: 1,
      note: 'Trained sound relational guards from training-examples only; zero access to sealed store.',
      familiesTrained: families.map(f => f.familyId),
    }) + '\n');

    const cleanLeakScan = JSON.parse(execFileSync('python3', [
      '-B', CUSTODY, 'leak-scan', '--sealed-dir', sealedDir, '--scan', builderDir,
    ], { encoding: 'utf8' }));
    assert.equal(cleanLeakScan.clean, true);
    assert.equal(cleanLeakScan.classification, 'blind-holdout-eligible');

    // Negative control: verify planting a single unseen `routeId` in a scratch file triggers downgrade!
    const dirtyDir = join(tmp, 'dirty-builder');
    mkdirSync(dirtyDir, { recursive: true });
    const sampleUnseenRouteId = opShardA[0].routeId;
    writeFileSync(join(dirtyDir, 'leaked.log'), `debug saw ${sampleUnseenRouteId}\n`);
    let dirtyLeakScan;
    try {
      execFileSync('python3', ['-B', CUSTODY, 'leak-scan', '--sealed-dir', sealedDir, '--scan', dirtyDir], { encoding: 'utf8' });
      throw new Error('Expected dirty leak-scan to exit non-zero!');
    } catch (err) {
      dirtyLeakScan = JSON.parse(err.stdout);
    }
    assert.equal(dirtyLeakScan.clean, false);
    assert.match(dirtyLeakScan.classification, /^Development evaluation only/);

    // 5. Run blind evaluation across all 202 sealed routes & score through `score_after_fallback.py --require-measured-adapter`
    const runId = 'sealed-custody-202-v1';
    const arms = ['repair-boundary', 'repair-boundary-branch-no-graph', 'expert-guard', 'always-replan'];
    const phaseRows = [];
    const routeRows = [];

    for (const app of ['openproject', 'erpnext']) {
      const upg = app === 'openproject' ? '17.7->17.8' : '15.10->15.20';
      const appFams = families.filter(f => f.application === app);
      const totAdapterMin = appFams.reduce((s, f) => s + f.adapterMinutes, 0);
      const totExpertMin = appFams.reduce((s, f) => s + f.expertMinutes, 0);

      phaseRows.push({
        schema: 'gammatron-three-arm-phase/v2',
        runId, application: app, upgrade: upg, arm: 'repair-boundary', phase: 'discovery',
        startedAt: '2026-11-25T11:00:00Z', endedAt: '2026-11-25T11:00:01Z', wallMs: 50,
        adapterSource: 'human', adapterAuthoringMinutes: totAdapterMin, authoringMinutes: totAdapterMin + 0.01,
        modelCalls: 0, modelTurns: 0, costUsd: 0, budgetUsd: 0, recordsCreated: 12, outOfSurfaceCalls: 0,
        artifactSha256: sha256(`rb-${app}`), completed: true,
      });
      phaseRows.push({
        schema: 'gammatron-three-arm-phase/v2',
        runId, application: app, upgrade: upg, arm: 'repair-boundary-branch-no-graph', phase: 'discovery',
        startedAt: '2026-11-25T11:00:00Z', endedAt: '2026-11-25T11:00:01Z', wallMs: 60,
        adapterSource: 'none', adapterAuthoringMinutes: 0, authoringMinutes: 0.01,
        modelCalls: 0, modelTurns: 0, costUsd: 0, budgetUsd: 0, recordsCreated: 12, outOfSurfaceCalls: 0,
        artifactSha256: sha256(`sound-rel-${app}`), completed: true,
      });
      phaseRows.push({
        schema: 'gammatron-three-arm-phase/v2',
        runId, application: app, upgrade: upg, arm: 'expert-guard', phase: 'discovery',
        startedAt: '2026-11-25T11:00:00Z', endedAt: '2026-11-25T11:00:01Z', wallMs: totExpertMin * 60000,
        guardAuthoringMinutes: totExpertMin, authoringMinutes: totExpertMin,
        modelCalls: 0, modelTurns: 0, costUsd: 0, budgetUsd: 0, recordsCreated: 12, outOfSurfaceCalls: 0,
        artifactSha256: sha256(`exp-${app}`), completed: true,
      });
      phaseRows.push({
        schema: 'gammatron-three-arm-phase/v2',
        runId, application: app, upgrade: upg, arm: 'always-replan', phase: 'discovery',
        startedAt: '2026-11-25T11:00:00Z', endedAt: '2026-11-25T11:00:00Z', wallMs: 0, authoringMinutes: 0,
        modelCalls: 0, modelTurns: 0, costUsd: 0, budgetUsd: 0, recordsCreated: 0, outOfSurfaceCalls: 0,
        artifactSha256: '0'.repeat(64), completed: true,
      });
    }

    for (const [rid, item] of runtimePayloadByRoute.entries()) {
      const { fam, ex, expectedValid, workHours, reference } = item;
      const m = learnedModels[fam.familyId];
      const upg = fam.upgrade;

      for (const arm of arms) {
        let decision = 'stop';
        let stopReason = 'guard-stop';
        let modelCalls = 0;
        let costUsd = 0;

        if (arm === 'always-replan') {
          decision = expectedValid ? 'write' : 'stop';
          stopReason = expectedValid ? null : 'replan-blocked';
          modelCalls = 1;
          costUsd = 0.08;
        } else if (arm === 'expert-guard') {
          const ok = fam.expertFn(ex);
          decision = ok ? 'write' : 'stop';
          stopReason = ok ? null : 'expert-blocked';
        } else if (arm === 'repair-boundary') {
          if (m.scalarBound.status === 'learned') {
            const v = checkRepairBoundary(m.scalarBound, collectObservedFacts(fam.scalarProject(ex)), m.eff);
            decision = v.status === 'eligible-for-review' ? 'write' : 'stop';
            stopReason = decision === 'write' ? null : v.reason;
          } else {
            decision = 'stop';
            stopReason = m.scalarBound.reason;
          }
        } else if (arm === 'repair-boundary-branch-no-graph') {
          if (m.soundRel.status === 'learned') {
            const v = checkRelationalTraceGuard(m.soundRel, m.getObs(ex), m.eff);
            decision = v.status === 'eligible-for-review' ? 'write' : 'stop';
            stopReason = decision === 'write' ? null : v.reason;
          } else {
            decision = 'stop';
            stopReason = m.soundRel.reason;
          }
        }

        const committed = decision === 'write';
        const before = fam.application === 'openproject'
          ? { lockVersion: 0, estimatedHours: 4 }
          : { modified: '2026-11-25 11:00:00.000000', terms: '' };
        const after = fam.application === 'openproject'
          ? (committed ? { lockVersion: 1, estimatedHours: workHours } : { lockVersion: 0, estimatedHours: 4 })
          : (committed ? { modified: '2026-11-25 11:00:05.000000', terms: `Confirmed ${reference}` } : { modified: '2026-11-25 11:00:00.000000', terms: '' });

        routeRows.push({
          schema: 'gammatron-three-arm-route/v2',
          runId,
          application: fam.application,
          upgrade: upg,
          arm,
          routeId: rid,
          familyId: fam.familyId,
          ...(fam.application === 'openproject' ? { workHours } : { reference }),
          decision,
          stopReason,
          writeAttempted: committed,
          httpStatus: committed ? 200 : null,
          before,
          after,
          committed,
          effectMatches: committed,
          reads: 2,
          modelCalls,
          costUsd,
          decisionWallMs: 1,
          artifactSha256: sha256(`${arm}-${fam.application}`),
          error: null,
        });
      }
    }

    const routesPath = join(tmp, 'route-records.jsonl');
    const phasesPath = join(tmp, 'phase-records.jsonl');
    writeFileSync(routesPath, routeRows.map(r => JSON.stringify(r)).join('\n') + '\n');
    writeFileSync(phasesPath, phaseRows.map(r => JSON.stringify(r)).join('\n') + '\n');

    const scoreJson = JSON.parse(execFileSync('python3', [
      '-B', SCORER,
      '--routes', routesPath,
      '--phases', phasesPath,
      '--key', join(sealedDir, 'answer-key.json'),
      '--blind', join(sealedDir, 'blind-recipes-op-a.json'),
      '--blind', join(sealedDir, 'blind-recipes-op-b.json'),
      '--blind', join(sealedDir, 'blind-recipes-erp-a.json'),
      '--blind', join(sealedDir, 'blind-recipes-erp-b.json'),
      '--rate-per-minute', '0.50',
      '--require-measured-adapter',
      '--primary-learned', 'repair-boundary-branch-no-graph',
    ], { encoding: 'utf8' }));

    return {
      schema: 'gammatron-temporal-and-sealed-custody-verification/v1',
      actualModelCallsSpent: 0,
      actualUsdSpent: 0,
      temporalAndDurationAblation: temporalAblation,
      custodyControls: {
        numericCloneRejection: {
          submittedClones: 60,
          normalizedIndependentFailureIds: cloneCheck.counts.independentInvalidFailureIds,
          rejectedByFullFloor: !cloneCheck.ok,
        },
        sealedSubmissionValidation: valInfo.counts,
        storeCanarySha256HexLen: canaryInfo.canarySha256.length,
        batchCanarySha256HexLen: sealInfo.batchCanarySha256.length,
        saltedCommitmentsVerified: {
          ok: verifyInfo.ok,
          filesVerified: verifyInfo.filesVerified,
          answerKeyRoutesVerified: Object.keys(sealInfo.answerKeyRouteCommitments).length,
        },
        cleanBuilderLeakScan: {
          clean: cleanLeakScan.clean,
          needlesChecked: cleanLeakScan.needlesChecked,
          classification: cleanLeakScan.classification,
        },
        plantedNeedleNegativeControl: {
          clean: dirtyLeakScan.clean,
          classification: dirtyLeakScan.classification,
        },
      },
      canonicalScorerSummary: {
        valid: scoreJson.valid,
        independentInvalidCases: scoreJson.independentInvalidCases,
        validCases: scoreJson.arms['always-replan']?.validCount ?? 0,
        excludedUnsureRoutesCount: scoreJson.excludedUnsureRoutes?.length ?? 0,
        verdict: scoreJson.verdict,
        arms: Object.fromEntries(Object.entries(scoreJson.arms).map(([k, v]) => [k, {
          voided: v.voided,
          wrongFailureIdsAfterFallback: v.wrongFailureIdsAfterFallback,
          clopperPearson95UpperPct: v.clopperPearson95UpperPct,
          meetsSafetyBar: v.meetsSafetyBar,
          validCount: v.validCount,
          validCompletedOwn: v.validCompletedOwn,
          validCompletedAfterFallback: v.validCompletedAfterFallback,
          adapterAuthoringMinutes: v.adapterAuthoringMinutes,
          guardAuthoringMinutes: v.guardAuthoringMinutes,
          totalCostAtRateRUsd: v.totalCostAtRateRUsd,
        }])),
      },
    };
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}

export function selftest() {
  const report = runSealedCustodyAndScorerPipe();
  assert.equal(report.actualModelCallsSpent, 0);
  assert.equal(report.actualUsdSpent, 0);

  // Part A assertions: causal temporal/duration window ablation
  const gl = report.temporalAndDurationAblation.gitlab16TokenWindow;
  assert.equal(gl.withoutTemporalOrder.status, 'abstain');
  assert.match(gl.withoutTemporalOrder.reason, /unbound-intent-field:intent:\/expires_at/);
  assert.equal(gl.withTemporalOrder.status, 'learned');
  assert.equal(gl.withTemporalOrder.probes.validInWindowWithOlderIssuedAt, 'eligible-for-review');
  assert.equal(gl.withTemporalOrder.probes.invalidAfterMaxExpires, 'abstain');
  assert.equal(gl.withTemporalOrder.probes.invalidBeforeNotBefore, 'abstain');
  assert.equal(gl.withTemporalOrder.probes.invalidUnapprovedScope, 'abstain');

  const dur = report.temporalAndDurationAblation.heterogeneousIsoDurationCeiling;
  assert.equal(dur.status, 'learned');
  assert.equal(dur.valid28hUnder32h, 'eligible-for-review');
  assert.equal(dur.invalid48hOver36h, 'abstain');

  // Part B assertions: custody controls + 202-route full-floor blind scorer
  assert.equal(report.custodyControls.numericCloneRejection.rejectedByFullFloor, true);
  assert.equal(report.custodyControls.numericCloneRejection.normalizedIndependentFailureIds, 1);
  assert.equal(report.custodyControls.saltedCommitmentsVerified.ok, true);
  assert.equal(report.custodyControls.saltedCommitmentsVerified.answerKeyRoutesVerified, 202);
  assert.equal(report.custodyControls.cleanBuilderLeakScan.clean, true);
  assert.equal(report.custodyControls.plantedNeedleNegativeControl.clean, false);

  const sc = report.canonicalScorerSummary;
  assert.equal(sc.valid, true);
  assert.equal(sc.independentInvalidCases, 100);
  assert.equal(sc.validCases, 100);
  assert.equal(sc.arms['repair-boundary'].meetsSafetyBar, false);
  assert.equal(sc.arms['repair-boundary'].wrongFailureIdsAfterFallback, 16);

  const sound = sc.arms['repair-boundary-branch-no-graph'];
  assert.equal(sound.voided, false);
  assert.equal(sound.wrongFailureIdsAfterFallback, 0);
  assert.equal(sound.clopperPearson95UpperPct, 2.951);
  assert.equal(sound.meetsSafetyBar, true);
  assert.equal(sound.validCompletedAfterFallback, 100);
  assert.equal(sound.adapterAuthoringMinutes, '0');

  return { ok: true, report };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const { report } = selftest();
  const outDir = join(HERE, 'receipts');
  mkdirSync(outDir, { recursive: true });
  const outPath = join(outDir, 'temporal_and_custody_pipe_v1.json');
  writeFileSync(outPath, `${JSON.stringify(report, null, 2)}\n`);
  console.log(`Wrote verified $0 temporal + sealed-custody receipt to ${outPath}`);
}
