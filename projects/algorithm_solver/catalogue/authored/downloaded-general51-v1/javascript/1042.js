'use strict';

// 1042. Flower Planting With No Adjacent (Medium).
// Specification: https://leetcode.com/problems/flower-planting-with-no-adjacent/description/
function solve(n, paths) {
  const graph = Array.from({ length: n }, () => []);
  for (const [a, b] of paths) { graph[a - 1].push(b - 1); graph[b - 1].push(a - 1); }
  const answer = new Array(n).fill(0);
  for (let garden = 0; garden < n; garden++) {
    const used = new Set();
    for (const neighbor of graph[garden]) { if (answer[neighbor] !== 0) used.add(answer[neighbor]); }
    for (let color = 1; color <= 4; color++) { if (!used.has(color)) { answer[garden] = color; break; } }
  }
  return answer;
}
const gardenNoAdj = solve;
class Solution { gardenNoAdj(n, paths) { return solve(n, paths); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, gardenNoAdj };
