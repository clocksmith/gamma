'use strict';

// 2973. Find Number of Coins to Place in Tree Nodes.
// Postorder aggregation retains only two minima and three maxima; O(n) time and space. Inputs are preserved.

function solve(edges, cost) {
  const n = cost.length, graph = cost.map(() => []), parent = Array(n).fill(-1), order = [0];
  for (const [a, b] of edges) { graph[a].push(b); graph[b].push(a); }
  for (let index = 0; index < order.length; index += 1) {
    const node = order[index];
    for (const neighbor of graph[node]) if (neighbor !== parent[node]) { parent[neighbor] = node; order.push(neighbor); }
  }
  const sizes = Array(n).fill(1), extremes = cost.map(() => []), answers = Array(n).fill(1);
  for (let index = order.length - 1; index >= 0; index -= 1) {
    const node = order[index];
    let values = [cost[node]];
    for (const child of graph[node]) {
      if (parent[child] !== node) continue;
      sizes[node] += sizes[child];
      values = values.concat(extremes[child]).sort((a, b) => a - b);
      if (values.length > 5) values = values.slice(0, 2).concat(values.slice(-3));
    }
    extremes[node] = values;
    const length = values.length;
    if (sizes[node] >= 3) answers[node] = Math.max(0, values[length - 1] * values[length - 2] * values[length - 3], values[0] * values[1] * values[length - 1]);
  }
  return answers;
}

const placedCoins = solve;
class Solution {
  placedCoins(edges, cost) { return solve(edges, cost); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, placedCoins };
