'use strict';

// 473. Matchsticks to Square (Medium).
// Specification: https://leetcode.com/problems/matchsticks-to-square/description/
function solve(matchsticks) {
  const total = matchsticks.reduce((sum, value) => sum + value, 0);
  if (total % 4 !== 0) return false;
  const target = total / 4;
  const sorted = matchsticks.slice().sort((a, b) => b - a);
  const sides = [0, 0, 0, 0];
  function backtrack(index) {
    if (index === sorted.length) return sides.every((side) => side === target);
    for (let side = 0; side < 4; side++) {
      if (sides[side] + sorted[index] > target) continue;
      sides[side] += sorted[index];
      if (backtrack(index + 1)) return true;
      sides[side] -= sorted[index];
      if (sides[side] === 0) break;
    }
    return false;
  }
  return backtrack(0);
}
const makesquare = solve;
class Solution { makesquare(matchsticks) { return solve(matchsticks); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, makesquare };
