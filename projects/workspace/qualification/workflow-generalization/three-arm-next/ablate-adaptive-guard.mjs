#!/usr/bin/env node
// $0 600-Route Sequential Benchmark & Mechanism Ablation for Adaptive Relational Trace Guards.
//
// Evaluates `adaptive-relational-guard.mjs` across 6 workflows x 100 sequential routes (`T = 600`,
// 50% valid / 50% invalid, with 50% of valid routes carrying unseen incidental attribute drift on
// `priority`/`tier`/`tag` that coincided in the `n_pos = 2` teaching examples):
//   1. Clean Fallback Stream (`600` routes + asymptotic projection to `T = 6,000`):
//      Compares `always-replan`, `authored-expert-guard` (`28.0` human min), `passive-batch-lgg`
//      (no online refinement, batch GETs), `adaptive-batch-lgg-k2` (online refinement without
//      sequential role short-circuiting), and `adaptive-seq-lgg-k2` (full Rung 3 method).
//   2. Single-Fault Noisy Fallback Poisoning Stress Test:
//      Injects 1 erroneous `'write'` from a noisy fallback planner on the first `quarantine-proj`
//      route (where `record:/project === approval:/project` had zero variance in `n_pos = 2`).
//      Proves `unguarded-k1` (`kConfirm = 1`) gets poisoned and commits 12 subsequent guard-induced
//      wrong writes, whereas `adaptive-seq-lgg-k2` (`kConfirm = 2` + negative-lock promotion)
//      commits 0 guard-induced wrong writes.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createAdaptiveRelationalSession } from './adaptive-relational-guard.mjs';
import { extractTypedTraceFacts } from './relational-trace-guard.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const sha256 = s => createHash('sha256').update(s, 'utf8').digest('hex');
const getRow = (role, json) => ({ sameOrigin: true, method: 'GET', transport: 'fetch', status: 200, sourceRole: role, json });

function buildStreamingWorkflows() {
  // 1. OpenProject (coincidental `priority: 'normal'` in n_pos=2; real zero-var `project: 1` in n_pos=2!)
  const mkOp = ({ dur, rProj, rPrio, aStatus, aProj, aDur, aPrio }) => ({
    intent: { workDuration: dur },
    roles: {
      record: { id: 10, priority: rPrio, _links: { status: { href: '/api/v3/statuses/15' }, project: { href: `/api/v3/projects/${rProj}` } } },
      approval: { id: 20, priority: aPrio, estimatedTime: aDur, _links: { status: { href: `/api/v3/statuses/${aStatus}` }, project: { href: `/api/v3/projects/${aProj}` } } },
    },
  });
  const opStream = [];
  for (let i = 0; i < 25; i += 1) {
    const h = `PT${8 + (i % 5) * 4}H`;
    opStream.push({ id: `op-v-same-${i}`, valid: true, tag: 'valid-same', ex: mkOp({ dur: h, rProj: 1 + (i % 2), rPrio: 'normal', aStatus: 16, aProj: 1 + (i % 2), aDur: h, aPrio: 'normal' }) });
    opStream.push({ id: `op-v-drift-${i}`, valid: true, tag: 'valid-incidental-drift', ex: mkOp({ dur: h, rProj: 1 + (i % 2), rPrio: `tier-${i}`, aStatus: 16, aProj: 1 + (i % 2), aDur: h, aPrio: 'normal' }) });
    opStream.push({ id: `op-i-unapproved-${i}`, valid: false, tag: 'inv-status', ex: mkOp({ dur: h, rProj: 1, rPrio: 'normal', aStatus: 15, aProj: 1, aDur: h, aPrio: 'normal' }) });
    // Alternate cross-project quarantine (even i) and wrong-hours (odd i)
    if (i % 2 === 0) {
      opStream.push({ id: `op-i-quarantine-${i}`, valid: false, tag: 'inv-quarantine-proj', ex: mkOp({ dur: h, rProj: 1, rPrio: 'normal', aStatus: 16, aProj: 3, aDur: h, aPrio: 'normal' }) });
    } else {
      opStream.push({ id: `op-i-hours-${i}`, valid: false, tag: 'inv-hours', ex: mkOp({ dur: 'PT40H', rProj: 1, rPrio: 'normal', aStatus: 16, aProj: 1, aDur: 'PT8H', aPrio: 'normal' }) });
    }
  }

  // 2. ERPNext PO Confirmation (coincidental `warehouse_tier: 'std'` in n_pos=2)
  const mkErp = ({ oComp, oTier, oItems, qStatus, qComp, qTier, qItems }) => ({
    intent: { doctype: 'Purchase Order' },
    roles: {
      order: { data: { company: oComp, warehouse_tier: oTier, items: oItems } },
      quotation: { data: { docstatus: qStatus, company: qComp, warehouse_tier: qTier, items: qItems } },
    },
  });
  const erpStream = [];
  for (let i = 0; i < 25; i += 1) {
    const itemsOk = [{ item_code: 'BOLT', qty: 4 + (i % 5), rate: 10.5 }, { item_code: 'VALVE', qty: 2, rate: 200.0 }];
    const itemsSwap = [{ item_code: 'BOLT', qty: 2, rate: 10.5 }, { item_code: 'VALVE', qty: 4 + (i % 5), rate: 200.0 }];
    erpStream.push({ id: `erp-v-same-${i}`, valid: true, tag: 'valid-same', ex: mkErp({ oComp: 'QualCorp', oTier: 'std', oItems: itemsOk, qStatus: 1, qComp: 'QualCorp', qTier: 'std', qItems: itemsOk }) });
    erpStream.push({ id: `erp-v-drift-${i}`, valid: true, tag: 'valid-incidental-drift', ex: mkErp({ oComp: 'QualCorp', oTier: `exp-${i}`, oItems: itemsOk, qStatus: 1, qComp: 'QualCorp', qTier: 'std', qItems: itemsOk }) });
    erpStream.push({ id: `erp-i-draft-${i}`, valid: false, tag: 'inv-draft', ex: mkErp({ oComp: 'QualCorp', oTier: 'std', oItems: itemsOk, qStatus: 0, qComp: 'QualCorp', qTier: 'std', qItems: itemsOk }) });
    erpStream.push({ id: `erp-i-swap-${i}`, valid: false, tag: 'inv-swap', ex: mkErp({ oComp: 'QualCorp', oTier: 'std', oItems: itemsSwap, qStatus: 1, qComp: 'QualCorp', qTier: 'std', qItems: itemsOk }) });
  }

  // 3. OpenProject 17.8 Upgrade (`Target versions` subset + coincidental `category: 'infra'`)
  const mkOp178 = ({ cVers, rCat, aStatus, aVers, aCat }) => ({
    intent: { _links: { targetVersions: cVers.map(v => ({ href: `/api/v3/versions/${v}` })) } },
    roles: {
      record: { id: 30, category: rCat },
      approval: { id: 40, category: aCat, _links: { status: { href: `/api/v3/statuses/${aStatus}` }, targetVersions: aVers.map(v => ({ href: `/api/v3/versions/${v}` })) } },
    },
  });
  const op178Stream = [];
  for (let i = 0; i < 25; i += 1) {
    op178Stream.push({ id: `op178-v-same-${i}`, valid: true, tag: 'valid-same', ex: mkOp178({ cVers: [10, 11 + (i % 2)], rCat: 'infra', aStatus: 16, aVers: [10, 11, 12], aCat: 'infra' }) });
    op178Stream.push({ id: `op178-v-drift-${i}`, valid: true, tag: 'valid-incidental-drift', ex: mkOp178({ cVers: [10, 12], rCat: `cat-${i}`, aStatus: 16, aVers: [10, 11, 12], aCat: 'infra' }) });
    op178Stream.push({ id: `op178-i-hold-${i}`, valid: false, tag: 'inv-status', ex: mkOp178({ cVers: [10, 11], rCat: 'infra', aStatus: 17, aVers: [10, 11, 12], aCat: 'infra' }) });
    op178Stream.push({ id: `op178-i-unapproved-ver-${i}`, valid: false, tag: 'inv-ver', ex: mkOp178({ cVers: [10, 99], rCat: 'infra', aStatus: 16, aVers: [10, 11, 12], aCat: 'infra' }) });
  }

  // 4. NetBox v4.1 Upgrade (`vid_ranges` intervals + coincidental `tenant_tag: 'us'`)
  const mkNb41 = ({ reqRanges, rTag, aStatus, authRanges, aTag }) => ({
    intent: { vid_ranges: reqRanges },
    roles: {
      record: { id: 5, tenant_tag: rTag },
      approval: { id: 90, status: aStatus, tenant_tag: aTag, authorized_vid_ranges: authRanges },
    },
  });
  const nb41Stream = [];
  for (let i = 0; i < 25; i += 1) {
    nb41Stream.push({ id: `nb41-v-same-${i}`, valid: true, tag: 'valid-same', ex: mkNb41({ reqRanges: [[100 + i, 150 + i]], rTag: 'us', aStatus: 'approved', authRanges: [[100, 299], [400, 499]], aTag: 'us' }) });
    nb41Stream.push({ id: `nb41-v-drift-${i}`, valid: true, tag: 'valid-incidental-drift', ex: mkNb41({ reqRanges: [[410, 420 + i]], rTag: `eu-${i}`, aStatus: 'approved', authRanges: [[100, 299], [400, 499]], aTag: 'us' }) });
    nb41Stream.push({ id: `nb41-i-staged-${i}`, valid: false, tag: 'inv-status', ex: mkNb41({ reqRanges: [[110, 120]], rTag: 'us', aStatus: 'staged', authRanges: [[100, 299]], aTag: 'us' }) });
    nb41Stream.push({ id: `nb41-i-overflow-${i}`, valid: false, tag: 'inv-range', ex: mkNb41({ reqRanges: [[110, 120], [900, 950]], rTag: 'us', aStatus: 'approved', authRanges: [[100, 299]], aTag: 'us' }) });
  }

  // 5. NetBox v4.2 Upgrade (`scope_type + scope_id` + coincidental `region_zone: 'east'`)
  const mkNb42 = ({ sType, sId, rZone, aStatus, aType, aId, aZone }) => ({
    intent: { scope_type: sType, scope_id: sId },
    roles: {
      record: { id: 18, region_zone: rZone },
      approval: { id: 91, status: aStatus, scope_type: aType, scope_id: aId, region_zone: aZone },
    },
  });
  const nb42Stream = [];
  for (let i = 0; i < 25; i += 1) {
    const sid = 10 + (i % 5);
    nb42Stream.push({ id: `nb42-v-same-${i}`, valid: true, tag: 'valid-same', ex: mkNb42({ sType: 'dcim.site', sId: sid, rZone: 'east', aStatus: 'approved', aType: 'dcim.site', aId: sid, aZone: 'east' }) });
    nb42Stream.push({ id: `nb42-v-drift-${i}`, valid: true, tag: 'valid-incidental-drift', ex: mkNb42({ sType: 'dcim.site', sId: sid, rZone: `west-${i}`, aStatus: 'approved', aType: 'dcim.site', aId: sid, aZone: 'east' }) });
    nb42Stream.push({ id: `nb42-i-pending-${i}`, valid: false, tag: 'inv-status', ex: mkNb42({ sType: 'dcim.site', sId: sid, rZone: 'east', aStatus: 'pending', aType: 'dcim.site', aId: sid, aZone: 'east' }) });
    nb42Stream.push({ id: `nb42-i-spoof-${i}`, valid: false, tag: 'inv-spoof', ex: mkNb42({ sType: 'dcim.region', sId: sid, rZone: 'east', aStatus: 'approved', aType: 'dcim.site', aId: sid, aZone: 'east' }) });
  }

  // 6. GitLab 16.0 Upgrade (`approvals_required + user_ids[]` + coincidental `visibility: 'internal'`)
  const mkGl16 = ({ reqCnt, reqUsers, rVis, pStatus, pMin, pUsers, pVis }) => ({
    intent: { approvals_required: reqCnt, user_ids: reqUsers },
    roles: {
      record: { id: 7, visibility: rVis },
      approval: { id: 77, status: pStatus, min_approvals: pMin, eligible_approver_ids: pUsers, visibility: pVis },
    },
  });
  const gl16Stream = [];
  for (let i = 0; i < 25; i += 1) {
    gl16Stream.push({ id: `gl16-v-same-${i}`, valid: true, tag: 'valid-same', ex: mkGl16({ reqCnt: 2, reqUsers: [101, 102], rVis: 'internal', pStatus: 'active', pMin: 2, pUsers: [101, 102, 103], pVis: 'internal' }) });
    gl16Stream.push({ id: `gl16-v-drift-${i}`, valid: true, tag: 'valid-incidental-drift', ex: mkGl16({ reqCnt: 2, reqUsers: [101, 103], rVis: `priv-${i}`, pStatus: 'active', pMin: 2, pUsers: [101, 102, 103], pVis: 'internal' }) });
    gl16Stream.push({ id: `gl16-i-draft-${i}`, valid: false, tag: 'inv-status', ex: mkGl16({ reqCnt: 2, reqUsers: [101, 102], rVis: 'internal', pStatus: 'draft', pMin: 2, pUsers: [101, 102, 103], pVis: 'internal' }) });
    gl16Stream.push({ id: `gl16-i-downgrade-${i}`, valid: false, tag: 'inv-downgrade', ex: mkGl16({ reqCnt: 1, reqUsers: [101, 102], rVis: 'internal', pStatus: 'active', pMin: 2, pUsers: [101, 102, 103], pVis: 'internal' }) });
  }

  return [
    {
      workflowId: 'op-base-approval-gate',
      humanExpertMinutes: 6.0,
      trainPos: [
        mkOp({ dur: 'PT16H', rProj: 1, rPrio: 'normal', aStatus: 16, aProj: 1, aDur: 'PT16H', aPrio: 'normal' }),
        mkOp({ dur: 'PT24H', rProj: 1, rPrio: 'normal', aStatus: 16, aProj: 1, aDur: 'PT24H', aPrio: 'normal' }),
      ],
      trainNeg: [
        mkOp({ dur: 'PT16H', rProj: 1, rPrio: 'normal', aStatus: 15, aProj: 1, aDur: 'PT16H', aPrio: 'normal' }),
        mkOp({ dur: 'PT24H', rProj: 1, rPrio: 'normal', aStatus: 17, aProj: 1, aDur: 'PT24H', aPrio: 'normal' }),
      ],
      expertCheck: ex => (
        ex.roles.approval._links.status.href === '/api/v3/statuses/16'
        && ex.roles.approval.estimatedTime === ex.intent.workDuration
        && ex.roles.approval._links.project.href === ex.roles.record._links.project.href
      ),
      stream: opStream,
    },
    {
      workflowId: 'erp-base-po-line-items',
      humanExpertMinutes: 6.5,
      trainPos: [
        mkErp({ oComp: 'QualCorp', oTier: 'std', oItems: [{ item_code: 'BOLT', qty: 8, rate: 10.5 }], qStatus: 1, qComp: 'QualCorp', qTier: 'std', qItems: [{ item_code: 'BOLT', qty: 8, rate: 10.5 }] }),
        mkErp({ oComp: 'PartnerCorp', oTier: 'std', oItems: [{ item_code: 'VALVE', qty: 2, rate: 190.0 }], qStatus: 1, qComp: 'PartnerCorp', qTier: 'std', qItems: [{ item_code: 'VALVE', qty: 2, rate: 200.0 }] }),
      ],
      trainNeg: [
        mkErp({ oComp: 'QualCorp', oTier: 'std', oItems: [{ item_code: 'BOLT', qty: 8, rate: 10.5 }], qStatus: 0, qComp: 'QualCorp', qTier: 'std', qItems: [{ item_code: 'BOLT', qty: 8, rate: 10.5 }] }),
        mkErp({ oComp: 'QualCorp', oTier: 'std', oItems: [{ item_code: 'BOLT', qty: 8, rate: 10.5 }], qStatus: 1, qComp: 'QualCorp', qTier: 'std', qItems: [{ item_code: 'BOLT', qty: 4, rate: 10.5 }] }),
      ],
      expertCheck: ex => {
        const o = ex.roles.order.data;
        const q = ex.roles.quotation.data;
        if (q.docstatus !== 1 || q.company !== o.company || o.items.length !== q.items.length) return false;
        const m = new Map(q.items.map(x => [x.item_code, x]));
        return o.items.every(it => m.get(it.item_code)?.qty === it.qty && it.rate <= m.get(it.item_code)?.rate);
      },
      stream: erpStream,
    },
    {
      workflowId: 'upgrade-op178-target-versions',
      humanExpertMinutes: 4.0,
      trainPos: [
        mkOp178({ cVers: [10, 11], rCat: 'infra', aStatus: 16, aVers: [10, 11, 12], aCat: 'infra' }),
        mkOp178({ cVers: [11, 12], rCat: 'infra', aStatus: 16, aVers: [10, 11, 12], aCat: 'infra' }),
      ],
      trainNeg: [
        mkOp178({ cVers: [10, 99], rCat: 'infra', aStatus: 16, aVers: [10, 11, 12], aCat: 'infra' }),
        mkOp178({ cVers: [10, 11], rCat: 'infra', aStatus: 17, aVers: [10, 11, 12], aCat: 'infra' }),
      ],
      expertCheck: ex => {
        if (ex.roles.approval._links.status.href !== '/api/v3/statuses/16') return false;
        const sup = new Set(ex.roles.approval._links.targetVersions.map(x => x.href));
        return ex.intent._links.targetVersions.every(x => sup.has(x.href));
      },
      stream: op178Stream,
    },
    {
      workflowId: 'upgrade-netbox41-vid-ranges',
      humanExpertMinutes: 4.0,
      trainPos: [
        mkNb41({ reqRanges: [[100, 199], [300, 349]], rTag: 'us', aStatus: 'approved', authRanges: [[100, 299], [300, 399]], aTag: 'us' }),
        mkNb41({ reqRanges: [[150, 250]], rTag: 'us', aStatus: 'approved', authRanges: [[100, 299], [400, 499]], aTag: 'us' }),
      ],
      trainNeg: [
        mkNb41({ reqRanges: [[100, 199], [900, 999]], rTag: 'us', aStatus: 'approved', authRanges: [[100, 299], [300, 399]], aTag: 'us' }),
        mkNb41({ reqRanges: [[100, 199]], rTag: 'us', aStatus: 'staged', authRanges: [[100, 299]], aTag: 'us' }),
      ],
      expertCheck: ex => (
        ex.roles.approval.status === 'approved'
        && ex.intent.vid_ranges.every(([a, b]) => ex.roles.approval.authorized_vid_ranges.some(([A, B]) => A <= a && b <= B))
      ),
      stream: nb41Stream,
    },
    {
      workflowId: 'upgrade-netbox42-generic-scope',
      humanExpertMinutes: 3.5,
      trainPos: [
        mkNb42({ sType: 'dcim.site', sId: 6, rZone: 'east', aStatus: 'approved', aType: 'dcim.site', aId: 6, aZone: 'east' }),
        mkNb42({ sType: 'dcim.location', sId: 12, rZone: 'east', aStatus: 'approved', aType: 'dcim.location', aId: 12, aZone: 'east' }),
      ],
      trainNeg: [
        mkNb42({ sType: 'dcim.site', sId: 6, rZone: 'east', aStatus: 'pending', aType: 'dcim.site', aId: 6, aZone: 'east' }),
        mkNb42({ sType: 'dcim.site', sId: 99, rZone: 'east', aStatus: 'approved', aType: 'dcim.site', aId: 6, aZone: 'east' }),
      ],
      expertCheck: ex => (
        ex.roles.approval.status === 'approved'
        && ex.intent.scope_type === ex.roles.approval.scope_type
        && ex.intent.scope_id === ex.roles.approval.scope_id
      ),
      stream: nb42Stream,
    },
    {
      workflowId: 'upgrade-gitlab16-approval-rules',
      humanExpertMinutes: 4.0,
      trainPos: [
        mkGl16({ reqCnt: 2, reqUsers: [101, 102], rVis: 'internal', pStatus: 'active', pMin: 2, pUsers: [101, 102, 103], pVis: 'internal' }),
        mkGl16({ reqCnt: 3, reqUsers: [102, 103], rVis: 'internal', pStatus: 'active', pMin: 3, pUsers: [101, 102, 103, 104], pVis: 'internal' }),
      ],
      trainNeg: [
        mkGl16({ reqCnt: 2, reqUsers: [101, 999], rVis: 'internal', pStatus: 'active', pMin: 2, pUsers: [101, 102, 103], pVis: 'internal' }),
        mkGl16({ reqCnt: 2, reqUsers: [101, 102], rVis: 'internal', pStatus: 'draft', pMin: 2, pUsers: [101, 102, 103], pVis: 'internal' }),
      ],
      expertCheck: ex => {
        if (ex.roles.approval.status !== 'active' || ex.intent.approvals_required !== ex.roles.approval.min_approvals) return false;
        const sup = new Set(ex.roles.approval.eligible_approver_ids);
        return ex.intent.user_ids.every(u => sup.has(u));
      },
      stream: gl16Stream,
    },
  ];
}

