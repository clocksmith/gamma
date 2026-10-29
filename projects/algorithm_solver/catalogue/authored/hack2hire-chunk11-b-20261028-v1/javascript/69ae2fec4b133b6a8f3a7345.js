"use strict";
// Hack2Hire 69ae2fec4b133b6a8f3a7345 (Largest Group of Mutual Strangers) over an INFERRED spec; qualification unknown.

function solve(n, connections) {
  const degree = new Array(n + 1).fill(0);
  for (const [a, b] of connections) { degree[a + 1]++; degree[b + 1]++; }
  for (let i = 0; i < n; i++) degree[i + 1] += degree[i]; // prefix sums: adjacency offsets
  const fill = degree.slice();
  const adjacency = new Array(2 * connections.length).fill(0);
  for (const [a, b] of connections) { adjacency[fill[a]++] = b; adjacency[fill[b]++] = a; }
  const parent = new Array(n).fill(-2), take = new Array(n).fill(1), skip = new Array(n).fill(0);
  let best = 0;
  for (let root = 0; root < n; root++) {
    if (parent[root] !== -2) continue;
    parent[root] = -1;
    const order = [root];
    for (let k = 0; k < order.length; k++) {
      const v = order[k];
      for (let e = degree[v]; e < degree[v + 1]; e++) {
        const w = adjacency[e];
        if (parent[w] === -2) { parent[w] = v; order.push(w); }
      }
    }
    for (let k = order.length - 1; k >= 0; k--) {
      const v = order[k], p = parent[v];
      if (p >= 0) { take[p] += skip[v]; skip[p] += Math.max(take[v], skip[v]); }
    }
    best += Math.max(take[root], skip[root]);
  }
  return best;
}

function largestStrangerGroup(n, connections) { return solve(n, connections); }

module.exports = solve;
module.exports.largestStrangerGroup = largestStrangerGroup;
