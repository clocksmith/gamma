'use strict';

// 3065. Minimum Operations to Exceed Threshold Value I (Easy).
// Specification: https://leetcode.com/problems/minimum-operations-to-exceed-threshold-value-i/description/
// O(n) time, O(1) auxiliary space; preserve nums.
function solve(nums, k) {
  let operations = 0;
  for (const value of nums) {
    if (value < k) operations++;
  }
  return operations;
}

const minOperations = solve;
class Solution {
  minOperations(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
