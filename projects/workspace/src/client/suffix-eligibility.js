// Unified suffix eligibility for Gammatron trace replay (#85 / #88):
//   1. `SuffixIndex` + `certifySuffix` + `labelsCompete` (bag overlap, accountedReach, blocking-dialog
//      refusal, unlabelled/unanswered/competing-label guards; proven on the $0.457 Sonnet 5.5 rung).
//   2. Embedded `suffixProfiles` + `evaluateSuffixEligibility` + `refineSuffixProfileOnCounterexample`
//      (active footprint R_u, live valuation nu(o, inputs), per-<form> dirty-field guard, L* guard
//      splitting and hidden-state exact-prefix demotion, typed slot roles, and landmark hints).
// Pure analysis and verification module: dispatches nothing and grants nothing; WorkspaceService
// and host prerequisite/authorization gates remain sole authorities before every effect.

import { structuralLocator } from '../adapters/page-query.js';
import { canonicalJson } from '../journal.js';

const INDEX_VERSION = 1;
const HASH = /^[a-f0-9]{64}$/;
const WRITABLE_TAGS = new Set(['input', 'select', 'textarea']);
const WRITABLE_ROLES = new Set(['textbox', 'searchbox', 'combobox', 'listbox', 'spinbutton', 'checkbox', 'radio', 'switch', 'slider']);
const BLOCKING_ROLES = new Set(['dialog', 'alertdialog', 'alert']);
const UNSUPPORTED_INPUTS = new Set(['submit', 'image', 'file', 'password', 'hidden']);
const NON_VALUE_INPUT_TYPES = new Set(['submit', 'button', 'reset', 'image']);
const STOPPED_DECISIONS = new Set(['checkpoint', 'repair-only', 'ambiguous', 'missing-slot', 'terminal']);

/** Frozen before the first evaluation run; change only with a new, separately reported run. */
export const DEFAULT_SUFFIX_POLICY = Object.freeze({ minOverlap: 0.6, maxLocalSteps: 24 });

const count = values => {
  const counts = new Map();
  for (const value of values) counts.set(value, (counts.get(value) ?? 0) + 1);
  return counts;
};
const labelTokens = label => (label ?? '').toLowerCase().replace(/[^\p{L}\p{N}]+/gu, ' ').trim().split(' ').filter(Boolean);
const isWritable = element => WRITABLE_TAGS.has(element.tag) || WRITABLE_ROLES.has(element.role);
const isActionable = element => !element.actionability
  || (element.actionability.visible !== false && !element.actionability.inert && !element.actionability.disabled);
const isAnswered = element => typeof element.value === 'string' && element.value.length > 0
  && !['checkbox', 'radio'].includes(element.inputType);
// Form state is carried when a control has a default-value flag and a form key; null means "in no form".
const hasFormState = element => typeof element.isDefaultValue === 'boolean'
  && (element.formKey === null || typeof element.formKey === 'string');

/** Two labels compete when one's words are all contained in the other's ("Email" vs "Confirm email"). */
export function labelsCompete(first, second) {
  const a = new Set(labelTokens(first)), b = new Set(labelTokens(second));
  if (!a.size || !b.size) return true;
  const [small, large] = a.size <= b.size ? [a, b] : [b, a];
  return [...small].every(token => large.has(token));
}

/** Private per-node page facts, keyed like the graph and hashed under the graph's own key. */
export class SuffixIndex {
  constructor() {
    this.nodes = new Map();
    this.frozen = false;
  }
  freeze() { this.frozen = true; return this; }
  note(dag, frame) {
    if (this.frozen || !frame?.meta || !HASH.test(frame.id)) return;
    this.nodes.set(frame.id, {
      scope: frame.meta.scope,
      slots: [...frame.meta.slots],
      clicks: frame.meta.clicks,
      bag: frame.observation.elements.map(element => dag.hash(['locator', structuralLocator(element)])).sort(),
    });
  }
  export() { return structuredClone({ version: INDEX_VERSION, nodes: [...this.nodes] }); }
  static restore(state) {
    if (state?.version !== INDEX_VERSION || !Array.isArray(state.nodes)) throw Error('Invalid suffix index');
    const index = new SuffixIndex();
    for (const entry of state.nodes) {
      const [id, meta] = Array.isArray(entry) && entry.length === 2 ? entry : [];
      if (!HASH.test(id ?? '') || index.nodes.has(id) || !meta || Object.keys(meta).sort().join() !== 'bag,clicks,scope,slots'
        || !HASH.test(meta.scope) || !Number.isSafeInteger(meta.clicks) || meta.clicks < 0
        || !Array.isArray(meta.slots) || meta.slots.some(slot => !HASH.test(slot))
        || !Array.isArray(meta.bag) || meta.bag.some(locator => !HASH.test(locator))) throw Error('Invalid suffix index node');
      index.nodes.set(id, structuredClone(meta));
    }
    return index;
  }
}

