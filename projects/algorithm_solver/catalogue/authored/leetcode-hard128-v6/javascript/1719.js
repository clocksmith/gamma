'use strict';

// 1719. Number Of Ways To Reconstruct A Tree.
// Verify containment of ancestor-neighborhood sets; O(v^2 + e) time and space. Inputs are preserved.

function solve(pairs) {
  const graph = new Map();
  for (const [a, b] of pairs) {
    if (!graph.has(a)) graph.set(a, new Set());
    if (!graph.has(b)) graph.set(b, new Set());
    graph.get(a).add(b); graph.get(b).add(a);
  }
  let root = null;
  for (const [node, neighbors] of graph) if (neighbors.size === graph.size - 1) { root = node; break; }
  if (root === null) return 0;
  let answer = 1;
  for (const [node, neighbors] of graph) {
    if (node === root) continue;
    let parent = null;
    for (const other of neighbors) {
      if (graph.get(other).size < neighbors.size) continue;
      if (parent === null || graph.get(other).size < graph.get(parent).size ||
          (graph.get(other).size === graph.get(parent).size && other < parent)) parent = other;
    }
    if (parent === null) return 0;
    for (const other of neighbors) if (other !== parent && !graph.get(parent).has(other)) return 0;
    if (graph.get(parent).size === neighbors.size) answer = 2;
  }
  return answer;
}

const checkWays = solve;
class Solution {
  checkWays(pairs) { return solve(pairs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkWays };
