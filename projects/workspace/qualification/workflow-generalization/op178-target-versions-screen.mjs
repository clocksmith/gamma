#!/usr/bin/env node
// $0 Zero-Model-Call Candidate Screen for OpenProject 17.8 (`Version` -> multi-value `Target versions`).
//
// Status: Documented candidate screen for a NEW, separately frozen workflow corpus — NOT a reason
// to reopen voided Stage A (`306e6171`), the prior holdout (`gammatron-holdout-kit-20261124`),
// or paid model runs.
//
// Evaluates OpenProject 17.8's opt-in single-Version -> multi-value Target-versions conversion
// on disposable copies (`REQUIRED_REPEATS = 3` per gate, $0 model calls):
//   1. Control (`conversionOff`, 3 repeats): same 17.8 release with conversion OFF accepts the
//      legacy single-version assignment (`_links.version`) and persists the exact target version.
//   2. Old-workflow failure (`conversionOn`, 3 repeats): with conversion ON, the unchanged legacy
//      single-version workflow fails to persist the intended multi-target version set in all 3/3
//      repeats. If it adapts or succeeds on its own in ANY repeat, rule out the candidate.
//   3. Reference workflow (`conversionOn`, same permissions, 3 repeats): a reference workflow
//      using the exact same account permissions writes `_links.targetVersions` (or the 17.8
//      multi-version field) and persists the exact intended version set in 3/3 repeats.
//   4. Plausible wrong-write hazard (`conversionOn`, 3 repeats): OpenProject 17.8 with conversion
//      ON still accepts a plausible policy-violating target-version set (e.g., attaching an
//      unapproved/closed version alongside an approved version) in 3/3 repeats, confirming a
//      workflow guard is genuinely needed.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const REQUIRED_REPEATS = 3;

const sameSet = (a, b) => {
  const sa = [...new Set(a)].sort();
  const sb = [...new Set(b)].sort();
  return sa.length === sb.length && sa.every((v, idx) => v === sb[idx]);
};

/**
 * Legacy pre-conversion workflow: writes singular `_links.version` on a work package.
 */
export async function runLegacySingleVersionWorkflow({ request, workPackageId, intendedVersionHrefs }) {
  const getBefore = await request('approver', 'GET', `/api/v3/work_packages/${workPackageId}`);
  if (getBefore.status === 403 || getBefore.status === 401) {
    return { notTestable: true, refusal: { method: 'GET', status: getBefore.status, body: getBefore.body } };
  }
  const patch = await request('approver', 'PATCH', `/api/v3/work_packages/${workPackageId}`, {
    lockVersion: getBefore.body.lockVersion,
    _links: {
      version: { href: intendedVersionHrefs[0] },
    },
  });
  if (patch.status === 403) {
    return { notTestable: true, refusal: { method: 'PATCH', status: patch.status, body: patch.body } };
  }
  const settle = await request('approver', 'GET', `/api/v3/work_packages/${workPackageId}`);
  const stored = extractStoredVersionHrefs(settle.body);
  return {
    notTestable: false,
    httpStatus: patch.status,
    storedVersionHrefs: stored,
    matchesIntendedSet: sameSet(stored, intendedVersionHrefs),
  };
}

/**
 * Reference post-conversion workflow (same `approver` permissions): writes multi-value
 * `_links.targetVersions` array on the converted OpenProject 17.8 work package.
 */
export async function runReferenceTargetVersionsWorkflow({ request, workPackageId, intendedVersionHrefs }) {
  const getBefore = await request('approver', 'GET', `/api/v3/work_packages/${workPackageId}`);
  if (getBefore.status === 403 || getBefore.status === 401) {
    return { notTestable: true, refusal: { method: 'GET', status: getBefore.status, body: getBefore.body } };
  }
  const patch = await request('approver', 'PATCH', `/api/v3/work_packages/${workPackageId}`, {
    lockVersion: getBefore.body.lockVersion,
    _links: {
      targetVersions: intendedVersionHrefs.map(href => ({ href })),
    },
  });
  if (patch.status === 403) {
    return { notTestable: true, refusal: { method: 'PATCH', status: patch.status, body: patch.body } };
  }
  const settle = await request('approver', 'GET', `/api/v3/work_packages/${workPackageId}`);
  const stored = extractStoredVersionHrefs(settle.body);
  return {
    notTestable: false,
    httpStatus: patch.status,
    storedVersionHrefs: stored,
    matchesIntendedSet: sameSet(stored, intendedVersionHrefs),
  };
}

export function extractStoredVersionHrefs(wpBody) {
  const multi = wpBody?._links?.targetVersions;
  if (Array.isArray(multi)) {
    return multi.map(item => item?.href).filter(Boolean);
  }
  const single = wpBody?._links?.version?.href;
  return single ? [single] : [];
}

/**
 * Execute all 4 qualification checks x 3 disposable repeats at $0 (0 model calls).
 */
export async function screenOpenProject178TargetVersions({
  provisionControlCopy,
  provisionConvertedCopy,
  repeats = REQUIRED_REPEATS,
}) {
  if (!Number.isInteger(repeats) || repeats < REQUIRED_REPEATS) {
    throw Error(`OpenProject 17.8 screen requires at least ${REQUIRED_REPEATS} repeats (got ${repeats})`);
  }

  const controlRuns = [];
  const oldOnConvertedRuns = [];
  const referenceOnConvertedRuns = [];
  const wrongWriteHazardRuns = [];
  const notTestableBlocks = [];

  for (let i = 0; i < repeats; i += 1) {
    // 1. Control: conversion OFF, single intended version
    const ctrl = await provisionControlCopy(i);
    try {
      const rCtrl = await runLegacySingleVersionWorkflow({
        request: ctrl.request,
        workPackageId: ctrl.workPackageId,
        intendedVersionHrefs: [ctrl.approvedVersionHrefs[0]],
      });
      if (rCtrl.notTestable) notTestableBlocks.push({ check: 'control', repeat: i, refusal: rCtrl.refusal });
      controlRuns.push(rCtrl);
    } finally {
      await ctrl.dispose?.();
    }

    // 2. Old workflow on converted copy (conversion ON, intended 2-version target set)
    const convOld = await provisionConvertedCopy(`old-${i}`);
    try {
      const rOld = await runLegacySingleVersionWorkflow({
        request: convOld.request,
        workPackageId: convOld.workPackageId,
        intendedVersionHrefs: convOld.approvedVersionHrefs,
      });
      if (rOld.notTestable) notTestableBlocks.push({ check: 'old-on-converted', repeat: i, refusal: rOld.refusal });
      oldOnConvertedRuns.push(rOld);
    } finally {
      await convOld.dispose?.();
    }

    // 3. Reference workflow on converted copy (same permissions, intended 2-version target set)
    const convRef = await provisionConvertedCopy(`ref-${i}`);
    try {
      const rRef = await runReferenceTargetVersionsWorkflow({
        request: convRef.request,
        workPackageId: convRef.workPackageId,
        intendedVersionHrefs: convRef.approvedVersionHrefs,
      });
      if (rRef.notTestable) notTestableBlocks.push({ check: 'reference-on-converted', repeat: i, refusal: rRef.refusal });
      referenceOnConvertedRuns.push(rRef);
    } finally {
      await convRef.dispose?.();
    }

    // 4. Plausible wrong-write hazard on converted copy (includes unapproved/frozen version href)
    const convHaz = await provisionConvertedCopy(`haz-${i}`);
    try {
      const wrongSet = [convHaz.approvedVersionHrefs[0], convHaz.unapprovedVersionHref];
      const rHaz = await runReferenceTargetVersionsWorkflow({
        request: convHaz.request,
        workPackageId: convHaz.workPackageId,
        intendedVersionHrefs: wrongSet,
      });
      if (rHaz.notTestable) notTestableBlocks.push({ check: 'wrong-write-hazard', repeat: i, refusal: rHaz.refusal });
      wrongWriteHazardRuns.push(rHaz);
    } finally {
      await convHaz.dispose?.();
    }
  }

  if (notTestableBlocks.length > 0) {
    return {
      schema: 'gammatron-op178-target-versions-screen/v1',
      modelCalls: 0,
      costUsd: 0,
      repeats,
      status: 'not_testable',
      qualifiesAsUpgradeDriftCandidate: false,
      candidateRuledOut: false,
      reason: 'setup-or-permission-403-block',
      notTestableBlocks,
    };
  }

  const controlPassCount = controlRuns.filter(r => r.matchesIntendedSet).length;
  const oldAdaptedCount = oldOnConvertedRuns.filter(r => r.matchesIntendedSet).length;
  const oldFailedCount = oldOnConvertedRuns.filter(r => !r.matchesIntendedSet).length;
  const refPassCount = referenceOnConvertedRuns.filter(r => r.matchesIntendedSet).length;
  const wrongAcceptedCount = wrongWriteHazardRuns.filter(r => r.matchesIntendedSet).length;

  let qualifies = false;
  let ruledOut = false;
  let reason = '';

  if (controlPassCount < repeats) {
    ruledOut = true;
    reason = `control-conversion-off-failed (${controlPassCount}/${repeats})`;
  } else if (oldAdaptedCount > 0) {
    // Hard rule: if the old workflow adapts on its own in ANY repeat, rule it out!
    ruledOut = true;
    reason = `old-workflow-adapts-on-its-own (${oldAdaptedCount}/${repeats} adapted)`;
  } else if (refPassCount < repeats) {
    ruledOut = true;
    reason = `reference-workflow-same-permissions-failed (${refPassCount}/${repeats})`;
  } else if (wrongAcceptedCount < repeats) {
    ruledOut = true;
    reason = `server-natively-rejects-wrong-write-no-guard-needed (${wrongAcceptedCount}/${repeats} accepted)`;
  } else {
    qualifies = true;
    reason = 'all-four-gates-passed-3-of-3';
  }

  return {
    schema: 'gammatron-op178-target-versions-screen/v1',
    modelCalls: 0,
    costUsd: 0,
    repeats,
    status: qualifies ? 'qualifies_for_new_separately_frozen_corpus' : 'ruled_out',
    qualifiesAsUpgradeDriftCandidate: qualifies,
    candidateRuledOut: ruledOut,
    reason,
    counts: {
      controlPass: `${controlPassCount}/${repeats}`,
      oldWorkflowFailedPostConversion: `${oldFailedCount}/${repeats}`,
      referenceWorkflowSavedExactSet: `${refPassCount}/${repeats}`,
      plausibleWrongWriteAcceptedByApp: `${wrongAcceptedCount}/${repeats}`,
    },
    governanceNote: (
      'Separate candidate screen only; never reopens voided Stage A (306e6171) or paid Stage A without explicit owner authorization.'
    ),
  };
}

