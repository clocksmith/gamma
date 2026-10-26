'use strict';

// 674. Longest Continuous Increasing Subsequence (Easy).
// Specification: https://leetcode.com/problems/longest-continuous-increasing-subsequence/description/
// O(n) time, O(1) space; reset the current run whenever strict increase ends.
function solve(nums) {
  let longest = 0;
  let current = 0;
  for (let index = 0; index < nums.length; index++) {
    current = index > 0 && nums[index] > nums[index - 1] ? current + 1 : 1;
    longest = Math.max(longest, current);
  }
  return longest;
}

const findLengthOfLCIS = solve;
class Solution {
  findLengthOfLCIS(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findLengthOfLCIS };
