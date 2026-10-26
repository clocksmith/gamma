'use strict';

// 3354. Make Array Elements Equal to Zero (Easy).
// Specification: https://leetcode.com/problems/make-array-elements-equal-to-zero/description/
// O(n) time, O(1) space; compare mass on each side of every zero without simulation.
function solve(nums) {
  let total = 0;
  for (const value of nums) total += value;
  let left = 0;
  let result = 0;
  for (const value of nums) {
    if (value === 0) {
      const difference = Math.abs(left - (total - left));
      if (difference === 0) result += 2;
      else if (difference === 1) result++;
    }
    left += value;
  }
  return result;
}

const countValidSelections = solve;
class Solution {
  countValidSelections(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countValidSelections };
