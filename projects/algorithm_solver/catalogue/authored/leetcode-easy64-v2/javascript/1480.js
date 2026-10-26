'use strict';

// 1480. Running Sum of 1d Array (Easy).
// Specification: https://leetcode.com/problems/running-sum-of-1d-array/description/
// O(n) time, O(n) output space; preserve nums.
function solve(nums) {
  const result = [];
  let total = 0;
  for (const value of nums) {
    total += value;
    result.push(total);
  }
  return result;
}

const runningSum = solve;
class Solution {
  runningSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, runningSum };
