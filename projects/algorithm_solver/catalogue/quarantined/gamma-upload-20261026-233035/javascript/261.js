'use strict';
// 261. Graph Valid Tree.
function solve(n, edges) {
  if (edges.length !== n - 1) return false;
  const parent = Array.from({ length: n }, (_, index) => index);
  function find(node) {
    while (parent[node] !== node) { parent[node] = parent[parent[node]]; node = parent[node]; }
    return node;
  }
  for (const [left, right] of edges) {
    const rootLeft = find(left); const rootRight = find(right);
    if (rootLeft === rootRight) return false;
    parent[rootLeft] = rootRight;
  }
  return true;
}
const validTree = solve;
class Solution { validTree(n, edges) { return solve(n, edges); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, validTree };
