#!/usr/bin/env node
// Target-Binding Completeness Gate & 4-Arm Pre-Deployment Selector v2 (`target-binding-soundness.mjs`).
//
// Identifies and closes a subtle structural soundness hazard in `relational-trace-guard.mjs`:
//   - Counterexample (Cross-Column Arithmetic / Unbound Write Target):
//     Suppose an order has `items = [{ qty: 20, rate: 100 }]` ($2,000) and `approval` has only a
//     scalar `budget_limit = 5000` (no `items` array on `approval`). If positive examples have
//     `budget_limit = 5000` ($2,000 and $4,000 <= $5,000) and a negative example has
//     `budget_limit = 3000` ($4,000 > $3,000), `learnRelationalTraceGuard` emits unary literals
//     `approval:/budget_limit === 5000 && approval:/status === "approved"` with ZERO predicates
//     referencing `intent` or `order`! On a test order of `60 x $100 = $6,000` under `budget_limit = 5000`,
//     that unbound guard commits a durable wrong write.
//   - Target-Binding Completeness (`verifyTargetBindingSoundness`):
//     Requires that a learned guard:
//       (1) contains >= 1 cross-role relational predicate linking a target role (`intent`, `record`,
//           `order`) to an authority role (`approval`, `quotation`, `policy`), and
//       (2) binds every non-constant/mutable payload path in `intent` (excluding static `doctype`)
//           via >= 1 cross-role predicate (`unbound-intent-field`).
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  checkRelationalTraceGuard,
  extractTypedTraceFacts,
  learnRelationalTraceGuard,
} from './relational-trace-guard.mjs';

const sha256 = s => createHash('sha256').update(s, 'utf8').digest('hex');
const roleOf = key => key.slice(0, key.indexOf(':'));

const DEFAULT_TARGET_ROLES = new Set(['intent', 'record', 'order']);
const DEFAULT_AUTH_ROLES = new Set(['approval', 'quotation', 'policy']);
const STATIC_INTENT_KEYS = new Set(['intent:/doctype']);

export function verifyTargetBindingSoundness(
  boundary,
  sampleObservation,
  {
    targetRoles = DEFAULT_TARGET_ROLES,
    authorityRoles = DEFAULT_AUTH_ROLES,
  } = {},
) {
  if (boundary?.status !== 'learned' || !Array.isArray(boundary.guard)) {
    return { sound: false, reasons: [boundary?.reason ?? 'boundary-not-learned'] };
  }

  const reasons = [];
  const crossPreds = boundary.guard.filter(p => p.right !== undefined);

  // Rule 1: At least one cross-role relational predicate must link a target role to an authority role.
  const linksTargetToAuth = crossPreds.some(p => {
    const rl = roleOf(p.left);
    const rr = roleOf(p.right);
    return (targetRoles.has(rl) && authorityRoles.has(rr))
      || (authorityRoles.has(rl) && targetRoles.has(rr));
  });
  if (!linksTargetToAuth) {
    reasons.push('unbound-target-to-authority');
  }

  // Rule 2: Every mutable `intent` field present in `sampleObservation` must be bound by >= 1 cross-role predicate.
  const intentPaths = Object.keys(sampleObservation?.facts ?? {}).filter(
    k => roleOf(k) === 'intent' && !STATIC_INTENT_KEYS.has(k),
  );
  for (const ip of intentPaths) {
    const isBound = crossPreds.some(p => p.left === ip || p.right === ip);
    if (!isBound) {
      reasons.push(`unbound-intent-field:${ip}`);
    }
  }

  // Rule 3: If `order` / `record` contains keyed child-table maps (`kmap`) and `intent` has no mutable fields,
  // at least one `kmap` on `order` / `record` must be bound across roles (catches `items` vs scalar `budget_limit`!).
  if (intentPaths.length === 0) {
    const targetKmaps = Object.entries(sampleObservation?.facts ?? {})
      .filter(([k, v]) => targetRoles.has(roleOf(k)) && v.type === 'kmap')
      .map(([k]) => k);
    if (targetKmaps.length > 0) {
      const anyKmapBound = targetKmaps.some(km => crossPreds.some(p => p.left === km || p.right === km));
      if (!anyKmapBound) {
        reasons.push(`unbound-target-kmap:${targetKmaps.join(',')}`);
      }
    }
  }

  return {
    sound: reasons.length === 0,
    reasons,
  };
}

