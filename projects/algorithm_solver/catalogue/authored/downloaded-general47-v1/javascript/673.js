'use strict';

// 673. Number of Longest Increasing Subsequence (Medium).
// Specification: https://leetcode.com/problems/number-of-longest-increasing-subsequence/description/
function solve(nums) {
  const lengths = new Array(nums.length).fill(1);
  const counts = new Array(nums.length).fill(1);
  let longest = 1;
  for (let i = 0; i < nums.length; i++) {
    for (let j = 0; j < i; j++) {
      if (nums[j] < nums[i]) {
        if (lengths[j] + 1 > lengths[i]) { lengths[i] = lengths[j] + 1; counts[i] = counts[j]; }
        else if (lengths[j] + 1 === lengths[i]) counts[i] += counts[j];
      }
    }
    longest = Math.max(longest, lengths[i]);
  }
  let total = 0;
  for (let i = 0; i < nums.length; i++) { if (lengths[i] === longest) total += counts[i]; }
  return total;
}
const findNumberOfLIS = solve;
class Solution { findNumberOfLIS(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findNumberOfLIS };
