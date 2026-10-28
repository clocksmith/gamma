'use strict';

// 554. Brick Wall (Medium).
// Specification: https://leetcode.com/problems/brick-wall/description/
function solve(wall) {
  const counts = new Map();
  for (const row of wall) {
    let position = 0;
    for (let i = 0; i < row.length - 1; i++) {
      position += row[i];
      counts.set(position, (counts.get(position) || 0) + 1);
    }
  }
  let best = 0;
  for (const count of counts.values()) best = Math.max(best, count);
  return wall.length - best;
}
const leastBricks = solve;
class Solution { leastBricks(wall) { return solve(wall); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, leastBricks };