/** Nodes reachable from a root along steps the session executed or the live page already shows settled. */
function accountedReach(nodes, isAccounted) {
  const hasIncoming = new Set();
  for (const node of nodes.values()) {
    for (const edge of node.edges ?? []) hasIncoming.add(edge.next);
    for (const next of node.repairs ?? []) hasIncoming.add(next);
  }
  const reach = new Set([...nodes.keys()].filter(id => !hasIncoming.has(id)));
  const queue = [...reach];
  while (queue.length) {
    const node = nodes.get(queue.pop());
    const nexts = [...(node.edges ?? []).filter(edge => isAccounted(edge.step)).map(edge => edge.next), ...(node.repairs ?? [])];
    for (const next of nexts) if (nodes.has(next) && !reach.has(next)) { reach.add(next); queue.push(next); }
  }
  return reach;
}

/**
 * Certify at most one learned node for a live frame that missed the exact hash (SuffixIndex mode).
 * session: { inputs: Map<slotHash,string>, clicks: Set<locatorHash>, executedSteps: step[],
 *            sameOutlineClicks: number, isGoalTerminal(id, node): boolean, formStateFresh?: boolean }
 * Returns { status: 'certified', nodeId, terminal } or { status: 'refused', reason, refusals }.
 * Refuses with `form-state-unavailable` before considering any candidate unless the frame carries
 * form state for every writable control and is the session's latest observation.
 */
