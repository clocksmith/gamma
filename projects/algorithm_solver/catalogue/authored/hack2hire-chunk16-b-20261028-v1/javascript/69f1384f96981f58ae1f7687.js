"use strict";
// Hack2Hire 69f1384f96981f58ae1f7687 (Minimum Root Edges Reversal) over an INFERRED spec; qualification unknown.

function solve(n, fromNodes, toNodes) {
  // compressed adjacency; against = 0 when walking along the edge, 1 when walking against it
  const degree = new Int32Array(n + 2);
  for (let i = 0; i < fromNodes.length; i++) { degree[fromNodes[i]]++; degree[toNodes[i]]++; }
  const start = new Int32Array(n + 2);
  for (let v = 1; v <= n; v++) start[v + 1] = start[v] + degree[v];
  const fill = start.slice();
  const target = new Int32Array(2 * fromNodes.length);
  const against = new Uint8Array(2 * fromNodes.length);
  for (let i = 0; i < fromNodes.length; i++) {
    const a = fromNodes[i], b = toNodes[i];
    target[fill[a]] = b; against[fill[a]++] = 0;
    target[fill[b]] = a; against[fill[b]++] = 1;
  }
  const parent = new Int32Array(n + 1), along = new Uint8Array(n + 1), seen = new Uint8Array(n + 1);
  const order = new Int32Array(n);
  let size = 1, base = 0;
  order[0] = 1; seen[1] = 1;
  for (let k = 0; k < size; k++) {
    const u = order[k];
    for (let e = start[u]; e < start[u + 1]; e++) {
      const v = target[e];
      if (!seen[v]) { seen[v] = 1; parent[v] = u; along[v] = against[e]; base += against[e]; order[size++] = v; }
    }
  }
  const cost = new Int32Array(n + 1);
  cost[1] = base;
  let best = base;
  for (let k = 1; k < size; k++) {
    const v = order[k];
    cost[v] = cost[parent[v]] + (along[v] === 0 ? 1 : -1);
    if (cost[v] < best) best = cost[v];
  }
  return best;
}

function minEdgeReversals(n, fromNodes, toNodes) { return solve(n, fromNodes, toNodes); }

module.exports = solve;
module.exports.minEdgeReversals = minEdgeReversals;
