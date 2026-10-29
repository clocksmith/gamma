"use strict";
// Hack2Hire 692d2a491abcca80b11223bf (Non-connected People Pairs) over an INFERRED spec; qualification unknown.

function solve(n, connections) {
  const parent = Array.from({length: n}, (_, i) => i);
  const size = new Array(n).fill(1);
  const find = (x) => {
    while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; } // path halving
    return x;
  };
  for (const [a, b] of connections) {
    let ra = find(a), rb = find(b);
    if (ra === rb) continue;
    if (size[ra] < size[rb]) [ra, rb] = [rb, ra];
    parent[rb] = ra;
    size[ra] += size[rb];
  }
  let same = 0;
  for (let v = 0; v < n; v++) if (parent[v] === v) same += size[v] * (size[v] - 1) / 2;
  return n * (n - 1) / 2 - same;
}

function countNonConnectedPairs(n, connections) { return solve(n, connections); }

module.exports = solve;
module.exports.countNonConnectedPairs = countNonConnectedPairs;
