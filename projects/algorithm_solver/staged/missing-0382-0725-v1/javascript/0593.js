'use strict';

// 593. Valid Square.

function solve(p1, p2, p3, p4) {
  const points = [p1, p2, p3, p4], distances = [];
  for (let i = 0; i < 4; i += 1) for (let j = i + 1; j < 4; j += 1) {
    distances.push((points[i][0] - points[j][0]) ** 2 + (points[i][1] - points[j][1]) ** 2);
  }
  distances.sort((a, b) => a - b);
  return distances[0] > 0 && distances.slice(0, 4).every(value => value === distances[0])
    && distances[4] === 2 * distances[0] && distances[5] === distances[4];
}

const validSquare = solve;
class Solution {
  validSquare(p1, p2, p3, p4) { return solve(p1, p2, p3, p4); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, validSquare };
