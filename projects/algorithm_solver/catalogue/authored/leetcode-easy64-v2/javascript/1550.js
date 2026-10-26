'use strict';

// 1550. Three Consecutive Odds (Easy).
// Specification: https://leetcode.com/problems/three-consecutive-odds/description/
// O(n) time, O(1) space; preserve arr.
function solve(arr) {
  let consecutive = 0;
  for (const value of arr) {
    consecutive = value % 2 !== 0 ? consecutive + 1 : 0;
    if (consecutive === 3) return true;
  }
  return false;
}

const threeConsecutiveOdds = solve;
class Solution {
  threeConsecutiveOdds(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, threeConsecutiveOdds };
