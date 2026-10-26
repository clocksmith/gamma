'use strict';

// 2368. Reachable Nodes With Restrictions: traverse the allowed component from zero without recursive depth limits.
// O(n + e) time and O(n + e) auxiliary space; inputs are read-only.
function solve(n, edges, restricted) {
  const blocked = new Set(restricted);
  if (blocked.has(0)) return 0;
  const graph = Array.from({ length: n }, () => []);
  for (const [left, right] of edges) {
    graph[left].push(right);
    graph[right].push(left);
  }
  const seen = new Set([0]);
  const stack = [0];
  while (stack.length) {
    const node = stack.pop();
    for (const neighbor of graph[node]) {
      if (!blocked.has(neighbor) && !seen.has(neighbor)) {
        seen.add(neighbor);
        stack.push(neighbor);
      }
    }
  }
  return seen.size;
}

const reachableNodes = solve;
class Solution {
  reachableNodes(n, edges, restricted) { return solve(n, edges, restricted); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reachableNodes };
