// Qualification-only harness & trusted same-origin observer for `RepairBoundary` (#88).
//
// Keeps `src/client/repair-boundary.js` exact to `0d1c4d6eb` while enforcing:
//   1. Four frozen separate records (`proposedRepair`, `effectContract`, `counterexamples`,
//      `learnedGuard`), canonical single-shared-step diff, and unchanged authority scope.
//   2. Strict separation between guard applicability ("this repair applies here") and
//      write authorization ("this write matches the approved effectContract"): even when
//      `learnedGuard` passes, any changed/extra/mismatched mutation field, method, or path
//      is rejected before write proposal (`verifyRequestedMutationAgainstEffectContract`).
//   3. Trusted same-origin Playwright `GET` (`fetch`/`xhr`) observer (`attachTrustedSameOriginReadObserver`)
//      feeding `collectObservedFacts` without pre-cooked boolean oracles.
//   4. Per-record `opbind-v1:<sha256>` instantiation (never reusing training record IDs or hashes)
//      and 5-arm comparison under matched server commit protections.

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
 * Mechanical HAL scalar projection for OpenProject v3 JSON payloads (`work_packages` & `activities`)
 * so `collectObservedFacts` receives safe integers and ISO-8601 durations without raw URLs, IDs,
 * free text, or task-specific boolean predicates.
 */
export function projectOpenProjectHalScalars(rawJson) {
  if (!rawJson || typeof rawJson !== 'object' || Array.isArray(rawJson)) return {};
  const out = {};
  if (Number.isSafeInteger(rawJson.lockVersion)) out.lockVersion = rawJson.lockVersion;
  if (typeof rawJson.estimatedTime === 'string') out.estimatedTime = rawJson.estimatedTime;
  const statusHref = rawJson?._links?.status?.href;
  if (typeof statusHref === 'string') {
    const m = statusHref.match(/\/api\/v3\/statuses\/(\d+)$/);
    if (m) out.statusCode = Number(m[1]);
  }
  const projectHref = rawJson?._links?.project?.href;
  if (typeof projectHref === 'string') {
    const pm = projectHref.match(/\/api\/v3\/projects\/(\d+)$/);
    if (pm) out.projectCode = Number(pm[1]);
  }
  const elements = rawJson?._embedded?.elements;
  if (Array.isArray(elements) && elements.length > 0) {
    out.entryCount = elements.length;
    const latest = elements[elements.length - 1];
    if (Number.isSafeInteger(latest?.version)) {
      out.latestVersion = latest.version;
    }
  }
  return out;
}

/**
 * Attach a passive, trusted same-origin `GET` (`fetch`/`xhr`) observer to a Playwright-compatible
 * `page` (`on('response', fn)` / `off('response', fn)`), mapping matched endpoints to stable
 * `sourceRole` names and feeding `collectObservedFacts` directly.
 */