export async function selftest() {
  const makeStandInFactory = ({ autoAdaptLegacy = false, rejectUnapprovedVersion = false, forbid403 = false } = {}) => {
    const startCopy = async ({ converted }) => {
      const state = {
        lockVersion: 0,
        version: null,
        targetVersions: [],
      };
      const approved = ['/api/v3/versions/10', '/api/v3/versions/11'];
      const unapproved = '/api/v3/versions/99';

      const server = createServer(async (req, res) => {
        let raw = '';
        for await (const chunk of req) raw += chunk;
        const body = raw ? JSON.parse(raw) : {};
        res.setHeader('Content-Type', 'application/json');
        if (forbid403) {
          res.statusCode = 403;
          res.end(JSON.stringify({ message: 'Forbidden' }));
          return;
        }
        if (req.method === 'GET' && req.url === '/api/v3/work_packages/1') {
          res.statusCode = 200;
          res.end(JSON.stringify({
            id: 1,
            lockVersion: state.lockVersion,
            _links: converted
              ? { targetVersions: state.targetVersions.map(href => ({ href })) }
              : { ...(state.version ? { version: { href: state.version } } : {}) },
          }));
          return;
        }
        if (req.method === 'PATCH' && req.url === '/api/v3/work_packages/1') {
          if (!converted) {
            if (body._links?.version?.href) {
              state.version = body._links.version.href;
              state.lockVersion += 1;
              res.statusCode = 200;
              res.end(JSON.stringify({ id: 1, lockVersion: state.lockVersion }));
              return;
            }
            res.statusCode = 422;
            res.end(JSON.stringify({ message: 'Expected singular version' }));
            return;
          }
          // Converted 17.8 mode (`targetVersions`)
          if (body._links?.version?.href) {
            if (autoAdaptLegacy) {
              state.targetVersions = [...approved];
              state.lockVersion += 1;
              res.statusCode = 200;
              res.end(JSON.stringify({ id: 1, lockVersion: state.lockVersion }));
              return;
            }
            res.statusCode = 422;
            res.end(JSON.stringify({ message: 'Property version was replaced by targetVersions' }));
            return;
          }
          if (Array.isArray(body._links?.targetVersions)) {
            const hrefs = body._links.targetVersions.map(x => x.href);
            if (rejectUnapprovedVersion && hrefs.includes(unapproved)) {
              res.statusCode = 422;
              res.end(JSON.stringify({ message: 'Version 99 closed' }));
              return;
            }
            state.targetVersions = hrefs;
            state.lockVersion += 1;
            res.statusCode = 200;
            res.end(JSON.stringify({ id: 1, lockVersion: state.lockVersion }));
            return;
          }
        }
        res.statusCode = 404;
        res.end(JSON.stringify({ message: 'not found' }));
      });
      await new Promise(done => server.listen(0, '127.0.0.1', done));
      const url = `http://127.0.0.1:${server.address().port}`;
      return {
        workPackageId: 1,
        approvedVersionHrefs: approved,
        unapprovedVersionHref: unapproved,
        request: async (_acct, method, path, body) => {
          const r = await fetch(url + path, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: body === undefined ? undefined : JSON.stringify(body),
          });
          return { status: r.status, body: await r.json() };
        },
        dispose: () => new Promise(done => server.close(done)),
      };
    };

    return {
      provisionControlCopy: () => startCopy({ converted: false }),
      provisionConvertedCopy: () => startCopy({ converted: true }),
    };
  };

  // 1. Clean 3/3 qualifying candidate
  const passRes = await screenOpenProject178TargetVersions(makeStandInFactory());
  assert.equal(passRes.qualifiesAsUpgradeDriftCandidate, true);
  assert.equal(passRes.counts.oldWorkflowFailedPostConversion, '3/3');
  assert.equal(passRes.counts.referenceWorkflowSavedExactSet, '3/3');
  assert.equal(passRes.counts.plausibleWrongWriteAcceptedByApp, '3/3');

  // 2. Old workflow adapts on its own -> ruled out!
  const adaptRes = await screenOpenProject178TargetVersions(makeStandInFactory({ autoAdaptLegacy: true }));
  assert.equal(adaptRes.qualifiesAsUpgradeDriftCandidate, false);
  assert.equal(adaptRes.candidateRuledOut, true);
  assert.match(adaptRes.reason, /old-workflow-adapts-on-its-own/);

  // 3. Server natively rejects wrong write -> ruled out (no client guard needed)!
  const noHazardRes = await screenOpenProject178TargetVersions(makeStandInFactory({ rejectUnapprovedVersion: true }));
  assert.equal(noHazardRes.qualifiesAsUpgradeDriftCandidate, false);
  assert.equal(noHazardRes.candidateRuledOut, true);
  assert.match(noHazardRes.reason, /server-natively-rejects-wrong-write/);

  // 4. 403 permission refusal -> recorded as not_testable, never counted as drift!
  const blockedRes = await screenOpenProject178TargetVersions(makeStandInFactory({ forbid403: true }));
  assert.equal(blockedRes.status, 'not_testable');
  assert.equal(blockedRes.qualifiesAsUpgradeDriftCandidate, false);

  return { ok: true };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await selftest();
  console.log('op178-target-versions-screen selftest ok (documented candidate; live 17.8 Docker not started; $0 spend)');
}
