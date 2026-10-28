'use strict';

// 1552. Magnetic Force Between Two Balls (Medium).
// Specification: https://leetcode.com/problems/magnetic-force-between-two-balls/description/
function canPlace(position, m, distance) {
  let placed = 1; let last = position[0];
  for (let i = 1; i < position.length; i++) {
    if (position[i] - last >= distance) { placed++; last = position[i]; if (placed >= m) return true; }
  }
  return placed >= m;
}
function solve(position, m) {
  const sorted = position.slice().sort((a, b) => a - b);
  let left = 1; let right = sorted[sorted.length - 1] - sorted[0]; let best = 1;
  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    if (canPlace(sorted, m, mid)) { best = mid; left = mid + 1; } else right = mid - 1;
  }
  return best;
}
const maxDistance = solve;
class Solution { maxDistance(position, m) { return solve(position, m); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxDistance };
