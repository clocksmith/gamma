'use strict';

// 2192. All Ancestors of a Node in a Directed Acyclic Graph (Medium).
// Specification: https://leetcode.com/problems/all-ancestors-of-a-node-in-a-directed-acyclic-graph/description/
function solve(n, edges) {
  const reverse = Array.from({ length: n }, () => []);
  for (const [from, to] of edges) reverse[to].push(from);
  const result = [];
  for (let node = 0; node < n; node++) {
    const seen = new Set();
    const stack = reverse[node].slice();
    while (stack.length > 0) {
      const current = stack.pop();
      if (seen.has(current)) continue;
      seen.add(current);
      for (const parent of reverse[current]) stack.push(parent);
    }
    result.push([...seen].sort((a, b) => a - b));
  }
  return result;
}
const getAncestors = solve;
class Solution { getAncestors(n, edges) { return solve(n, edges); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, getAncestors };
