'use strict';

// 3553. Minimum Weighted Subgraph With the Required Paths II.
// The three-terminal subtree has half the sum of its three pairwise distances; binary lifting answers each distance; O((n+q) log n) time and O(n log n+q) space. Inputs are preserved.

function solve(edges, queries) {
  const n = edges.length + 1, graph = Array.from({ length: n }, () => []);
  for (const [first, second, weight] of edges) { graph[first].push([second, weight]); graph[second].push([first, weight]); }
  let levels = 1;
  while (2 ** levels <= n) levels += 1;
  const ancestor = Array.from({ length: levels }, () => new Int32Array(n));
  const depth = new Int32Array(n), distance = new Float64Array(n), order = [0];
  for (let index = 0; index < order.length; index += 1) {
    const node = order[index];
    for (const [child, weight] of graph[node]) {
      if (child === ancestor[0][node]) continue;
      ancestor[0][child] = node; depth[child] = depth[node] + 1; distance[child] = distance[node] + weight;
      order.push(child);
    }
  }
  for (let level = 1; level < levels; level += 1) {
    for (let node = 0; node < n; node += 1) ancestor[level][node] = ancestor[level - 1][ancestor[level - 1][node]];
  }
  function lca(first, second) {
    if (depth[first] < depth[second]) [first, second] = [second, first];
    const difference = depth[first] - depth[second];
    for (let level = 0; level < levels; level += 1) if (difference & (1 << level)) first = ancestor[level][first];
    if (first === second) return first;
    for (let level = levels - 1; level >= 0; level -= 1) {
      if (ancestor[level][first] !== ancestor[level][second]) { first = ancestor[level][first]; second = ancestor[level][second]; }
    }
    return ancestor[0][first];
  }
  function path(first, second) { return distance[first] + distance[second] - 2 * distance[lca(first, second)]; }
  return queries.map(([first, second, destination]) => (path(first, second) + path(first, destination) + path(second, destination)) / 2);
}

const minimumWeight = solve;
class Solution {
  minimumWeight(edges, queries) { return solve(edges, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumWeight };
