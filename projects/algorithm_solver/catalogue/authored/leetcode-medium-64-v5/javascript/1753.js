'use strict';

// 1753. Maximum Score From Removing Stones: bound pair removals by half the total and the two smaller piles.
// O(1) time and O(1) auxiliary space; inputs are read-only.
function solve(a, b, c) {
  const total = a + b + c;
  return Math.min(Math.floor(total / 2), total - Math.max(a, b, c));
}

const maximumScore = solve;
class Solution {
  maximumScore(a, b, c) { return solve(a, b, c); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumScore };
