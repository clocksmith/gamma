'use strict';

// 473. Matchsticks to Square.

function solve(matchsticks) {
  const total = matchsticks.reduce((sum, value) => sum + value, 0);
  if (matchsticks.length < 4 || total % 4 !== 0) return false;
  const target = total / 4, sticks = matchsticks.slice().sort((a, b) => b - a), sides = [0, 0, 0, 0];
  if (sticks[0] > target) return false;
  function place(index) {
    if (index === sticks.length) return true;
    const tried = new Set();
    for (let side = 0; side < 4; side += 1) {
      const before = sides[side];
      if (tried.has(before) || before + sticks[index] > target) continue;
      tried.add(before); sides[side] += sticks[index];
      if (place(index + 1)) return true;
      sides[side] = before;
    }
    return false;
  }
  return place(0);
}

const makesquare = solve;
class Solution {
  makesquare(matchsticks) { return solve(matchsticks); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, makesquare };