export function attachTrustedSameOriginReadObserver(
  page,
  { allowedOrigin, roleMatchers, projectJson = null },
) {
  if (!page || typeof page.on !== 'function') {
    throw Error('attachTrustedSameOriginReadObserver requires a Playwright-compatible page');
  }
  const expectedOrigin = new URL(allowedOrigin).origin;
  const latestByRole = new Map();
  const pendingReads = new Set();
  let endpointCallCount = 0;

  const onResponse = response => {
    const p = (async () => {
      try {
        const req = response.request();
        const transport = req.resourceType();
        if (transport !== 'fetch' && transport !== 'xhr') return;
        if (req.method() !== 'GET') return;
        const parsedUrl = new URL(response.url());
        if (parsedUrl.origin !== expectedOrigin) return;
        endpointCallCount += 1;
        const status = response.status();
        if (status < 200 || status >= 300) return;
        const matched = roleMatchers.find(rule => rule.matches(parsedUrl.pathname, parsedUrl));
        if (!matched) return;
        const rawBody = await response.json();
        const json = projectJson ? projectJson(rawBody, matched.role) : rawBody;
        latestByRole.set(matched.role, {
          sameOrigin: true,
          method: 'GET',
          transport,
          status,
          sourceRole: matched.role,
          json,
        });
      } catch {
        // Ignore non-JSON or aborted responses; missing required roles trigger fail-closed abstention.
      }
    })();
    pendingReads.add(p);
    p.finally(() => pendingReads.delete(p));
  };

  page.on('response', onResponse);

  return {
    async snapshotObservedFacts() {
      await Promise.all([...pendingReads]);
      const responses = [...latestByRole.values()];
      return {
        responses,
        observed: collectObservedFacts(responses),
        endpointCalls: endpointCallCount,
      };
    },
    resetWindow() {
      latestByRole.clear();
      endpointCallCount = 0;
    },
    detach() {
      if (typeof page.off === 'function') page.off('response', onResponse);
      else if (typeof page.removeListener === 'function') page.removeListener('response', onResponse);
    },
  };
}

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
  if (!preUpgradeAuthorityScope || preUpgradeAuthorityScope !== proposedRepair.authorityScope) {
    const err = Error('Repair changed authority scope; refusing promotion');
    err.code = 'repair-authority-changed';
    throw err;
  }
  if (preUpgradeSteps.length !== proposedRepair.steps.length) {
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
 * Verify that a requested mutation (`method`, `path`, `intendedChanges`, and optional `wireBody`)
 * strictly matches what `effectContract` approved. A learned guard can only say "this repair
 * applies here"; ONLY `effectContract` authorizes which fields and values may be written.
 */
export function verifyRequestedMutationAgainstEffectContract({
  effectContract,
  recordId,
  preCommitLockVersion,
  requestedMutation,
  observedFacts = null,
  expectedOperationBinding = null,
}) {
  if (
    !effectContract
    || effectContract.schema !== 'approved-effect-contract/v1'
    || typeof effectContract.method !== 'string'
    || typeof effectContract.endpointTemplate !== 'string'
    || !Array.isArray(effectContract.allowedChangeKeys)
    || effectContract.allowedChangeKeys.length === 0
  ) {
    return { ok: false, reason: 'malformed-effect-contract' };
  }
  if (!requestedMutation || typeof requestedMutation !== 'object') {
    return { ok: false, reason: 'missing-requested-mutation' };
  }

  const expectedPath = effectContract.endpointTemplate.replace(
    '{recordId}',
    encodeURIComponent(String(recordId ?? '')),
  );
  if (requestedMutation.method !== effectContract.method || requestedMutation.path !== expectedPath) {
    return { ok: false, reason: 'unapproved-mutation-endpoint-or-method' };
  }

  const changes = requestedMutation.intendedChanges;
  if (!changes || typeof changes !== 'object' || Array.isArray(changes)) {
    return { ok: false, reason: 'missing-intended-changes' };
  }
  const changeKeys = Object.keys(changes);
  if (changeKeys.length === 0) {
    return { ok: false, reason: 'empty-intended-changes' };
  }

  const allowedSet = new Set(effectContract.allowedChangeKeys);
  for (const k of changeKeys) {
    if (!allowedSet.has(k)) {
      return { ok: false, reason: 'unapproved-mutation-field', field: k };
    }
  }

  const fixedChanges = effectContract.fixedChanges ?? {};
  for (const [k, approvedVal] of Object.entries(fixedChanges)) {
    if (!Object.hasOwn(changes, k) || changes[k] !== approvedVal) {
      return { ok: false, reason: 'changed-write-violates-approved-contract', field: k };
    }
  }

  const factBoundChanges = effectContract.factBoundChanges ?? {};
  for (const [k, factKey] of Object.entries(factBoundChanges)) {
    if (!Object.hasOwn(changes, k)) {
      return { ok: false, reason: 'missing-fact-bound-change-field', field: k };
    }
    if (!observedFacts || !Object.hasOwn(observedFacts, factKey)) {
      return { ok: false, reason: 'missing-authoritative-fact-for-write-check', field: k };
    }
    if (changes[k] !== observedFacts[factKey]) {
      return { ok: false, reason: 'changed-write-diverges-from-approved-terms', field: k };
    }
  }

  if (requestedMutation.wireBody !== undefined) {
    const wb = requestedMutation.wireBody;
    if (!wb || typeof wb !== 'object' || Array.isArray(wb)) {
      return { ok: false, reason: 'malformed-wire-body' };
    }
    if (wb.lockVersion !== preCommitLockVersion) {
      return { ok: false, reason: 'wire-lock-version-mismatch' };
    }
    if (
      expectedOperationBinding
      && !String(wb.journalNotes ?? '').includes(expectedOperationBinding)
    ) {
      return { ok: false, reason: 'wire-body-missing-operation-binding' };
    }
    const allowedWireTopKeys = new Set(['lockVersion', 'journalNotes']);
    if (Object.hasOwn(changes, 'subject')) {
      allowedWireTopKeys.add('subject');
      if (wb.subject !== changes.subject) return { ok: false, reason: 'wire-subject-mismatch' };
    }
    if (Object.hasOwn(changes, 'estimatedTime')) {
      allowedWireTopKeys.add('estimatedTime');
      if (wb.estimatedTime !== changes.estimatedTime) {
        return { ok: false, reason: 'wire-estimated-time-mismatch' };
      }
    }
    if (Object.hasOwn(changes, 'descriptionRaw')) {
      allowedWireTopKeys.add('description');
      if ((wb.description?.raw ?? null) !== changes.descriptionRaw) {
        return { ok: false, reason: 'wire-description-mismatch' };
      }
    }
    if (Object.hasOwn(changes, 'statusHref')) {
      allowedWireTopKeys.add('_links');
      const linkKeys = Object.keys(wb._links ?? {});
      if (
        linkKeys.some(lk => lk !== 'status')
        || (wb._links?.status?.href ?? null) !== changes.statusHref
      ) {
        return { ok: false, reason: 'wire-status-link-mismatch' };
      }
    }
    for (const wk of Object.keys(wb)) {
      if (!allowedWireTopKeys.has(wk)) {
        return { ok: false, reason: 'unapproved-wire-body-field', field: wk };
      }
    }
  }

  return { ok: true };
}

export function instantiateRecordEffectBinding({
  effectContract,
  recordId,
  actorHref,
  preCommitLockVersion,
  clientOperationId,
  requestedMutation,
  observedFacts = null,
  forbiddenHashes = new Set(),
  forbiddenRecordIds = new Set(),
}) {
  const recKey = String(recordId ?? '');
  if (!recKey || forbiddenRecordIds.has(recKey)) {
    const err = Error(`Refusing held-out instantiation on training or empty recordId: ${recKey}`);
    err.code = 'training-record-reused-in-holdout';
    throw err;
  }
  const contractCheck = verifyRequestedMutationAgainstEffectContract({
    effectContract,
    recordId: recKey,
    preCommitLockVersion,
    requestedMutation: { ...requestedMutation, wireBody: undefined },
    observedFacts,
  });
  if (!contractCheck.ok) {
    const err = Error(`Requested mutation rejected by effect contract: ${contractCheck.reason}`);
    err.code = 'effect-contract-violation';
    err.reason = contractCheck.reason;
    err.field = contractCheck.field ?? null;
    throw err;
  }

  const binding = computeOpenProjectOperationBinding({
    workPackageId: recKey,
    preCommitLockVersion,
    expectedActorHref: actorHref,
    intendedChanges: requestedMutation.intendedChanges,
    clientOperationId,
  });
  if (forbiddenHashes.has(binding)) {
    const err = Error('Refusing reuse of training operation binding hash on held-out route');
    err.code = 'training-operation-hash-reused';
    throw err;
  }
  if (requestedMutation.wireBody !== undefined) {
    const wireCheck = verifyRequestedMutationAgainstEffectContract({
      effectContract,
      recordId: recKey,
      preCommitLockVersion,
      requestedMutation,
      observedFacts,
      expectedOperationBinding: binding,
    });
    if (!wireCheck.ok) {
      const err = Error(`Requested wire body rejected by effect contract: ${wireCheck.reason}`);
      err.code = 'effect-contract-violation';
      err.reason = wireCheck.reason;
      throw err;
    }
  }
  return binding;
}

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
  if (
    !effectContract
    || effectContract.schema !== 'approved-effect-contract/v1'
    || !Array.isArray(effectContract.allowedChangeKeys)
    || effectContract.allowedChangeKeys.length === 0
  ) {
    throw Error('freezeQualificationRepairBundle requires a complete approved-effect-contract/v1');
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

export function evaluateHeldOutRouteWithFrozenBundle(bundle, heldOutRoute) {
  const { sha256, ...core } = bundle ?? {};
  if (!sha256 || sha256Hex(canonicalJson(core)) !== sha256) {
    const err = Error('Frozen qualification bundle integrity check failed');
    err.code = 'tampered-qualification-bundle';
    throw err;
  }

  const observation = collectObservedFacts(heldOutRoute.responses);
  const endpointCalls = Array.isArray(heldOutRoute.responses) ? heldOutRoute.responses.length : 0;

  // Enforce the approved effect contract FIRST and INDEPENDENTLY of the learned guard:
  // even when `learnedGuard` would pass, a changed/unapproved write is rejected here.
  let routeBinding;
  try {
    routeBinding = instantiateRecordEffectBinding({
      effectContract: bundle.effectContract,
      recordId: heldOutRoute.recordId,
      actorHref: heldOutRoute.actorHref,
      preCommitLockVersion: heldOutRoute.preCommitLockVersion,
      clientOperationId: heldOutRoute.clientOperationId,
      requestedMutation: heldOutRoute.requestedMutation,
      observedFacts: observation.status === 'observed' ? observation.facts : null,
      forbiddenHashes: new Set([bundle.trainingReferenceBinding]),
      forbiddenRecordIds: new Set(bundle.trainingRecordIds),
    });
  } catch (err) {
    if (err?.code === 'effect-contract-violation') {
      return {
        status: 'abstain',
        reason: err.reason,
        rejectedByEffectContract: true,
        routeOperationBinding: null,
        fieldObservations: observation.status === 'observed' ? Object.keys(observation.facts).length : 0,
        endpointCalls,
      };
    }
    throw err;
  }

  if (bundle.learnedGuard.status !== 'learned') {
    return {
      status: 'abstain',
      reason: bundle.learnedGuard.reason,
      rejectedByEffectContract: false,
      routeOperationBinding: routeBinding,
      fieldObservations: 0,
      endpointCalls,
    };
  }

  const reboundGuard = Object.freeze({
    status: 'learned',
    intendedEffect: routeBinding,
    guard: bundle.learnedGuard.guard,
  });
  const check = checkRepairBoundary(reboundGuard, observation, routeBinding);
  return {
    ...check,
    rejectedByEffectContract: false,
    routeOperationBinding: routeBinding,
    fieldObservations:
      observation.status === 'observed' ? bundle.learnedGuard.trainingReadCount : 0,
    endpointCalls,
  };
}

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

      const obs = collectObservedFacts(route.responses);
      const contractCheck = verifyRequestedMutationAgainstEffectContract({
        effectContract: frozenBundle.effectContract,
        recordId: route.recordId,
        preCommitLockVersion: route.preCommitLockVersion,
        requestedMutation: route.requestedMutation,
        observedFacts: obs.status === 'observed' ? obs.facts : null,
      });

      if (arm === 'conventional-script') {
        attemptWrite = true;
      } else if (arm === 'always-replan') {
        epCalls = route.responses.length;
        obsCount = obs.status === 'observed' ? Object.keys(obs.facts).length : 0;
        calls = replanCallsPerRoute;
        attemptWrite = obs.status === 'observed' && contractCheck.ok && route.groundTruthValidTransfer === true;
      } else if (arm === 'shared-repair-without-learned-guard') {
        // Same approved-effect & commit protections active, without the learned applicability guard:
        attemptWrite = contractCheck.ok;
      } else if (arm === 'handwritten-guard') {
        epCalls = route.responses.length;
        const hw = handwrittenGuardFn(obs);
        obsCount = hw.fieldObservations ?? 0;
        attemptWrite = contractCheck.ok && hw.status === 'eligible-for-review';
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
        if (route.groundTruthValidTransfer && contractCheck.ok) {
          if (!route.serverRejectsAtCommit) {
            verifiedValidTransfers += 1;
          }
        } else {
          attemptedWrongTransfers += 1;
          if (!route.serverRejectsAtCommit) {
            committedWrongEffects += 1;
          }
        }
      } else if (route.groundTruthValidTransfer && contractCheck.ok) {
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
