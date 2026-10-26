'use strict';

// 3701. Compute Alternating Sum (Easy).
// Specification: https://leetcode.com/problems/compute-alternating-sum/description/
// O(n) time, O(1) space; preserve nums.
function solve(nums) {
  let result = 0;
  let sign = 1;
  for (const value of nums) {
    result += sign * value;
    sign = -sign;
  }
  return result;
}

const alternatingSum = solve;
class Solution {
  alternatingSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, alternatingSum };
