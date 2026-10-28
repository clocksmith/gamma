'use strict';

// 310. Minimum Height Trees (Medium).
// Specification: https://leetcode.com/problems/minimum-height-trees/description/
function solve(n, edges) {
  if (n === 1) return [0];
  const graph = Array.from({ length: n }, () => []);
  const degree = new Array(n).fill(0);
  for (const [a, b] of edges) { graph[a].push(b); graph[b].push(a); degree[a]++; degree[b]++; }
  let leaves = [];
  for (let i = 0; i < n; i++) { if (degree[i] === 1) leaves.push(i); }
  let remaining = n;
  while (remaining > 2) {
    remaining -= leaves.length;
    const nextLeaves = [];
    for (const leaf of leaves) {
      for (const neighbor of graph[leaf]) { degree[neighbor]--; if (degree[neighbor] === 1) nextLeaves.push(neighbor); }
    }
    leaves = nextLeaves;
  }
  return leaves.sort((a, b) => a - b);
}
const findMinHeightTrees = solve;
class Solution { findMinHeightTrees(n, edges) { return solve(n, edges); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMinHeightTrees };
