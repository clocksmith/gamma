/**
 * 3807. Minimum Cost to Repair Edges to Traverse a Graph
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(n, edges, k).
 * Algorithm: Binary search the repair threshold; bounded breadth-first search checks at most k edges.
 * Complexity: O(m log m + (n+m) log m) time; O(n+m) space.
 * Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Ordered-positional solve; native forwarding name included only when confirmed.
 * Specification: https://leetcode.com/problems/minimum-cost-to-repair-edges-to-traverse-a-graph/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3807.Minimum%20Cost%20to%20Repair%20Edges%20to%20Traverse%20a%20Graph/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 * Contract note: money is a threshold for repairing all affordable edges, not their summed repair costs.
 */

function solve(n, edges, k) {
  const adjacency = Array.from({ length: n }, () => []);
  for (const [first, second, cost] of edges) {
    adjacency[first].push([second, cost]);
    adjacency[second].push([first, cost]);
  }
  const costs = [...new Set(edges.map(edge => edge[2]))].sort((a, b) => a - b);
  function reachable(budget) {
    const distance = new Int32Array(n).fill(-1);
    distance[0] = 0;
    const queue = [0];
    for (let head = 0; head < queue.length; head += 1) {
      const node = queue[head];
      if (node === n - 1) return true;
      if (distance[node] === k) continue;
      for (const [neighbor, cost] of adjacency[node]) {
        if (cost <= budget && distance[neighbor] === -1) {
          distance[neighbor] = distance[node] + 1;
          queue.push(neighbor);
        }
      }
    }
    return false;
  }
  if (costs.length === 0 || !reachable(costs[costs.length - 1])) return -1;
  let left = 0;
  let right = costs.length - 1;
  while (left < right) {
    const middle = Math.floor((left + right) / 2);
    if (reachable(costs[middle])) right = middle;
    else left = middle + 1;
  }
  return costs[left];
}

function minCost(n, edges, k) {
  return solve(n, edges, k);
}

class Solution {
  minCost(n, edges, k) {
    return solve(n, edges, k);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, minCost, Solution };
}
