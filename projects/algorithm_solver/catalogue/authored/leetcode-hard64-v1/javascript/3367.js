'use strict';

// 3367. Maximize Sum of Weights after Edge Removals: iterative tree dynamic programming with positive child-edge gains.
// O(n log n) time and O(n) auxiliary space. Inputs are preserved.
function solve(edges, k) {
  const n = edges.length + 1;
  const graph = Array.from({ length: n }, () => []);
  for (const [first, second, weight] of edges) {
    graph[first].push([second, weight]);
    graph[second].push([first, weight]);
  }
  const parent = new Int32Array(n).fill(-1);
  const order = [0];
  for (let index = 0; index < order.length; index += 1) {
    const node = order[index];
    for (const [child] of graph[node]) {
      if (child !== parent[node]) {
        parent[child] = node;
        order.push(child);
      }
    }
  }
  const free = new Float64Array(n);
  const used = new Float64Array(n);
  for (let index = order.length - 1; index >= 0; index -= 1) {
    const node = order[index];
    let base = 0;
    const gains = [];
    for (const [child, weight] of graph[node]) {
      if (parent[child] !== node) continue;
      base += free[child];
      const gain = weight + used[child] - free[child];
      if (gain > 0) gains.push(gain);
    }
    gains.sort((a, b) => b - a);
    let selected = 0;
    for (let position = 0; position < Math.min(k, gains.length); position += 1) selected += gains[position];
    free[node] = base + selected;
    if (k === 0) used[node] = -Infinity;
    else used[node] = free[node] - (gains.length >= k ? gains[k - 1] : 0);
  }
  return free[0];
}

const maximizeSumOfWeights = solve;
class Solution {
  maximizeSumOfWeights(edges, k) { return solve(edges, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximizeSumOfWeights };
