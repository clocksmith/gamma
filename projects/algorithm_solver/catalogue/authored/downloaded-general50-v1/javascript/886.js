'use strict';

// 886. Possible Bipartition (Medium).
// Specification: https://leetcode.com/problems/possible-bipartition/description/
function solve(n, dislikes) {
  const graph = Array.from({ length: n + 1 }, () => []);
  for (const [a, b] of dislikes) { graph[a].push(b); graph[b].push(a); }
  const color = new Array(n + 1).fill(0);
  for (let start = 1; start <= n; start++) {
    if (color[start] !== 0) continue;
    color[start] = 1;
    const queue = [start];
    while (queue.length > 0) {
      const node = queue.shift();
      for (const neighbor of graph[node]) {
        if (color[neighbor] === 0) { color[neighbor] = -color[node]; queue.push(neighbor); }
        else if (color[neighbor] === color[node]) return false;
      }
    }
  }
  return true;
}
const possibleBipartition = solve;
class Solution { possibleBipartition(n, dislikes) { return solve(n, dislikes); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, possibleBipartition };
