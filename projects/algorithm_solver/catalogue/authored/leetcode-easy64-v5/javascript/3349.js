'use strict';

// 3349. Adjacent Increasing Subarrays Detection I (Easy).
// Specification: https://leetcode.com/problems/adjacent-increasing-subarrays-detection-i/description/
// O(n) time, O(1) auxiliary space; use one run split in two or adjacent increasing runs.
function solve(nums, k) {
  let previousRun = 0;
  let currentRun = 0;
  for (let index = 0; index < nums.length; index++) {
    if (index === 0 || nums[index] > nums[index - 1]) {
      currentRun++;
    } else {
      previousRun = currentRun;
      currentRun = 1;
    }
    if (Math.floor(currentRun / 2) >= k || Math.min(previousRun, currentRun) >= k) return true;
  }
  return false;
}

const hasIncreasingSubarrays = solve;
class Solution {
  hasIncreasingSubarrays(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, hasIncreasingSubarrays };
