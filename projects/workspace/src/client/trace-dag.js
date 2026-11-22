// Opt-in client trace DAG with state reconvergence, graph reduction and dynamic programming.
// The workspace service remains the sole effect dispatcher; unfinished or uncertain runs teach nothing.
import { createHmac, randomBytes, randomUUID } from 'node:crypto';
import { canonicalJson } from '../journal.js';
import { structuralLocator, structuralOutlineHash } from '../adapters/page-query.js';
import { createFieldGroupScope } from './field-group-scope.js';
import {
  analyzeTraceGraph,
  compressTraceRecords,
  normalizeGoalTerminals,
  reduceTraceGraph,
  solveRecipeDp,
  topologicalSort,
} from './trace-graph-dp.js';
import {
  certifySuffix,
  computeReachableLandmarks,
  evaluateSuffixEligibility,
  mergeSuffixProfiles,
  normalizeRoutePattern,
  refineSuffixProfileOnCounterexample,
  resolveRoleBoundInputs,
  validateSuffixProfiles,
} from './suffix-eligibility.js';

const VERSION = 3;
const SUPPORTED_VERSIONS = [1, 2, VERSION];
const HASH = /^[a-f0-9]{64}$/;
const KINDS = ['fill', 'select', 'click'];
const REPAIRABLE = new Set(['unseen-branch', 'ambiguous-branch', 'missing-locator', 'ambiguous-locator']);

function checkLimits(limits) {
  if (!limits || Object.keys(limits).sort().join() !== 'maxEdges,maxNodes,maxSteps'
    || Object.values(limits).some(value => !Number.isSafeInteger(value) || value < 1)) {
    throw Error('Trace limits require positive maxNodes, maxEdges and maxSteps');
  }
}

function validEdgeShape(edge, version) {
  if (!edge || typeof edge !== 'object' || Array.isArray(edge)) return false;
  const keys = Object.keys(edge).sort().join();
  if (version < VERSION) return keys === 'next,step';
  if (keys === 'next,step') return true;
  return keys === 'next,step,weight'
    && typeof edge.weight === 'number'
    && Number.isFinite(edge.weight)
    && edge.weight > 0;
}

/** A bounded recipe DAG. Version 3 keys nodes by canonical screen + satisfied-slot state so
 * alternative prefixes, repairs and sub-recipes reconverge, compress and route via Bellman DP.
 * Versions 1 and 2 restore with their original ordered-prefix fingerprints intact.
 */
export class TraceDag {
  constructor(limits, { version = VERSION } = {}) {
    checkLimits(limits);
    if (!SUPPORTED_VERSIONS.includes(version)) throw Error('Unsupported trace version');
    this.version = version;
    this.limits = Object.freeze({ ...limits });
    this.key = randomBytes(32).toString('hex');
    this.nodes = new Map();
    this.goalTerminals = new Map();
    this.suffixProfiles = new Map();
    this.slotRoles = new Map();
  }
  hash(value) { return createHmac('sha256', this.key).update(canonicalJson(value)).digest('hex'); }
  export() {
    return structuredClone({
      version: this.version,
      key: this.key,
      limits: this.limits,
      nodes: [...this.nodes],
      ...(this.goalTerminals.size ? { goalTerminals: [...this.goalTerminals] } : {}),
      ...(this.suffixProfiles.size ? { suffixProfiles: [...this.suffixProfiles] } : {}),
      ...(this.slotRoles.size ? { slotRoles: [...this.slotRoles] } : {}),
    });
  }
  solve({ inputs = {}, slotRoles = null, goal = null, replanPenalty } = {}) {
    const { bound } = resolveRoleBoundInputs({
      inputs,
      slotRoles,
      learnedSlotRoles: this.slotRoles,
      hashFn: value => this.hash(value),
    });
    const availableSlots = new Set(bound.keys());
    const targetGoal = goal !== null ? this.hash(['goal', goal]) : null;
    return solveRecipeDp(this.nodes, this.limits, {
      availableSlots,
      targetGoal,
      goalTerminals: this.goalTerminals,
      ...(replanPenalty !== undefined ? { replanPenalty } : {}),
    });
  }
  reachableLandmarks({ inputs = {}, slotRoles = null, goal = null, maxLandmarks = 3 } = {}) {
    const dp = this.solve({ inputs, slotRoles, goal });
    return computeReachableLandmarks(this, dp, { maxLandmarks });
  }
  refineOnCounterexample(nodeId, failingObservation) {
    return refineSuffixProfileOnCounterexample(this, nodeId, failingObservation);
  }
  compressionStats() {
    return analyzeTraceGraph(this.nodes, this.limits);
  }
  /** Private generated state only. Loading never starts a session or dispatches an action. */
  static restore(state, limits) {
    if (!SUPPORTED_VERSIONS.includes(state?.version)) throw Error('Invalid trace cache');
    const stateKeys = state && typeof state === 'object' ? Object.keys(state).filter(
      k => state.version < VERSION || !['goalTerminals', 'suffixProfiles', 'slotRoles'].includes(k),
    ).sort().join() : '';
    const allAllowed = state && typeof state === 'object'
      && Object.keys(state).every(k => ['version', 'key', 'limits', 'nodes', 'goalTerminals', 'suffixProfiles', 'slotRoles'].includes(k));
    const validStateKeys = allAllowed && stateKeys === 'key,limits,nodes,version'
      && (state.version >= VERSION || (state.goalTerminals === undefined && state.suffixProfiles === undefined && state.slotRoles === undefined));
    const dag = new TraceDag(limits, { version: state.version });
    if (!validStateKeys || !HASH.test(state.key)
      || canonicalJson(state.limits) !== canonicalJson(limits) || !Array.isArray(state.nodes)
      || state.nodes.length > limits.maxNodes) throw Error('Invalid trace cache');
    const nodes = new Map();
    let edges = 0;
    const expectedKeys = state.version === 1 ? 'depth,edges,terminal' : 'depth,edges,repairs,terminal';
    for (const entry of state.nodes) {
      if (!Array.isArray(entry) || entry.length !== 2) throw Error('Invalid trace node');
      const [id, node] = entry;
      if (!HASH.test(id) || nodes.has(id) || !node || Object.keys(node).sort().join() !== expectedKeys
        || !Number.isSafeInteger(node.depth) || node.depth < 0 || node.depth > limits.maxSteps
        || typeof node.terminal !== 'boolean' || !Array.isArray(node.edges)) throw Error('Invalid trace node');
      const repairs = state.version === 1 ? [] : node.repairs;
      if (!Array.isArray(repairs) || repairs.some(next => !HASH.test(next)) || new Set(repairs).size !== repairs.length) {
        throw Error('Invalid trace repair');
      }
      edges += repairs.length;
      if (edges + node.edges.length > limits.maxEdges) throw Error('Trace edge limit');
      for (const edge of node.edges) {
        if (!validEdgeShape(edge, state.version)
          || !HASH.test(edge.next) || !edge.step || Object.keys(edge.step).sort().join() !== 'kind,locator,slot'
          || !KINDS.includes(edge.step.kind) || !HASH.test(edge.step.locator)
          || (edge.step.kind === 'click' ? edge.step.slot !== null : !HASH.test(edge.step.slot))) {
          throw Error('Invalid trace edge');
        }
        edges++;
      }
      const cloned = structuredClone(node);
      if (state.version === 1) cloned.repairs = [];
      nodes.set(id, cloned);
    }
    if (edges > limits.maxEdges) throw Error('Trace edge limit');
    for (const [id, node] of nodes) for (const next of node.repairs) {
      // One narrowing bridge from group identity to exact-page identity, never a chain or cycle.
      const target = nodes.get(next);
      const invalidDepth = state.version < VERSION ? target?.depth !== node.depth : target?.depth < node.depth;
      if (next === id || !target || invalidDepth || target.repairs.length || node.terminal) {
        throw Error('Invalid trace repair boundary');
      }
    }
    if (state.version < VERSION) {
      for (const node of nodes.values()) for (const edge of node.edges) {
        if (nodes.get(edge.next)?.depth !== node.depth + 1) throw Error('Trace must be acyclic');
      }
    } else {
      topologicalSort(nodes, limits.maxSteps);
    }
    const goalTerminals = new Map();
    if (state.goalTerminals !== undefined) {
      if (!Array.isArray(state.goalTerminals) || !state.goalTerminals.length) throw Error('Invalid trace goalTerminals');
      for (const item of state.goalTerminals) {
        if (!Array.isArray(item) || item.length !== 2) throw Error('Invalid trace goalTerminals');
        const [goalHash, ids] = item;
        if (!HASH.test(goalHash) || goalTerminals.has(goalHash) || !Array.isArray(ids) || !ids.length
          || ids.some(id => !HASH.test(id) || !nodes.get(id)?.terminal) || new Set(ids).size !== ids.length) {
          throw Error('Invalid trace goalTerminals');
        }
        goalTerminals.set(goalHash, [...ids].sort());
      }
    }
    const suffixProfiles = validateSuffixProfiles(state.suffixProfiles, nodes);
    const slotRoles = new Map();
    if (state.slotRoles !== undefined) {
      if (!Array.isArray(state.slotRoles)) throw Error('Invalid trace slotRoles');
      for (const item of state.slotRoles) {
        if (!Array.isArray(item) || item.length !== 2 || !HASH.test(item[0]) || typeof item[1] !== 'string' || !item[1].trim()) {
          throw Error('Invalid trace slotRoles');
        }
        slotRoles.set(item[0], item[1]);
      }
    }
    dag.key = state.key;
    dag.nodes = nodes;
    dag.goalTerminals = goalTerminals;
    dag.suffixProfiles = suffixProfiles;
    dag.slotRoles = slotRoles;
    return dag;
  }
  /** Union same-key private snapshots, reducing dominated detours in v3. */
  static merge(left, right, limits) {
    const a = TraceDag.restore(left, limits), b = TraceDag.restore(right, limits);
    if (a.key !== b.key) throw Error('Workflow key lineage differs');
    if (a.version !== b.version && (a.version < VERSION || b.version < VERSION)
      && (a.version === VERSION || b.version === VERSION)) {
      throw Error('Cannot merge ordered-prefix legacy graph with state-reconvergent v3 graph');
    }
    const targetVersion = Math.max(a.version, b.version, 2);
    for (const [id, incoming] of b.nodes) {
      const node = a.nodes.get(id);
      if (!node) { a.nodes.set(id, incoming); continue; }
      if (targetVersion < VERSION && node.depth !== incoming.depth) throw Error('Workflow depth differs');
      node.terminal ||= incoming.terminal;
      for (const next of incoming.repairs) if (!node.repairs.includes(next)) node.repairs.push(next);
      for (const edge of incoming.edges) {
        const match = node.edges.find(existing => existing.next === edge.next
          && canonicalJson(existing.step) === canonicalJson(edge.step));
        if (!match) {
          node.edges.push(edge);
        } else if (edge.weight !== undefined || match.weight !== undefined) {
          match.weight = Math.min(match.weight ?? 1, edge.weight ?? 1);
        }
      }
    }
    if (targetVersion === VERSION) {
      const { nodes: reduced } = reduceTraceGraph(a.nodes, limits);
      const mergedGoals = new Map([...a.goalTerminals.entries()].map(([g, ids]) => [g, [...ids]]));
      for (const [g, ids] of b.goalTerminals) {
        mergedGoals.set(g, [...new Set([...(mergedGoals.get(g) ?? []), ...ids])]);
      }
      const normGoals = normalizeGoalTerminals(mergedGoals, reduced);
      const mergedProfiles = mergeSuffixProfiles(a.suffixProfiles, b.suffixProfiles, reduced);
      const mergedRoles = new Map([...a.slotRoles, ...b.slotRoles]);
      return TraceDag.restore({
        version: VERSION,
        key: a.key,
        limits,
        nodes: [...reduced],
        ...(normGoals.size ? { goalTerminals: [...normGoals] } : {}),
        ...(mergedProfiles.size ? { suffixProfiles: [...mergedProfiles] } : {}),
        ...(mergedRoles.size ? { slotRoles: [...mergedRoles].sort(([x], [y]) => x.localeCompare(y)) } : {}),
      }, limits);
    }
    for (const node of a.nodes.values()) {
      node.edges.sort((x, y) => canonicalJson(x).localeCompare(canonicalJson(y)));
      node.repairs.sort();
    }
    return TraceDag.restore({
      version: targetVersion,
      key: a.key,
      limits,
      nodes: [...a.nodes].sort(([x], [y]) => x.localeCompare(y)),
    }, limits);
  }
  /** Stitch sequential/modular v3 recipes sharing a key so first's terminals hand off into second. */
  static compose(first, second, limits) {
    const a = TraceDag.restore(first, limits), b = TraceDag.restore(second, limits);
    if (a.version !== VERSION || b.version !== VERSION) {
      throw Error('Recipe composition requires v3 state-reconvergent graphs');
    }
    if (a.key !== b.key) throw Error('Workflow key lineage differs');
    const combined = new Map([...a.nodes].map(([id, node]) => [id, structuredClone(node)]));
    for (const [id, incoming] of b.nodes) {
      const existing = combined.get(id);
      if (!existing) {
        combined.set(id, structuredClone(incoming));
        continue;
      }
      const continuesInSecond = !incoming.terminal && (incoming.edges.length > 0 || incoming.repairs.length > 0);
      existing.terminal = continuesInSecond ? false : (existing.terminal || incoming.terminal);
      for (const next of incoming.repairs) if (!existing.repairs.includes(next)) existing.repairs.push(next);
      for (const edge of incoming.edges) {
        const match = existing.edges.find(prev => prev.next === edge.next
          && canonicalJson(prev.step) === canonicalJson(edge.step));
        if (!match) {
          existing.edges.push(structuredClone(edge));
        } else if (edge.weight !== undefined || match.weight !== undefined) {
          match.weight = Math.min(match.weight ?? 1, edge.weight ?? 1);
        }
      }
    }
    const { nodes: reduced } = reduceTraceGraph(combined, limits);
    const composedGoals = new Map([...a.goalTerminals.entries()].map(([g, ids]) => [g, [...ids]]));
    for (const [g, ids] of b.goalTerminals) {
      composedGoals.set(g, [...new Set([...(composedGoals.get(g) ?? []), ...ids])]);
    }
    const normGoals = normalizeGoalTerminals(composedGoals, reduced);
    const composedProfiles = mergeSuffixProfiles(a.suffixProfiles, b.suffixProfiles, reduced);
    const composedRoles = new Map([...a.slotRoles, ...b.slotRoles]);
    return TraceDag.restore({
      version: VERSION,
      key: a.key,
      limits,
      nodes: [...reduced],
      ...(normGoals.size ? { goalTerminals: [...normGoals] } : {}),
      ...(composedProfiles.size ? { suffixProfiles: [...composedProfiles] } : {}),
      ...(composedRoles.size ? { slotRoles: [...composedRoles].sort(([x], [y]) => x.localeCompare(y)) } : {}),
    }, limits);
  }
  static composeAll(graphs, limits) {
    if (!Array.isArray(graphs) || graphs.length < 1) throw Error('At least one recipe graph is required');
    let acc = TraceDag.restore(graphs[0], limits);
    for (let i = 1; i < graphs.length; i++) {
      acc = TraceDag.compose(acc.export(), graphs[i], limits);
    }
    return acc;
  }
  session(options) {
    if (options.fieldGroups && (!options.accountScope || typeof options.assertContext !== 'function'
      || typeof options.authorizeStep !== 'function')) throw Error('Scoped reuse requires account and disclosure verifiers');
    return new TraceSession(this, options);
  }
  publish(records, terminal, repairs = [], { pruneDetours = true, suffixProfiles = null, slotRoles = null } = {}) {
    const nodes = new Map([...this.nodes].map(([id, node]) => [id, structuredClone(node)]));
    if (this.version < VERSION) {
      for (const { id, depth, step, next } of records) {
        const node = nodes.get(id) ?? { depth, edges: [], repairs: [], terminal: false };
        if (!node.edges.some(edge => canonicalJson(edge) === canonicalJson({ step, next }))) node.edges.push({ step, next });
        nodes.set(id, node);
      }
      for (const { id, depth, next } of repairs) {
        const node = nodes.get(id) ?? { depth, edges: [], repairs: [], terminal: false };
        if (!node.repairs.includes(next)) node.repairs.push(next);
        nodes.set(id, node);
      }
      const node = nodes.get(terminal.id) ?? { depth: terminal.depth, edges: [], repairs: [], terminal: false };
      node.terminal = true;
      nodes.set(terminal.id, node);
      const nextVersion = 2;
      const restored = TraceDag.restore({ version: nextVersion, key: this.key, limits: this.limits, nodes: [...nodes] }, this.limits);
      this.version = nextVersion;
      this.nodes = restored.nodes;
      return;
    }

    const compressed = compressTraceRecords(records, terminal);
    for (const { id, depth, step, next, weight } of compressed.records) {
      const node = nodes.get(id) ?? { depth, edges: [], repairs: [], terminal: false };
      const incomingEdge = weight !== undefined ? { next, step, weight } : { next, step };
      const existing = node.edges.find(edge => edge.next === next && canonicalJson(edge.step) === canonicalJson(step));
      if (!existing) {
        node.edges.push(incomingEdge);
      } else if (weight !== undefined || existing.weight !== undefined) {
        existing.weight = Math.min(existing.weight ?? 1, weight ?? 1);
      }
      nodes.set(id, node);
    }
    for (const { id, depth, next } of repairs) {
      const node = nodes.get(id) ?? { depth, edges: [], repairs: [], terminal: false };
      if (!node.repairs.includes(next)) node.repairs.push(next);
      nodes.set(id, node);
    }
    const term = compressed.terminal;
    const termNode = nodes.get(term.id) ?? { depth: term.depth, edges: [], repairs: [], terminal: false };
    termNode.terminal = true;
    nodes.set(term.id, termNode);

    const nextGoals = new Map([...this.goalTerminals.entries()].map(([g, ids]) => [g, [...ids]]));
    if (term.goal) {
      nextGoals.set(term.goal, [...new Set([...(nextGoals.get(term.goal) ?? []), term.id])]);
    }
    const { nodes: reduced } = reduceTraceGraph(nodes, this.limits, { pruneDeadEnds: true, pruneDetours });
    const normGoals = normalizeGoalTerminals(nextGoals, reduced);
    const incomingProfiles = suffixProfiles instanceof Map
      ? suffixProfiles
      : Array.isArray(suffixProfiles) ? new Map(suffixProfiles) : new Map();
    const mergedProfiles = mergeSuffixProfiles(this.suffixProfiles, incomingProfiles, reduced);
    const incomingRoles = slotRoles instanceof Map
      ? slotRoles
      : Array.isArray(slotRoles) ? new Map(slotRoles) : new Map();
    const mergedRoles = new Map([...this.slotRoles, ...incomingRoles]);
    const restored = TraceDag.restore({
      version: VERSION,
      key: this.key,
      limits: this.limits,
      nodes: [...reduced],
      ...(normGoals.size ? { goalTerminals: [...normGoals] } : {}),
      ...(mergedProfiles.size ? { suffixProfiles: [...mergedProfiles] } : {}),
      ...(mergedRoles.size ? { slotRoles: [...mergedRoles].sort(([x], [y]) => x.localeCompare(y)) } : {}),
    }, this.limits);
    this.nodes = restored.nodes;
    this.goalTerminals = restored.goalTerminals;
    this.suffixProfiles = restored.suffixProfiles;
    this.slotRoles = restored.slotRoles;
  }
}

/** Explicit session API for a controller/workflow, not model-provided policy.
 * intermediateClicks contains trusted structural locator tuples, never selectors.
 * Changing template purpose requires a new template string.
 */
class TraceSession {
  constructor(dag, { service, owner, pageId, intent, template, inputs = {}, intermediateClicks = [], signal,
    assertContext = async () => {}, authorizeStep = async () => {}, accountScope = null, fieldGroups = null, goal = null,
    suffixIndex = null, executedSteps = [],
    suffixEligibility = false, slotRoles = null, inertFormLocators = [],
    assertPrerequisite = null, requirePrerequisiteCheck = false }) {
    if (typeof template !== 'string' || !template || typeof pageId !== 'string' || !pageId
      || typeof intent !== 'string' || !intent) throw Error('Trace requires template, pageId and intent');
    if (goal !== null && (typeof goal !== 'string' || !goal.trim())) throw Error('Invalid trace goal');
    if (requirePrerequisiteCheck && typeof assertPrerequisite !== 'function') {
      throw Object.assign(Error('Write boundary requires an explicit server-side assertPrerequisite check'), {
        code: 'missing-prerequisite-check',
      });
    }
    this.dag = dag;
    this.service = service;
    this.supportsRegionDeltas = typeof service?.reconcile === 'function' || service?.supportsRegionDeltas === true;
    this.identity = { ...owner, pageId };
    this.intent = intent;
    this.template = template;
    this.goal = goal;
    this.goalHash = goal !== null ? dag.hash(['goal', goal]) : null;
    if (accountScope !== null && (typeof accountScope !== 'string' || !accountScope.trim())) throw Error('Invalid trace account scope');
    this.accountScope = accountScope;
    this.fieldScope = fieldGroups ? createFieldGroupScope(fieldGroups, dag.limits.maxSteps) : null;
    // Opt-in: without suffixIndex or suffixEligibility every path below behaves exactly as before.
    this.suffixIndex = suffixIndex;
    this.priorSteps = structuredClone(executedSteps);
    this.suffixEligibility = Boolean(suffixEligibility);
    this.slotRolesPolicy = slotRoles ? structuredClone(slotRoles) : null;
    this.inertFormLocators = Array.isArray(inertFormLocators) ? structuredClone(inertFormLocators) : [];
    this.assertPrerequisite = assertPrerequisite;
    this.requirePrerequisiteCheck = Boolean(requirePrerequisiteCheck);
    this.options = { service, owner, pageId, intent, template, inputs, intermediateClicks, signal,
      assertContext, authorizeStep, accountScope, fieldGroups, goal,
      suffixIndex, executedSteps,
      suffixEligibility: this.suffixEligibility, slotRoles: this.slotRolesPolicy, inertFormLocators: this.inertFormLocators,
      assertPrerequisite: this.assertPrerequisite, requirePrerequisiteCheck: this.requirePrerequisiteCheck };
    const roleBinding = resolveRoleBoundInputs({
      inputs,
      slotRoles: this.slotRolesPolicy,
      learnedSlotRoles: dag.slotRoles,
      hashFn: value => dag.hash(value),
    });
    this.boundInputs = roleBinding.bound;
    this.ambiguousRoles = roleBinding.ambiguousRoles;
    this.inputs = new Map([...roleBinding.bound.entries()].map(([slotHash, entry]) => [slotHash, entry.value]));
    this.slotNames = new Map([...roleBinding.bound.entries()].map(([slotHash, entry]) => [slotHash, entry.slotName]));
    this.assertContext = assertContext;
    this.authorizeStep = authorizeStep;
    this.clicks = new Set(intermediateClicks.map(locator => dag.hash(['locator', locator])));
    this.signal = signal;
    this.prefix = dag.hash(['start']);
    this.outlineSlots = [];
    this.sameOutlineClicks = 0;
    this.groupProgress = this.fieldScope ? this.fieldScope.initialProgress() : null;
    this.depth = 0;
    this.records = [];
    this.repairs = [];
    this.stagedSuffixProfiles = new Map();
    this.stagedSlotRoles = new Map();
    this.certifiedSuffixRejoins = [];
    this.lastObservationVersion = null;
    this.lastObservation = null;
    this.regionSelectors = [];
    this.stage0Profile = {
      actionsCount: 0,
      valueActionsCount: 0,
      regionScopedActions: 0,
      observationCalls: 0,
      currentRevisionReuses: 0,
      sinceVersionDeltaChecks: 0,
      sinceVersionUnchangedRegions: 0,
      sinceVersionChangedRegions: 0,
      dispatchCheckMs: 0,
      browserExecuteMs: 0,
      valueSettleMs: 0,
      postSnapshotMs: 0,
      journalBeforeOutcomeMs: 0,
      totalDispatchMs: 0,
      observeElapsedMs: 0,
    };
    this.traceEvents = [];
    this.repairedSession = false;
    this.nextId = null;
    this.terminal = null;
    this.stopped = false;
    this.busy = false;
  }
  stop(reason, result) {
    this.stopped = true;
    this.stopReason = reason;
    return { status: 'stopped', reason, steps: this.depth, ...(result ? { result } : {}) };
  }
  async exclusive(task) {
    if (this.busy || this.stopped) throw Error('Trace session is busy or stopped; no implicit resume');
    this.busy = true;
    try { this.signal?.throwIfAborted(); return await task(); }
    catch (error) { this.stopped = true; throw error; }
    finally { this.busy = false; }
  }
  async assertSettled() {
    this.signal?.throwIfAborted();
    await this.assertContext();
    const outstanding = await this.service.outstanding(this.identity);
    if (outstanding.some(action => action.isUncertain || action.dispatchStatus === 'queued'
      || (action.dispatchStatus === 'dispatched' && !action.outcome))) {
      throw Error('Resolve outstanding actions before recording or replaying a trace');
    }
  }
  frame(observation, fieldScope = this.fieldScope, stateOverride = null) {
    if (observation.isTruncated !== false || !Array.isArray(observation.elements)) {
      throw Error('Trace requires a complete element observation');
    }
    const baseScope = [this.template, new URL(observation.url).origin, observation.readScope ?? null];
    if (this.accountScope !== null) baseScope.push(this.accountScope);
    const computeV3 = () => {
      const scope = [...baseScope];
      if (fieldScope) {
        const groupState = stateOverride ?? this.groupProgress;
        const outline = fieldScope.outline(observation, groupState);
        scope.push(['verified-field-groups-v1', fieldScope.policy]);
        const stateKey = ['scoped-v3', groupState.groupIndex, groupState.filledSlots];
        return { observation, id: this.dag.hash([scope, stateKey, outline]), outline };
      }
      const outline = structuralOutlineHash(observation.elements);
      const outlineSlots = stateOverride?.outlineSlots ?? this.outlineSlots;
      const sameOutlineClicks = stateOverride?.sameOutlineClicks ?? this.sameOutlineClicks;
      const stateKey = observation.elements.length === 0 && this.goalHash !== null
        ? ['state-v3-goal-leaf', this.goalHash]
        : ['state-v3', outlineSlots, sameOutlineClicks];
      return { observation, id: this.dag.hash([scope, stateKey, outline]), outline,
        meta: { scope: this.dag.hash(['suffix-scope', scope]), slots: outlineSlots, clicks: sameOutlineClicks } };
    };
    if (this.dag.version < VERSION) {
      const scope = [...baseScope];
      const outline = fieldScope ? fieldScope.outline(observation, this.depth)
        : structuralOutlineHash(observation.elements);
      if (fieldScope) scope.push(['verified-field-groups-v1', fieldScope.policy]);
      const legacyId = this.dag.hash([scope, this.prefix, outline]);
      if (this.dag.nodes.size === 0 || this.dag.nodes.has(legacyId)) {
        return { observation, id: legacyId, outline };
      }
      const v3Frame = computeV3();
      if (this.dag.nodes.has(v3Frame.id)) return v3Frame;
      return { observation, id: legacyId, outline };
    }
    return computeV3();
  }
  /** The index matcher reads form state on every frame it judges, so the session asks for it
   * whether or not the profile matcher is on (suffix-repair-rules.md, rule 1). */
  get wantsFormState() {
    return this.suffixEligibility || Boolean(this.suffixIndex);
  }
  get plainObserveCommand() {
    return this.suffixIndex ? { ...this.identity, includeFormState: true } : this.identity;
  }
  async observe({ ifCurrentVersion, sinceVersion } = {}) {
    if (ifCurrentVersion === undefined) {
      await this.assertSettled();
    } else {
      this.signal?.throwIfAborted();
    }
    const obsT0 = performance.now();
    const regionCommand = this.supportsRegionDeltas
      ? {
          ...this.identity,
          ...(this.regionSelectors.length ? { regions: this.regionSelectors } : { autoControlRegions: true }),
          ...(ifCurrentVersion !== undefined ? { ifCurrentVersion } : {}),
          ...(this.wantsFormState ? { includeFormState: true } : {}),
        }
      : this.plainObserveCommand;
    const obs = await this.service.observe(regionCommand);
    this.stage0Profile.observationCalls += 1;
    if (ifCurrentVersion !== undefined && obs.observationVersion === ifCurrentVersion) {
      this.stage0Profile.currentRevisionReuses += 1;
    }
    if (this.supportsRegionDeltas && Array.isArray(obs.elements)) {
      const registeredRegions = obs.regions ? Object.keys(obs.regions) : [];
      this.regionSelectors = registeredRegions.length > 0
        ? registeredRegions.slice(0, 16)
        : [...new Set(obs.elements.map(e => e.selector).filter(Boolean))].slice(0, 16);
      if (sinceVersion !== undefined && this.regionSelectors.length > 0 && Number.isInteger(obs.observationVersion)) {
        const delta = await this.service.observe({
          ...this.identity,
          regions: this.regionSelectors,
          view: 'outline',
          sinceVersion,
          ifCurrentVersion: obs.observationVersion,
          ...(this.wantsFormState ? { includeFormState: true } : {}),
        });
        this.stage0Profile.sinceVersionDeltaChecks += 1;
        for (const entry of Object.values(delta.regions ?? {})) {
          if (entry?.unchanged) this.stage0Profile.sinceVersionUnchangedRegions += 1;
          else this.stage0Profile.sinceVersionChangedRegions += 1;
        }
      }
    }
    this.stage0Profile.observeElapsedMs = Number(
      (this.stage0Profile.observeElapsedMs + (performance.now() - obsT0)).toFixed(3),
    );
    this.lastObservationVersion = Number.isInteger(obs.observationVersion) ? obs.observationVersion : null;
    this.lastObservation = obs;
    return this.frame(obs);
  }
  async execute(before, step) {
    if (this.depth >= this.dag.limits.maxSteps) return this.stop('step-limit');
    const progressArg = this.dag.version < VERSION ? this.depth : this.groupProgress;
    const matches = before.observation.elements.filter(element => this.fieldScope
      ? this.fieldScope.matches(step, element, progressArg, this.dag)
      : this.dag.hash(['locator', structuralLocator(element)]) === step.locator);
    if (matches.length !== 1) return this.stop(matches.length ? 'ambiguous-locator' : 'missing-locator');
    const element = matches[0];
    if (!element.label || element.formAction || ['submit', 'image', 'file', 'password', 'hidden'].includes(element.inputType)) {
      return this.stop('unsupported-target');
    }
    if (step.kind === 'click' && !this.clicks.has(step.locator)) return this.stop('intermediate-click-not-authorized');
    if (step.kind !== 'click' && (!this.inputs.has(step.slot) || typeof this.inputs.get(step.slot) !== 'string')) {
      return this.stop('missing-input-slot');
    }
    await this.assertContext();
    const origin = new URL(before.observation.url).origin;
    const locator = structuralLocator(element);
    const slot = this.slotNames.get(step.slot) ?? null;
    await this.authorizeStep({ origin, kind: step.kind, locator, slot });
    if (typeof this.assertPrerequisite === 'function') {
      const prereq = await this.assertPrerequisite({
        origin, url: before.observation.url, kind: step.kind, locator, slot, stepIndex: this.depth,
      });
      if (prereq === false || prereq?.ok === false) {
        throw Object.assign(Error(prereq?.reason || 'Server prerequisite check refused action'), {
          code: 'prerequisite-refused',
        });
      }
    }
    this.signal?.throwIfAborted();
    const useRegionScope = this.supportsRegionDeltas
      && (step.kind === 'fill' || step.kind === 'select')
      && Boolean(element.selector && before.observation.regions?.[element.selector]);
    if (useRegionScope) this.stage0Profile.regionScopedActions += 1;
    const admitted = await this.service.submitAction({ ...this.identity, actionId: randomUUID(),
      authorizedIntent: this.intent, observationVersion: before.observation.observationVersion,
      ...(useRegionScope ? { observationScope: { kind: 'regions', selectors: [element.selector] } } : {}),
      kind: step.kind, target: { handle: element.handle, selector: element.selector, digest: element.digest },
      ...(step.kind === 'click' ? {} : { params: { value: this.inputs.get(step.slot) } }) });
    const result = await admitted.result;
    const prof = result.evidence?.dispatchProfileMs;
    if (prof) {
      this.stage0Profile.actionsCount += 1;
      if (step.kind !== 'click') this.stage0Profile.valueActionsCount += 1;
      this.stage0Profile.dispatchCheckMs = Number((this.stage0Profile.dispatchCheckMs + (prof.dispatchCheckMs ?? 0)).toFixed(3));
      this.stage0Profile.browserExecuteMs = Number((this.stage0Profile.browserExecuteMs + (prof.browserExecuteMs ?? 0)).toFixed(3));
      this.stage0Profile.valueSettleMs = Number((this.stage0Profile.valueSettleMs + (prof.valueSettleMs ?? 0)).toFixed(3));
      this.stage0Profile.postSnapshotMs = Number((this.stage0Profile.postSnapshotMs + (prof.postSnapshotMs ?? 0)).toFixed(3));
      this.stage0Profile.journalBeforeOutcomeMs = Number((this.stage0Profile.journalBeforeOutcomeMs + (prof.journalBeforeOutcomeMs ?? 0)).toFixed(3));
      this.stage0Profile.totalDispatchMs = Number((this.stage0Profile.totalDispatchMs + (prof.totalDispatchMs ?? 0)).toFixed(3));
    }
    if (result.outcome !== 'completed') return this.stop('action-not-completed', result);
    this.depth++;
    this.prefix = this.dag.hash([this.prefix, step]);
    let after;
    if (this.supportsRegionDeltas && Number.isInteger(result.postObservationVersion)) {
      const prevOutline = before.outline;
      if (step.kind === 'click') {
        this.regionSelectors = [];
      }
      after = await this.observe({
        ifCurrentVersion: result.postObservationVersion,
        sinceVersion: step.kind !== 'click' ? before.observation.observationVersion : undefined,
      });
      const afterObs = after.observation;
      if (afterObs.isTruncated !== false || !Array.isArray(afterObs.elements)) {
        throw Error('Trace requires a complete element observation');
      }
      if (this.fieldScope) {
        this.groupProgress = this.fieldScope.advanceProgress(this.groupProgress, step);
      } else {
        const nextOutline = structuralOutlineHash(afterObs.elements);
        if (nextOutline !== prevOutline) {
          this.outlineSlots = [];
          this.sameOutlineClicks = 0;
          this.regionSelectors = [...new Set(afterObs.elements.map(e => e.selector).filter(Boolean))].slice(0, 16);
        } else if (step.kind === 'click') {
          this.sameOutlineClicks += 1;
        } else if (!this.outlineSlots.includes(step.slot)) {
          this.outlineSlots = [...this.outlineSlots, step.slot].sort();
        }
      }
      after = this.frame(afterObs);
    } else {
      await this.assertSettled();
      const afterObs = await this.service.observe(this.plainObserveCommand);
      if (afterObs.isTruncated !== false || !Array.isArray(afterObs.elements)) {
        throw Error('Trace requires a complete element observation');
      }
      this.lastObservationVersion = Number.isInteger(afterObs.observationVersion) ? afterObs.observationVersion : null;
      this.lastObservation = afterObs;
      if (this.fieldScope) {
        this.groupProgress = this.fieldScope.advanceProgress(this.groupProgress, step);
      } else {
        const nextOutline = structuralOutlineHash(afterObs.elements);
        if (nextOutline !== before.outline) {
          this.outlineSlots = [];
          this.sameOutlineClicks = 0;
        } else if (step.kind === 'click') {
          this.sameOutlineClicks += 1;
        } else if (!this.outlineSlots.includes(step.slot)) {
          this.outlineSlots = [...this.outlineSlots, step.slot].sort();
        }
      }
      after = this.frame(afterObs);
    }
    return {
      status: 'completed',
      result,
      after,
      label: element.label,
      slotName: step.kind === 'click' ? null : (this.slotNames.get(step.slot) ?? null),
    };
  }
  #stageNodeProfile(before, spec, step) {
    if (!this.suffixEligibility || this.fieldScope) return;
    const { origin, routePattern } = normalizeRoutePattern(before.observation.url);
    const existing = this.stagedSuffixProfiles.get(before.id);
    const locatorTable = new Map(existing?.locatorTable ?? []);
    locatorTable.set(step.locator, spec.locator);
    const slotLocators = new Map(existing?.slotLocators ?? []);
    if (step.slot) {
      slotLocators.set(step.slot, spec.locator);
      const role = this.slotRolesPolicy?.[spec.slot];
      if (typeof role === 'string' && role.trim()) {
        this.stagedSlotRoles.set(step.slot, role);
      }
    }
    for (const reqSlotHash of this.outlineSlots) {
      if (slotLocators.has(reqSlotHash)) continue;
      const expectedVal = this.inputs.get(reqSlotHash);
      const matchEl = before.observation.elements.find(el => el.value === expectedVal);
      if (matchEl) slotLocators.set(reqSlotHash, structuralLocator(matchEl));
    }
    const onScreenStepLocators = [...new Set([...(existing?.onScreenStepLocators ?? []), step.locator])].sort();
    const referenceControls = (before.observation.elements ?? []).map(el => ({
      locator: structuralLocator(el),
      value: el.value ?? null,
      text: el.text ?? '',
    }));
    this.stagedSuffixProfiles.set(before.id, {
      origin,
      routePattern,
      locatorTable: [...locatorTable.entries()].sort(([a], [b]) => a.localeCompare(b)),
      slotLocators: [...slotLocators.entries()].sort(([a], [b]) => a.localeCompare(b)),
      onScreenStepLocators,
      requiredSlots: [...this.outlineSlots],
      sameOutlineClicks: this.sameOutlineClicks,
      referenceControls,
      extraGuards: existing?.extraGuards ?? [],
      requiresExactPrefix: false,
    });
  }
  /** Slot provenance is structural: callers cannot pass a literal params.value at this API. */
  record(spec, observation = null, { weight } = {}) {
    return this.exclusive(async () => {
      if (!spec || Object.keys(spec).some(key => !['kind', 'locator', 'slot'].includes(key))
        || !KINDS.includes(spec.kind) || !Array.isArray(spec.locator) || spec.locator.length !== 4
        || spec.locator.some(value => typeof value !== 'string')
        || (spec.kind === 'click' ? spec.slot !== undefined : typeof spec.slot !== 'string')) {
        return this.stop('uncacheable-step');
      }
      if (weight !== undefined && (typeof weight !== 'number' || !Number.isFinite(weight) || weight <= 0)) {
        throw Error('Invalid trace step weight');
      }
      const step = { kind: spec.kind, locator: this.dag.hash(['locator', spec.locator]),
        slot: spec.kind === 'click' ? null : this.dag.hash(['slot', spec.slot]) };
      // A planner must execute against the observation it actually saw, not silently rebind
      // its decision after the page changes. Cache replay still resolves a fresh live target.
      await this.assertSettled();
      if (observation) {
        this.lastObservationVersion = Number.isInteger(observation.observationVersion) ? observation.observationVersion : null;
        this.lastObservation = observation;
      }
      const before = observation ? this.frame(observation) : await this.observe();
      if (this.nextId && this.nextId !== before.id) return this.stop('unseen-branch');
      const beforeSlotsSnapshot = [...this.outlineSlots];
      const beforeClicksSnapshot = this.sameOutlineClicks;
      const depth = this.depth;
      const executed = await this.execute(before, step);
      if (executed.status === 'completed') {
        this.suffixIndex?.note(this.dag, before);
        this.suffixIndex?.note(this.dag, executed.after);
        if (this.suffixEligibility && !this.fieldScope) {
          const savedSlots = this.outlineSlots;
          const savedClicks = this.sameOutlineClicks;
          this.outlineSlots = beforeSlotsSnapshot;
          this.sameOutlineClicks = beforeClicksSnapshot;
          this.#stageNodeProfile(before, spec, step);
          this.outlineSlots = savedSlots;
          this.sameOutlineClicks = savedClicks;
        }
        this.records.push({
          id: before.id,
          depth,
          step,
          next: executed.after.id,
          ...(weight !== undefined ? { weight } : {}),
        });
        this.traceEvents.push({
          phase: this.repairedSession ? 'repaired-edge' : 'learned-edge',
          stepIndex: depth,
          kind: spec.kind,
          label: executed.label,
          slot: spec.slot ?? null,
          fromNode: before.id.slice(0, 12),
          toNode: executed.after.id.slice(0, 12),
        });
        this.nextId = executed.after.id;
      }
      return { status: executed.status, reason: executed.reason, result: executed.result };
    });
  }
  /** Resume only a structural miss, with the actual executed prefix. No browser effect occurs
   * here. A group-to-exact bridge narrows the remaining recipe; it never guesses group meaning.
   * The caller still must independently verify the whole result before finish/publication.
   */
  async repair() {
    if (this.busy || !this.stopped || !REPAIRABLE.has(this.stopReason)) throw Error('Trace stop cannot teach a repair');
    const before = await this.observe(
      this.supportsRegionDeltas && this.lastObservationVersion !== null
        ? { ifCurrentVersion: this.lastObservationVersion }
        : undefined,
    );
    if (this.nextId && this.nextId !== before.id) throw Error('Repair prefix changed; no verified continuation');
    const continuation = new TraceSession(this.dag, { ...this.options, fieldGroups: null });
    continuation.prefix = this.prefix;
    continuation.outlineSlots = this.fieldScope ? [...this.groupProgress.filledSlots] : [...this.outlineSlots];
    continuation.sameOutlineClicks = this.sameOutlineClicks;
    continuation.depth = this.depth;
    continuation.priorSteps = structuredClone(this.priorSteps);
    continuation.records = structuredClone(this.records);
    continuation.repairs = structuredClone(this.repairs);
    continuation.stagedSuffixProfiles = new Map(this.stagedSuffixProfiles);
    continuation.stagedSlotRoles = new Map(this.stagedSlotRoles);
    continuation.certifiedSuffixRejoins = structuredClone(this.certifiedSuffixRejoins);
    continuation.stage0Profile = structuredClone(this.stage0Profile);
    continuation.lastObservationVersion = this.lastObservationVersion;
    continuation.lastObservation = this.lastObservation;
    continuation.regionSelectors = [...this.regionSelectors];
    continuation.traceEvents = structuredClone(this.traceEvents);
    continuation.repairedSession = true;
    const exact = continuation.frame(before.observation);
    if (this.fieldScope) continuation.repairs.push({ id: before.id, depth: this.depth, next: exact.id });
    continuation.nextId = exact.id;
    return continuation;
  }
  #suffixEnabled(dp) {
    return Boolean(this.suffixIndex && dp && !this.fieldScope && this.dag.version >= VERSION);
  }
  /** Ask whether a learned node's remaining local steps hold on this live frame. No effect occurs here. */
  #certifySuffix(before, dp, expected) {
    const outcome = certifySuffix({ dag: this.dag, index: this.suffixIndex, dp, frame: before, restrictTo: expected,
      session: { inputs: this.inputs, clicks: this.clicks, sameOutlineClicks: this.sameOutlineClicks,
        inertFormLocators: this.inertFormLocators,
        // Fresh: the frame must be the session's latest observation, never one carried over.
        formStateFresh: before.observation === this.lastObservation,
        executedSteps: [...this.priorSteps, ...this.records.map(record => record.step)],
        isGoalTerminal: (id, node) => this.#isGoalTerminal(id, node) } });
    this.traceEvents.push({
      phase: outcome.status === 'certified' ? 'suffix-certified' : 'suffix-refused',
      atStep: this.depth,
      node: before.id.slice(0, 12),
      ...(outcome.status === 'certified'
        ? { learnedNode: outcome.nodeId.slice(0, 12) }
        : { reason: outcome.reason, refusals: outcome.refusals }),
    });
    return outcome.status === 'certified' ? outcome : null;
  }
  #isGoalTerminal(nodeId, node) {
    if (!node?.terminal) return false;
    if (this.goalHash === null) return true;
    return Boolean(this.dag.goalTerminals.get(this.goalHash)?.includes(nodeId));
  }
  #isVerifiedSuffixTransition(exactEdges, targetNodeId, afterObs) {
    if (exactEdges.some(edge => edge.next === targetNodeId)) return true;
    const queue = exactEdges.map(edge => edge.next);
    const seen = new Set(queue);
    while (queue.length > 0) {
      const curId = queue.shift();
      if (curId === targetNodeId) return true;
      const curNode = this.dag.nodes.get(curId);
      for (const edge of curNode?.edges ?? []) {
        if (edge.step.kind === 'click' || seen.has(edge.next)) continue;
        const expected = this.inputs.get(edge.step.slot);
        const match = (afterObs.elements ?? []).find(
          el => this.dag.hash(['locator', structuralLocator(el)]) === edge.step.locator,
        );
        if (match && expected !== undefined && String(match.value ?? '') === expected) {
          seen.add(edge.next);
          queue.push(edge.next);
        }
      }
    }
    return false;
  }
  #recordFallback(before, reason) {
    let pathname = null;
    try { pathname = new URL(before.observation.url).pathname; } catch { pathname = null; }
    this.traceEvents.push({
      phase: 'fallback',
      atStep: this.depth,
      node: before.id.slice(0, 12),
      reason,
      pathname,
    });
  }
  #resolveSuffixNode(before, dp) {
    if (!this.suffixEligibility || this.fieldScope || this.dag.version < VERSION || !dp) {
      return null;
    }
    const safetyObs = before.observation.unfilteredElements
      ? { ...before.observation, elements: before.observation.unfilteredElements }
      : before.observation;
    const elig = evaluateSuffixEligibility({
      dag: this.dag,
      dp,
      observation: safetyObs,
      boundInputs: this.boundInputs,
      ambiguousRoles: this.ambiguousRoles,
      targetGoalHash: this.goalHash,
      sameOutlineClicks: this.sameOutlineClicks,
      inertFormLocators: this.inertFormLocators,
    });
    if (!elig.eligible) {
      this.lastSuffixRejection = elig;
      return null;
    }
    const decision = dp.policy.get(elig.nodeId);
    const inAuthorizedView = before.observation.elements.filter(
      el => this.dag.hash(['locator', structuralLocator(el)]) === decision?.step?.locator,
    );
    if (inAuthorizedView.length !== 1) {
      this.lastSuffixRejection = { eligible: false, reason: 'unauthorized-or-hidden-footprint-locator' };
      return null;
    }
    return elig;
  }
  /** Call only after the task's pre-submit acceptance checks pass. No final action is cached. */
  finish({ publish = true, pruneDetours = true } = {}) {
    return this.exclusive(async () => {
      const terminal = await this.observe(
        this.supportsRegionDeltas && this.lastObservationVersion !== null
          ? { ifCurrentVersion: this.lastObservationVersion }
          : undefined,
      );
      if (!this.records.length || this.nextId !== terminal.id) return this.stop('changed-terminal');
      this.suffixIndex?.note(this.dag, terminal);
      this.terminal = {
        id: terminal.id,
        depth: this.depth,
        ...(this.goalHash !== null ? { goal: this.goalHash } : {}),
      };
      if (this.suffixEligibility && !this.fieldScope) {
        const byId = this.stagedSuffixProfiles;
        for (let i = this.records.length - 1; i >= 0; i--) {
          const rec = this.records[i];
          const cur = byId.get(rec.id);
          const nxt = byId.get(rec.next);
          if (cur && nxt && cur.origin === nxt.origin && cur.routePattern === nxt.routePattern) {
            const mergedTable = new Map([...cur.locatorTable, ...nxt.locatorTable]);
            cur.locatorTable = [...mergedTable.entries()].sort(([a], [b]) => a.localeCompare(b));
            cur.onScreenStepLocators = [...new Set([...cur.onScreenStepLocators, ...nxt.onScreenStepLocators])].sort();
          }
        }
      }
      if (publish) {
        this.dag.publish(this.records, this.terminal, this.repairs, {
          pruneDetours,
          ...(this.stagedSuffixProfiles.size ? { suffixProfiles: this.stagedSuffixProfiles } : {}),
          ...(this.stagedSlotRoles.size ? { slotRoles: this.stagedSlotRoles } : {}),
        });
      }
      return this.stop('recorded-submit-boundary');
    });
  }
  /** Continue replay from the current in-progress state when a repair reconverges onto the DAG.
   * Stops non-destructively on structural misses so planner recording can still continue if needed.
   */
  continueReplay() {
    return this.exclusive(async () => {
      if (this.dag.version < VERSION) return { continuedSteps: 0, reason: 'legacy-version', reachedTerminal: false };
      const availableSlots = new Set(
        [...this.inputs.entries()]
          .filter(([, value]) => typeof value === 'string')
          .map(([slotHash]) => slotHash),
      );
      const dp = solveRecipeDp(this.dag.nodes, this.dag.limits, {
        availableSlots,
        targetGoal: this.goalHash,
        goalTerminals: this.dag.goalTerminals,
      });
      let before = await this.observe(
        this.supportsRegionDeltas && this.lastObservationVersion !== null
          ? { ifCurrentVersion: this.lastObservationVersion }
          : undefined,
      );
      if (this.nextId && this.nextId !== before.id) {
        return { continuedSteps: 0, reason: 'prefix-mismatch', reachedTerminal: false };
      }
      if (this.#suffixEnabled(dp)) {
        let continuedSteps = 0, expected = null;
        for (;;) {
          let lookupId = before.id, node = this.dag.nodes.get(lookupId);
          if (expected && node && !expected.has(lookupId)) node = undefined;
          else if (!node) {
            lookupId = this.#certifySuffix(before, dp, expected)?.nodeId ?? lookupId;
            node = this.dag.nodes.get(lookupId);
          }
          expected = null;
          if (!node) return { continuedSteps, reason: 'unseen-branch', reachedTerminal: false };
          if (this.#isGoalTerminal(lookupId, node)) return { continuedSteps, reason: 'submit-boundary', reachedTerminal: true };
          const decision = dp.policy.get(lookupId);
          if (!decision || decision.kind === 'checkpoint' || decision.kind === 'repair-only'
            || decision.kind === 'ambiguous' || decision.kind === 'missing-slot') {
            return { continuedSteps, reason: decision?.kind ?? 'unseen-branch', reachedTerminal: false };
          }
          const step = decision.step;
          const depth = this.depth;
          const executed = await this.execute(before, step);
          if (executed.status !== 'completed') {
            return { continuedSteps, reason: executed.reason, reachedTerminal: false, halted: true, result: executed.result };
          }
          continuedSteps += 1;
          this.records.push({ id: before.id, depth, step, next: executed.after.id });
          this.traceEvents.push({
            phase: lookupId === before.id ? 'reconverged-suffix-replay' : 'certified-suffix-replay',
            stepIndex: depth,
            kind: step.kind,
            label: executed.label,
            slot: executed.slotName,
            fromNode: before.id.slice(0, 12),
            toNode: executed.after.id.slice(0, 12),
            acceptedWhy: 'reconverged-node-dp-path-to-target-goal-and-live-locator-verified',
          });
          this.nextId = executed.after.id;
          const successors = node.edges.filter(edge => canonicalJson(edge.step) === canonicalJson(step)).map(edge => edge.next);
          if (!successors.includes(executed.after.id)) {
            expected = new Set(successors);
          }
          before = executed.after;
        }
      }
      let continuedSteps = 0;
      let activeNodeId = this.dag.nodes.has(before.id) ? before.id : null;
      if (!activeNodeId) {
        const suffixMatch = this.#resolveSuffixNode(before, dp);
        if (suffixMatch) {
          activeNodeId = suffixMatch.nodeId;
          this.outlineSlots = [...suffixMatch.profile.requiredSlots];
          this.certifiedSuffixRejoins.push({
            phase: 'mid-repair-suffix-rejoin',
            atStep: this.depth,
            fromFrameId: before.id,
            rejoinedNodeId: activeNodeId,
            cost: suffixMatch.cost,
            rejoinObservation: {
              url: before.observation.url,
              elements: (before.observation.elements ?? []).map(el => ({
                role: el.role, label: el.label, tag: el.tag, inputType: el.inputType, value: el.value, text: el.text,
              })),
            },
          });
        }
      }
      for (;;) {
        const node = activeNodeId ? this.dag.nodes.get(activeNodeId) : null;
        if (!node) return { continuedSteps, reason: 'unseen-branch', reachedTerminal: false };
        if (this.#isGoalTerminal(activeNodeId, node)) return { continuedSteps, reason: 'submit-boundary', reachedTerminal: true };
        const decision = dp.policy.get(activeNodeId);
        if (!decision || decision.kind === 'checkpoint' || decision.kind === 'repair-only'
          || decision.kind === 'ambiguous' || decision.kind === 'missing-slot') {
          return { continuedSteps, reason: decision?.kind ?? 'unseen-branch', reachedTerminal: false };
        }
        const step = decision.step;
        const depth = this.depth;
        const executed = await this.execute(before, step);
        if (executed.status !== 'completed') {
          return { continuedSteps, reason: executed.reason, reachedTerminal: false, halted: true, result: executed.result };
        }
        continuedSteps += 1;
        this.records.push({ id: before.id, depth, step, next: executed.after.id });
        this.traceEvents.push({
          phase: 'reconverged-suffix-replay',
          stepIndex: depth,
          kind: step.kind,
          label: executed.label,
          slot: executed.slotName,
          fromNode: activeNodeId.slice(0, 12),
          toNode: executed.after.id.slice(0, 12),
          acceptedWhy: activeNodeId === before.id
            ? 'reconverged-node-dp-path-to-target-goal-and-live-locator-verified'
            : 'suffix-eligible-footprint-and-dirty-form-guards-verified',
        });
        this.nextId = executed.after.id;
        const exactEdges = node.edges.filter(edge => canonicalJson(edge.step) === canonicalJson(step));
        if (exactEdges.some(edge => edge.next === executed.after.id)) {
          activeNodeId = executed.after.id;
        } else if (this.suffixEligibility) {
          const terminalEdge = exactEdges.find(edge => this.#isGoalTerminal(edge.next, this.dag.nodes.get(edge.next))
            && executed.after.observation.elements.length === 0);
          if (terminalEdge) {
            activeNodeId = terminalEdge.next;
          } else {
            const nextSuffix = this.#resolveSuffixNode(executed.after, dp);
            if (nextSuffix && this.#isVerifiedSuffixTransition(exactEdges, nextSuffix.nodeId, executed.after.observation)) {
              activeNodeId = nextSuffix.nodeId;
            } else {
              this.#recordFallback(executed.after, 'unseen-branch');
              return { continuedSteps, reason: 'unseen-branch', reachedTerminal: false };
            }
          }
        } else {
          this.#recordFallback(executed.after, 'unseen-branch');
          return { continuedSteps, reason: 'unseen-branch', reachedTerminal: false };
        }
        before = executed.after;
      }
    });
  }
  #inferMidFormEntry(before, dp) {
    if (this.depth !== 0 || this.fieldScope || this.dag.version < VERSION) return before;
    const preSatisfied = [];
    for (const [slotHash, slotValue] of this.inputs) {
      if (typeof slotValue !== 'string' || !slotValue.length) continue;
      const matching = before.observation.elements.filter(element => element.value === slotValue
        && element.label && !element.formAction
        && !['submit', 'image', 'file', 'password', 'hidden'].includes(element.inputType));
      if (matching.length === 1) preSatisfied.push(slotHash);
    }
    if (!preSatisfied.length) return before;
    preSatisfied.sort();
    const candidate = this.frame(before.observation, null, { outlineSlots: preSatisfied, sameOutlineClicks: 0 });
    if (!this.dag.nodes.has(candidate.id)) return before;
    const currentCost = dp ? (dp.values.get(before.id) ?? Infinity) : Infinity;
    const candidateCost = dp ? (dp.values.get(candidate.id) ?? Infinity) : Infinity;
    if (this.dag.nodes.has(before.id) && !(candidateCost < currentCost)) return before;
    this.outlineSlots = preSatisfied;
    return candidate;
  }
  replay() {
    return this.exclusive(async () => {
      const availableSlots = new Set(
        [...this.inputs.entries()]
          .filter(([, value]) => typeof value === 'string')
          .map(([slotHash]) => slotHash),
      );
      const hasKnownGoal = this.goalHash === null || Boolean(this.dag.goalTerminals.get(this.goalHash)?.length);
      const dp = this.dag.version >= VERSION
        ? solveRecipeDp(this.dag.nodes, this.dag.limits, {
            availableSlots,
            targetGoal: this.goalHash,
            goalTerminals: this.dag.goalTerminals,
          })
        : null;
      let before = await this.observe();
      before = this.#inferMidFormEntry(before, dp);
      if (this.#suffixEnabled(dp)) {
        let expected = null;
        for (;;) {
          let lookupId = before.id, node = this.dag.nodes.get(lookupId);
          if (expected && node && !expected.has(lookupId)) node = undefined;
          else if (!node) {
            lookupId = this.#certifySuffix(before, dp, expected)?.nodeId ?? lookupId;
            node = this.dag.nodes.get(lookupId);
          }
          expected = null;
          if (!node) {
            this.#recordFallback(before, 'unseen-branch');
            return this.stop('unseen-branch');
          }
          if (this.#isGoalTerminal(lookupId, node)) return this.stop('submit-boundary');
          if (this.fieldScope && node.repairs.length) {
            const exactSlots = this.dag.version >= VERSION ? [...this.groupProgress.filledSlots] : [];
            const exact = this.frame(before.observation, null, { outlineSlots: exactSlots, sameOutlineClicks: this.sameOutlineClicks });
            if (node.repairs.includes(exact.id)) {
              this.repairs.push({ id: before.id, depth: this.depth, next: exact.id });
              this.outlineSlots = exactSlots;
              this.fieldScope = null;
              this.groupProgress = null;
              before = exact;
              this.nextId = exact.id;
              lookupId = before.id;
              node = this.dag.nodes.get(lookupId);
              if (this.#isGoalTerminal(lookupId, node)) return this.stop('submit-boundary');
            }
          }
          const decision = dp.policy.get(lookupId);
          if (!decision || decision.kind === 'checkpoint' || decision.kind === 'repair-only') {
            const why = decision?.kind === 'checkpoint' ? 'checkpoint-reached-for-unseen-goal' : 'unseen-branch';
            this.#recordFallback(before, why);
            return this.stop('unseen-branch');
          }
          if (decision.kind === 'ambiguous') {
            this.#recordFallback(before, 'ambiguous-branch');
            return this.stop('ambiguous-branch');
          }
          const step = decision.step;
          const depth = this.depth;
          const executed = await this.execute(before, step);
          if (executed.status !== 'completed') {
            this.#recordFallback(before, executed.reason);
            return executed;
          }
          this.records.push({ id: before.id, depth, step, next: executed.after.id });
          this.traceEvents.push({
            phase: lookupId === before.id ? 'prefix-replay' : 'certified-suffix-replay',
            stepIndex: depth,
            kind: step.kind,
            label: executed.label,
            slot: executed.slotName,
            fromNode: before.id.slice(0, 12),
            toNode: executed.after.id.slice(0, 12),
            acceptedWhy: hasKnownGoal
              ? 'dp-path-to-target-goal-and-live-locator-verified'
              : 'slot-feasible-prefix-toward-known-checkpoint-and-live-locator-verified',
          });
          this.nextId = executed.after.id;
          const successors = node.edges.filter(edge => canonicalJson(edge.step) === canonicalJson(step)).map(edge => edge.next);
          if (!successors.includes(executed.after.id)) {
            expected = new Set(successors);
          }
          before = executed.after;
        }
      }
      let activeNodeId = this.dag.nodes.has(before.id) ? before.id : null;
      if (!activeNodeId) {
        const suffixMatch = this.#resolveSuffixNode(before, dp);
        if (suffixMatch) {
          activeNodeId = suffixMatch.nodeId;
          this.outlineSlots = [...suffixMatch.profile.requiredSlots];
          this.certifiedSuffixRejoins.push({
            phase: 'initial-suffix-rejoin',
            atStep: this.depth,
            fromFrameId: before.id,
            rejoinedNodeId: activeNodeId,
            cost: suffixMatch.cost,
            rejoinObservation: {
              url: before.observation.url,
              elements: (before.observation.elements ?? []).map(el => ({
                role: el.role, label: el.label, tag: el.tag, inputType: el.inputType, value: el.value, text: el.text,
              })),
            },
          });
        }
      }
      for (;;) {
        let node = activeNodeId ? this.dag.nodes.get(activeNodeId) : null;
        if (!node) {
          this.#recordFallback(before, this.lastSuffixRejection?.reason ?? 'unseen-branch');
          return this.stop('unseen-branch');
        }
        if (this.#isGoalTerminal(activeNodeId, node)) return this.stop('submit-boundary');
        if (this.fieldScope && node.repairs.length) {
          const exactSlots = this.dag.version >= VERSION ? [...this.groupProgress.filledSlots] : [];
          const exact = this.frame(before.observation, null, { outlineSlots: exactSlots, sameOutlineClicks: this.sameOutlineClicks });
          if (node.repairs.includes(exact.id)) {
            this.repairs.push({ id: before.id, depth: this.depth, next: exact.id });
            this.outlineSlots = exactSlots;
            this.fieldScope = null;
            this.groupProgress = null;
            before = exact;
            this.nextId = exact.id;
            activeNodeId = exact.id;
            node = this.dag.nodes.get(activeNodeId);
            if (this.#isGoalTerminal(activeNodeId, node)) return this.stop('submit-boundary');
          }
        }
        let step;
        if (dp) {
          const decision = dp.policy.get(activeNodeId);
          if (!decision || decision.kind === 'checkpoint' || decision.kind === 'repair-only') {
            const why = decision?.kind === 'checkpoint' ? 'checkpoint-reached-for-unseen-goal' : 'unseen-branch';
            this.#recordFallback(before, why);
            return this.stop('unseen-branch');
          }
          if (decision.kind === 'ambiguous') {
            this.#recordFallback(before, 'ambiguous-branch');
            return this.stop('ambiguous-branch');
          }
          step = decision.step;
        } else {
          const steps = new Map(node.edges.map(edge => [canonicalJson(edge.step), edge.step]));
          if (steps.size !== 1) {
            this.#recordFallback(before, 'ambiguous-branch');
            return this.stop('ambiguous-branch');
          }
          step = steps.values().next().value;
        }
        const depth = this.depth;
        const executed = await this.execute(before, step);
        if (executed.status !== 'completed') {
          this.#recordFallback(before, executed.reason);
          return executed;
        }
        this.records.push({ id: before.id, depth, step, next: executed.after.id });
        this.traceEvents.push({
          phase: activeNodeId === before.id ? 'prefix-replay' : 'suffix-eligible-replay',
          stepIndex: depth,
          kind: step.kind,
          label: executed.label,
          slot: executed.slotName,
          fromNode: activeNodeId.slice(0, 12),
          toNode: executed.after.id.slice(0, 12),
          acceptedWhy: activeNodeId !== before.id
            ? 'suffix-eligible-footprint-and-dirty-form-guards-verified'
            : hasKnownGoal
              ? 'dp-path-to-target-goal-and-live-locator-verified'
              : 'slot-feasible-prefix-toward-known-checkpoint-and-live-locator-verified',
        });
        this.nextId = executed.after.id;
        const exactEdges = node.edges.filter(edge => canonicalJson(edge.step) === canonicalJson(step));
        if (exactEdges.some(edge => edge.next === executed.after.id)) {
          activeNodeId = executed.after.id;
        } else if (this.suffixEligibility) {
          const terminalEdge = exactEdges.find(edge => this.#isGoalTerminal(edge.next, this.dag.nodes.get(edge.next))
            && executed.after.observation.elements.length === 0);
          if (terminalEdge) {
            activeNodeId = terminalEdge.next;
          } else {
            const nextSuffix = this.#resolveSuffixNode(executed.after, dp);
            if (nextSuffix && this.#isVerifiedSuffixTransition(exactEdges, nextSuffix.nodeId, executed.after.observation)) {
              activeNodeId = nextSuffix.nodeId;
            } else {
              this.#recordFallback(executed.after, this.lastSuffixRejection?.reason ?? 'unseen-branch');
              return this.stop('unseen-branch');
            }
          }
        } else {
          this.#recordFallback(executed.after, 'unseen-branch');
          return this.stop('unseen-branch');
        }
        before = executed.after;
      }
    });
  }
}
