'use strict';

// 3108. Minimum Cost Walk in Weighted Graph.
// A walk may include every edge in its connected component; union-find plus component AND. O((n+e+q)*alpha(n)) time, O(n) space. Inputs are preserved.

function solve(n, edges, query) {
  const parent = Array.from({ length: n }, (_, i) => i), size = Array(n).fill(1);
  function find(node) { while (parent[node] !== node) { parent[node] = parent[parent[node]]; node = parent[node]; } return node; }
  for (const [first, second] of edges) {
    let a = find(first), b = find(second);
    if (a === b) continue;
    if (size[a] < size[b]) [a, b] = [b, a];
    parent[b] = a; size[a] += size[b];
  }
  const value = Array(n).fill(-1);
  for (const [a, , weight] of edges) value[find(a)] &= weight;
  return query.map(([a, b]) => a === b ? 0 : find(a) === find(b) ? value[find(a)] : -1);
}

const minimumCost = solve;
class Solution {
  minimumCost(n, edges, query) { return solve(n, edges, query); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumCost };
