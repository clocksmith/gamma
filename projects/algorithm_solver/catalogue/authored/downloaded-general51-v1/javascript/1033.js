'use strict';

// 1033. Moving Stones Until Consecutive (Medium).
// Specification: https://leetcode.com/problems/moving-stones-until-consecutive/description/
function solve(a, b, c) {
  const sorted = [a, b, c].sort((x, y) => x - y);
  const [x, y, z] = sorted;
  if (z - x === 2) return [0, 0];
  const minimum = (y - x <= 2 || z - y <= 2) ? 1 : 2;
  return [minimum, z - x - 2];
}
const numMovesStones = solve;
class Solution { numMovesStones(a, b, c) { return solve(a, b, c); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numMovesStones };