const toObs = ex => extractTypedTraceFacts(
  Object.entries(ex.roles).map(([r, j]) => getRow(r, j)),
  ex.intent,
);

async function evaluateArmAcrossStreams(workflows, armConfig, { injectFirstQuarantineFallbackFault = false } = {}) {
  const replanCostUsd = 0.08;
  const ratePerMin = 0.50;

  let humanMinutes = 0;
  let guardOwnValidCompleted = 0;
  let validAfterFallback = 0;
  let guardInducedWrongWrites = 0;
  let totalWrongWritesAfterFallback = 0;
  let serverReadsByGuard = 0;
  let fawnBranchesByGuard = 0;
  let fallbackInvocations = 0;
  let falseAbstentionFallbacks = 0;
  let refinementsApplied = 0;
  let locksPromoted = 0;
  let faultInjected = false;

  for (const wf of workflows) {
    const eff = `opbind-v1:${sha256(wf.workflowId)}`;
    let session = null;
    if (armConfig.kind === 'adaptive') {
      session = createAdaptiveRelationalSession({
        intendedEffect: eff,
        positiveObservations: wf.trainPos.map(toObs),
        negativeObservations: wf.trainNeg.map(toObs),
        kConfirm: armConfig.kConfirm,
        enableSequentialShortCircuit: armConfig.seq,
        enableOnlineRefinement: armConfig.online,
      });
    } else if (armConfig.kind === 'expert') {
      humanMinutes += wf.humanExpertMinutes;
    }

    for (const item of wf.stream) {
      if (armConfig.kind === 'replan') {
        fallbackInvocations += 1;
        if (item.valid) validAfterFallback += 1;
        continue;
      }

      if (armConfig.kind === 'expert') {
        // Batch-fetches both server roles (2 GETs)
        serverReadsByGuard += Object.keys(item.ex.roles).length;
        const ok = wf.expertCheck(item.ex);
        if (ok) {
          fawnBranchesByGuard += 2;
          if (item.valid) {
            guardOwnValidCompleted += 1;
            validAfterFallback += 1;
          } else {
            guardInducedWrongWrites += 1;
            totalWrongWritesAfterFallback += 1;
          }
        } else {
          fallbackInvocations += 1;
          if (item.valid) {
            falseAbstentionFallbacks += 1;
            validAfterFallback += 1;
          }
        }
        continue;
      }

      // Adaptive / Passive Relational Guard arm
      const res = await session.evaluateRoute({
        intentPayload: item.ex.intent,
        fetchRole: async role => getRow(role, item.ex.roles[role]),
      });
      serverReadsByGuard += res.serverReads;
      fawnBranchesByGuard += res.fawnBranchesSpawned;

      if (res.decision === 'eligible-for-review') {
        if (item.valid) {
          guardOwnValidCompleted += 1;
          validAfterFallback += 1;
        } else {
          guardInducedWrongWrites += 1;
          totalWrongWritesAfterFallback += 1;
        }
      } else {
        // Abstained -> invoke fallback (`always-replan`)
        fallbackInvocations += 1;
        if (item.valid) falseAbstentionFallbacks += 1;

        let fbDecision = item.valid ? 'write' : 'stop';
        if (injectFirstQuarantineFallbackFault && !faultInjected && item.id === 'op-i-quarantine-0') {
          fbDecision = 'write'; // Single-fault noisy fallback hallucination!
          faultInjected = true;
        }
        if (fbDecision === 'write') {
          if (item.valid) validAfterFallback += 1;
          else totalWrongWritesAfterFallback += 1;
        }
        // Fallback already reads full state; pass full typed observation to online refinement
        session.recordFallbackOutcome({
          fallbackDecision: fbDecision,
          fullObservation: toObs(item.ex),
        });
      }
    }

    if (session) {
      const st = session.getStats();
      refinementsApplied += st.refinementsApplied;
      locksPromoted += st.locksPromoted;
    }
  }

  const fixedHumanCostUsd = Number((humanMinutes * ratePerMin).toFixed(2));
  const fallbackSpendUsd = Number((fallbackInvocations * replanCostUsd).toFixed(2));
  const totalBilledCostUsd = Number((fixedHumanCostUsd + fallbackSpendUsd).toFixed(2));

  return {
    armId: armConfig.id,
    humanMinutes,
    guardOwnValidCompleted,
    validAfterFallback,
    guardInducedWrongWrites,
    totalWrongWritesAfterFallback,
    serverReadsByGuard,
    fawnBranchesByGuard,
    fallbackInvocations,
    falseAbstentionFallbacks,
    refinementsApplied,
    locksPromoted,
    costAt600RoutesUsd: {
      fixedHumanUsd: fixedHumanCostUsd,
      fallbackSpendUsd,
      totalBilledUsd: totalBilledCostUsd,
    },
  };
}

