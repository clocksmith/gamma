'use strict';

// 1800. Maximum Ascending Subarray Sum (Easy).
// Specification: https://leetcode.com/problems/maximum-ascending-subarray-sum/description/
// O(n) time, O(1) auxiliary space. The problem guarantees positive values.
function solve(nums) {
  let current = nums[0];
  let best = current;
  for (let index = 1; index < nums.length; index++) {
    if (nums[index] > nums[index - 1]) current += nums[index];
    else current = nums[index];
    best = Math.max(best, current);
  }
  return best;
}

const maxAscendingSum = solve;
class Solution {
  maxAscendingSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxAscendingSum };
