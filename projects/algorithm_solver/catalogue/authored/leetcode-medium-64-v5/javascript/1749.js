'use strict';

// 1749. Maximum Absolute Sum of Any Subarray: take the difference between the largest and smallest prefix sums.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums) {
  let prefix = 0;
  let lowest = 0;
  let highest = 0;
  for (const value of nums) {
    prefix += value;
    lowest = Math.min(lowest, prefix);
    highest = Math.max(highest, prefix);
  }
  return highest - lowest;
}

const maxAbsoluteSum = solve;
class Solution {
  maxAbsoluteSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxAbsoluteSum };
