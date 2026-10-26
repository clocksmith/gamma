'use strict';

// 1708. Largest Subarray Length K (Easy).
// Specification: https://leetcode.com/problems/largest-subarray-length-k/description/
// O(n) time, O(k) result space; distinct input values make the first element decisive.
function solve(nums, k) {
  let bestStart = 0;
  for (let start = 1; start <= nums.length - k; start++) {
    if (nums[start] > nums[bestStart]) bestStart = start;
  }
  return nums.slice(bestStart, bestStart + k);
}

const largestSubarray = solve;
class Solution {
  largestSubarray(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestSubarray };
