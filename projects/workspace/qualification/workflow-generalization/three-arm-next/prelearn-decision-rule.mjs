#!/usr/bin/env node
// $0 Pre-Learning Eligibility & Payback Decision Rule for Gammatron Rung 2 (#88).
//
// Predicts BEFORE spending model discovery or deployment budget which strategy in
// `{'always-replan', 'authored-guard', 'learned-repair-boundary'}` should be used
// for a workflow family at target volume `V` and authoring-time rate `r`:
//   1. Runs `learnRepairBoundary` on the projected contrast observations ($0).
//      If `status !== 'learned'` (`no-separating-guard`, `ambiguous-minimum`, etc.),
//      the learned guard abstains on 100% of cases (paying full `always-replan`
//      fallback on every route PLUS adapter setup), so it is strictly dominated at
//      every volume `V >= 0` (`learnedEligible: false`).
//   2. Audits raw GET response JSON across the contrast set for unprojected structural
//      variance (`array-of-objects` line items, multi-value HAL link arrays such as
//      OpenProject 17.8 `_links.targetVersions`, non-integer floats such as unit `rate`,
//      or non-empty free-text fields such as `description`/`terms`) that collapsed to
//      identical scalar facts. Rejects `learned-repair-boundary` when contrast negatives
//      differ in unprojected structure (`learnedEligible: false`).
//   3. Flags multi-role read plans that collapse to a single `equals-literal` predicate
//      (`underConstrainedSingleLiteral: true`) unless explicitly cleared by counterfactual
//      contrast checks.
//   4. Among safety-eligible arms, computes total cost `C(V; r) = C_fixed(r) + V * c_route`
//      at rates `0`, `r`, and `2r`, selecting the lowest-cost safe option and reporting
//      exact break-even workflow volumes `V*`.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { learnRepairBoundary } from '../../../src/client/repair-boundary.js';

const sha256 = s => createHash('sha256').update(s, 'utf8').digest('hex');

/**
 * Inspect raw GET JSON bodies from contrast examples to detect structural policy-bearing
 * fields (arrays of objects/links, floats, free text) that `collectObservedFacts` drops.
 */
export function auditRawResponseStructure(rawResponsesByExample) {
  const findings = new Set();
  const walk = (val, keyName = '', depth = 0) => {
    if (depth > 6 || val === null || val === undefined) return;
    if (Array.isArray(val)) {
      if (val.length > 0 && typeof val[0] === 'object') {
        findings.add(`array-of-objects:${keyName || 'root'}`);
      } else if (val.length > 1) {
        findings.add(`multi-value-array:${keyName || 'root'}`);
      }
      for (const item of val.slice(0, 8)) walk(item, keyName, depth + 1);
      return;
    }
    if (typeof val === 'number' && !Number.isInteger(val)) {
      findings.add(`non-integer-decimal:${keyName}`);
      return;
    }
    if (typeof val === 'string') {
      if (/(?:description|terms|note|comment|hold|embargo)/i.test(keyName) && val.trim().length > 0) {
        findings.add(`free-text-policy-field:${keyName}`);
      }
      return;
    }
    if (typeof val === 'object') {
      for (const [k, v] of Object.entries(val)) {
        if (k === '_links' && v && typeof v === 'object') {
          for (const [lk, lv] of Object.entries(v)) {
            if (Array.isArray(lv)) findings.add(`multi-value-hal-link:${lk}`);
          }
        }
        walk(v, k, depth + 1);
      }
    }
  };

  for (const ex of rawResponsesByExample ?? []) {
    for (const resp of ex ?? []) walk(resp?.body ?? resp);
  }
  return [...findings].sort();
}

