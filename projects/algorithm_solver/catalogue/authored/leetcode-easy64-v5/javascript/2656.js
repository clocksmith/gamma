'use strict';

// 2656. Maximum Sum With Exactly K Elements (Easy).
// Specification: https://leetcode.com/problems/maximum-sum-with-exactly-k-elements/description/
// O(n) time, O(1) auxiliary space; preserve nums.
function solve(nums, k) {
  let largest = nums[0];
  for (const value of nums) largest = Math.max(largest, value);
  return k * largest + k * (k - 1) / 2;
}

const maximizeSum = solve;
class Solution {
  maximizeSum(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximizeSum };
