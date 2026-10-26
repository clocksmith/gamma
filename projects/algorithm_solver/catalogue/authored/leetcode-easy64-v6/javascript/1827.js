'use strict';

// 1827. Minimum Operations to Make the Array Increasing (Easy).
// Specification: https://leetcode.com/problems/minimum-operations-to-make-the-array-increasing/description/
// O(n) time, O(1) space; track the smallest feasible predecessor without mutating nums.
function solve(nums) {
  let previous = nums[0];
  let operations = 0;
  for (let index = 1; index < nums.length; index++) {
    const required = Math.max(nums[index], previous + 1);
    operations += required - nums[index];
    previous = required;
  }
  return operations;
}

const minOperations = solve;
class Solution {
  minOperations(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
