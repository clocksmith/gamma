// Stage 1 (#85 / #88): Suffix eligibility over active downstream footprints R_u,
// live post-condition valuation nu(o, inputs), dirty-<form>-field safety guard,
// L*-style counterexample footprint refinement, typed slot roles, and read-only landmarks.
// Pure analysis and verification helper; WorkspaceService remains sole dispatch authority.

import { structuralLocator } from '../adapters/page-query.js';
import { canonicalJson } from '../journal.js';

const HASH = /^[a-f0-9]{64}$/;
const VALUE_TAGS = new Set(['input', 'select', 'textarea']);
const NON_VALUE_INPUT_TYPES = new Set(['submit', 'button', 'reset', 'image']);

export function normalizeRoutePattern(rawUrl) {
  const parsed = new URL(rawUrl);
  const parts = parsed.pathname.split('/').map(segment => {
    if (!segment) return '';
    if (/^\d+$/.test(segment)) return ':int';
    if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(segment)) return ':uuid';
    if (/^[A-Z]{2,6}-\d{2,}$/.test(segment)) return ':code';
    return segment;
  });
  return {
    origin: parsed.origin,
    routePattern: parts.join('/') || '/',
  };
}

export function isActionableElement(element) {
  if (!element) return false;
  if (!element.actionability) return true;
  return Boolean(
    element.actionability.visible
    && !element.actionability.inert
    && !element.actionability.disabled,
  );
}

function defaultAttributeValue(element) {
  if (!Array.isArray(element.attributes)) return '';
  const attr = element.attributes.find(([name]) => name === 'value');
  return attr ? String(attr[1] ?? '') : '';
}

function isValueBearingControl(element) {
  const tag = (element.tag ?? '').toLowerCase();
  const role = (element.role ?? '').toLowerCase();
  const inputType = (element.inputType ?? '').toLowerCase();
  if (tag === 'button' || tag === 'a' || role === 'button' || role === 'link') return false;
  if (tag === 'input' && NON_VALUE_INPUT_TYPES.has(inputType)) return false;
  if (VALUE_TAGS.has(tag)) return true;
  return ['textbox', 'searchbox', 'combobox', 'listbox', 'checkbox', 'radio', 'switch', 'spinbutton', 'slider'].includes(role);
}

/**
 * Guardrail 2: An untracked field in the committing <form> is safe ONLY if it is
 * empty, at its HTML default value, or explicitly whitelisted inert by host policy.
 */
export function isCleanOrWhitelistedFormControl(element, whitelistedLocators = new Set()) {
  const locKey = canonicalJson(structuralLocator(element));
  if (whitelistedLocators.has(locKey)) return true;
  if (typeof element.isDefaultValue === 'boolean') {
    return element.isDefaultValue;
  }
  const val = element.value;
  if (val === null || val === undefined || val === '') return true;
  return String(val) === defaultAttributeValue(element);
}

/**
 * Resolve input bindings across exact slot names and explicit host-declared typed slot roles.
 * Refuses ambiguous role bindings when >=2 inputs share the same role without an exact slot match.
 */
export function resolveRoleBoundInputs({ inputs = {}, slotRoles = null, learnedSlotRoles = new Map(), hashFn }) {
  const directMap = new Map();
  const roleCandidates = new Map();
  for (const [slotName, value] of Object.entries(inputs)) {
    if (typeof value !== 'string') continue;
    const slotHash = hashFn(['slot', slotName]);
    directMap.set(slotHash, { slotName, value, via: 'exact-slot' });
    const role = slotRoles?.[slotName];
    if (typeof role === 'string' && role.trim()) {
      const list = roleCandidates.get(role) ?? [];
      list.push({ slotName, slotHash, value });
      roleCandidates.set(role, list);
    }
  }
  const bound = new Map(directMap);
  const ambiguousRoles = new Set();
  for (const [learnedSlotHash, role] of learnedSlotRoles.entries()) {
    if (bound.has(learnedSlotHash)) continue;
    const matches = roleCandidates.get(role) ?? [];
    if (matches.length === 1) {
      bound.set(learnedSlotHash, {
        slotName: matches[0].slotName,
        value: matches[0].value,
        via: `role:${role}`,
      });
    } else if (matches.length > 1) {
      ambiguousRoles.add(role);
    }
  }
  return { bound, ambiguousRoles };
}

