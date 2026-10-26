'use strict';

// 2249. Count Lattice Points Inside a Circle: enumerate bounded integer coordinates and deduplicate points satisfying a squared-radius check.
// O(sum(r^2)) time and O(U) auxiliary space for U distinct covered points; inputs are read-only.
function solve(circles) {
  const covered = new Set();
  for (const [x, y, radius] of circles) {
    const squared = radius * radius;
    for (let column = x - radius; column <= x + radius; column += 1) {
      for (let row = y - radius; row <= y + radius; row += 1) {
        const dx = column - x;
        const dy = row - y;
        if (dx * dx + dy * dy <= squared) covered.add(`${column},${row}`);
      }
    }
  }
  return covered.size;
}

const countLatticePoints = solve;
class Solution {
  countLatticePoints(circles) { return solve(circles); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countLatticePoints };
