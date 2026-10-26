'use strict';

// 1557. Minimum Number of Vertices to Reach All Nodes: select exactly the zero-indegree vertices of the directed acyclic graph.
// O(n + e) time and O(n) auxiliary space; inputs are read-only.
function solve(n, edges) {
  const incoming = new Uint8Array(n);
  for (const [start, end] of edges) incoming[end] = 1;
  const result = [];
  for (let node = 0; node < n; node += 1) {
    if (!incoming[node]) result.push(node);
  }
  return result;
}

const findSmallestSetOfVertices = solve;
class Solution {
  findSmallestSetOfVertices(n, edges) { return solve(n, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findSmallestSetOfVertices };