function collectDownstreamStepHashes(startId, nodes, targetTerminalSet = null) {
  const stepLocatorHashes = new Set();
  const requiredSlotHashes = new Set();
  const visited = new Set();
  const queue = [startId];
  while (queue.length > 0) {
    const id = queue.shift();
    if (visited.has(id)) continue;
    visited.add(id);
    const node = nodes.get(id);
    if (!node) continue;
    if (targetTerminalSet ? targetTerminalSet.has(id) : node.terminal) continue;
    for (const edge of node.edges ?? []) {
      stepLocatorHashes.add(edge.step.locator);
      if (edge.step.slot) requiredSlotHashes.add(edge.step.slot);
      if (!visited.has(edge.next)) queue.push(edge.next);
    }
  }
  return { stepLocatorHashes, requiredSlotHashes };
}

export function validateSuffixProfiles(rawProfiles, nodes) {
  const out = new Map();
  if (rawProfiles === undefined) return out;
  if (!Array.isArray(rawProfiles)) throw Error('Invalid trace suffixProfiles');
  for (const entry of rawProfiles) {
    if (!Array.isArray(entry) || entry.length !== 2) throw Error('Invalid trace suffixProfiles entry');
    const [nodeId, profile] = entry;
    if (!HASH.test(nodeId) || out.has(nodeId) || !profile || typeof profile !== 'object' || Array.isArray(profile)) {
      throw Error('Invalid trace suffixProfile node');
    }
    if (!nodes.has(nodeId)) continue;
    if (typeof profile.origin !== 'string' || !profile.origin
      || typeof profile.routePattern !== 'string' || !profile.routePattern
      || !Array.isArray(profile.locatorTable)
      || !Array.isArray(profile.requiredSlots) || profile.requiredSlots.some(s => !HASH.test(s))
      || !Number.isSafeInteger(profile.sameOutlineClicks) || profile.sameOutlineClicks < 0
      || typeof profile.requiresExactPrefix !== 'boolean') {
      throw Error('Invalid trace suffixProfile fields');
    }
    out.set(nodeId, structuredClone(profile));
  }
  return out;
}

export function mergeSuffixProfiles(leftMap, rightMap, nodes) {
  const merged = new Map();
  for (const [id, prof] of leftMap.entries()) {
    if (nodes.has(id)) merged.set(id, structuredClone(prof));
  }
  for (const [id, incoming] of rightMap.entries()) {
    if (!nodes.has(id)) continue;
    const prev = merged.get(id);
    if (!prev) {
      merged.set(id, structuredClone(incoming));
      continue;
    }
    const tableMap = new Map([
      ...(prev.locatorTable ?? []),
      ...(incoming.locatorTable ?? []),
    ]);
    const guardMap = new Map([
      ...(prev.extraGuards ?? []).map(g => [canonicalJson(g.locator), g]),
      ...(incoming.extraGuards ?? []).map(g => [canonicalJson(g.locator), g]),
    ]);
    merged.set(id, {
      origin: prev.origin,
      routePattern: prev.routePattern,
      locatorTable: [...tableMap.entries()].sort(([a], [b]) => a.localeCompare(b)),
      slotLocators: [...new Map([...(prev.slotLocators ?? []), ...(incoming.slotLocators ?? [])]).entries()]
        .sort(([a], [b]) => a.localeCompare(b)),
      requiredSlots: [...new Set([...prev.requiredSlots, ...incoming.requiredSlots])].sort(),
      sameOutlineClicks: Math.max(prev.sameOutlineClicks, incoming.sameOutlineClicks),
      referenceControls: prev.referenceControls ?? incoming.referenceControls ?? [],
      extraGuards: [...guardMap.values()],
      requiresExactPrefix: Boolean(prev.requiresExactPrefix || incoming.requiresExactPrefix),
    });
  }
  return new Map([...merged.entries()].sort(([a], [b]) => a.localeCompare(b)));
}

/**
 * Evaluate suffix eligibility on a cache miss (`!dag.nodes.has(before.id)`).
 * Returns { eligible: true, nodeId, profile, diagnostics } ONLY if all prerequisite,
 * active-footprint, live slot valuation nu(o, inputs), and dirty-<form>-field guards pass.
 */
export function evaluateSuffixEligibility({
  dag,
  dp,
  observation,
  boundInputs,
  ambiguousRoles = new Set(),
  targetGoalHash = null,
  sameOutlineClicks = 0,
  inertFormLocators = [],
}) {
  const rejections = [];
  if (observation?.isTruncated !== false || !Array.isArray(observation?.elements)) {
    return { eligible: false, reason: 'incomplete-observation', rejections };
  }
  const { origin, routePattern } = normalizeRoutePattern(observation.url);
  const inertSet = new Set(inertFormLocators.map(loc => canonicalJson(loc)));
  const actionableElements = observation.elements.filter(isActionableElement);
  const targetTerminals = targetGoalHash !== null
    ? new Set(dag.goalTerminals.get(targetGoalHash) ?? [])
    : null;

  const candidates = [];
  for (const [nodeId, profile] of dag.suffixProfiles.entries()) {
    const node = dag.nodes.get(nodeId);
    if (!node) continue;
    const decision = dp.policy.get(nodeId);
    const cost = dp.values.get(nodeId) ?? Infinity;
    if (!decision || !Number.isFinite(cost)) continue;
    if (decision.kind !== 'step' && decision.kind !== 'terminal') continue;
    // Do not jump straight to a zero-step terminal leaf on a suffix miss: terminals require exact verification.
    if (decision.kind === 'terminal') continue;

    if (profile.origin !== origin || profile.routePattern !== routePattern) {
      continue;
    }
    if (profile.requiresExactPrefix) {
      rejections.push({ nodeId, reason: 'demoted-to-exact-prefix-by-hidden-state' });
      continue;
    }
    if (sameOutlineClicks < profile.sameOutlineClicks) {
      rejections.push({ nodeId, reason: 'missing-prerequisite-approval-click' });
      continue;
    }

    const locatorByHash = new Map(profile.locatorTable ?? []);
    const slotLocatorByHash = new Map(profile.slotLocators ?? []);
    const { stepLocatorHashes, requiredSlotHashes } = collectDownstreamStepHashes(nodeId, dag.nodes, targetTerminals);

    // Check role ambiguity on any downstream required slot.
    let roleConflict = false;
    for (const slotHash of requiredSlotHashes) {
      const role = dag.slotRoles.get(slotHash);
      if (role && ambiguousRoles.has(role) && !boundInputs.has(slotHash)) {
        roleConflict = true;
        break;
      }
      if (!boundInputs.has(slotHash)) {
        roleConflict = true;
        break;
      }
    }
    if (roleConflict) {
      rejections.push({ nodeId, reason: 'missing-or-ambiguous-slot-binding' });
      continue;
    }

    // Verify live post-condition valuation nu(o, inputs) for required upstream same-screen slots!
    let prereqFailed = false;
    const satisfiedPrereqSelectors = new Set();
    for (const reqSlotHash of profile.requiredSlots) {
      const expected = boundInputs.get(reqSlotHash);
      const reqLoc = slotLocatorByHash.get(reqSlotHash);
      if (!expected) {
        prereqFailed = true;
        break;
      }
      if (reqLoc) {
        const matches = actionableElements.filter(el => canonicalJson(structuralLocator(el)) === canonicalJson(reqLoc));
        if (matches.length !== 1 || String(matches[0].value ?? '') !== expected.value) {
          prereqFailed = true;
          break;
        }
        satisfiedPrereqSelectors.add(matches[0].selector);
      }
    }
    if (prereqFailed) {
      rejections.push({ nodeId, reason: 'unsatisfied-live-slot-valuation' });
      continue;
    }

    // Active downstream footprint R_u check: every immediate and same-screen footprint locator must resolve uniquely.
    const immediateStepHash = decision.step.locator;
    const immediateMatches = actionableElements.filter(
      el => dag.hash(['locator', structuralLocator(el)]) === immediateStepHash,
    );
    if (immediateMatches.length !== 1) {
      rejections.push({
        nodeId,
        reason: immediateMatches.length === 0 ? 'missing-footprint-locator' : 'ambiguous-footprint-locator',
      });
      continue;
    }

    // Check all same-screen R_u locators present in profile.onScreenStepLocators + L* extraGuards.
    const matchedFootprintSelectors = new Set([immediateMatches[0].selector]);
    const touchedFormKeys = new Set();
    if (immediateMatches[0].formKey) touchedFormKeys.add(immediateMatches[0].formKey);

    let footprintFailed = null;
    for (const locHash of profile.onScreenStepLocators ?? [immediateStepHash]) {
      if (!stepLocatorHashes.has(locHash)) continue;
      const locTuple = locatorByHash.get(locHash);
      const matches = locTuple
        ? actionableElements.filter(el => canonicalJson(structuralLocator(el)) === canonicalJson(locTuple))
        : actionableElements.filter(el => dag.hash(['locator', structuralLocator(el)]) === locHash);
      if (matches.length !== 1) {
        footprintFailed = matches.length === 0 ? 'missing-footprint-locator' : 'ambiguous-footprint-locator';
        break;
      }
      matchedFootprintSelectors.add(matches[0].selector);
      if (matches[0].formKey) touchedFormKeys.add(matches[0].formKey);
    }
    if (!footprintFailed) {
      for (const guard of profile.extraGuards ?? []) {
        const matches = observation.elements.filter(
          el => canonicalJson(structuralLocator(el)) === canonicalJson(guard.locator),
        );
        if (guard.mustBeAbsent) {
          if (matches.length > 0) { footprintFailed = 'lstar-guard-refuted'; break; }
        } else {
          if (matches.length !== 1) { footprintFailed = 'lstar-guard-refuted'; break; }
          if (guard.expectedValue !== undefined && String(matches[0].value ?? '') !== guard.expectedValue) {
            footprintFailed = 'lstar-guard-refuted';
            break;
          }
          if (guard.expectedText !== undefined && String(matches[0].text ?? '') !== guard.expectedText) {
            footprintFailed = 'lstar-guard-refuted';
            break;
          }
          matchedFootprintSelectors.add(matches[0].selector);
        }
      }
    }
    if (footprintFailed) {
      rejections.push({ nodeId, reason: footprintFailed });
      continue;
    }

    // Guardrail 2: Dirty-extra-<form>-field safety guard!
    // Every value-bearing control inside the committing <form> (or on the screen when formKey is absent)
    // that is NOT in R_u and NOT a verified prerequisite slot MUST be empty, default, or whitelisted inert.
    let dirtyField = null;
    for (const el of observation.elements) {
      if (!isValueBearingControl(el)) continue;
      if (matchedFootprintSelectors.has(el.selector) || satisfiedPrereqSelectors.has(el.selector)) continue;
      const inCommittingForm = touchedFormKeys.size > 0
        ? (el.formKey !== undefined ? touchedFormKeys.has(el.formKey) : true)
        : true;
      if (!inCommittingForm) continue;
      if (!isCleanOrWhitelistedFormControl(el, inertSet)) {
        dirtyField = structuralLocator(el);
        break;
      }
    }
    if (dirtyField) {
      rejections.push({ nodeId, reason: 'dirty-untracked-form-field', dirtyField });
      continue;
    }

    candidates.push({
      nodeId,
      profile,
      cost,
      satisfiedPrereqCount: profile.requiredSlots.length,
      sameOutlineClicks: profile.sameOutlineClicks,
    });
  }

  if (candidates.length === 0) {
    return {
      eligible: false,
      reason: rejections[0]?.reason ?? 'no-matching-suffix',
      rejections,
    };
  }

  // Same-Route Prerequisite Non-Skip Invariant (#85):
  // Never greedily pick a deeper suffix `v` on the same route if an eligible upstream node `u`
  // reaches `v` on the same route and `u`'s immediate step (an approval click still visible on `o`,
  // or a field write not yet holding its target input value) has NOT yet been executed!
  const candidateById = new Map(candidates.map(c => [c.nodeId, c]));
  const isReachableSameRoute = (startId, targetId) => {
    const startProf = dag.suffixProfiles.get(startId);
    const seen = new Set([startId]);
    const queue = [startId];
    while (queue.length > 0) {
      const cur = queue.shift();
      const node = dag.nodes.get(cur);
      for (const edge of node?.edges ?? []) {
        if (edge.next === targetId) return true;
        const nextProf = dag.suffixProfiles.get(edge.next);
        if (!seen.has(edge.next)
          && nextProf
          && nextProf.origin === startProf?.origin
          && nextProf.routePattern === startProf?.routePattern) {
          seen.add(edge.next);
          queue.push(edge.next);
        }
      }
    }
    return false;
  };
  const isImmediateStepPendingOnPage = (nodeId, ancProf) => {
    const step = dp.policy.get(nodeId)?.step;
    if (!step) return false;
    if (step.kind === 'click') {
      return sameOutlineClicks <= (ancProf?.sameOutlineClicks ?? 0)
        && actionableElements.some(el => dag.hash(['locator', structuralLocator(el)]) === step.locator);
    }
    const expected = boundInputs.get(step.slot)?.value;
    const match = actionableElements.find(el => dag.hash(['locator', structuralLocator(el)]) === step.locator);
    return !match || String(match.value ?? '') !== expected;
  };

  const unblockedCandidates = candidates.filter(cand => {
    for (const [ancId, ancProf] of dag.suffixProfiles.entries()) {
      if (ancId === cand.nodeId) continue;
      if (ancProf.origin !== origin || ancProf.routePattern !== routePattern) continue;
      if (!Number.isFinite(dp.values.get(ancId) ?? Infinity)) continue;
      if (isReachableSameRoute(ancId, cand.nodeId) && isImmediateStepPendingOnPage(ancId, ancProf)) {
        rejections.push({ nodeId: cand.nodeId, reason: 'prerequisite-step-still-pending', blockedBy: ancId });
        return false;
      }
    }
    return true;
  });
  void candidateById;

  if (unblockedCandidates.length === 0) {
    return {
      eligible: false,
      reason: rejections.at(-1)?.reason ?? 'no-matching-suffix',
      rejections,
    };
  }

  unblockedCandidates.sort((a, b) => {
    if (b.satisfiedPrereqCount !== a.satisfiedPrereqCount) return b.satisfiedPrereqCount - a.satisfiedPrereqCount;
    if (b.sameOutlineClicks !== a.sameOutlineClicks) return b.sameOutlineClicks - a.sameOutlineClicks;
    if (Math.abs(a.cost - b.cost) > 1e-9) return a.cost - b.cost;
    return a.nodeId.localeCompare(b.nodeId);
  });

  if (unblockedCandidates.length > 1) {
    const top = unblockedCandidates[0];
    const runnerUp = unblockedCandidates[1];
    const topStep = canonicalJson(dp.policy.get(top.nodeId)?.step);
    const runnerStep = canonicalJson(dp.policy.get(runnerUp.nodeId)?.step);
    if (top.satisfiedPrereqCount === runnerUp.satisfiedPrereqCount
      && top.sameOutlineClicks === runnerUp.sameOutlineClicks
      && Math.abs(top.cost - runnerUp.cost) <= 1e-9
      && topStep !== runnerStep) {
      return {
        eligible: false,
        reason: 'ambiguous-suffix-candidate',
        rejections,
      };
    }
  }

  return {
    eligible: true,
    nodeId: unblockedCandidates[0].nodeId,
    profile: unblockedCandidates[0].profile,
    cost: unblockedCandidates[0].cost,
    rejections,
  };
}

/**
 * L*-style counterexample footprint refinement:
 * When a suffix-rejoined run fails a post-condition or fails verifyReview(), compare the
 * teaching reference controls at nodeId against the failing observation. If a visible control
 * or value/text distinguishes them, refine R_u <- R_u U {guard}; if zero visible DOM differences
 * exist (pure hidden server-side state drift), demote nodeId to requiresExactPrefix = true.
 */
export function refineSuffixProfileOnCounterexample(dag, nodeId, failingObservation) {
  const profile = dag.suffixProfiles.get(nodeId);
  if (!profile) return { action: 'none' };
  // Collect nodeId plus any same-route downstream nodes so a route-level counterexample refines the whole segment.
  const segmentIds = [nodeId];
  const seen = new Set([nodeId]);
  for (let i = 0; i < segmentIds.length; i++) {
    const cur = dag.nodes.get(segmentIds[i]);
    for (const edge of cur?.edges ?? []) {
      const nextProf = dag.suffixProfiles.get(edge.next);
      if (!seen.has(edge.next)
        && nextProf
        && nextProf.origin === profile.origin
        && nextProf.routePattern === profile.routePattern) {
        seen.add(edge.next);
        segmentIds.push(edge.next);
      }
    }
  }
  const applyGuardToSegment = guard => {
    for (const id of segmentIds) {
      const p = dag.suffixProfiles.get(id);
      if (!p) continue;
      const keys = new Set((p.extraGuards ?? []).map(g => canonicalJson(g.locator)));
      if (!keys.has(canonicalJson(guard.locator))) {
        p.extraGuards = [...(p.extraGuards ?? []), structuredClone(guard)];
      }
    }
  };

  const refControls = profile.referenceControls ?? [];
  const failControls = (failingObservation?.elements ?? []).map(el => ({
    locator: structuralLocator(el),
    value: el.value ?? null,
    text: el.text ?? '',
  }));

  const refByLoc = new Map(refControls.map(c => [canonicalJson(c.locator), c]));
  const failByLoc = new Map(failControls.map(c => [canonicalJson(c.locator), c]));
  const existingGuardKeys = new Set((profile.extraGuards ?? []).map(g => canonicalJson(g.locator)));

  // 1. Control present in reference teaching observation that is missing or changed in failing observation.
  for (const [key, ref] of refByLoc.entries()) {
    if (existingGuardKeys.has(key)) continue;
    const fail = failByLoc.get(key);
    if (!fail) {
      applyGuardToSegment({ locator: ref.locator, expectedText: ref.text });
      return { action: 'lstar-added-missing-control-guard', locator: ref.locator, refinedNodes: segmentIds.length };
    }
    if (ref.text !== fail.text) {
      applyGuardToSegment({ locator: ref.locator, expectedText: ref.text });
      return { action: 'lstar-added-text-guard', locator: ref.locator, expectedText: ref.text, refinedNodes: segmentIds.length };
    }
  }

  // 2. Extra control present in failing observation that was absent during verified teaching.
  for (const [key, fail] of failByLoc.entries()) {
    if (existingGuardKeys.has(key)) continue;
    if (!refByLoc.has(key)) {
      applyGuardToSegment({ locator: fail.locator, mustBeAbsent: true });
      return { action: 'lstar-added-absence-guard', locator: fail.locator, refinedNodes: segmentIds.length };
    }
  }

  // 3. Zero visible DOM differences: hidden server-side state drift! Demote segment to exact-prefix only.
  for (const id of segmentIds) {
    const p = dag.suffixProfiles.get(id);
    if (p) p.requiresExactPrefix = true;
  }
  return { action: 'demoted-to-exact-prefix-hidden-state', nodeId, refinedNodes: segmentIds.length };
}

