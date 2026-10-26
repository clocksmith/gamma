'use strict';

// 3487. Maximum Unique Subarray Sum After Deletion (Easy).
// Specification: https://leetcode.com/problems/maximum-unique-subarray-sum-after-deletion/description/
// O(n) expected time, O(n) space; keep distinct positives or the largest single value.
function solve(nums) {
  const positive = new Set();
  let largest = nums[0];
  let total = 0;
  for (const value of nums) {
    largest = Math.max(largest, value);
    if (value > 0 && !positive.has(value)) {
      positive.add(value);
      total += value;
    }
  }
  return positive.size > 0 ? total : largest;
}

const maxSum = solve;
class Solution {
  maxSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSum };
