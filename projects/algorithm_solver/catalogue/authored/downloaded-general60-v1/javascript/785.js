'use strict';

// 785. Is Graph Bipartite? (Medium).
// Specification: https://leetcode.com/problems/is-graph-bipartite/description/
function solve(graph) {
  const color = new Array(graph.length).fill(-1);
  for (let start = 0; start < graph.length; start++) {
    if (color[start] !== -1) continue;
    color[start] = 0;
    const queue = [start];
    while (queue.length > 0) {
      const node = queue.shift();
      for (const neighbor of graph[node]) {
        if (color[neighbor] === -1) { color[neighbor] = 1 - color[node]; queue.push(neighbor); }
        else if (color[neighbor] === color[node]) return false;
      }
    }
  }
  return true;
}
const isBipartite = solve;
class Solution { isBipartite(graph) { return solve(graph); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isBipartite };
