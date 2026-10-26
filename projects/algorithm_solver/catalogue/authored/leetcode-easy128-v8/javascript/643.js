'use strict';

// 643. Maximum Average Subarray I (Easy).
// Specification: https://leetcode.com/problems/maximum-average-subarray-i/description/
// O(n) time, O(1) auxiliary space; maintain the exact integer sum of each k-wide window.
function solve(nums, k) {
  let total = 0;
  for (let index = 0; index < k; index++) total += nums[index];
  let largest = total;
  for (let index = k; index < nums.length; index++) {
    total += nums[index] - nums[index - k];
    largest = Math.max(largest, total);
  }
  return largest / k;
}

const findMaxAverage = solve;
class Solution {
  findMaxAverage(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMaxAverage };
