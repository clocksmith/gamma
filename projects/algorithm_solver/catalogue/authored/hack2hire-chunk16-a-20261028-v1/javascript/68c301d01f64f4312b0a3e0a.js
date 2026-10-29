"use strict";
// Hack2Hire 68c301d01f64f4312b0a3e0a (Maximum Ski Score) over an INFERRED spec; qualification unknown.

function solve(routes, checkpoints) {
  const reward = new Map();
  for (const [name, value] of checkpoints) reward.set(name, value);
  const out = new Map();
  for (const [start, cost, end] of routes) {
    if (!out.has(start)) out.set(start, []);
    out.get(start).push([cost, end]);
  }
  const none = [];
  const next = (v) => out.get(v) || none;
  const seen = new Set(['lodge']);
  const order = [];
  const stack = ['lodge'];
  while (stack.length) {
    const v = stack.pop();
    order.push(v);
    for (const [, w] of next(v)) if (!seen.has(w)) { seen.add(w); stack.push(w); }
  }
  const indegree = new Map();
  for (const v of order) indegree.set(v, 0);
  for (const v of order) for (const [, w] of next(v)) indegree.set(w, indegree.get(w) + 1);
  const topo = [];
  const ready = ['lodge'];
  while (ready.length) {
    const v = ready.pop();
    topo.push(v);
    for (const [, w] of next(v)) {
      const d = indegree.get(w) - 1;
      indegree.set(w, d);
      if (d === 0) ready.push(w);
    }
  }
  const best = new Map();
  for (let i = topo.length - 1; i >= 0; i--) {
    const v = topo[i];
    const edges = next(v);
    if (edges.length === 0) { best.set(v, 0); continue; }
    let value = null;
    for (const [cost, w] of edges) {
      const candidate = (reward.has(w) ? reward.get(w) : 0) - cost + best.get(w);
      if (value === null || candidate > value) value = candidate;
    }
    best.set(v, value);
  }
  return best.get('lodge');
}

function maxSkiScore(routes, checkpoints) { return solve(routes, checkpoints); }

module.exports = solve;
module.exports.maxSkiScore = maxSkiScore;