export function certifySuffix({ dag, index, dp, frame, session, restrictTo = null, policy = DEFAULT_SUFFIX_POLICY }) {
  const refusals = new Map();
  const refused = reason => ({ status: 'refused', reason, refusals: Object.fromEntries(refusals) });
  if (!frame?.meta || !index || !dp) return refused('suffix-unavailable');
  const elements = frame.observation.elements;
  // Where a host policy hides controls from the planner, form state is judged on the unfiltered view.
  const stateView = frame.observation.unfilteredElements ?? elements;
  if (session.formStateFresh === false
    || stateView.some(element => isWritable(element) && !hasFormState(element))) return refused('form-state-unavailable');
  if (elements.some(element => BLOCKING_ROLES.has(element.role))) return refused('blocking-dialog');
  const live = elements.map(element => ({ element, locator: dag.hash(['locator', structuralLocator(element)]) }));
  const liveCounts = count(live.map(entry => entry.locator));

  const slotLocators = new Map();
  for (const node of dag.nodes.values()) {
    for (const { step } of node.edges ?? []) {
      if (step.kind === 'click') continue;
      if (!slotLocators.has(step.slot)) slotLocators.set(step.slot, new Set());
      slotLocators.get(step.slot).add(step.locator);
    }
  }
  // A slot is settled when exactly one live control at a learned locator for it already holds the input.
  const settled = slot => {
    const value = session.inputs.get(slot), locators = slotLocators.get(slot);
    if (typeof value !== 'string' || !value.length || !locators) return false;
    const holders = live.filter(entry => locators.has(entry.locator));
    return holders.length === 1 && holders[0].element.value === value;
  };
  const executedSlots = new Set(session.executedSteps.filter(step => step.kind !== 'click').map(step => step.slot));
  const executedClicks = new Set(session.executedSteps.filter(step => step.kind === 'click').map(step => step.locator));
  const slotDone = slot => executedSlots.has(slot) || settled(slot);
  const reach = accountedReach(dag.nodes, step => step.kind === 'click' ? executedClicks.has(step.locator) : slotDone(step.slot));

  const eligible = [];
  for (const [id, meta] of index.nodes) {
    const node = dag.nodes.get(id);
    if (!node || meta.scope !== frame.meta.scope || (restrictTo && !restrictTo.has(id))) continue;
    const reject = reason => { refusals.set(reason, (refusals.get(reason) ?? 0) + 1); };
    if (!reach.has(id)) { reject('prefix-unaccounted'); continue; }

    const learnedCounts = count(meta.bag);
    let common = 0;
    for (const [locator, learned] of learnedCounts) common += Math.min(learned, liveCounts.get(locator) ?? 0);
    if (common < policy.minOverlap * Math.max(meta.bag.length, live.length)) { reject('page-mismatch'); continue; }
    if (meta.slots.some(slot => !slotDone(slot))) { reject('prefix-slot-unaccounted'); continue; }
    if (meta.clicks !== session.sameOutlineClicks) { reject('click-progress-differs'); continue; }

    // Writable controls the learned page did not have.
    const spare = new Map(learnedCounts);
    const added = live.filter(({ locator }) => {
      const left = spare.get(locator) ?? 0;
      if (left > 0) { spare.set(locator, left - 1); return false; }
      return true;
    }).map(entry => entry.element).filter(isWritable);
    if (added.some(element => !element.label)) { reject('unlabelled-added-control'); continue; }

    const terminal = session.isGoalTerminal(id, node);
    const targets = [];
    let failure = null, cursor = id;
    for (let stepIndex = 0; !terminal && stepIndex < policy.maxLocalSteps; stepIndex++) {
      const current = dag.nodes.get(cursor), decision = dp.policy.get(cursor);
      if (!current || !decision?.step || STOPPED_DECISIONS.has(decision.kind)) {
        if (stepIndex === 0) failure = 'no-policy-step';
        break;
      }
      const { step } = decision;
      const matches = live.filter(entry => entry.locator === step.locator);
      // Later targets may only appear after an earlier answer; an absent one ends the local check.
      if (matches.length === 0 && stepIndex > 0) break;
      if (matches.length !== 1) { failure = matches.length ? 'ambiguous-target' : 'missing-target'; break; }
      const { element } = matches[0];
      if (!element.label || element.formAction || UNSUPPORTED_INPUTS.has(element.inputType)) { failure = 'unsupported-target'; break; }
      // A step this session cannot take ends the lookahead; it only refuses the node when it is the next step.
      const cannot = reason => { if (stepIndex === 0) failure = reason; };
      if (step.kind === 'click') {
        // Leaving the page while a new question is unanswered could skip a required answer: hand it to the planner.
        if (!session.clicks.has(step.locator)) cannot('click-not-authorized');
        else if (added.some(control => isActionable(control) && !isAnswered(control))) cannot('unanswered-added-control');
        else targets.push(element);
        break;
      }
      if (typeof session.inputs.get(step.slot) !== 'string') { cannot('missing-input-slot'); break; }
      if (slotDone(step.slot)) { failure = 'pending-fill-already-done'; break; }
      targets.push(element);
      const outcomes = current.edges.filter(edge => edge.step.kind === step.kind && edge.step.locator === step.locator
        && edge.step.slot === step.slot);
      if (outcomes.length !== 1) break;
      cursor = outcomes[0].next;
    }
    if (failure) { reject(failure); continue; }

    // A new control must not compete in meaning with a pending target.
    if (added.some(element => targets.some(target => labelsCompete(element.label, target.label)))) {
      reject('lookalike-added-control'); continue;
    }
    // Guardrail 2: an untouched non-default field inside a target <form> must not silently ride along.
    const targetForms = new Set(targets.map(target => target.formKey).filter(Boolean));
    if (targetForms.size > 0) {
      const executedLocators = new Set((session.executedSteps ?? []).map(step => step.locator));
      const targetLocators = new Set(targets.map(target => dag.hash(['locator', structuralLocator(target)])));
      const whitelistedInert = new Set((session.inertFormLocators ?? []).map(loc => canonicalJson(loc)));
      const allControls = frame.observation.unfilteredElements ?? frame.observation.elements;
      const hasDirtyUntracked = allControls.some(el => {
        if (!el.formKey || !targetForms.has(el.formKey) || el.isDefaultValue !== false) return false;
        const locHash = dag.hash(['locator', structuralLocator(el)]);
        if (executedLocators.has(locHash) || targetLocators.has(locHash)) return false;
        if ([...session.inputs.values()].some(v => typeof v === 'string' && v.length > 0 && el.value === v)) return false;
        return !whitelistedInert.has(canonicalJson(structuralLocator(el)));
      });
      if (hasDirtyUntracked) {
        reject('dirty-untracked-form-field'); continue;
      }
    }
    eligible.push({ id, terminal });
  }
  if (eligible.length !== 1) return refused(eligible.length ? 'ambiguous-candidates' : 'no-eligible-candidate');
  return { status: 'certified', nodeId: eligible[0].id, terminal: eligible[0].terminal };
}

