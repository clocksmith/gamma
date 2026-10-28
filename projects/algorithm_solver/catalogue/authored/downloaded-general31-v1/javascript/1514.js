'use strict';

// 1514. Path with Maximum Probability (Medium).
// Specification: https://leetcode.com/problems/path-with-maximum-probability/description/
function solve(n, edges, succProb, start, end) {
  const graph = Array.from({ length: n }, () => []);
  for (let i = 0; i < edges.length; i++) {
    const [a, b] = edges[i];
    graph[a].push([b, succProb[i]]);
    graph[b].push([a, succProb[i]]);
  }
  const best = new Array(n).fill(0);
  best[start] = 1;
  const visited = new Array(n).fill(false);
  for (let step = 0; step < n; step++) {
    let node = -1; let value = 0;
    for (let i = 0; i < n; i++) { if (!visited[i] && best[i] > value) { value = best[i]; node = i; } }
    if (node === -1) break;
    visited[node] = true;
    for (const [neighbor, prob] of graph[node]) {
      if (best[node] * prob > best[neighbor]) best[neighbor] = best[node] * prob;
    }
  }
  return best[end];
}
const maxProbability = solve;
class Solution { maxProbability(n, edges, succProb, start, end) { return solve(n, edges, succProb, start, end); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProbability };
