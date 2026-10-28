'use strict';

// 1182. Shortest Distance to Target Color (Medium).
// Specification: https://leetcode.com/problems/shortest-distance-to-target-color/description/
function nearest(positions, target) {
  let left = 0; let right = positions.length - 1; let best = Infinity;
  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    best = Math.min(best, Math.abs(positions[mid] - target));
    if (positions[mid] < target) left = mid + 1; else right = mid - 1;
  }
  return best;
}
function solve(colors, queries) {
  const positions = [[], [], [], []];
  for (let i = 0; i < colors.length; i++) positions[colors[i]].push(i);
  const result = [];
  for (const [index, color] of queries) {
    const best = nearest(positions[color], index);
    result.push(best === Infinity ? -1 : best);
  }
  return result;
}
const shortestDistanceColor = solve;
class Solution { shortestDistanceColor(colors, queries) { return solve(colors, queries); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, shortestDistanceColor };
