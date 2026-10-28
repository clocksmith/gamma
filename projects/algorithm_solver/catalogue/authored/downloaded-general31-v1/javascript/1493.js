'use strict';

// 1493. Longest Subarray of 1's After Deleting One Element (Medium).
// Specification: https://leetcode.com/problems/longest-subarray-of-1s-after-deleting-one-element/description/
function solve(nums) {
  let left = 0; let zeros = 0; let best = 0;
  for (let right = 0; right < nums.length; right++) {
    if (nums[right] === 0) zeros++;
    while (zeros > 1) { if (nums[left] === 0) zeros--; left++; }
    best = Math.max(best, right - left + 1);
  }
  return best - 1;
}
const longestSubarray = solve;
class Solution { longestSubarray(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestSubarray };
