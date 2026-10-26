'use strict';

// 3512. Minimum Operations to Make Array Sum Divisible by K (Easy).
// Specification: https://leetcode.com/problems/minimum-operations-to-make-array-sum-divisible-by-k/description/
// O(n) time, O(1) space; reduce the positive total to its nearest lower multiple.
function solve(nums, k) {
  let total = 0;
  for (const value of nums) total += value;
  return total % k;
}

const minOperations = solve;
class Solution {
  minOperations(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