// --- Active-footprint suffixProfiles, per-<form> dirty-field guard, L* refinement & landmarks ---

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
  return isActionable(element);
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
  return WRITABLE_TAGS.has(tag) || WRITABLE_ROLES.has(role);
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
      onScreenStepLocators: [...new Set([...(prev.onScreenStepLocators ?? []), ...(incoming.onScreenStepLocators ?? [])])].sort(),
      requiredSlots: [...new Set([...prev.requiredSlots, ...incoming.requiredSlots])].sort(),
      sameOutlineClicks: Math.max(prev.sameOutlineClicks, incoming.sameOutlineClicks),
      referenceControls: prev.referenceControls ?? incoming.referenceControls ?? [],
      extraGuards: [...guardMap.values()],
      requiresExactPrefix: Boolean(prev.requiresExactPrefix || incoming.requiresExactPrefix),
    });
  }
  return new Map([...merged.entries()].sort(([a], [b]) => a.localeCompare(b)));
}

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
  if (observation.elements.some(el => BLOCKING_ROLES.has(el.role))) {
    return { eligible: false, reason: 'blocking-dialog', rejections };
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
    if (decision.kind !== 'step') continue;

    if (profile.origin !== origin || profile.routePattern !== routePattern) continue;
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

    const matchedFootprintSelectors = new Set([immediateMatches[0].selector]);
    const matchedFootprintElements = [immediateMatches[0]];
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
      matchedFootprintElements.push(matches[0]);
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

    // Competing-label lookalike check on added writable controls within the committing form,
    // plus Guardrail 2 dirty-extra-<form>-field check!
    const refLocatorKeys = new Set((profile.referenceControls ?? []).map(c => canonicalJson(c.locator)));
    let dirtyField = null;
    let lookalikeAdded = null;
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
      const elLocKey = canonicalJson(structuralLocator(el));
      if (!refLocatorKeys.has(elLocKey) && !inertSet.has(elLocKey)) {
        if (matchedFootprintElements.some(target => isValueBearingControl(target) && labelsCompete(el.label, target.label))) {
          lookalikeAdded = structuralLocator(el);
          break;
        }
      }
    }
    if (dirtyField) {
      rejections.push({ nodeId, reason: 'dirty-untracked-form-field', dirtyField });
      continue;
    }
    if (lookalikeAdded) {
      rejections.push({ nodeId, reason: 'lookalike-added-control', lookalikeAdded });
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

export function refineSuffixProfileOnCounterexample(dag, nodeId, failingObservation) {
  const profile = dag.suffixProfiles.get(nodeId);
  if (!profile) return { action: 'none' };
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

  for (const [key, fail] of failByLoc.entries()) {
    if (existingGuardKeys.has(key)) continue;
    if (!refByLoc.has(key)) {
      applyGuardToSegment({ locator: fail.locator, mustBeAbsent: true });
      return { action: 'lstar-added-absence-guard', locator: fail.locator, refinedNodes: segmentIds.length };
    }
  }

  for (const id of segmentIds) {
    const p = dag.suffixProfiles.get(id);
    if (p) p.requiresExactPrefix = true;
  }
  return { action: 'demoted-to-exact-prefix-hidden-state', nodeId, refinedNodes: segmentIds.length };
}

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