export function evaluatePrelearnDecisionRule({
  intendedEffect,
  positiveObservations,
  negativeObservations,
  rawResponsesByExample = [],
  rolesReadCount = 1,
  allowSingleLiteralOnMultiRole = false,
  adapterMinutes = 0,
  guardMinutes = 0,
  learnedDiscoveryUsd = 0,
  guardDiscoveryUsd = 0,
  replanCostPerRouteUsd = 0.08,
  learnedValidAbstainRate = 0.0,
  guardValidAbstainRate = 0.0,
  invalidFraction = 0.5,
  ratePerMinuteUsd = 0.50,
  targetVolume = 200,
}) {
  const boundary = learnRepairBoundary({
    positive: positiveObservations,
    negative: negativeObservations,
    intendedEffect,
  });
  const structuralHazards = auditRawResponseStructure(rawResponsesByExample);
  const singleLiteralMultiRole = (
    boundary.status === 'learned'
    && rolesReadCount >= 2
    && boundary.guard.length === 1
    && boundary.guard[0].kind === 'equals-literal'
  );

  const disqualifyReasons = [];
  if (boundary.status !== 'learned') {
    disqualifyReasons.push(`boundary-not-learned:${boundary.reason}`);
  }
  if (structuralHazards.some(h => h.startsWith('multi-value-hal-link:') || h.startsWith('free-text-policy-field:'))) {
    disqualifyReasons.push(`unprojected-hazard:${structuralHazards.join(',')}`);
  }
  if (singleLiteralMultiRole && !allowSingleLiteralOnMultiRole) {
    disqualifyReasons.push(`under-constrained-single-literal:${boundary.guard[0].left}===${boundary.guard[0].value}`);
  }

  const learnedEligible = disqualifyReasons.length === 0;

  // Marginal per-route expected spend (assuming safe arms abstain on 100% of invalid routes
  // and `validAbstainRate` of valid routes, handing every abstention to `always-replan`):
  const validFrac = 1.0 - invalidFraction;
  const margReplan = replanCostPerRouteUsd;
  const margGuard = (invalidFraction + validFrac * guardValidAbstainRate) * replanCostPerRouteUsd;
  const margLearned = learnedEligible
    ? (invalidFraction + validFrac * learnedValidAbstainRate) * replanCostPerRouteUsd
    : replanCostPerRouteUsd;

  const evalAtRate = r => {
    const fixedReplan = 0;
    const fixedGuard = guardDiscoveryUsd + r * guardMinutes;
    const fixedLearned = learnedDiscoveryUsd + r * adapterMinutes;

    const costReplan = fixedReplan + targetVolume * margReplan;
    const costGuard = fixedGuard + targetVolume * margGuard;
    const costLearned = learnedEligible ? (fixedLearned + targetVolume * margLearned) : Infinity;

    const vStarGuardVsReplan = margReplan > margGuard ? fixedGuard / (margReplan - margGuard) : Infinity;
    const vStarLearnedVsReplan = (learnedEligible && margReplan > margLearned)
      ? fixedLearned / (margReplan - margLearned)
      : Infinity;

    let recommended = 'always-replan';
    let bestCost = costReplan;
    if (costGuard < bestCost) {
      recommended = 'authored-guard';
      bestCost = costGuard;
    }
    if (learnedEligible && costLearned < bestCost) {
      recommended = 'learned-repair-boundary';
      bestCost = costLearned;
    }

    return {
      ratePerMinuteUsd: Number(r.toFixed(4)),
      recommended,
      costAtTargetVolumeUsd: {
        'always-replan': Number(costReplan.toFixed(4)),
        'authored-guard': Number(costGuard.toFixed(4)),
        'learned-repair-boundary': learnedEligible ? Number(costLearned.toFixed(4)) : null,
      },
      breakEvenGuardVsReplanRoutes: Number.isFinite(vStarGuardVsReplan) ? Number(vStarGuardVsReplan.toFixed(2)) : null,
      breakEvenLearnedVsReplanRoutes: Number.isFinite(vStarLearnedVsReplan) ? Number(vStarLearnedVsReplan.toFixed(2)) : null,
    };
  };

  const atZero = evalAtRate(0);
  const atR = evalAtRate(ratePerMinuteUsd);
  const atDoubleR = evalAtRate(2 * ratePerMinuteUsd);

  return {
    schema: 'gammatron-prelearn-decision-rule/v1',
    learnedEligible,
    disqualifyReasons,
    structuralHazards,
    learnedBoundaryStatus: boundary.status,
    learnedGuard: boundary.status === 'learned' ? boundary.guard : null,
    targetVolume,
    byRate: { zero: atZero, r: atR, doubleR: atDoubleR },
    rateRobustChoice: (
      atZero.recommended === atR.recommended && atR.recommended === atDoubleR.recommended
        ? atR.recommended
        : 'rate-sensitive'
    ),
  };
}

