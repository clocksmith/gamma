'use strict';

// 797. All Paths From Source to Target (Medium).
// Specification: https://leetcode.com/problems/all-paths-from-source-to-target/description/
function solve(graph) {
  const result = [];
  const target = graph.length - 1;
  function dfs(node, path) {
    if (node === target) { result.push(path.slice()); return; }
    for (const next of graph[node]) { path.push(next); dfs(next, path); path.pop(); }
  }
  dfs(0, [0]);
  return result;
}
const allPathsSourceTarget = solve;
class Solution { allPathsSourceTarget(graph) { return solve(graph); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, allPathsSourceTarget };
