'use strict';

// 684. Redundant Connection (Medium).
// Specification: https://leetcode.com/problems/redundant-connection/description/
function solve(edges) {
  const parent = {};
  function find(x) {
    if (parent[x] === undefined) parent[x] = x;
    if (parent[x] !== x) parent[x] = find(parent[x]);
    return parent[x];
  }
  for (const [a, b] of edges) {
    const rootA = find(a); const rootB = find(b);
    if (rootA === rootB) return [a, b];
    parent[rootA] = rootB;
  }
  return [];
}
const findRedundantConnection = solve;
class Solution { findRedundantConnection(edges) { return solve(edges); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findRedundantConnection };
