// Equal-evidence executable skill baselines for the fair-fight & modular-suffix comparison (#88):
//   1. `attested-linear-skill` (`allowSafeJumps: false`): starts cursor at step 0, never jumps across
//      unexecuted screens, and shares identical observations (`includeFormState: true`), dirty-<form>
//      checks, HMAC `[role="status"]` / `<output>` checks, versioned `attestPrerequisites` refutation,
//      step authorization, prerequisite checks, journaled idempotency, planner, and repair learning.
//   2. `attested-checkpointed-skill` (`allowSafeJumps: true, allowCallableSharedSuffixes: false`):
//      adds safe forward jumps onto a recorded trajectory checkpoint when that trajectory's linear
//      prefix is carried, visibly settled on the page, or server-attested (`holds: true`).
//   3. `attested-modular-skill` (`allowSafeJumps: true, allowCallableSharedSuffixes: true`):
//      factors recorded trajectories into callable screen-level shared subroutines (`procId` keyed by
//      `(accountScope, urlOrigin, urlPath, visitOrd)`) with disjunctive caller-chain preconditions and
//      in-place subroutine repair reuse across all callers—testing `TraceDag` + Bellman DP against a
//      baseline that CAN share suffixes and reuse repairs across branches (`src/client/skill-exec.js`
//      remains untouched as the frozen historical baseline from v1/v2).

import { createHmac, randomBytes } from 'node:crypto';
import { structuralLocator } from '../adapters/page-query.js';
import { canonicalJson } from '../journal.js';
import {
  computeStatusSignatures,
  hasDirtyUntrackedFormControl,
  labelsCompete,
  normalizeAttestationAnswers,
  normalizeRoutePattern,
} from './suffix-eligibility.js';

const BOOK_VERSION = 1;
const MAX_TRAJECTORIES = 32;
const WRITABLE_TAGS = new Set(['input', 'select', 'textarea']);
const WRITABLE_ROLES = new Set(['textbox', 'searchbox', 'combobox', 'listbox', 'spinbutton', 'checkbox', 'radio', 'switch', 'slider']);
const UNSUPPORTED_INPUTS = new Set(['submit', 'image', 'file', 'password', 'hidden']);

const keyOf = element => canonicalJson(structuralLocator(element));
const isWritable = element => WRITABLE_TAGS.has(element.tag) || WRITABLE_ROLES.has(element.role);
const isActionable = element => !element.actionability
  || (element.actionability.visible !== false && !element.actionability.inert && !element.actionability.disabled);
const isEmpty = element => element.value === '' || element.value === null || element.value === undefined;
const stepIdentityKey = step => canonicalJson({
  kind: step.kind,
  locator: step.locator,
  slot: step.slot ?? null,
});

function makeHasher(hexKey) {
  const keyBuf = Buffer.from(hexKey, 'hex');
  return value => createHmac('sha256', keyBuf).update(canonicalJson(value)).digest('hex');
}

function buildInputsMap(inputs, hashFn) {
  const map = new Map();
  if (!inputs || typeof inputs !== 'object') return map;
  for (const [slotName, value] of Object.entries(inputs)) {
    if (typeof value === 'string') {
      map.set(hashFn(['slot', slotName]), value);
    }
  }
  return map;
}

function normalizeSkillRoutePath(rawUrlOrPath) {
  let parsed;
  try {
    parsed = rawUrlOrPath instanceof URL
      ? rawUrlOrPath
      : new URL(rawUrlOrPath.startsWith('http') ? rawUrlOrPath : `https://route.invalid${rawUrlOrPath.startsWith('/') ? '' : '/'}${rawUrlOrPath}`);
  } catch {
    return String(rawUrlOrPath ?? '/');
  }
  const basePattern = normalizeRoutePattern(parsed.href).routePattern;
  if (typeof parsed.hash === 'string' && parsed.hash.startsWith('#/')) {
    const hashPathOnly = parsed.hash.slice(1).split('?')[0];
    const hashPattern = normalizeRoutePattern(`https://route.invalid${hashPathOnly}`).routePattern;
    return `${basePattern.replace(/\/$/, '')}#${hashPattern}`;
  }
  return basePattern;
}

function prepareStep(step) {
  return {
    ...step,
    urlPath: normalizeSkillRoutePath(step.urlPath ?? '/'),
    key: canonicalJson(step.locator),
    taught: new Set(step.page ?? []),
  };
}

/**
 * Factor recorded trajectories into callable screen-level shared subroutines.
 * Newest trajectories are indexed first within each subroutine's `implementations` list so
 * verified repairs supersede older implementations while preserving all taught caller links.
 */