/**
 * Sound wrapper around `learnRelationalTraceGuard` that enforces `verifyTargetBindingSoundness`.
 */
export function learnSoundRelationalTraceGuard({
  positive,
  negative,
  intendedEffect,
  inductionMode = 'lgg-closure',
} = {}) {
  const raw = learnRelationalTraceGuard({ positive, negative, intendedEffect, inductionMode });
  if (raw.status !== 'learned') return raw;
  const check = verifyTargetBindingSoundness(raw, positive[0]);
  if (!check.sound) {
    return Object.freeze({
      status: 'abstain',
      reason: check.reasons[0],
      allSoundnessReasons: Object.freeze(check.reasons),
      rejectedUnsoundGuard: raw.guard,
    });
  }
  return raw;
}

/**
 * Pre-deployment selector v2 over `{'always-replan', 'zero-adapter-relational-lgg', 'authored-expert-guard'}`.
 */
export function evaluatePrelearnSelectorV2({
  intendedEffect,
  positiveObservations,
  negativeObservations,
  expertGuardMinutes = 5.0,
  replanCostPerRouteUsd = 0.08,
  invalidFraction = 0.5,
  warmupConfirmations = 2,
  ratePerMinuteUsd = 0.50,
  targetVolume = 150,
}) {
  const learned = learnSoundRelationalTraceGuard({
    positive: positiveObservations,
    negative: negativeObservations,
    intendedEffect,
    inductionMode: 'lgg-closure',
  });
  const relationalEligible = learned.status === 'learned';

  const evalAtRate = r => {
    const costReplan = targetVolume * replanCostPerRouteUsd;
    const costExpert = (r * expertGuardMinutes) + (invalidFraction * targetVolume * replanCostPerRouteUsd);
    const warmupRoutes = Math.min((1 - invalidFraction) * targetVolume, warmupConfirmations);
    const costRelational = relationalEligible
      ? ((invalidFraction * targetVolume + warmupRoutes) * replanCostPerRouteUsd)
      : Infinity;

    let recommended = 'always-replan';
    let best = costReplan;
    if (costExpert < best) {
      recommended = 'authored-expert-guard';
      best = costExpert;
    }
    if (relationalEligible && costRelational <= best) {
      recommended = 'zero-adapter-relational-lgg';
      best = costRelational;
    }
    return {
      ratePerMinuteUsd: r,
      recommended,
      costsUsd: {
        'always-replan': Number(costReplan.toFixed(4)),
        'authored-expert-guard': Number(costExpert.toFixed(4)),
        'zero-adapter-relational-lgg': relationalEligible ? Number(costRelational.toFixed(4)) : null,
      },
    };
  };

  return {
    schema: 'gammatron-prelearn-selector/v2',
    relationalEligible,
    disqualifyReason: relationalEligible ? null : learned.reason,
    learnedGuard: relationalEligible ? learned.guard : null,
    byRate: {
      zero: evalAtRate(0),
      r: evalAtRate(ratePerMinuteUsd),
      doubleR: evalAtRate(2 * ratePerMinuteUsd),
    },
  };
}