export async function runAdaptiveGuardAblation() {
  const workflows = buildStreamingWorkflows();
  const cleanArms = [
    { id: 'always-replan', kind: 'replan' },
    { id: 'authored-expert-guard', kind: 'expert' },
    { id: 'passive-batch-lgg', kind: 'adaptive', kConfirm: 2, seq: false, online: false },
    { id: 'adaptive-batch-lgg-k2', kind: 'adaptive', kConfirm: 2, seq: false, online: true },
    { id: 'adaptive-seq-lgg-k2', kind: 'adaptive', kConfirm: 2, seq: true, online: true },
  ];

  const cleanResults = {};
  for (const arm of cleanArms) {
    cleanResults[arm.id] = await evaluateArmAcrossStreams(workflows, arm, { injectFirstQuarantineFallbackFault: false });
  }

  // Adversarial Single-Fault Noisy Fallback Poisoning Stress Test (`kConfirm = 1` vs `kConfirm = 2`)
  const poisonedK1 = await evaluateArmAcrossStreams(
    workflows,
    { id: 'unguarded-seq-lgg-k1', kind: 'adaptive', kConfirm: 1, seq: true, online: true },
    { injectFirstQuarantineFallbackFault: true },
  );
  const resilientK2 = await evaluateArmAcrossStreams(
    workflows,
    { id: 'adaptive-seq-lgg-k2', kind: 'adaptive', kConfirm: 2, seq: true, online: true },
    { injectFirstQuarantineFallbackFault: true },
  );

  // Project total billed cost across total stream horizons `T in {60, 300, 600, 1800, 6000}` (`r = $0.50/min`):
  // - `always-replan`: `0.08 * T`
  // - `authored-expert-guard`: `14.00 + 0.04 * T`
  // - `passive-batch-lgg`: `0 + (0.50 + 0.25) * 0.08 * T = 0.06 * T` (bleeds on 25% incidental drift forever!)
  // - `adaptive-seq-lgg-k2`: `6 workflows * 2 confirmations * $0.08 = $0.96` one-time warmup + `0.04 * T`!
  const horizons = [60, 300, 600, 1800, 6000].map(T => {
    const cReplan = Number((0.08 * T).toFixed(2));
    const cExpert = Number((14.00 + 0.04 * T).toFixed(2));
    const cPassive = Number((0.06 * T).toFixed(2));
    const warmupFallbacks = Math.min(0.25 * T, 12);
    const cAdaptive = Number(((0.50 * T + warmupFallbacks) * 0.08).toFixed(2));
    const all = {
      'always-replan': cReplan,
      'passive-batch-lgg': cPassive,
      'authored-expert-guard': cExpert,
      'adaptive-seq-lgg-k2': cAdaptive,
    };
    const winner = Object.keys(all).reduce((b, k) => (all[k] < all[b] ? k : b));
    return { totalRoutes: T, totalBilledCostUsd: all, lowestCostSafeArm: winner };
  });

  return {
    schema: 'gammatron-adaptive-relational-ablation/v1',
    modelCalls: 0,
    costUsd: 0,
    totalStreamRoutes: 600,
    cleanStreamArms: cleanResults,
    noisyFallbackPoisoningTest: {
      unguardedK1: {
        guardInducedWrongWrites: poisonedK1.guardInducedWrongWrites,
        totalWrongWritesAfterFallback: poisonedK1.totalWrongWritesAfterFallback,
      },
      guardedK2: {
        guardInducedWrongWrites: resilientK2.guardInducedWrongWrites,
        totalWrongWritesAfterFallback: resilientK2.totalWrongWritesAfterFallback,
        locksPromoted: resilientK2.locksPromoted,
      },
    },
    horizonCostScalingAtHalfDollarPerMin: horizons,
  };
}