/**
 * Read-only landmark attraction hints for the planner on cache misses.
 */
export function computeReachableLandmarks(dag, dp, { maxLandmarks = 3 } = {}) {
  if (!dag?.suffixProfiles?.size || !dp) return [];
  const byRoute = new Map();
  for (const [nodeId, profile] of dag.suffixProfiles.entries()) {
    if (profile.requiresExactPrefix) continue;
    const cost = dp.values.get(nodeId) ?? Infinity;
    const decision = dp.policy.get(nodeId);
    if (!Number.isFinite(cost) || cost <= 0 || decision?.kind !== 'step') continue;
    const locatorMap = new Map(profile.locatorTable ?? []);
    const controls = (profile.onScreenStepLocators ?? [])
      .map(h => locatorMap.get(h)?.[1])
      .filter(Boolean);
    const prev = byRoute.get(profile.routePattern);
    if (!prev || cost > prev.stepsSavedToGoal) {
      byRoute.set(profile.routePattern, {
        routePattern: profile.routePattern,
        requiredControls: controls,
        stepsSavedToGoal: cost,
      });
    }
  }
  return [...byRoute.values()]
    .sort((a, b) => b.stepsSavedToGoal - a.stepsSavedToGoal || a.routePattern.localeCompare(b.routePattern))
    .slice(0, maxLandmarks);
}
