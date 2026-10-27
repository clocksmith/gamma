/**
 * 3787. Find Diameter Endpoints of a Tree
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(n, edges).
 * Algorithm: Three breadth-first searches; a vertex is a diameter endpoint iff its distance to either fixed diameter endpoint equals the diameter.
 * Complexity: O(n) time and space.
 * Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Ordered-positional solve; native forwarding name included only when confirmed.
 * Specification: https://leetcode.com/problems/find-diameter-endpoints-of-a-tree/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3787.Find%20Diameter%20Endpoints%20of%20a%20Tree/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 * Contract note: Returns a binary string, not just one pair of diameter endpoints.
 */

function solve(n, edges) {
  const adjacency = Array.from({ length: n }, () => []);
  for (const [first, second] of edges) {
    adjacency[first].push(second);
    adjacency[second].push(first);
  }
  function distancesFrom(start) {
    const distances = new Int32Array(n).fill(-1);
    distances[start] = 0;
    const queue = [start];
    for (let head = 0; head < queue.length; head += 1) {
      const node = queue[head];
      for (const neighbor of adjacency[node]) {
        if (distances[neighbor] === -1) {
          distances[neighbor] = distances[node] + 1;
          queue.push(neighbor);
        }
      }
    }
    return [queue[queue.length - 1], distances];
  }
  const [first] = distancesFrom(0);
  const [second, fromFirst] = distancesFrom(first);
  const [, fromSecond] = distancesFrom(second);
  const diameter = fromFirst[second];
  const result = [];
  for (let node = 0; node < n; node += 1) {
    result.push(fromFirst[node] === diameter || fromSecond[node] === diameter ? "1" : "0");
  }
  return result.join("");
}

function findSpecialNodes(n, edges) {
  return solve(n, edges);
}

class Solution {
  findSpecialNodes(n, edges) {
    return solve(n, edges);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, findSpecialNodes, Solution };
}
