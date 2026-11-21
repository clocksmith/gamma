// Opt-in suffix eligibility for trace replay. On an exact state-hash miss it answers one question:
// may replay continue from a learned node whose remaining local steps are still valid on the live page?
// It dispatches nothing and grants nothing. The session and workspace service keep every existing
// check (unique live target, authorization, settled effects) for each step that follows.
import { structuralLocator } from '../adapters/page-query.js';

const INDEX_VERSION = 1;
const HASH = /^[a-f0-9]{64}$/;
const WRITABLE_TAGS = new Set(['input', 'select', 'textarea']);
const WRITABLE_ROLES = new Set(['textbox', 'searchbox', 'combobox', 'listbox', 'spinbutton', 'checkbox', 'radio', 'switch', 'slider']);
const BLOCKING_ROLES = new Set(['dialog', 'alertdialog', 'alert']);
const UNSUPPORTED_INPUTS = new Set(['submit', 'image', 'file', 'password', 'hidden']);
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
 * Certify at most one learned node for a live frame that missed the exact hash.
 * session: { inputs: Map<slotHash,string>, clicks: Set<locatorHash>, executedSteps: step[],
 *            sameOutlineClicks: number, isGoalTerminal(id, node): boolean }
 * Returns { status: 'certified', nodeId, terminal } or { status: 'refused', reason, refusals }.
 */
export function certifySuffix({ dag, index, dp, frame, session, restrictTo = null, policy = DEFAULT_SUFFIX_POLICY }) {
  const refusals = new Map();
  const refused = reason => ({ status: 'refused', reason, refusals: Object.fromEntries(refusals) });
  if (!frame?.meta || !index || !dp) return refused('suffix-unavailable');
  const elements = frame.observation.elements;
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
    eligible.push({ id, terminal });
  }
  if (eligible.length !== 1) return refused(eligible.length ? 'ambiguous-candidates' : 'no-eligible-candidate');
  return { status: 'certified', nodeId: eligible[0].id, terminal: eligible[0].terminal };
}
