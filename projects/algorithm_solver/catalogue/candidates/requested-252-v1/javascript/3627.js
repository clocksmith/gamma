'use strict';

// 3627. Maximum Median Sum of Subsequences of Size 3.
// Specification: https://leetcode.com/problems/maximum-median-sum-of-subsequences-of-size-3/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(n log n) time, O(n) space; length is divisible by three.
// Inputs are not modified.

function solve(nums) {
  const ordered = nums.slice().sort((a, b) => a - b);
  let answer = 0;
  for (let index = 0; index < ordered.length / 3; index++) answer += ordered[ordered.length - 2 - 2 * index];
  return answer;
}

const maximumMedianSum = solve;
class Solution {
  maximumMedianSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumMedianSum };
