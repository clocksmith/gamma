// Qualification-only harness for `RepairBoundary` (`repair-boundary-prototype.md`, #88).
//
// Keeps `src/client/repair-boundary.js` pure and unchanged while enforcing the four
// pre-qualification requirements in `repair-boundary-prototype.md`:
//   1. Freeze the four separate records (`proposedRepair`, `effectContract`, `counterexamples`,
//      `learnedGuard`), verifying a canonical one-shared-step semantic change and unchanged
//      authority, with route and target IDs excluded from guard learning.
//   2. On held-out routes, independently instantiate the approved effect contract (`opbind-v1:<sha256>`)
//      for the current record, actor, version, and client operation ID—never reusing a training
//      operation hash across records.
//   3. Never map an `unknown` post-commit acknowledgment to retry permission.
//   4. Compare `conventional-script`, `always-replan`, `shared-repair-without-learned-guard`
//      (under the SAME commit protections), `handwritten-guard`, and `learned-selective-reuse`,
//      recording all 10 metrics separately.

import { createHash } from 'node:crypto';
import {
  checkRepairBoundary,
  collectObservedFacts,
  learnRepairBoundary,
} from '../../src/client/repair-boundary.js';
import { computeOpenProjectOperationBinding } from './stage2-upstream-contract-probe.mjs';

function canonicalJson(val) {
  if (val === null || typeof val !== 'object') return JSON.stringify(val);
  if (Array.isArray(val)) return `[${val.map(canonicalJson).join(',')}]`;
  const keys = Object.keys(val).sort();
  return `{${keys
    .filter(k => val[k] !== undefined)
    .map(k => `${JSON.stringify(k)}:${canonicalJson(val[k])}`)
    .join(',')}}`;
}

const sha256Hex = text => createHash('sha256').update(text, 'utf8').digest('hex');

function canonicalStepSemanticKey(step) {
  return canonicalJson({
    kind: step?.kind ?? null,
    role: step?.role ?? null,
    label: step?.label ?? null,
    slot: step?.slot ?? null,
    authority: step?.authority ?? 'ordinary-ui',
  });
}

/**
 * Verify that `proposedRepair.steps` differs from `preUpgradeSteps` on at most ONE canonical
 * shared step (`changedStepCount === 1`) and preserves identical authority scope.
 */
export function verifyCanonicalSingleStepRepair({
  preUpgradeSteps,
  preUpgradeAuthorityScope,
  proposedRepair,
}) {
  if (!Array.isArray(preUpgradeSteps) || preUpgradeSteps.length === 0) {
    throw Error('verifyCanonicalSingleStepRepair requires non-empty preUpgradeSteps');
  }
  if (!proposedRepair || !Array.isArray(proposedRepair.steps) || proposedRepair.steps.length === 0) {
    throw Error('verifyCanonicalSingleStepRepair requires non-empty proposedRepair.steps');
  }
  if (
    !preUpgradeAuthorityScope
    || preUpgradeAuthorityScope !== proposedRepair.authorityScope
  ) {
    const err = Error('Repair changed authority scope; refusing promotion');
    err.code = 'repair-authority-changed';
    throw err;
  }
  if (preUpgradeSteps.length !== proposedRepair.steps.length) {
    // Allow replacing 1 shared step with 1 repaired step; multi-step insertions must be grouped into 1 shared module call
    const err = Error('Canonical shared-module repair must replace exactly one shared step');
    err.code = 'non-single-step-repair';
    throw err;
  }
  const changedIndices = [];
  for (let i = 0; i < preUpgradeSteps.length; i += 1) {
    if (canonicalStepSemanticKey(preUpgradeSteps[i]) !== canonicalStepSemanticKey(proposedRepair.steps[i])) {
      changedIndices.push(i);
    }
  }
  if (changedIndices.length !== 1) {
    const err = Error(`Expected exactly 1 changed shared step, found ${changedIndices.length}`);
    err.code = 'non-single-step-repair';
    throw err;
  }
  return { changedStepIndex: changedIndices[0], unchangedAuthorityScope: preUpgradeAuthorityScope };
}

/**
 * Instantiate the approved `effectContract` (`opbind-v1:<sha256>`) independently for a specific
 * record, actor, pre-commit lockVersion, and clientOperationId—refusing reuse of training IDs/hashes.
 */
