"use strict";
// Hack2Hire 6a2b14eb97d3b4b32966cb00 (Factory Network Cost Minimization, variant 3 of 3) over an INFERRED spec; qualification unknown.

function solve(costs, edges) {
  const n = costs.length, adjacent = Array.from({length: n}, () => []);
  for (const [u, v] of edges) { adjacent[u].push(v); adjacent[v].push(u); }
  const parent = new Int32Array(n).fill(-1), seen = new Uint8Array(n), order = [], stack = [0];
  seen[0] = 1;
  while (stack.length) {
    const v = stack.pop(); order.push(v);
    for (const w of adjacent[v]) if (!seen[w]) { seen[w] = 1; parent[w] = v; stack.push(w); }
  }
  const best1 = new Array(n), base = new Array(n).fill(0), extra = new Array(n).fill(null);
  for (let k = n - 1; k >= 0; k--) {
    const v = order[k], row = costs[v], add = extra[v];
    let b1 = Infinity, i1 = -1, b2 = Infinity;
    for (let j = 0; j < row.length; j++) {
      const value = row[j] + base[v] + (add !== null && add.has(j) ? add.get(j) : 0);
      if (value < b1) { b2 = b1; b1 = value; i1 = j; }
      else if (value < b2) b2 = value;
    }
    if (b1 === Infinity) return -1;
    best1[v] = b1;
    const p = parent[v];
    if (p >= 0) {
      base[p] += b1;
      if (extra[p] === null) extra[p] = new Map();
      extra[p].set(i1, (extra[p].get(i1) || 0) + (b2 - b1));
    }
  }
  return best1[0];
}

function minimumCost(costs, edges) { return solve(costs, edges); }

module.exports = solve;
module.exports.minimumCost = minimumCost;
