'use strict';

// 2846. Minimum Edge Weight Equilibrium Queries in a Tree. Binary-lifting LCA and root-prefix counts for the 26 edge weights; O((n+q)*(log(n+1)+26)) time and O(n*(log(n+1)+26)) auxiliary space. Inputs are preserved.

function solve(n, edges, queries) {
  const graph = Array.from({ length: n }, () => []);
  for (const [first, second, weight] of edges) {
    graph[first].push([second, weight - 1]);
    graph[second].push([first, weight - 1]);
  }
  const levels = Math.max(1, Math.floor(Math.log2(n)) + 1);
  const ancestor = Array.from({ length: levels }, () => Array(n).fill(0));
  const depth = Array(n).fill(-1);
  depth[0] = 0;
  const counts = Array.from({ length: n }, () => Array(26).fill(0));
  const order = [0];
  for (let index = 0; index < order.length; index += 1) {
    const node = order[index];
    for (const [neighbor, weight] of graph[node]) {
      if (depth[neighbor] !== -1) continue;
      ancestor[0][neighbor] = node;
      depth[neighbor] = depth[node] + 1;
      counts[neighbor] = counts[node].slice();
      counts[neighbor][weight] += 1;
      order.push(neighbor);
    }
  }
  for (let level = 1; level < levels; level += 1) {
    for (let node = 0; node < n; node += 1) ancestor[level][node] = ancestor[level - 1][ancestor[level - 1][node]];
  }
  function commonAncestor(first, second) {
    if (depth[first] < depth[second]) [first, second] = [second, first];
    const difference = depth[first] - depth[second];
    for (let level = 0; level < levels; level += 1) if ((difference & (1 << level)) !== 0) first = ancestor[level][first];
    if (first === second) return first;
    for (let level = levels - 1; level >= 0; level -= 1) {
      if (ancestor[level][first] !== ancestor[level][second]) {
        first = ancestor[level][first];
        second = ancestor[level][second];
      }
    }
    return ancestor[0][first];
  }
  return queries.map(([first, second]) => {
    const common = commonAncestor(first, second);
    const length = depth[first] + depth[second] - 2 * depth[common];
    let largest = 0;
    for (let weight = 0; weight < 26; weight += 1) largest = Math.max(largest, counts[first][weight] + counts[second][weight] - 2 * counts[common][weight]);
    return length - largest;
  });
}

const minOperationsQueries = solve;
class Solution {
  minOperationsQueries(n, edges, queries) { return solve(n, edges, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperationsQueries };
