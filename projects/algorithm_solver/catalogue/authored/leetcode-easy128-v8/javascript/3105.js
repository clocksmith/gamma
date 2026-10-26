'use strict';

// 3105. Longest Strictly Increasing or Strictly Decreasing Subarray (Easy).
// Specification: https://leetcode.com/problems/longest-strictly-increasing-or-strictly-decreasing-subarray/description/
// O(n) time, O(1) space; independently track strict increasing and decreasing runs.
function solve(nums) {
  let increasing = 1;
  let decreasing = 1;
  let longest = 1;
  for (let index = 1; index < nums.length; index++) {
    increasing = nums[index] > nums[index - 1] ? increasing + 1 : 1;
    decreasing = nums[index] < nums[index - 1] ? decreasing + 1 : 1;
    longest = Math.max(longest, increasing, decreasing);
  }
  return longest;
}

const longestMonotonicSubarray = solve;
class Solution {
  longestMonotonicSubarray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestMonotonicSubarray };
