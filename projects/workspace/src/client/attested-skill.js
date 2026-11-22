// Equal-evidence executable skill baselines for the fair-fight comparison (#88):
//   1. `attested-linear-skill` (`allowSafeJumps: false`): starts cursor at step 0, never jumps across
//      unexecuted screens, and shares identical observations (`includeFormState: true`), dirty-<form>
//      checks, HMAC `[role="status"]` / `<output>` checks, versioned `attestPrerequisites` refutation,
//      step authorization, prerequisite checks, journaled idempotency, planner, and repair learning.
//   2. `attested-checkpointed-skill` (`allowSafeJumps: true`): identical to `attested-linear-skill`,
//      plus safe forward jumps onto a recorded trajectory checkpoint when every step in that
//      trajectory's linear prefix is carried, visibly settled on the page, or server-attested.
// Neither skill representation merges state nodes across distinct trajectories (`src/client/skill-exec.js`
// remains untouched as the frozen historical baseline from v1/v2).

import { createHmac, randomBytes } from 'node:crypto';
import { structuralLocator } from '../adapters/page-query.js';
import { canonicalJson } from '../journal.js';
import {
  computeStatusSignatures,
  hasDirtyUntrackedFormControl,
  labelsCompete,
  normalizeAttestationAnswers,
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
    urlPath: parsedUrl.pathname,
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
 * Equal-evidence planner wrapper for `attested-linear-skill` (`allowSafeJumps: false`) and
 * `attested-checkpointed-skill` (`allowSafeJumps: true`).
 */
export function createAttestedSkillPlanner({
  book,
  planner,
  allowSafeJumps = false,
  attestPrerequisites = null,
  inertFormLocators = [],
  recordId = null,
}) {
  if (!(book instanceof AttestedSkillBook)) throw Error('createAttestedSkillPlanner requires an AttestedSkillBook');
  const trajectories = book.trajectories.map(traj => ({
    accountScope: traj.accountScope ?? null,
    terminalStatus: traj.terminalStatus ?? null,
    steps: traj.steps.map(step => ({
      ...step,
      key: canonicalJson(step.locator),
      taught: new Set(step.page ?? []),
    })),
  }));
  const whitelistedInert = new Set((inertFormLocators ?? []).map(loc => canonicalJson(loc)));
  const stats = {
    mode: allowSafeJumps ? 'attested-checkpointed-skill' : 'attested-linear-skill',
    scriptSteps: 0,
    handBacks: 0,
    skippedSteps: 0,
    safeJumps: 0,
    attestedJumps: 0,
    refusedJumps: 0,
    attestationRefuted: 0,
    guardRefusals: {},
    reasons: {},
  };

  let activeTrajIdx = trajectories.length === 1 ? 0 : null;
  let at = 0;
  let pendingProposal = null;
  let pendingPlannerStep = null;
  let handed = false;
  let unanchoredHandBacks = 0;
  const carriedSteps = [];
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
    const liveOrigin = new URL(obs.url).origin;
    if ((context.accountScope ?? null) !== (traj.accountScope ?? null)) {
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
    if (step.urlOrigin && step.urlOrigin !== liveOrigin) {
      return { ok: false, reason: 'origin-mismatch' };
    }
    if (canonicalJson(step.status ?? []) !== liveStatusJson) {
      return { ok: false, reason: 'status-changed' };
    }
    const found = elements.filter(el => keyOf(el) === step.key && isActionable(el));
    if (found.length !== 1) {
      return { ok: false, reason: found.length ? 'ambiguous-target' : 'missing-target' };
    }
    const target = found[0];
    if (!target.label || target.formAction || UNSUPPORTED_INPUTS.has(target.inputType)) {
      return { ok: false, reason: 'unsupported-target' };
    }
    if (step.kind !== 'click' && typeof inputs[step.slot] !== 'string') {
      return { ok: false, reason: 'missing-input-slot' };
    }
    if (step.kind === 'click' && allowedClickKeys && !allowedClickKeys.has(step.key)) {
      return { ok: false, reason: 'click-not-authorized' };
    }

    // Collect local targets on the same screen up to the first click for competing-label and dirty-form checks.
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

    return { ok: true, terminal: false, idx, step, target, skippedCount: idx - rawIdx };
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

  return {
    identity: {
      ...(planner?.identity ?? {}),
      skill: allowSafeJumps ? 'attested-checkpointed-skill' : 'attested-linear-skill',
    },
    stats: () => structuredClone(stats),
    predicateVersions: () => structuredClone(attestedPredicates),
    unavailablePredicates: () => structuredClone(unavailablePredicates),
    commitVerifiedRepair(accountScope = null, finalObservation = null, finalInputs = null) {
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

      // Settle previous proposal or planner step.
      if (pendingProposal !== null) {
        if (last?.status === 'completed') {
          carriedSteps.push({
            kind: pendingProposal.step.kind,
            locator: pendingProposal.step.locator,
            slot: pendingProposal.step.slot ?? null,
          });
          if (pendingProposal.step.slot) suppliedSlots.add(pendingProposal.step.slot);
          recordedRunSteps.push(pendingProposal.captured);
          activeTrajIdx = pendingProposal.trajIdx;
          at = pendingProposal.stepIdx + 1;
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
        if (activeTrajIdx !== null && last.kind === 'click') {
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

      if (trajectories.length === 0) {
        return handBack('empty-skill-book', context, rest);
      }

      const inputsMap = buildInputsMap(inputs, book.hash);
      const liveStatusJson = canonicalJson(computeStatusSignatures(elements, inputsMap, book.hash));
      const allowedClickKeys = Array.isArray(context.intermediateClickLocators)
        ? new Set(context.intermediateClickLocators.map(loc => canonicalJson(loc)))
        : null;

      // 1. Try advancing along the active trajectory (or selecting a step-0 trajectory at turn 0).
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
          // Only directly executable at step 0 if every skipped step in [0..check.idx-1] was visibly settled on Screen 1.
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
        // Linear skill recovery along its active trajectory when planner returned to the current cursor.
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

      // 2. Screen missed step 0 / current cursor: evaluate interior checkpoints for refutation (both modes)
      //    and safe attested forward jumps (`allowSafeJumps: true`).
      const carriedKeys = new Set(carriedSteps.map(stepIdentityKey));
      const screenMatchingCheckpoints = [];
      for (let tIdx = trajectories.length - 1; tIdx >= 0; tIdx -= 1) {
        const traj = trajectories[tIdx];
        for (let sIdx = 0; sIdx < traj.steps.length; sIdx += 1) {
          const check = evaluateCheckpointOnScreen(traj, sIdx, context, liveStatusJson, allowedClickKeys);
          if (!check.ok || check.terminal) continue;
          // Avoid duplicate evaluation when advanceSettled landed on the same idx.
          if (screenMatchingCheckpoints.some(c => c.tIdx === tIdx && c.idx === check.idx)) continue;
          // Ensure all remaining slots in this trajectory exist in `inputs`.
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

        let attestedKeys = new Set();
        let refutableKeys = new Set();
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
              refutableKeys = new Set(keys.filter((_, i) => parsed.refutableByIndex[i] === true));
              parsedPredicates = parsed.predicateVersions;
              if (parsed.unavailable.length > 0) {
                unavailablePredicates.push(...parsed.unavailable);
              }
            }
          } catch {
            attValid = false;
          }
        }

        const accountedCandidates = [];
        let anyPotentiallyAttested = false;
        for (const cand of screenMatchingCheckpoints) {
          const prefix = cand.traj.steps.slice(0, cand.idx);
          const canAttestStep = s => s.urlPath !== cand.step.urlPath;
          const withoutAtt = prefix.every(s => isPrefixStepCarriedOrSettled(s, elements, inputs, carriedKeys));
          const withAtt = prefix.every(s => isPrefixStepCarriedOrSettled(s, elements, inputs, carriedKeys)
            || (canAttestStep(s) && attestedKeys.has(stepIdentityKey(s))));
          const ifAllRefutableTrue = prefix.every(s => isPrefixStepCarriedOrSettled(s, elements, inputs, carriedKeys)
            || (canAttestStep(s) && refutableKeys.has(stepIdentityKey(s))));
          if (withAtt) {
            accountedCandidates.push({ ...cand, usedAttestation: !withoutAtt });
          } else if (ifAllRefutableTrue) {
            anyPotentiallyAttested = true;
          }
        }

        // Entry refutation symmetry across both `attested-linear-skill` and `attested-checkpointed-skill`:
        if (carriedSteps.length === 0 && attValid && refutableKeys.size > 0
          && accountedCandidates.length === 0 && anyPotentiallyAttested) {
          stats.attestationRefuted += 1;
          noteGuardRefusal('attestation-refuted');
          return {
            tool: 'ask_human',
            input: { reason: 'Prerequisite attestation refused mid-workflow entry' },
          };
        }

        const selectableCandidates = allowSafeJumps
          ? accountedCandidates
          : accountedCandidates.filter(cand => !cand.usedAttestation && carriedSteps.length > 0);

        if (accountedCandidates.length > 0 && selectableCandidates.length === 0) {
          stats.refusedJumps += 1;
          return handBack('linear-skill-no-jump', context, rest);
        }

        if (selectableCandidates.length > 0) {
          // Deduplicate candidates by next proposed action `(kind, key, slot)`; prefer latest learned trajectory.
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

      // Zero-action goal terminal check (mirrors TraceSession.#isExactEntryAccounted terminal exemption: dispatches 0 writes).
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