export function selftest() {
  const eff = `opbind-v1:${sha256('prelearn-selftest')}`;
  const obs = facts => ({ status: 'observed', facts });

  // Case 1: OpenProject 17.8 multi-value `Target versions` -> rejected at $0 (`learnedEligible: false`),
  // picks `authored-guard` at V=200 and `always-replan` at V=10!
  const op178HighV = evaluatePrelearnDecisionRule({
    intendedEffect: eff,
    positiveObservations: [
      obs({ 'record:/v0': 10, 'record:/v1': 11, 'approval:/v0': 10, 'approval:/v1': 11, 'approval:/v2': 12 }),
      obs({ 'record:/v0': 11, 'record:/v1': 12, 'approval:/v0': 10, 'approval:/v1': 11, 'approval:/v2': 12 }),
    ],
    negativeObservations: [
      obs({ 'record:/v0': 10, 'record:/v1': 99, 'approval:/v0': 10, 'approval:/v1': 11, 'approval:/v2': 12 }),
    ],
    rawResponsesByExample: [[{ _links: { targetVersions: [{ href: '/v/10' }, { href: '/v/11' }] } }]],
    rolesReadCount: 2,
    adapterMinutes: 5,
    guardMinutes: 6,
    replanCostPerRouteUsd: 0.08,
    ratePerMinuteUsd: 0.50,
    targetVolume: 200,
  });
  assert.equal(op178HighV.learnedEligible, false);
  assert.equal(op178HighV.byRate.r.recommended, 'authored-guard');

  const op178LowV = evaluatePrelearnDecisionRule({
    intendedEffect: eff,
    positiveObservations: [obs({ 'record:/v0': 10 }), obs({ 'record:/v0': 11 })],
    negativeObservations: [obs({ 'record:/v0': 10 })],
    rolesReadCount: 2,
    adapterMinutes: 5,
    guardMinutes: 6,
    replanCostPerRouteUsd: 0.08,
    ratePerMinuteUsd: 0.50,
    targetVolume: 10,
  });
  assert.equal(op178LowV.learnedEligible, false);
  assert.equal(op178LowV.byRate.r.recommended, 'always-replan');

  // Case 2: Under-constrained 1-literal guard (`approval:/statusCode === 16`) on 2-role read plan -> rejected!
  const singleLit = evaluatePrelearnDecisionRule({
    intendedEffect: eff,
    positiveObservations: [
      obs({ 'record:/hours': 16, 'approval:/statusCode': 16, 'approval:/hours': 16 }),
      obs({ 'record:/hours': 24, 'approval:/statusCode': 16, 'approval:/hours': 24 }),
    ],
    negativeObservations: [
      obs({ 'record:/hours': 16, 'approval:/statusCode': 15, 'approval:/hours': 16 }),
    ],
    rolesReadCount: 2,
    adapterMinutes: 2,
    guardMinutes: 8,
    targetVolume: 300,
  });
  assert.equal(singleLit.learnedEligible, false);
  assert.ok(singleLit.disqualifyReasons.some(r => r.startsWith('under-constrained-single-literal:')));

  // Case 3: Clean multi-clause scalar equality with pre-existing reused adapter (`adapterMinutes: 0.5 < guardMinutes: 10`) -> `learned-repair-boundary` wins!
  const cleanScalar = evaluatePrelearnDecisionRule({
    intendedEffect: eff,
    positiveObservations: [
      obs({ 'record:/hours': 16, 'approval:/statusCode': 16, 'approval:/hours': 16 }),
      obs({ 'record:/hours': 24, 'approval:/statusCode': 16, 'approval:/hours': 24 }),
    ],
    negativeObservations: [
      obs({ 'record:/hours': 16, 'approval:/statusCode': 15, 'approval:/hours': 16 }),
      obs({ 'record:/hours': 24, 'approval:/statusCode': 16, 'approval:/hours': 8 }),
    ],
    rolesReadCount: 2,
    adapterMinutes: 0.5,
    guardMinutes: 10,
    learnedDiscoveryUsd: 0.05,
    guardDiscoveryUsd: 0.25,
    replanCostPerRouteUsd: 0.08,
    ratePerMinuteUsd: 0.50,
    targetVolume: 300,
  });
  assert.equal(cleanScalar.learnedEligible, true);
  assert.equal(cleanScalar.rateRobustChoice, 'learned-repair-boundary');
  return { ok: true };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  selftest();
  console.log('prelearn-decision-rule selftest ok ($0 spend)');
}
