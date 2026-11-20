// Pure DAG reduction, path compression and backward dynamic programming for browser recipes.
// Keeps graph transformations deterministic, idempotent and free of browser or planner authority.

export function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
  if (value && typeof value === 'object') {
    const keys = Object.keys(value).filter(key => value[key] !== undefined).sort();
    return `{${keys.map(key => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

const DEFAULT_REPLAN_PENALTY = 1000;
const COST_EPSILON = 1e-9;

function cloneNodes(nodes) {
  return new Map([...nodes].map(([id, node]) => [id, structuredClone(node)]));
}

function terminalSignature(set) {
  return [...set].sort().join(',');
}

/** Contract intra-trace state revisitations (u -> ... -> u) before staging into the DAG. */
export function compressTraceRecords(records, terminal) {
  if (!Array.isArray(records) || !records.length) {
    return { records: [], terminal: terminal ? { ...terminal, depth: 0 } : null, contractedSteps: 0 };
  }
  const states = [records[0].id, ...records.map(record => record.next)];
  const contracted = [];
  let cursor = 0;
  while (cursor < records.length) {
    // Jump directly to the last visit of states[cursor] so zero-progress detours vanish.
    let lastVisit = cursor;
    for (let probe = states.length - 1; probe > cursor; probe--) {
      if (states[probe] === states[cursor]) {
        lastVisit = probe;
        break;
      }
    }
    if (lastVisit >= records.length) break;
    const chosen = records[lastVisit];
    contracted.push({
      ...structuredClone(chosen),
      depth: contracted.length,
    });
    cursor = lastVisit + 1;
  }
  const finalId = terminal?.id ?? states.at(-1);
  return {
    records: contracted,
    terminal: terminal
      ? { id: finalId, depth: contracted.length, ...(terminal.goal ? { goal: terminal.goal } : {}) }
      : null,
    contractedSteps: records.length - contracted.length,
  };
}

/** Deterministic Kahn topological sort over both step edges (+1 depth) and repair bridges (+0 depth). */
export function topologicalSort(nodes, maxSteps = Infinity) {
  const inDegree = new Map();
  const adjacency = new Map();
  for (const [id, node] of nodes) {
    inDegree.set(id, 0);
    adjacency.set(id, []);
    if (!node) throw Error('Invalid trace node');
  }
  for (const [id, node] of nodes) {
    for (const edge of node.edges ?? []) {
      if (edge.next === id || !nodes.has(edge.next)) throw Error('Trace must be acyclic');
      adjacency.get(id).push({ next: edge.next, stepDelta: 1 });
      inDegree.set(edge.next, inDegree.get(edge.next) + 1);
    }
    for (const next of node.repairs ?? []) {
      if (next === id || !nodes.has(next)) throw Error('Invalid trace repair boundary');
      adjacency.get(id).push({ next, stepDelta: 0 });
      inDegree.set(next, inDegree.get(next) + 1);
    }
  }
  const ready = [...inDegree.entries()]
    .filter(([, deg]) => deg === 0)
    .map(([id]) => id)
    .sort();
  const order = [];
  const rank = new Map([...nodes.keys()].map(id => [id, 0]));
  while (ready.length) {
    const id = ready.shift();
    order.push(id);
    const baseRank = rank.get(id);
    for (const { next, stepDelta } of adjacency.get(id)) {
      const candidate = baseRank + stepDelta;
      if (candidate > rank.get(next)) rank.set(next, candidate);
      const remaining = inDegree.get(next) - 1;
      inDegree.set(next, remaining);
      if (remaining === 0) {
        ready.push(next);
        ready.sort();
      }
    }
  }
  if (order.length !== nodes.size) throw Error('Trace must be acyclic');
  for (const depth of rank.values()) {
    if (depth > maxSteps) throw Error('Trace step limit');
  }
  return { order, rank };
}

function computeReverseReachable(nodes) {
  const reverse = new Map([...nodes.keys()].map(id => [id, []]));
  for (const [id, node] of nodes) {
    for (const edge of node.edges ?? []) {
      if (reverse.has(edge.next)) reverse.get(edge.next).push(id);
    }
    for (const next of node.repairs ?? []) {
      if (reverse.has(next)) reverse.get(next).push(id);
    }
  }
  const reachable = new Set();
  const queue = [];
  for (const [id, node] of nodes) {
    if (node.terminal) {
      reachable.add(id);
      queue.push(id);
    }
  }
  while (queue.length) {
    const current = queue.shift();
    for (const prev of reverse.get(current) ?? []) {
      if (!reachable.has(prev)) {
        reachable.add(prev);
        queue.push(prev);
      }
    }
  }
  return reachable;
}

function isPureClickRelay(node) {
  return !node.terminal
    && (!node.repairs || node.repairs.length === 0)
    && node.edges.length > 0
    && node.edges.every(edge => edge.step.kind === 'click');
}

// Compute unique reconvergence target and step count for a pure-click chain starting at startId.
function tracePureClickChain(startId, nodes) {
  const visited = new Set();
  let current = startId;
  let steps = 0;
  while (nodes.has(current) && !visited.has(current)) {
    visited.add(current);
    const node = nodes.get(current);
    if (!isPureClickRelay(node)) return { target: current, steps };
    const targets = new Set(node.edges.map(edge => edge.next));
    if (targets.size !== 1) return null;
    current = [...targets][0];
    steps += 1;
  }
  return null;
}

/** Reduce a DAG by pruning dead branches, compressing dominated click detours and normalizing ranks. */
export function reduceTraceGraph(nodes, limits, { pruneDeadEnds = true, pruneDetours = true } = {}) {
  const working = cloneNodes(nodes);
  topologicalSort(working, limits.maxSteps);
  let deadNodesRemoved = 0;
  let deadEdgesRemoved = 0;
  let detourEdgesRemoved = 0;
  let detourNodesRemoved = 0;

  if (pruneDeadEnds && working.size > 0) {
    const live = computeReverseReachable(working);
    for (const id of [...working.keys()]) {
      if (!live.has(id)) {
        working.delete(id);
        deadNodesRemoved++;
      }
    }
    for (const node of working.values()) {
      const beforeEdges = node.edges.length;
      node.edges = node.edges.filter(edge => live.has(edge.next));
      deadEdgesRemoved += beforeEdges - node.edges.length;
      node.repairs = (node.repairs ?? []).filter(next => live.has(next));
    }
  }

  if (pruneDetours && working.size > 0) {
    const initialInDegree = new Map([...working.keys()].map(id => [id, 0]));
    for (const node of working.values()) {
      for (const edge of node.edges) initialInDegree.set(edge.next, (initialInDegree.get(edge.next) ?? 0) + 1);
      for (const next of node.repairs ?? []) initialInDegree.set(next, (initialInDegree.get(next) ?? 0) + 1);
    }
    for (const node of working.values()) {
      if (node.edges.length < 2) continue;
      const clickRoutes = node.edges.map((edge, index) => {
        if (edge.step.kind !== 'click') return null;
        const chain = tracePureClickChain(edge.next, working);
        if (!chain) return null;
        const baseWeight = edge.weight ?? 1;
        return { index, target: chain.target, totalCost: baseWeight + chain.steps };
      });
      const minByTarget = new Map();
      for (const route of clickRoutes) {
        if (!route) continue;
        const prev = minByTarget.get(route.target);
        if (prev === undefined || route.totalCost < prev) minByTarget.set(route.target, route.totalCost);
      }
      const keep = node.edges.filter((_, index) => {
        const route = clickRoutes[index];
        if (!route) return true;
        return route.totalCost <= minByTarget.get(route.target) + COST_EPSILON;
      });
      detourEdgesRemoved += node.edges.length - keep.length;
      node.edges = keep;
    }

    // Garbage-collect intermediate relay nodes orphaned when their only incoming detour was pruned.
    let removedAny = true;
    while (removedAny) {
      removedAny = false;
      const currentInDegree = new Map([...working.keys()].map(id => [id, 0]));
      for (const node of working.values()) {
        for (const edge of node.edges) currentInDegree.set(edge.next, (currentInDegree.get(edge.next) ?? 0) + 1);
        for (const next of node.repairs ?? []) currentInDegree.set(next, (currentInDegree.get(next) ?? 0) + 1);
      }
      for (const [id, node] of [...working.entries()]) {
        if (!node.terminal && (initialInDegree.get(id) ?? 0) > 0 && (currentInDegree.get(id) ?? 0) === 0) {
          working.delete(id);
          detourNodesRemoved++;
          removedAny = true;
        }
      }
    }
  }

  const { rank } = topologicalSort(working, limits.maxSteps);
  const orderedEntries = [...working.entries()].sort(([leftId], [rightId]) => {
    const rankDiff = (rank.get(leftId) ?? 0) - (rank.get(rightId) ?? 0);
    return rankDiff !== 0 ? rankDiff : leftId.localeCompare(rightId);
  });
  const normalized = new Map();
  for (const [id, node] of orderedEntries) {
    const dedupedEdges = new Map();
    for (const edge of node.edges) {
      const key = canonicalJson({ next: edge.next, step: edge.step });
      const prev = dedupedEdges.get(key);
      if (!prev) {
        dedupedEdges.set(key, structuredClone(edge));
      } else if (edge.weight !== undefined || prev.weight !== undefined) {
        const mergedWeight = Math.min(prev.weight ?? 1, edge.weight ?? 1);
        dedupedEdges.set(key, { next: edge.next, step: structuredClone(edge.step), weight: mergedWeight });
      }
    }
    const sortedEdges = [...dedupedEdges.values()]
      .sort((left, right) => canonicalJson(left).localeCompare(canonicalJson(right)));
    const sortedRepairs = [...new Set(node.repairs ?? [])].sort();
    normalized.set(id, {
      depth: rank.get(id) ?? 0,
      edges: sortedEdges,
      repairs: sortedRepairs,
      terminal: Boolean(node.terminal),
    });
  }
  return {
    nodes: normalized,
    stats: { deadNodesRemoved, deadEdgesRemoved, detourEdgesRemoved, detourNodesRemoved },
  };
}

export function normalizeGoalTerminals(goalTerminals, nodes) {
  const out = new Map();
  if (!goalTerminals) return out;
  const entries = goalTerminals instanceof Map ? [...goalTerminals.entries()] : goalTerminals;
  for (const [goalHash, ids] of entries) {
    const liveIds = [...new Set(ids)].filter(id => nodes.get(id)?.terminal).sort();
    if (liveIds.length) out.set(goalHash, liveIds);
  }
  return new Map([...out.entries()].sort(([a], [b]) => a.localeCompare(b)));
}

/** Backward Bellman dynamic programming over the recipe DAG.
 * Goal completion predicates (`goalTerminals`: goalHash -> terminal node IDs) live outside shared
 * nodes so a screen that completed an earlier goal can act as an intermediate stop for a later goal.
 */
export function solveRecipeDp(nodes, limits, {
  availableSlots = null,
  targetGoal = null,
  goalTerminals = null,
  replanPenalty = DEFAULT_REPLAN_PENALTY,
} = {}) {
  const { order } = topologicalSort(nodes, limits.maxSteps);
  const values = new Map();
  const terminals = new Map();
  const policy = new Map();
  const goalMap = normalizeGoalTerminals(goalTerminals, nodes);
  const targetGoalNodes = targetGoal !== null ? new Set(goalMap.get(targetGoal) ?? []) : null;
  const knownGoal = targetGoal !== null && targetGoalNodes.size > 0;
  const checkpointNodes = targetGoal !== null && !knownGoal
    ? new Set([...goalMap.values()].flat())
    : null;

  for (let idx = order.length - 1; idx >= 0; idx--) {
    const id = order[idx];
    const node = nodes.get(id);
    if (targetGoal === null ? Boolean(node.terminal) : (knownGoal && targetGoalNodes.has(id))) {
      values.set(id, 0);
      terminals.set(id, new Set([id]));
      policy.set(id, { kind: 'terminal', cost: 0 });
      continue;
    }
    if (checkpointNodes?.has(id)) {
      values.set(id, 0);
      terminals.set(id, new Set([id]));
      policy.set(id, { kind: 'checkpoint', cost: 0 });
      continue;
    }

    const actionGroups = new Map();
    for (const edge of node.edges ?? []) {
      const stepKey = canonicalJson(edge.step);
      let group = actionGroups.get(stepKey);
      if (!group) {
        group = { stepKey, step: edge.step, outcomes: [] };
        actionGroups.set(stepKey, group);
      }
      group.outcomes.push(edge);
    }

    const feasible = [];
    let firstMissingSlotStep = null;
    for (const group of [...actionGroups.values()].sort((a, b) => a.stepKey.localeCompare(b.stepKey))) {
      const slotOk = group.step.kind === 'click'
        || availableSlots === null
        || availableSlots.has(group.step.slot);
      if (!slotOk) {
        firstMissingSlotStep ??= group.step;
        continue;
      }
      let totalOutcomeCost = 0;
      let totalWeight = 0;
      let reachableCount = 0;
      const reachedTerminals = new Set();
      for (const edge of group.outcomes) {
        const nextVal = values.get(edge.next) ?? Infinity;
        totalWeight += edge.weight ?? 1;
        if (Number.isFinite(nextVal)) {
          reachableCount++;
          totalOutcomeCost += nextVal;
          for (const term of terminals.get(edge.next) ?? []) reachedTerminals.add(term);
        } else {
          totalOutcomeCost += replanPenalty;
        }
      }
      if (reachableCount === 0) continue;
      const meanStepCost = totalWeight / group.outcomes.length;
      const expectedContinuation = totalOutcomeCost / group.outcomes.length;
      const qValue = meanStepCost + expectedContinuation;
      feasible.push({
        stepKey: group.stepKey,
        step: group.step,
        q: qValue,
        terminals: reachedTerminals,
      });
    }

    let repairBest = Infinity;
    const repairTerminals = new Set();
    for (const repairId of node.repairs ?? []) {
      const repairVal = values.get(repairId) ?? Infinity;
      if (repairVal < repairBest) repairBest = repairVal;
      for (const term of terminals.get(repairId) ?? []) repairTerminals.add(term);
    }

    if (feasible.length === 0) {
      if (firstMissingSlotStep) {
        values.set(id, repairBest);
        terminals.set(id, repairTerminals);
        policy.set(id, { kind: 'missing-slot', step: firstMissingSlotStep, cost: Infinity });
      } else if (Number.isFinite(repairBest)) {
        values.set(id, repairBest);
        terminals.set(id, repairTerminals);
        policy.set(id, { kind: 'repair-only', cost: repairBest });
      } else {
        values.set(id, Infinity);
        terminals.set(id, new Set());
      }
      continue;
    }

    const minQ = Math.min(...feasible.map(candidate => candidate.q));
    const best = feasible.filter(candidate => Math.abs(candidate.q - minQ) <= COST_EPSILON);
    const mergedTerminals = new Set(repairTerminals);
    for (const candidate of best) {
      for (const term of candidate.terminals) mergedTerminals.add(term);
    }
    const effectiveValue = Math.min(minQ, repairBest);
    values.set(id, effectiveValue);
    terminals.set(id, mergedTerminals);

    if (best.length === 1) {
      policy.set(id, { kind: 'step', step: best[0].step, cost: minQ, confluentTieBreak: false });
      continue;
    }

    // Multiple actions achieve identical minimal expected cost. Allow deterministic tie-breaking
    // only when every tied optimal branch converges to the exact same terminal postcondition set.
    const refSig = terminalSignature(best[0].terminals);
    const isConfluent = refSig.length > 0
      && best.every(candidate => terminalSignature(candidate.terminals) === refSig);
    if (isConfluent) {
      policy.set(id, { kind: 'step', step: best[0].step, cost: minQ, confluentTieBreak: true });
    } else {
      policy.set(id, { kind: 'ambiguous', candidates: best.length, cost: minQ });
    }
  }

  return { values, policy, terminals, order };
}

/** Structural and compression diagnostics for a TraceDag node map. */
export function analyzeTraceGraph(nodes, limits) {
  const { order, rank } = topologicalSort(nodes, limits.maxSteps);
  const inDegree = new Map([...nodes.keys()].map(id => [id, 0]));
  let edgeCount = 0;
  let repairBridgeCount = 0;
  let terminalCount = 0;
  for (const node of nodes.values()) {
    if (node.terminal) terminalCount++;
    edgeCount += node.edges.length;
    repairBridgeCount += (node.repairs ?? []).length;
    for (const edge of node.edges) inDegree.set(edge.next, (inDegree.get(edge.next) ?? 0) + 1);
    for (const next of node.repairs ?? []) inDegree.set(next, (inDegree.get(next) ?? 0) + 1);
  }
  const sharedMergeNodes = [...inDegree.values()].filter(deg => deg > 1).length;
  const dp = solveRecipeDp(nodes, limits);
  let confluentDiamonds = 0;
  for (const decision of dp.policy.values()) {
    if (decision.kind === 'step' && decision.confluentTieBreak) confluentDiamonds++;
  }
  const roots = order.filter(id => (inDegree.get(id) ?? 0) === 0);
  const optimalRootCosts = Object.fromEntries(roots.map(id => [id, dp.values.get(id) ?? null]));
  const maxDepth = rank.size ? Math.max(...rank.values()) : 0;
  return {
    nodeCount: nodes.size,
    edgeCount,
    repairBridgeCount,
    terminalCount,
    sharedMergeNodes,
    confluentDiamonds,
    maxDepth,
    optimalRootCosts,
  };
}