export function selftest() {
  const getRow = (role, json) => ({ sameOrigin: true, method: 'GET', transport: 'fetch', status: 200, sourceRole: role, json });
  const eff = `opbind-v1:${sha256('soundness-selftest')}`;

  // 1. Constructive counterexample: Cross-column `sum(qty * rate) <= approval.budget_limit`!
  //    Verify raw `learnRelationalTraceGuard` learns an unsound unary literal (`budget_limit === 5000`)
  //    and commits a wrong write on `$6,000 > $5,000`, whereas `learnSoundRelationalTraceGuard` catches
  //    `unbound-target-to-authority` / `unbound-target-kmap` and abstains!
  const mkBudgetObs = (items, budgetLimit, status) => extractTypedTraceFacts([
    getRow('order', { data: { company: 'QualCorp', items } }),
    getRow('approval', { data: { company: 'QualCorp', budget_limit: budgetLimit, status } }),
  ], { doctype: 'Purchase Order' });

  const bPos = [
    mkBudgetObs([{ item_code: 'BOLT', qty: 20, rate: 100 }], 5000, 'approved'),
    mkBudgetObs([{ item_code: 'TURBINE', qty: 4, rate: 1000 }], 5000, 'approved'),
  ];
  const bNeg = [
    mkBudgetObs([{ item_code: 'TURBINE', qty: 4, rate: 1000 }], 3000, 'approved'),
    mkBudgetObs([{ item_code: 'BOLT', qty: 20, rate: 100 }], 5000, 'draft'),
  ];
  const overBudgetTest = mkBudgetObs([{ item_code: 'TURBINE', qty: 6, rate: 1000 }], 5000, 'approved'); // $6,000 > $5,000!

  const rawBudget = learnRelationalTraceGuard({ positive: bPos, negative: bNeg, intendedEffect: eff });
  assert.equal(rawBudget.status, 'learned');
  const rawOverVerdict = checkRelationalTraceGuard(rawBudget, overBudgetTest, eff);
  assert.equal(rawOverVerdict.status, 'eligible-for-review'); // Unchecked learner commits wrong write!

  const soundBudget = learnSoundRelationalTraceGuard({ positive: bPos, negative: bNeg, intendedEffect: eff });
  assert.equal(soundBudget.status, 'abstain');
  assert.match(soundBudget.reason, /unbound-target-kmap/);

  // Selector v2 rejects learned guard on budget arithmetic, choosing `authored-expert-guard` at V=200 and `always-replan` at V=10!
  const selHigh = evaluatePrelearnSelectorV2({ intendedEffect: eff, positiveObservations: bPos, negativeObservations: bNeg, targetVolume: 200 });
  assert.equal(selHigh.relationalEligible, false);
  assert.equal(selHigh.byRate.r.recommended, 'authored-expert-guard');

  const selLow = evaluatePrelearnSelectorV2({ intendedEffect: eff, positiveObservations: bPos, negativeObservations: bNeg, targetVolume: 10 });
  assert.equal(selLow.byRate.r.recommended, 'always-replan');

  // 2. Also verify `unbound-intent-field` catches `min-cover` under-constraint on NetBox 4.2 (`scope_type` dropped)!
  const mkNb42 = (sType, sId, aStatus, aType, aId) => extractTypedTraceFacts(
    [getRow('approval', { status: aStatus, scope_type: aType, scope_id: aId })],
    { scope_type: sType, scope_id: sId },
  );
  const nbPos = [mkNb42('dcim.site', 6, 'approved', 'dcim.site', 6), mkNb42('dcim.location', 12, 'approved', 'dcim.location', 12)];
  const nbNeg = [mkNb42('dcim.site', 6, 'pending', 'dcim.site', 6), mkNb42('dcim.site', 99, 'approved', 'dcim.site', 6)];
  const minCoverRaw = learnRelationalTraceGuard({ positive: nbPos, negative: nbNeg, intendedEffect: eff, inductionMode: 'min-cover' });
  assert.equal(minCoverRaw.status, 'learned');
  const minCoverSound = verifyTargetBindingSoundness(minCoverRaw, nbPos[0]);
  assert.equal(minCoverSound.sound, false);
  assert.ok(minCoverSound.reasons.includes('unbound-intent-field:intent:/scope_type'));

  // Whereas `lgg-closure` binds BOTH `scope_type` and `scope_id` and passes `verifyTargetBindingSoundness`!
  const lggSound = learnSoundRelationalTraceGuard({ positive: nbPos, negative: nbNeg, intendedEffect: eff, inductionMode: 'lgg-closure' });
  assert.equal(lggSound.status, 'learned');

  const selClean = evaluatePrelearnSelectorV2({ intendedEffect: eff, positiveObservations: nbPos, negativeObservations: nbNeg, targetVolume: 150 });
  assert.equal(selClean.relationalEligible, true);
  assert.equal(selClean.byRate.r.recommended, 'zero-adapter-relational-lgg');

  return { ok: true };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  selftest();
  console.log('target-binding-soundness & prelearn-selector-v2 selftest ok ($0 spend)');
}