export function compileCallableSubroutines(rawTrajectories, { minOverlap = 0.60 } = {}) {
  const procs = new Map();
  const bucketsByUrl = new Map();

  const controlOverlap = (countsA, lenA, countsB, lenB) => {
    const denom = Math.max(lenA, lenB);
    if (denom === 0) return 1;
    let common = 0;
    for (const [loc, nA] of countsA) {
      common += Math.min(nA, countsB.get(loc) ?? 0);
    }
    return common / denom;
  };

  const buildCounts = arr => {
    const m = new Map();
    for (const k of arr ?? []) m.set(k, (m.get(k) ?? 0) + 1);
    return m;
  };

  const resolveOrCreateProc = (accountScope, urlOrigin, urlPath, ord, firstStep) => {
    const bucketKey = canonicalJson([accountScope ?? null, urlOrigin, urlPath, ord]);
    if (!bucketsByUrl.has(bucketKey)) bucketsByUrl.set(bucketKey, []);
    const bucket = bucketsByUrl.get(bucketKey);
    const stepBag = firstStep.learnedCounts ?? firstStep.page ?? [];
    const stepCounts = buildCounts(stepBag);

    for (const candidateProc of bucket) {
      const overlap = controlOverlap(
        stepCounts,
        stepBag.length,
        candidateProc.anchorCounts,
        candidateProc.anchorLen,
      );
      if (overlap >= minOverlap) return candidateProc;
    }

    const procId = canonicalJson([accountScope ?? null, urlOrigin, urlPath, ord, bucket.length]);
    const created = {
      id: procId,
      accountScope: accountScope ?? null,
      urlOrigin,
      urlPath,
      anchorCounts: stepCounts,
      anchorLen: stepBag.length,
      isEntry: false,
      callers: new Set(),
      callees: new Set(),
      terminalStatuses: [],
      implementations: [],
    };
    bucket.push(created);
    procs.set(procId, created);
    return created;
  };

  // Pass 1 (newest to oldest) populates implementations so verified repairs take priority.
  for (let tIdx = rawTrajectories.length - 1; tIdx >= 0; tIdx -= 1) {
    const traj = rawTrajectories[tIdx];
    if (!traj?.steps?.length) continue;
    const segments = [];
    for (const rawStep of traj.steps) {
      const prev = segments[segments.length - 1];
      if (prev && prev.urlOrigin === rawStep.urlOrigin && prev.urlPath === rawStep.urlPath) {
        prev.steps.push(prepareStep(rawStep));
      } else {
        segments.push({
          urlOrigin: rawStep.urlOrigin,
          urlPath: rawStep.urlPath,
          steps: [prepareStep(rawStep)],
        });
      }
    }
    const visitCounts = new Map();
    const segProcIds = [];
    for (let sIdx = 0; sIdx < segments.length; sIdx += 1) {
      const seg = segments[sIdx];
      const urlKey = `${seg.urlOrigin}|${seg.urlPath}`;
      const ord = visitCounts.get(urlKey) ?? 0;
      visitCounts.set(urlKey, ord + 1);
      const proc = resolveOrCreateProc(
        traj.accountScope ?? null,
        seg.urlOrigin,
        seg.urlPath,
        ord,
        seg.steps[0],
      );
      const procId = proc.id;
      segProcIds.push(procId);
      if (sIdx === 0) proc.isEntry = true;
      if (sIdx === segments.length - 1 && Array.isArray(traj.terminalStatus) && traj.terminalStatus.length > 0) {
        const tsJson = canonicalJson(traj.terminalStatus);
        if (!proc.terminalStatuses.some(existing => canonicalJson(existing) === tsJson)) {
          proc.terminalStatuses.push(structuredClone(traj.terminalStatus));
        }
      }
      const sig = canonicalJson(seg.steps.map(s => ({
        kind: s.kind,
        locator: s.locator,
        slot: s.slot ?? null,
        status: s.status ?? [],
        page: s.page ?? [],
      })));
      let matchingImpl = proc.implementations.find(impl => impl.signature === sig);
      if (!matchingImpl) {
        matchingImpl = {
          implIdx: proc.implementations.length,
          sourceTrajIdx: tIdx,
          signature: sig,
          accountScope: traj.accountScope ?? null,
          terminalStatus: sIdx === segments.length - 1 ? (traj.terminalStatus ?? null) : null,
          calleeIds: new Set(),
          steps: seg.steps,
        };
        proc.implementations.push(matchingImpl);
      } else if (sIdx === segments.length - 1 && traj.terminalStatus && !matchingImpl.terminalStatus) {
        matchingImpl.terminalStatus = traj.terminalStatus;
      }
      seg.matchingImpl = matchingImpl;
    }
    for (let sIdx = 0; sIdx < segProcIds.length - 1; sIdx += 1) {
      const caller = procs.get(segProcIds[sIdx]);
      const callee = procs.get(segProcIds[sIdx + 1]);
      caller.callees.add(callee.id);
      callee.callers.add(caller.id);
      segments[sIdx].matchingImpl?.calleeIds.add(callee.id);
    }
  }

  let deduplicatedSteps = 0;
  for (const proc of procs.values()) {
    const uniq = new Set();
    for (const impl of proc.implementations) {
      for (const step of impl.steps) uniq.add(stepIdentityKey(step));
    }
    deduplicatedSteps += uniq.size;
  }

  return { procs, subroutineCount: procs.size, deduplicatedSteps };
}

function enumerateCallerChains(procs, targetProcId, maxDepth = 16) {
  const chains = [];
  const target = procs.get(targetProcId);
  if (!target) return chains;
  if (target.isEntry) chains.push([]);
  const dfs = (curId, suffixChain, visited) => {
    if (suffixChain.length > maxDepth) return;
    const cur = procs.get(curId);
    if (!cur) return;
    for (const callerId of cur.callers) {
      if (visited.has(callerId)) continue;
      const caller = procs.get(callerId);
      if (!caller) continue;
      const nextChain = [callerId, ...suffixChain];
      if (caller.isEntry) chains.push(nextChain);
      visited.add(callerId);
      dfs(callerId, nextChain, visited);
      visited.delete(callerId);
    }
  };
  dfs(targetProcId, [], new Set([targetProcId]));
  return chains;
}

function hasFeasibleDownstreamCallPath(procs, procId, implIdx, inputs, maxDepth = 6, visited = new Set()) {
  const proc = procs.get(procId);
  const impl = proc?.implementations?.[implIdx];
  if (!proc || !impl) return false;
  const missingLocalSlot = impl.steps.some(
    s => s.kind !== 'click' && typeof inputs?.[s.slot] !== 'string',
  );
  if (missingLocalSlot) return false;
  if (impl.terminalStatus !== null || !impl.calleeIds || impl.calleeIds.size === 0 || maxDepth <= 0) {
    return true;
  }
  const nextVisited = new Set(visited);
  nextVisited.add(procId);
  for (const calleeId of impl.calleeIds) {
    if (nextVisited.has(calleeId)) continue;
    const calleeProc = procs.get(calleeId);
    if (!calleeProc) continue;
    for (let cIdx = 0; cIdx < calleeProc.implementations.length; cIdx += 1) {
      if (hasFeasibleDownstreamCallPath(procs, calleeId, cIdx, inputs, maxDepth - 1, nextVisited)) {
        return true;
      }
    }
  }
  return false;
}

export class AttestedSkillBook {
  constructor({ key = randomBytes(32).toString('hex'), trajectories = [] } = {}) {
    if (typeof key !== 'string' || !/^[a-f0-9]{64}$/.test(key)) throw Error('Invalid skill book HMAC key');
    this.key = key;
    this.hash = makeHasher(key);
    this.trajectories = structuredClone(trajectories);
  }

  addTrajectory(trajectory) {
    if (!trajectory || !Array.isArray(trajectory.steps) || trajectory.steps.length === 0) {
      throw Error('Invalid attested skill trajectory');
    }
    const serialized = canonicalJson(trajectory);
    if (this.trajectories.some(existing => canonicalJson(existing) === serialized)) {
      return false;
    }
    if (this.trajectories.length >= MAX_TRAJECTORIES) {
      this.trajectories.shift();
    }
    this.trajectories.push(structuredClone(trajectory));
    return true;
  }

  compiledSubroutineStats() {
    const compiled = compileCallableSubroutines(this.trajectories);
    return {
      subroutineCount: compiled.subroutineCount,
      deduplicatedSteps: compiled.deduplicatedSteps,
    };
  }

  export() {
    return structuredClone({
      version: BOOK_VERSION,
      key: this.key,
      trajectories: this.trajectories,
    });
  }

  static restore(state) {
    if (state?.version !== BOOK_VERSION || typeof state.key !== 'string' || !Array.isArray(state.trajectories)) {
      throw Error('Invalid attested skill book');
    }
    return new AttestedSkillBook({ key: state.key, trajectories: state.trajectories });
  }
}

function obsOf(context) {
  return context?.rawObservation ?? context?.observation ?? { url: 'https://unknown.invalid/', elements: [] };
}

function captureStepFromContext(context, decision, hashFn) {
  const obs = obsOf(context);
  const elements = obs.elements ?? [];
  const element = elements.find(candidate => candidate.handle === decision?.input?.handle);
  if (!element) return null;
  const inputsMap = buildInputsMap(context.inputs, hashFn);
  const parsedUrl = new URL(obs.url);
  return {
    kind: decision.input.kind,
    locator: structuralLocator(element),
    ...(decision.input.slot === undefined ? {} : { slot: decision.input.slot }),
    urlOrigin: parsedUrl.origin,
    urlPath: normalizeSkillRoutePath(parsedUrl),
    page: [...new Set(elements.filter(isWritable).map(keyOf))].sort(),
    learnedCounts: elements.map(keyOf),
    status: computeStatusSignatures(elements, inputsMap, hashFn),
  };
}

/** Record one teaching trajectory into an `AttestedSkillBook` once verified completion succeeds. */
export function recordAttestedSkillTeaching(planner, { book, accountScope = null }) {
  const steps = [];
  let pending = null;
  const settle = context => {
    if (pending && context?.lastResult?.status === 'completed' && context.lastResult.kind === pending.kind) {
      steps.push(pending);
    }
    pending = null;
  };
  return {
    planner: {
      identity: planner.identity,
      next: async (context, ...rest) => {
        settle(context);
        const decision = await planner.next(context, ...rest);
        if (decision?.tool === 'act') {
          pending = captureStepFromContext(context, decision, book.hash);
        }
        return decision;
      },
    },
    commitVerified(finalObservation = null, finalInputs = null) {
      if (pending) {
        steps.push(pending);
        pending = null;
      }
      if (!steps.length) throw Error('Attested skill teaching recorded zero steps');
      const terminalStatus = finalObservation && Array.isArray(finalObservation.elements)
        ? computeStatusSignatures(finalObservation.elements, buildInputsMap(finalInputs, book.hash), book.hash)
        : null;
      const trajectory = {
        accountScope,
        steps,
        ...(terminalStatus ? { terminalStatus } : {}),
      };
      book.addTrajectory(trajectory);
      return structuredClone(trajectory);
    },
  };
}

/**
 * Equal-evidence planner wrapper for:
 *   - `attested-linear-skill` (`allowSafeJumps: false`)
 *   - `attested-checkpointed-skill` (`allowSafeJumps: true, allowCallableSharedSuffixes: false`)
 *   - `attested-modular-skill` (`allowSafeJumps: true, allowCallableSharedSuffixes: true`)
 */
export function createAttestedSkillPlanner({
  book,
  planner,
  allowSafeJumps = false,
  allowCallableSharedSuffixes = false,
  allowDownstreamLookahead = allowCallableSharedSuffixes,
  maxLookaheadDepth = 6,
  attestPrerequisites = null,
  inertFormLocators = [],
  recordId = null,
  repairBoundaryGate = null,
}) {
  if (!(book instanceof AttestedSkillBook)) throw Error('createAttestedSkillPlanner requires an AttestedSkillBook');
  const modularMode = Boolean(allowSafeJumps && allowCallableSharedSuffixes);
  // Opt-in, frozen qualification replay only. The trusted caller must classify
  // every emitted action; this check never replaces dispatcher/server authority.
  if (repairBoundaryGate !== null && (!modularMode || typeof repairBoundaryGate !== 'function')) {
    throw Error('Repair boundary gate requires attested modular skill and a trusted callback');
  }
  const downstreamLookahead = Boolean(modularMode && allowDownstreamLookahead && maxLookaheadDepth > 0);
  const modeName = modularMode
    ? 'attested-modular-skill'
    : (allowSafeJumps ? 'attested-checkpointed-skill' : 'attested-linear-skill');

  const trajectories = book.trajectories.map(traj => ({
    accountScope: traj.accountScope ?? null,
    terminalStatus: traj.terminalStatus ?? null,
    steps: traj.steps.map(prepareStep),
  }));
  const compiled = modularMode ? compileCallableSubroutines(book.trajectories) : null;
  const whitelistedInert = new Set((inertFormLocators ?? []).map(loc => canonicalJson(loc)));
  const stats = {
    mode: modeName,
    scriptSteps: 0,
    handBacks: 0,
    skippedSteps: 0,
    safeJumps: 0,
    attestedJumps: 0,
    sharedSuffixCalls: 0,
    refusedJumps: 0,
    attestationRefuted: 0,
    entryRestsOnUnavailablePrerequisite: false,
    guardRefusals: {},
    reasons: {},
  };

  let activeTrajIdx = !modularMode && trajectories.length === 1 ? 0 : null;
  let activeProcId = null;
  let activeImplIdx = 0;
  let at = 0;
  let pendingProposal = null;
  let pendingPlannerStep = null;
  let handed = false;
  let unanchoredHandBacks = 0;
  let entryUnavailableActive = false;
  const carriedSteps = [];
  const completedProcIds = new Set();
  const suppliedSlots = new Set();
  const attestedPredicates = [];
  const unavailablePredicates = [];
  const recordedRunSteps = [];

  const noteGuardRefusal = reason => {
    stats.guardRefusals[reason] = (stats.guardRefusals[reason] ?? 0) + 1;
  };

  const mergePredicates = list => {
    const seen = new Set(attestedPredicates.map(p => `${p.account ?? ''}|${p.record}|${p.predicate}`));
    for (const p of list ?? []) {
      const k = `${p.account ?? ''}|${p.record}|${p.predicate}`;
      if (!seen.has(k)) {
        seen.add(k);
        attestedPredicates.push(p);
      }
    }
  };

  const handBack = async (reason, context, rest) => {
    stats.handBacks += 1;
    stats.reasons[reason] = (stats.reasons[reason] ?? 0) + 1;
    if (repairBoundaryGate) {
      return { tool: 'ask_human', input: { reason: 'Frozen repair replay has no accounted checkpoint' } };
    }
    handed = true;
    unanchoredHandBacks += 1;
    const decision = await planner.next(context, ...rest);
    if (decision?.tool === 'act') {
      pendingPlannerStep = captureStepFromContext(context, decision, book.hash);
    }
    return decision;
  };

  function advanceSettled(traj, startIdx, elements, inputs) {
    let idx = startIdx;
    while (idx < traj.steps.length && traj.steps[idx].kind !== 'click') {
      const step = traj.steps[idx];
      const found = elements.filter(el => keyOf(el) === step.key);
      const settledOnPage = found.length === 1
        && typeof inputs?.[step.slot] === 'string'
        && found[0].value === inputs[step.slot];
      if (!settledOnPage && !suppliedSlots.has(step.slot)) break;
      idx += 1;
    }
    return idx;
  }

  function evaluateCheckpointOnScreen(traj, rawIdx, context, liveStatusJson, allowedClickKeys) {
    const obs = obsOf(context);
    const elements = obs.elements ?? [];
    const inputs = context.inputs ?? {};
    if ((context.accountScope ?? null) !== traj.accountScope) {
      return { ok: false, reason: 'account-scope-mismatch' };
    }
    const idx = advanceSettled(traj, rawIdx, elements, inputs);
    if (idx >= traj.steps.length) {
      if (traj.terminalStatus && canonicalJson(traj.terminalStatus) !== liveStatusJson) {
        return { ok: false, reason: 'status-changed' };
      }
      return { ok: true, terminal: true, idx, skippedCount: idx - rawIdx };
    }
    const step = traj.steps[idx];
    let parsedUrl;
    try {
      parsedUrl = new URL(obs.url);
    } catch {
      return { ok: false, reason: 'invalid-url' };
    }
    if (parsedUrl.origin !== step.urlOrigin) {
      return { ok: false, reason: 'origin-mismatch' };
    }
    if (elements.some(el => el.role === 'dialog' || el.role === 'alertdialog' || el.role === 'alert')) {
      return { ok: false, reason: 'blocking-dialog' };
    }
    if (canonicalJson(step.status ?? []) !== liveStatusJson) {
      return { ok: false, reason: 'status-changed' };
    }
    const holders = elements.filter(el => keyOf(el) === step.key && isActionable(el));
    if (holders.length !== 1) {
      return { ok: false, reason: holders.length ? 'ambiguous-target' : 'missing-target' };
    }
    const target = holders[0];
    if (!target.label || target.formAction || UNSUPPORTED_INPUTS.has(target.inputType)) {
      return { ok: false, reason: 'unsupported-target' };
    }
    if (step.kind !== 'click' && typeof inputs[step.slot] !== 'string') {
      return { ok: false, reason: 'missing-input-slot' };
    }
    if (step.kind === 'click' && allowedClickKeys && !allowedClickKeys.has(step.key)) {
      return { ok: false, reason: 'click-not-authorized' };
    }

    const localTargets = [target];
    for (let k = idx + 1; k < traj.steps.length; k += 1) {
      const later = traj.steps[k];
      if (later.urlPath !== step.urlPath) break;
      const m = elements.filter(el => keyOf(el) === later.key && isActionable(el));
      if (m.length === 1) localTargets.push(m[0]);
      if (later.kind === 'click') break;
    }

    const learnedCounts = new Map();
    for (const k of step.learnedCounts ?? step.page ?? []) {
      learnedCounts.set(k, (learnedCounts.get(k) ?? 0) + 1);
    }
    const spare = new Map(learnedCounts);
    const addedWritable = elements.filter(el => {
      const k = keyOf(el);
      const left = spare.get(k) ?? 0;
      if (left > 0) { spare.set(k, left - 1); return false; }
      return true;
    }).filter(isWritable);

    if (addedWritable.some(el => !el.label)) {
      return { ok: false, reason: 'unlabelled-added-control' };
    }
    if (step.kind === 'click') {
      const remainingKeys = new Set(traj.steps.slice(idx).map(s => s.key));
      const novelEmpty = elements.some(el => isWritable(el) && isActionable(el) && isEmpty(el)
        && !step.taught.has(keyOf(el)) && !remainingKeys.has(keyOf(el)));
      if (novelEmpty) {
        return { ok: false, reason: 'new-empty-control-before-click' };
      }
    }
    if (addedWritable.some(el => localTargets.some(t => labelsCompete(el.label, t.label)))) {
      return { ok: false, reason: 'lookalike-added-control' };
    }

    const targetForms = new Set(localTargets.map(t => t.formKey).filter(Boolean));
    if (targetForms.size > 0) {
      const allowedLocatorJsons = new Set([
        ...carriedSteps.map(s => canonicalJson(s.locator)),
        ...localTargets.map(keyOf),
      ]);
      const allControls = context.unfilteredElements ?? elements;
      const hasFormMetadata = allControls.filter(isWritable).every(
        el => typeof el.isDefaultValue === 'boolean' && (el.formKey === null || typeof el.formKey === 'string'),
      );
      if (!hasFormMetadata) {
        return { ok: false, reason: 'form-state-unavailable' };
      }
      if (hasDirtyUntrackedFormControl({
        allControls,
        targetForms,
        allowedLocatorJsons,
        inputValues: Object.values(inputs),
        whitelistedInert,
      })) {
        return { ok: false, reason: 'dirty-untracked-form-field' };
      }
    }

    return { ok: true, terminal: false, idx, step, target, skippedCount: idx - rawIdx, addedCount: addedWritable.length };
  }

  function isPrefixStepCarriedOrSettled(prefixStep, elements, inputs, carriedKeys) {
    if (carriedKeys.has(stepIdentityKey(prefixStep))) return true;
    if (prefixStep.kind === 'click') return false;
    if (suppliedSlots.has(prefixStep.slot)) return true;
    const expected = inputs?.[prefixStep.slot];
    if (typeof expected !== 'string' || !expected.length) return false;
    const found = elements.filter(el => keyOf(el) === prefixStep.key);
    return found.length === 1 && found[0].value === expected;
  }

  async function queryAttestations(askedMap, obs, context) {
    let attestedKeys = new Set();
    let explicitlyRefutedKeys = new Set();
    let unavailableKeys = new Set();
    let attValid = false;
    let parsedPredicates = [];

    if (askedMap.size > 0 && typeof attestPrerequisites === 'function') {
      try {
        const parsedUrl = new URL(obs.url);
        const rawAnswers = await attestPrerequisites({
          origin: parsedUrl.origin,
          url: obs.url,
          skipped: structuredClone([...askedMap.values()]),
        });
        const parsed = normalizeAttestationAnswers(rawAnswers, {
          expectedCount: askedMap.size,
          accountScope: context.accountScope ?? null,
          recordId: context.recordId ?? recordId ?? null,
        });
        if (parsed.valid) {
          attValid = true;
          const keys = [...askedMap.keys()];
          attestedKeys = new Set(keys.filter((_, i) => parsed.holdsByIndex[i] === true));
          explicitlyRefutedKeys = new Set(keys.filter((_, i) => parsed.explicitlyRefutedByIndex[i] === true));
          unavailableKeys = new Set(keys.filter((_, i) => parsed.unavailableByIndex[i] === true));
          parsedPredicates = parsed.predicateVersions;
          if (parsed.unavailable.length > 0) {
            unavailablePredicates.push(...parsed.unavailable);
          }
        } else {
          explicitlyRefutedKeys = new Set(askedMap.keys());
        }
      } catch {
        attValid = false;
        explicitlyRefutedKeys = new Set(askedMap.keys());
      }
    }
    return { attestedKeys, explicitlyRefutedKeys, unavailableKeys, attValid, parsedPredicates };
  }

  async function nextModular(context, rest, { obs, elements, inputs, liveStatusJson, allowedClickKeys, wasHanded }) {
    const { procs } = compiled;
    if (procs.size === 0) return handBack('empty-skill-book', context, rest);
    const carriedKeys = new Set(carriedSteps.map(stepIdentityKey));

    const emitModularAct = async (procId, implIdx, stepIdx, step, target) => {
      if (repairBoundaryGate) {
        let eligibility;
        try {
          eligibility = await repairBoundaryGate({
            procId,
            stepIdx,
            stepKey: stepIdentityKey(step),
            accountScope: context.accountScope ?? null,
            recordId: context.recordId ?? recordId ?? null,
            url: obs.url,
          });
        } catch {
          // Unavailable evidence is not permission to attempt the old route.
        }
        if (eligibility?.status !== 'eligible-for-review') {
          noteGuardRefusal('repair-boundary-abstain');
          return { tool: 'ask_human', input: { reason: 'Repair boundary not verified' } };
        }
      }
      const decision = {
        tool: 'act',
        input: {
          kind: step.kind,
          handle: target.handle,
          ...(step.kind === 'click' ? {} : { slot: step.slot }),
        },
      };
      pendingProposal = {
        procId,
        implIdx,
        stepIdx,
        step,
        captured: captureStepFromContext(context, decision, book.hash),
      };
      return decision;
    };

    const implDownstreamFeasible = (procId, iIdx) =>
      !downstreamLookahead
      || hasFeasibleDownstreamCallPath(procs, procId, iIdx, inputs, maxLookaheadDepth);

    // 1a. Entry-subroutine selection at turn 0.
    if (activeProcId === null && carriedSteps.length === 0) {
      const entryMatches = [];
      let firstFailure = 'missing-target';
      for (const proc of procs.values()) {
        if (!proc.isEntry) continue;
        for (let iIdx = 0; iIdx < proc.implementations.length; iIdx += 1) {
          const impl = proc.implementations[iIdx];
          const check = evaluateCheckpointOnScreen(impl, 0, context, liveStatusJson, allowedClickKeys);
          if (!check.ok) {
            firstFailure = check.reason;
            continue;
          }
          if (!check.terminal) {
            const missingSlot = impl.steps.slice(check.idx).some(s => s.kind !== 'click' && typeof inputs[s.slot] !== 'string');
            if (missingSlot || !implDownstreamFeasible(proc.id, iIdx)) {
              firstFailure = 'missing-input-slot';
              continue;
            }
          }
          const allSettled = impl.steps.slice(0, check.idx).every(s => isPrefixStepCarriedOrSettled(s, elements, inputs, carriedKeys));
          if (allSettled) {
            entryMatches.push({ procId: proc.id, implIdx: iIdx, check });
          }
        }
      }
      if (entryMatches.length > 0) {
        const minAdded = Math.min(...entryMatches.map(m => m.check.addedCount ?? 0));
        const bestMatches = entryMatches.filter(m => (m.check.addedCount ?? 0) === minAdded);
        const chosen = bestMatches[0];
        const conflicts = bestMatches.some(
          other => !other.check.terminal && !chosen.check.terminal
            && stepIdentityKey(other.check.step) !== stepIdentityKey(chosen.check.step),
        );
        if (conflicts) {
          noteGuardRefusal('ambiguous-callable-branch');
          return handBack('ambiguous-callable-branch', context, rest);
        }
        activeProcId = chosen.procId;
        activeImplIdx = chosen.implIdx;
        at = chosen.check.idx;
        stats.skippedSteps += chosen.check.skippedCount;
        if (chosen.check.terminal) {
          return { tool: 'finish', input: { summary: 'Attested modular skill completed' } };
        }
        return emitModularAct(chosen.procId, chosen.implIdx, chosen.check.idx, chosen.check.step, chosen.check.target);
      }
      noteGuardRefusal(firstFailure);
    } else if (activeProcId !== null && !wasHanded) {
      // 1b. Continue inside current subroutine, or call a shared suffix in `activeProc.callees`.
      const activeProc = procs.get(activeProcId);
      if (activeProc && !implDownstreamFeasible(activeProcId, activeImplIdx)) {
        const switchIdx = activeProc.implementations.findIndex((candImpl, sIdx) =>
          sIdx !== activeImplIdx
          && at < candImpl.steps.length
          && candImpl.steps.slice(0, at).every(s => isPrefixStepCarriedOrSettled(s, elements, inputs, carriedKeys))
          && implDownstreamFeasible(activeProcId, sIdx));
        if (switchIdx >= 0) activeImplIdx = switchIdx;
      }
      const activeImpl = activeProc?.implementations?.[activeImplIdx];
      if (activeProc && activeImpl) {
        if (at < activeImpl.steps.length && implDownstreamFeasible(activeProcId, activeImplIdx)) {
          const check = evaluateCheckpointOnScreen(activeImpl, at, context, liveStatusJson, allowedClickKeys);
          if (check.ok) {
            if (!check.terminal) {
              // Check whether any sibling implementation of `activeProc` with no greater `addedCount`
              // whose prefix [0..at-1] is carried/settled proposes a conflicting action on this screen.
              const curAdded = check.addedCount ?? 0;
              const siblingConflict = activeProc.implementations.some((sibImpl, sIdx) => {
                if (sIdx === activeImplIdx || at >= sibImpl.steps.length) return false;
                if (!implDownstreamFeasible(activeProcId, sIdx)) return false;
                const prefixOk = sibImpl.steps.slice(0, at).every(
                  s => isPrefixStepCarriedOrSettled(s, elements, inputs, carriedKeys),
                );
                if (!prefixOk) return false;
                const sibCheck = evaluateCheckpointOnScreen(sibImpl, at, context, liveStatusJson, allowedClickKeys);
                if (!sibCheck.ok || sibCheck.terminal) return false;
                if ((sibCheck.addedCount ?? 0) > curAdded) return false;
                const missingSlot = sibImpl.steps.slice(sibCheck.idx).some(
                  s => s.kind !== 'click' && typeof inputs[s.slot] !== 'string',
                );
                if (missingSlot) return false;
                return stepIdentityKey(sibCheck.step) !== stepIdentityKey(check.step);
              });
              if (siblingConflict) {
                noteGuardRefusal('ambiguous-callable-branch');
                return handBack('ambiguous-callable-branch', context, rest);
              }
              stats.skippedSteps += check.skippedCount;
              at = check.idx;
              return emitModularAct(activeProcId, activeImplIdx, check.idx, check.step, check.target);
            }
            stats.skippedSteps += check.skippedCount;
            at = check.idx;
            completedProcIds.add(activeProcId);
          } else {
            noteGuardRefusal(check.reason);
          }
        }
        if (at >= activeImpl.steps.length) {
          if (!elements.some(isWritable) && activeProc.terminalStatuses.some(ts => canonicalJson(ts) === liveStatusJson)) {
            if (unanchoredHandBacks === 0) {
              return { tool: 'finish', input: { summary: 'Attested modular skill completed' } };
            }
            return handBack('script-finished-after-recovery', context, rest);
          }
          const calleeMatches = [];
          let calleeFailure = null;
          for (const calleeId of activeProc.callees) {
            const calleeProc = procs.get(calleeId);
            if (!calleeProc) continue;
            for (let iIdx = 0; iIdx < calleeProc.implementations.length; iIdx += 1) {
              const impl = calleeProc.implementations[iIdx];
              const check = evaluateCheckpointOnScreen(impl, 0, context, liveStatusJson, allowedClickKeys);
              if (!check.ok) {
                calleeFailure = check.reason;
                continue;
              }
              if (check.terminal) continue;
              const missingSlot = impl.steps.slice(check.idx).some(s => s.kind !== 'click' && typeof inputs[s.slot] !== 'string');
              if (missingSlot || !implDownstreamFeasible(calleeId, iIdx)) {
                calleeFailure = 'missing-input-slot';
                continue;
              }
              const allSettled = impl.steps.slice(0, check.idx).every(s => isPrefixStepCarriedOrSettled(s, elements, inputs, carriedKeys));
              if (allSettled) {
                calleeMatches.push({ procId: calleeId, implIdx: iIdx, check });
              }
            }
          }
          if (calleeMatches.length > 0) {
            const minAdded = Math.min(...calleeMatches.map(m => m.check.addedCount ?? 0));
            const bestCallees = calleeMatches.filter(m => (m.check.addedCount ?? 0) === minAdded);
            const chosen = bestCallees[0];
            const conflicts = bestCallees.some(
              other => stepIdentityKey(other.check.step) !== stepIdentityKey(chosen.check.step),
            );
            if (conflicts) {
              noteGuardRefusal('ambiguous-callable-branch');
              return handBack('ambiguous-callable-branch', context, rest);
            }
            activeProcId = chosen.procId;
            activeImplIdx = chosen.implIdx;
            at = chosen.check.idx;
            stats.sharedSuffixCalls += 1;
            stats.skippedSteps += chosen.check.skippedCount;
            return emitModularAct(chosen.procId, chosen.implIdx, chosen.check.idx, chosen.check.step, chosen.check.target);
          }
          if (calleeFailure) noteGuardRefusal(calleeFailure);
        }
      }
    }

    // 2. Mid-workflow entry or post-detour rejoin onto any callable subroutine whose caller chain is accounted.
    const candidates = [];
    for (const proc of procs.values()) {
      for (let iIdx = 0; iIdx < proc.implementations.length; iIdx += 1) {
        const impl = proc.implementations[iIdx];
        for (let sIdx = 0; sIdx < impl.steps.length; sIdx += 1) {
          const check = evaluateCheckpointOnScreen(impl, sIdx, context, liveStatusJson, allowedClickKeys);
          if (!check.ok || check.terminal) continue;
          if (candidates.some(c => c.procId === proc.id && c.implIdx === iIdx && c.idx === check.idx)) continue;
          const missingSlot = impl.steps.slice(check.idx).some(s => s.kind !== 'click' && typeof inputs[s.slot] !== 'string');
          if (missingSlot || !implDownstreamFeasible(proc.id, iIdx)) continue;
          const intraOk = impl.steps.slice(0, check.idx).every(s => isPrefixStepCarriedOrSettled(s, elements, inputs, carriedKeys));
          if (!intraOk) continue;
          candidates.push({
            procId: proc.id,
            proc,
            implIdx: iIdx,
            impl,
            idx: check.idx,
            step: check.step,
            target: check.target,
            addedCount: check.addedCount ?? 0,
            chains: enumerateCallerChains(procs, proc.id),
          });
        }
      }
    }

    if (candidates.length > 0) {
      const askedMap = new Map();
      for (const cand of candidates) {
        for (const chain of cand.chains) {
          for (const callerId of chain) {
            if (completedProcIds.has(callerId)) continue;
            const callerProc = procs.get(callerId);
            for (const cImpl of callerProc?.implementations ?? []) {
              for (const s of cImpl.steps) {
                if (s.urlPath === cand.step.urlPath) continue;
                if (isPrefixStepCarriedOrSettled(s, elements, inputs, carriedKeys)) continue;
                const k = stepIdentityKey(s);
                if (!askedMap.has(k)) {
                  askedMap.set(k, {
                    kind: s.kind,
                    slot: s.kind === 'click' ? null : s.slot,
                    locator: s.kind === 'click' ? s.locator : null,
                  });
                }
              }
            }
          }
        }
      }

      const { attestedKeys, explicitlyRefutedKeys, unavailableKeys, attValid, parsedPredicates } =
        await queryAttestations(askedMap, obs, context);

      const callerHoldsUnder = (callerId, currentUrlPath, stepPred) => {
        if (completedProcIds.has(callerId)) return true;
        const callerProc = procs.get(callerId);
        if (!callerProc) return false;
        return callerProc.implementations.some(cImpl =>
          cImpl.steps.every(s => isPrefixStepCarriedOrSettled(s, elements, inputs, carriedKeys)
            || (s.urlPath !== currentUrlPath && stepPred(s))));
      };

      const accountedCandidates = [];
      let anyUnrefuted = false;
      let anyEvaluated = false;

      for (const cand of candidates) {
        const withoutAtt = cand.chains.some(chain =>
          chain.every(callerId => callerHoldsUnder(callerId, cand.step.urlPath, () => false)));
        const withAtt = cand.chains.some(chain =>
          chain.every(callerId => callerHoldsUnder(callerId, cand.step.urlPath, s => attestedKeys.has(stepIdentityKey(s)))));
        const ifUnrefuted = cand.chains.some(chain =>
          chain.every(callerId => callerHoldsUnder(
            callerId,
            cand.step.urlPath,
            s => attestedKeys.has(stepIdentityKey(s)) || unavailableKeys.has(stepIdentityKey(s)),
          )));
        const ifEvaluated = cand.chains.some(chain =>
          chain.every(callerId => callerHoldsUnder(
            callerId,
            cand.step.urlPath,
            s => attestedKeys.has(stepIdentityKey(s))
              || unavailableKeys.has(stepIdentityKey(s))
              || explicitlyRefutedKeys.has(stepIdentityKey(s)),
          )));
        if (withAtt) {
          accountedCandidates.push({ ...cand, usedAttestation: !withoutAtt });
        } else if (ifUnrefuted) {
          anyUnrefuted = true;
        } else if (ifEvaluated) {
          anyEvaluated = true;
        }
      }

      if (carriedSteps.length === 0 && accountedCandidates.length === 0) {
        if (anyUnrefuted) {
          entryUnavailableActive = true;
          stats.entryRestsOnUnavailablePrerequisite = true;
        } else if ((attValid || explicitlyRefutedKeys.size > 0) && explicitlyRefutedKeys.size > 0 && anyEvaluated) {
          stats.attestationRefuted += 1;
          noteGuardRefusal('attestation-refuted');
          return {
            tool: 'ask_human',
            input: { reason: 'Prerequisite attestation refused mid-workflow entry' },
          };
        }
      }

      if (accountedCandidates.length > 0) {
        // Prefer in-session carried/settled continuations over attested jumps, then minimal added controls.
        accountedCandidates.sort((a, b) =>
          (Number(a.usedAttestation) - Number(b.usedAttestation))
          || ((a.addedCount ?? 0) - (b.addedCount ?? 0)));
        const first = accountedCandidates[0];
        const tier = accountedCandidates.filter(
          c => c.usedAttestation === first.usedAttestation && (c.addedCount ?? 0) === (first.addedCount ?? 0),
        );
        const chosen = tier[0];
        const conflicts = tier.some(
          other => stepIdentityKey(other.step) !== stepIdentityKey(chosen.step),
        );
        if (conflicts) {
          noteGuardRefusal('ambiguous-callable-branch');
          return handBack('ambiguous-callable-branch', context, rest);
        }
        if (chosen.usedAttestation && parsedPredicates.length > 0) {
          mergePredicates(parsedPredicates);
        }
        activeProcId = chosen.procId;
        activeImplIdx = chosen.implIdx;
        at = chosen.idx;
        unanchoredHandBacks = 0;
        stats.safeJumps += 1;
        if (chosen.usedAttestation) stats.attestedJumps += 1;
        return emitModularAct(chosen.procId, chosen.implIdx, chosen.idx, chosen.step, chosen.target);
      }
    }

    if (carriedSteps.length > 0 && !elements.some(isWritable)) {
      const matchingTerminal = [...procs.values()].some(proc =>
        (context.accountScope ?? null) === proc.accountScope
        && proc.terminalStatuses.some(ts => canonicalJson(ts) === liveStatusJson));
      if (matchingTerminal) {
        return { tool: 'finish', input: { summary: 'Attested modular skill reached verified terminal' } };
      }
    }

    return handBack('no-accounted-checkpoint', context, rest);
  }

  return {
    identity: {
      ...(planner?.identity ?? {}),
      skill: modeName,
    },
    stats: () => structuredClone(stats),
    predicateVersions: () => structuredClone(attestedPredicates),
    unavailablePredicates: () => structuredClone(unavailablePredicates),
    entryRestsOnUnavailablePrerequisite: () => entryUnavailableActive,
    commitVerifiedRepair(accountScope = null, finalObservation = null, finalInputs = null) {
      if (repairBoundaryGate) return false;
      if (pendingPlannerStep) {
        recordedRunSteps.push(pendingPlannerStep);
        pendingPlannerStep = null;
      }
      if (stats.handBacks === 0 || recordedRunSteps.length === 0) return false;
      const terminalStatus = finalObservation && Array.isArray(finalObservation.elements)
        ? computeStatusSignatures(finalObservation.elements, buildInputsMap(finalInputs, book.hash), book.hash)
        : null;
      return book.addTrajectory({
        accountScope,
        steps: recordedRunSteps,
        ...(terminalStatus ? { terminalStatus } : {}),
      });
    },
    next: async (context, ...rest) => {
      const obs = obsOf(context);
      const elements = obs.elements ?? [];
      const inputs = context.inputs ?? {};
      const last = context.lastResult;

      if (pendingProposal !== null) {
        if (last?.status === 'completed') {
          carriedSteps.push({
            kind: pendingProposal.step.kind,
            locator: pendingProposal.step.locator,
            slot: pendingProposal.step.slot ?? null,
          });
          if (pendingProposal.step.slot) suppliedSlots.add(pendingProposal.step.slot);
          recordedRunSteps.push(pendingProposal.captured);
          if (modularMode) {
            activeProcId = pendingProposal.procId;
            activeImplIdx = pendingProposal.implIdx;
            at = pendingProposal.stepIdx + 1;
            const proc = compiled.procs.get(activeProcId);
            const impl = proc?.implementations?.[activeImplIdx];
            if (impl && at >= impl.steps.length) {
              completedProcIds.add(activeProcId);
            }
          } else {
            activeTrajIdx = pendingProposal.trajIdx;
            at = pendingProposal.stepIdx + 1;
          }
          stats.scriptSteps += 1;
        }
        pendingProposal = null;
      } else if (handed && last?.status === 'completed') {
        if (pendingPlannerStep) {
          carriedSteps.push({
            kind: pendingPlannerStep.kind,
            locator: pendingPlannerStep.locator,
            slot: pendingPlannerStep.slot ?? null,
          });
          recordedRunSteps.push(pendingPlannerStep);
        }
        if (typeof last.slot === 'string') suppliedSlots.add(last.slot);
        if (!modularMode && activeTrajIdx !== null && last.kind === 'click') {
          const traj = trajectories[activeTrajIdx];
          const clicked = traj.steps.findIndex((s, i) => i >= at && s.kind === 'click' && s.locator[1] === last.label);
          if (clicked >= 0) {
            const cKeys = new Set(carriedSteps.map(stepIdentityKey));
            const interveningAccounted = traj.steps.slice(at, clicked)
              .every(s => isPrefixStepCarriedOrSettled(s, elements, inputs, cKeys));
            if (interveningAccounted) at = clicked + 1;
          }
        }
      }
      pendingPlannerStep = null;
      const wasHanded = handed;
      handed = false;

      const inputsMap = buildInputsMap(inputs, book.hash);
      const liveStatusJson = canonicalJson(computeStatusSignatures(elements, inputsMap, book.hash));
      const allowedClickKeys = Array.isArray(context.intermediateClickLocators)
        ? new Set(context.intermediateClickLocators.map(loc => canonicalJson(loc)))
        : null;

      if (modularMode) {
        return nextModular(context, rest, { obs, elements, inputs, liveStatusJson, allowedClickKeys, wasHanded });
      }

      if (trajectories.length === 0) {
        return handBack('empty-skill-book', context, rest);
      }

      // 1. Flat-trajectory step-0 or cursor continuation (`attested-linear-skill` and `attested-checkpointed-skill`).
      if (activeTrajIdx === null && carriedSteps.length === 0) {
        const step0Matches = [];
        let firstFailure = 'missing-target';
        for (let tIdx = trajectories.length - 1; tIdx >= 0; tIdx -= 1) {
          const traj = trajectories[tIdx];
          const check = evaluateCheckpointOnScreen(traj, 0, context, liveStatusJson, allowedClickKeys);
          if (!check.ok) {
            firstFailure = check.reason;
            continue;
          }
          const carriedKeys = new Set(carriedSteps.map(stepIdentityKey));
          const allSettled = traj.steps.slice(0, check.idx).every(s => isPrefixStepCarriedOrSettled(s, elements, inputs, carriedKeys));
          if (allSettled) step0Matches.push({ tIdx, check });
        }
        if (step0Matches.length > 0) {
          const chosen = step0Matches[0];
          activeTrajIdx = chosen.tIdx;
          at = chosen.check.idx;
          stats.skippedSteps += chosen.check.skippedCount;
          if (chosen.check.terminal) {
            return { tool: 'finish', input: { summary: 'Attested skill completed' } };
          }
          const decision = {
            tool: 'act',
            input: {
              kind: chosen.check.step.kind,
              handle: chosen.check.target.handle,
              ...(chosen.check.step.kind === 'click' ? {} : { slot: chosen.check.step.slot }),
            },
          };
          pendingProposal = {
            trajIdx: chosen.tIdx,
            stepIdx: chosen.check.idx,
            step: chosen.check.step,
            captured: captureStepFromContext(context, decision, book.hash),
          };
          return decision;
        }
        noteGuardRefusal(firstFailure);
      } else if (activeTrajIdx !== null && !wasHanded) {
        const traj = trajectories[activeTrajIdx];
        const check = evaluateCheckpointOnScreen(traj, at, context, liveStatusJson, allowedClickKeys);
        if (check.ok) {
          stats.skippedSteps += check.skippedCount;
          at = check.idx;
          if (check.terminal) {
            if (unanchoredHandBacks === 0) {
              return { tool: 'finish', input: { summary: 'Attested skill completed' } };
            }
            return handBack('script-finished-after-recovery', context, rest);
          }
          const decision = {
            tool: 'act',
            input: {
              kind: check.step.kind,
              handle: check.target.handle,
              ...(check.step.kind === 'click' ? {} : { slot: check.step.slot }),
            },
          };
          pendingProposal = {
            trajIdx: activeTrajIdx,
            stepIdx: check.idx,
            step: check.step,
            captured: captureStepFromContext(context, decision, book.hash),
          };
          return decision;
        }
        noteGuardRefusal(check.reason);
      } else if (activeTrajIdx !== null && wasHanded && !allowSafeJumps) {
        const traj = trajectories[activeTrajIdx];
        const check = evaluateCheckpointOnScreen(traj, at, context, liveStatusJson, allowedClickKeys);
        if (check.ok) {
          stats.skippedSteps += check.skippedCount;
          at = check.idx;
          if (check.terminal) {
            return handBack('script-finished-after-recovery', context, rest);
          }
          const decision = {
            tool: 'act',
            input: {
              kind: check.step.kind,
              handle: check.target.handle,
              ...(check.step.kind === 'click' ? {} : { slot: check.step.slot }),
            },
          };
          pendingProposal = {
            trajIdx: activeTrajIdx,
            stepIdx: check.idx,
            step: check.step,
            captured: captureStepFromContext(context, decision, book.hash),
          };
          return decision;
        }
      }

      // 2. Interior checkpoints: hub universal-refutation rule + safe jumps (`allowSafeJumps: true`).
      const carriedKeys = new Set(carriedSteps.map(stepIdentityKey));
      const screenMatchingCheckpoints = [];
      for (let tIdx = trajectories.length - 1; tIdx >= 0; tIdx -= 1) {
        const traj = trajectories[tIdx];
        for (let sIdx = 0; sIdx < traj.steps.length; sIdx += 1) {
          const check = evaluateCheckpointOnScreen(traj, sIdx, context, liveStatusJson, allowedClickKeys);
          if (!check.ok || check.terminal) continue;
          if (screenMatchingCheckpoints.some(c => c.tIdx === tIdx && c.idx === check.idx)) continue;
          const missingDownstreamSlot = traj.steps.slice(check.idx).some(
            later => later.kind !== 'click' && typeof inputs[later.slot] !== 'string',
          );
          if (missingDownstreamSlot) continue;
          screenMatchingCheckpoints.push({ tIdx, traj, idx: check.idx, step: check.step, target: check.target });
        }
      }

      if (screenMatchingCheckpoints.length > 0) {
        const askedMap = new Map();
        for (const cand of screenMatchingCheckpoints) {
          for (const prefixStep of cand.traj.steps.slice(0, cand.idx)) {
            if (isPrefixStepCarriedOrSettled(prefixStep, elements, inputs, carriedKeys)) continue;
            const k = stepIdentityKey(prefixStep);
            if (!askedMap.has(k)) {
              askedMap.set(k, {
                kind: prefixStep.kind,
                slot: prefixStep.kind === 'click' ? null : prefixStep.slot,
                locator: prefixStep.kind === 'click' ? prefixStep.locator : null,
              });
            }
          }
        }

        const { attestedKeys, explicitlyRefutedKeys, unavailableKeys, attValid, parsedPredicates } =
          await queryAttestations(askedMap, obs, context);

        const accountedCandidates = [];
        let anyUnrefuted = false;
        let anyEvaluated = false;
        for (const cand of screenMatchingCheckpoints) {
          const prefix = cand.traj.steps.slice(0, cand.idx);
          const canAttestStep = s => s.urlPath !== cand.step.urlPath;
          const withoutAtt = prefix.every(s => isPrefixStepCarriedOrSettled(s, elements, inputs, carriedKeys));
          const withAtt = prefix.every(s => isPrefixStepCarriedOrSettled(s, elements, inputs, carriedKeys)
            || (canAttestStep(s) && attestedKeys.has(stepIdentityKey(s))));
          const ifUnrefuted = prefix.every(s => isPrefixStepCarriedOrSettled(s, elements, inputs, carriedKeys)
            || (canAttestStep(s) && (attestedKeys.has(stepIdentityKey(s)) || unavailableKeys.has(stepIdentityKey(s)))));
          const ifEvaluated = prefix.every(s => isPrefixStepCarriedOrSettled(s, elements, inputs, carriedKeys)
            || (canAttestStep(s) && (attestedKeys.has(stepIdentityKey(s))
              || unavailableKeys.has(stepIdentityKey(s))
              || explicitlyRefutedKeys.has(stepIdentityKey(s)))));
          if (withAtt) {
            accountedCandidates.push({ ...cand, usedAttestation: !withoutAtt });
          } else if (ifUnrefuted) {
            anyUnrefuted = true;
          } else if (ifEvaluated) {
            anyEvaluated = true;
          }
        }

        // Hub universal-refutation symmetry: an untaken branch returning `holds: false` does NOT
        // refute a sibling branch whose unverified step returned `{ status: 'unavailable' }`.
        if (carriedSteps.length === 0 && accountedCandidates.length === 0) {
          if (anyUnrefuted) {
            entryUnavailableActive = true;
            stats.entryRestsOnUnavailablePrerequisite = true;
          } else if ((attValid || explicitlyRefutedKeys.size > 0) && explicitlyRefutedKeys.size > 0 && anyEvaluated) {
            stats.attestationRefuted += 1;
            noteGuardRefusal('attestation-refuted');
            return {
              tool: 'ask_human',
              input: { reason: 'Prerequisite attestation refused mid-workflow entry' },
            };
          }
        }

        const selectableCandidates = allowSafeJumps
          ? accountedCandidates
          : accountedCandidates.filter(cand => !cand.usedAttestation && carriedSteps.length > 0);

        if (accountedCandidates.length > 0 && selectableCandidates.length === 0) {
          stats.refusedJumps += 1;
          return handBack('linear-skill-no-jump', context, rest);
        }

        if (selectableCandidates.length > 0) {
          const chosen = selectableCandidates[0];
          const conflicting = selectableCandidates.some(
            other => other.tIdx === chosen.tIdx && stepIdentityKey(other.step) !== stepIdentityKey(chosen.step),
          );
          if (conflicting) {
            noteGuardRefusal('ambiguous-checkpoint');
            return handBack('ambiguous-checkpoint', context, rest);
          }
          if (chosen.usedAttestation && parsedPredicates.length > 0) {
            mergePredicates(parsedPredicates);
          }
          activeTrajIdx = chosen.tIdx;
          at = chosen.idx;
          if (allowSafeJumps) {
            unanchoredHandBacks = 0;
            stats.safeJumps += 1;
            if (chosen.usedAttestation) stats.attestedJumps += 1;
          }
          const decision = {
            tool: 'act',
            input: {
              kind: chosen.step.kind,
              handle: chosen.target.handle,
              ...(chosen.step.kind === 'click' ? {} : { slot: chosen.step.slot }),
            },
          };
          pendingProposal = {
            trajIdx: chosen.tIdx,
            stepIdx: chosen.idx,
            step: chosen.step,
            captured: captureStepFromContext(context, decision, book.hash),
          };
          return decision;
        }
      }

      if (allowSafeJumps && carriedSteps.length > 0 && !elements.some(isWritable)) {
        const matchingTerminal = trajectories.some(traj =>
          (context.accountScope ?? null) === (traj.accountScope ?? null)
          && Array.isArray(traj.terminalStatus) && traj.terminalStatus.length > 0
          && canonicalJson(traj.terminalStatus) === liveStatusJson);
        if (matchingTerminal) {
          return { tool: 'finish', input: { summary: 'Attested checkpointed skill reached verified terminal' } };
        }
      }

      return handBack('no-accounted-checkpoint', context, rest);
    },
  };
}
