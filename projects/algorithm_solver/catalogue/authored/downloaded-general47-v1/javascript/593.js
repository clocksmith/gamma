'use strict';

// 593. Valid Square (Medium).
// Specification: https://leetcode.com/problems/valid-square/description/
function solve(p1, p2, p3, p4) {
  const points = [p1, p2, p3, p4];
  const distances = [];
  for (let i = 0; i < 4; i++) {
    for (let j = i + 1; j < 4; j++) {
      const dx = points[i][0] - points[j][0]; const dy = points[i][1] - points[j][1];
      distances.push(dx * dx + dy * dy);
    }
  }
  distances.sort((a, b) => a - b);
  return distances[0] > 0 && distances[0] === distances[1] && distances[1] === distances[2] && distances[2] === distances[3] && distances[4] === distances[5] && distances[4] === 2 * distances[0];
}
const validSquare = solve;
class Solution { validSquare(p1, p2, p3, p4) { return solve(p1, p2, p3, p4); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, validSquare };
