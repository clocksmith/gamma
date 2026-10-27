'use strict';
// 323. Number of Connected Components in an Undirected Graph.
function solve(n, edges) {
  const parent = Array.from({ length: n }, (_, index) => index); let count = n;
  function find(node) {
    while (parent[node] !== node) { parent[node] = parent[parent[node]]; node = parent[node]; }
    return node;
  }
  for (const [left, right] of edges) {
    const rootLeft = find(left); const rootRight = find(right);
    if (rootLeft !== rootRight) { parent[rootLeft] = rootRight; count -= 1; }
  }
  return count;
}
const countComponents = solve;
class Solution { countComponents(n, edges) { return solve(n, edges); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, countComponents };