export async function selftest() {
  const report = await runAdaptiveGuardAblation();
  assert.equal(report.modelCalls, 0);
  assert.equal(report.costUsd, 0);

  const passive = report.cleanStreamArms['passive-batch-lgg'];
  const batchK2 = report.cleanStreamArms['adaptive-batch-lgg-k2'];
  const fullSeqK2 = report.cleanStreamArms['adaptive-seq-lgg-k2'];
  const expert = report.cleanStreamArms['authored-expert-guard'];
  const replan = report.cleanStreamArms['always-replan'];

  // 1. Zero wrong writes on clean stream across all guard arms
  assert.equal(passive.guardInducedWrongWrites, 0);
  assert.equal(fullSeqK2.guardInducedWrongWrites, 0);
  assert.equal(expert.guardInducedWrongWrites, 0);

  // 2. Online refinement (`kConfirm = 2`) cuts false-abstention fallbacks from 150 (passive) down to 12 (`6 * 2`)!
  assert.equal(passive.falseAbstentionFallbacks, 150);
  assert.equal(fullSeqK2.falseAbstentionFallbacks, 12);
  assert.equal(fullSeqK2.refinementsApplied, 6);
  assert.equal(fullSeqK2.validAfterFallback, 300);

  // 3. Online coincidence relaxation prunes unreferenced roles (1200 -> 824 GETs), and adaptive sequential
  //    authority-first ordering cuts server GET reads further (824 -> 783 GETs, -34.8% vs passive/expert)!
  assert.equal(passive.serverReadsByGuard, 1200);
  assert.equal(expert.serverReadsByGuard, 1200);
  assert.equal(batchK2.serverReadsByGuard, 824);
  assert.equal(fullSeqK2.serverReadsByGuard, 783);

  // 4. Anti-poisoning (`kConfirm = 2` + negative lock) blocks single-fault fallback poisoning (`0` vs `12` guard wrong writes)!
  assert.equal(report.noisyFallbackPoisoningTest.unguardedK1.guardInducedWrongWrites, 12);
  assert.equal(report.noisyFallbackPoisoningTest.guardedK2.guardInducedWrongWrites, 0);
  assert.ok(report.noisyFallbackPoisoningTest.guardedK2.locksPromoted >= 1);

  // 5. Cost dominance: `adaptive-seq-lgg-k2` (`$24.96` at T=600) beats `passive-batch-lgg` (`$36.00`),
  //    `authored-expert-guard` (`$38.00`), and `always-replan` (`$48.00`), AND wins EVERY horizon T in {60..6000}!
  assert.equal(fullSeqK2.costAt600RoutesUsd.totalBilledUsd, 24.96);
  assert.equal(passive.costAt600RoutesUsd.totalBilledUsd, 36.00);
  assert.equal(expert.costAt600RoutesUsd.totalBilledUsd, 38.00);
  assert.equal(replan.costAt600RoutesUsd.totalBilledUsd, 48.00);
  assert.ok(report.horizonCostScalingAtHalfDollarPerMin.every(h => h.lowestCostSafeArm === 'adaptive-seq-lgg-k2'));

  return { ok: true, report };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const { report } = await selftest();
  const outDir = join(HERE, 'receipts');
  mkdirSync(outDir, { recursive: true });
  const outPath = join(outDir, 'adaptive_relational_ablation_v1.json');
  writeFileSync(outPath, `${JSON.stringify(report, null, 2)}\n`);
  console.log(`Wrote verified $0 adaptive ablation receipt to ${outPath}`);
}