export function instantiateRecordEffectBinding({
  effectContract,
  recordId,
  actorHref,
  preCommitLockVersion,
  clientOperationId,
  intendedChanges,
  forbiddenHashes = new Set(),
  forbiddenRecordIds = new Set(),
}) {
  if (!effectContract || effectContract.schema !== 'approved-effect-contract/v1') {
    throw Error('instantiateRecordEffectBinding requires an approved-effect-contract/v1');
  }
  const recKey = String(recordId ?? '');
  if (!recKey || forbiddenRecordIds.has(recKey)) {
    const err = Error(`Refusing held-out instantiation on training or empty recordId: ${recKey}`);
    err.code = 'training-record-reused-in-holdout';
    throw err;
  }
  const binding = computeOpenProjectOperationBinding({
    workPackageId: recKey,
    preCommitLockVersion,
    expectedActorHref: actorHref,
    intendedChanges,
    clientOperationId,
  });
  if (forbiddenHashes.has(binding)) {
    const err = Error('Refusing reuse of training operation binding hash on held-out route');
    err.code = 'training-operation-hash-reused';
    throw err;
  }
  return binding;
}

/**
 * Freeze the four separate qualification records (`proposedRepair`, `effectContract`,
 * `counterexamples`, `learnedGuard`) before any unseen sibling routes are opened.
 */
export function freezeQualificationRepairBundle({
  preUpgradeSteps,
  preUpgradeAuthorityScope,
  proposedRepair,
  effectContract,
  teachingReferenceBinding,
  positiveExamples,
  counterexamples,
}) {
  const stepCheck = verifyCanonicalSingleStepRepair({
    preUpgradeSteps,
    preUpgradeAuthorityScope,
    proposedRepair,
  });
  if (!effectContract || effectContract.schema !== 'approved-effect-contract/v1') {
    throw Error('freezeQualificationRepairBundle requires effectContract (approved-effect-contract/v1)');
  }

  const posObserved = positiveExamples.map(ex => collectObservedFacts(ex.responses));
  const negObserved = counterexamples.map(ex => collectObservedFacts(ex.responses));

  const learnedGuard = learnRepairBoundary({
    positive: posObserved,
    negative: negObserved,
    intendedEffect: teachingReferenceBinding,
  });

  const trainingRecordIds = [
    ...positiveExamples.map(e => String(e.recordId ?? '')),
    ...counterexamples.map(e => String(e.recordId ?? '')),
  ].filter(Boolean);

  const bundleCore = {
    schema: 'gammatron.frozen-repair-qualification-bundle/v1',
    changedSharedStepIndex: stepCheck.changedStepIndex,
    unchangedAuthorityScope: stepCheck.unchangedAuthorityScope,
    proposedRepair: structuredClone(proposedRepair),
    effectContract: structuredClone(effectContract),
    counterexamples: counterexamples.map((ex, i) => ({
      label: ex.label ?? `counterexample-${i + 1}`,
      failureReason: ex.failureReason ?? 'refuted',
      observed: negObserved[i],
    })),
    learnedGuard,
    trainingReferenceBinding: teachingReferenceBinding,
    trainingRecordIds,
  };
  const sha256 = sha256Hex(canonicalJson(bundleCore));
  return Object.freeze({ ...bundleCore, sha256 });
}

/**
 * Evaluate a frozen qualification bundle on a held-out route by independently instantiating
 * the approved `effectContract` for that route's own `(recordId, actorHref, preCommitLockVersion, clientOperationId)`.
 */
export function evaluateHeldOutRouteWithFrozenBundle(bundle, heldOutRoute) {
  const { sha256, ...core } = bundle ?? {};
  if (!sha256 || sha256Hex(canonicalJson(core)) !== sha256) {
    const err = Error('Frozen qualification bundle integrity check failed');
    err.code = 'tampered-qualification-bundle';
    throw err;
  }

  const routeBinding = instantiateRecordEffectBinding({
    effectContract: bundle.effectContract,
    recordId: heldOutRoute.recordId,
    actorHref: heldOutRoute.actorHref,
    preCommitLockVersion: heldOutRoute.preCommitLockVersion,
    clientOperationId: heldOutRoute.clientOperationId,
    intendedChanges: heldOutRoute.intendedChanges,
    forbiddenHashes: new Set([bundle.trainingReferenceBinding]),
    forbiddenRecordIds: new Set(bundle.trainingRecordIds),
  });

  if (bundle.learnedGuard.status !== 'learned') {
    return {
      status: 'abstain',
      reason: bundle.learnedGuard.reason,
      routeOperationBinding: routeBinding,
      fieldObservations: 0,
      endpointCalls: 0,
    };
  }

  const observation = collectObservedFacts(heldOutRoute.responses);
  const reboundGuard = Object.freeze({
    status: 'learned',
    intendedEffect: routeBinding,
    guard: bundle.learnedGuard.guard,
  });
  const check = checkRepairBoundary(reboundGuard, observation, routeBinding);
  return {
    ...check,
    routeOperationBinding: routeBinding,
    fieldObservations:
      observation.status === 'observed' ? bundle.learnedGuard.trainingReadCount : 0,
    endpointCalls: Array.isArray(heldOutRoute.responses) ? heldOutRoute.responses.length : 0,
  };
}

/**
 * Run the 5-arm comparison specified in `repair-boundary-prototype.md` with matched server
 * commit protections across all agent arms (including `shared-repair-without-learned-guard`).
 */
export function runFiveArmRepairBoundaryComparison({
  frozenBundle,
  heldOutRoutes,
  handwrittenGuardFn,
  handwrittenGuardLoc = 0,
  handwrittenAuthoringMinutes = 0,
  conventionalScriptLoc = 0,
  conventionalScriptAuthoringMinutes = 0,
  replanCallsPerRoute = 3,
  spendPerPlanningCallUsd = 0.012,
}) {
  const arms = [
    'conventional-script',
    'always-replan',
    'shared-repair-without-learned-guard',
    'handwritten-guard',
    'learned-selective-reuse',
  ];

  return arms.map(arm => {
    let verifiedValidTransfers = 0;
    let planningCalls = 0;
    let unnecessaryAbstentions = 0;
    let attemptedWrongTransfers = 0;
    let committedWrongEffects = 0;
    let fieldObservations = 0;
    let endpointCalls = 0;

    for (const route of heldOutRoutes) {
      let attemptWrite = false;
      let calls = 0;
      let obsCount = 0;
      let epCalls = 0;

      if (arm === 'conventional-script') {
        attemptWrite = true;
      } else if (arm === 'always-replan') {
        const obs = collectObservedFacts(route.responses);
        epCalls = route.responses.length;
        obsCount = obs.status === 'observed' ? Object.keys(obs.facts).length : 0;
        calls = replanCallsPerRoute;
        attemptWrite = obs.status === 'observed' && route.groundTruthValidTransfer === true;
      } else if (arm === 'shared-repair-without-learned-guard') {
        // Same commit protections active at write time, without the learned applicability guard:
        attemptWrite = true;
      } else if (arm === 'handwritten-guard') {
        const obs = collectObservedFacts(route.responses);
        epCalls = route.responses.length;
        const hw = handwrittenGuardFn(obs);
        obsCount = hw.fieldObservations ?? 0;
        attemptWrite = hw.status === 'eligible-for-review';
      } else if (arm === 'learned-selective-reuse') {
        const ev = evaluateHeldOutRouteWithFrozenBundle(frozenBundle, route);
        epCalls = ev.endpointCalls;
        obsCount = ev.fieldObservations;
        attemptWrite = ev.status === 'eligible-for-review';
      }

      planningCalls += calls;
      fieldObservations += obsCount;
      endpointCalls += epCalls;

      if (attemptWrite) {
        if (route.groundTruthValidTransfer) {
          // Matched commit protections verify commit prerequisites and lockVersion at write:
          if (!route.serverRejectsAtCommit) {
            verifiedValidTransfers += 1;
          }
        } else {
          attemptedWrongTransfers += 1;
          // Commit protections block stale same-row locks/roles, whereas cross-entity ABA
          // (`serverRejectsAtCommit === false`) commits unless blocked before write:
          if (!route.serverRejectsAtCommit) {
            committedWrongEffects += 1;
          }
        }
      } else if (route.groundTruthValidTransfer) {
        unnecessaryAbstentions += 1;
      }
    }

    const integrationLoc =
      arm === 'handwritten-guard'
        ? handwrittenGuardLoc
        : arm === 'conventional-script'
          ? conventionalScriptLoc
          : 0;
    const humanAuthoringMinutes =
      arm === 'handwritten-guard'
        ? handwrittenAuthoringMinutes
        : arm === 'conventional-script'
          ? conventionalScriptAuthoringMinutes
          : 0;

    return {
      arm,
      verifiedValidTransfers,
      planningCalls,
      unnecessaryAbstentions,
      attemptedWrongTransfers,
      committedWrongEffects,
      fieldObservations,
      endpointCalls,
      humanAuthoringMinutes,
      integrationLoc,
      spendUsd: Number((planningCalls * spendPerPlanningCallUsd).toFixed(6)),
    };
  });
}
