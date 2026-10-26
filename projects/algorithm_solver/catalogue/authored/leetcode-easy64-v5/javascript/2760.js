'use strict';

// 2760. Longest Even Odd Subarray With Threshold (Easy).
// Specification: https://leetcode.com/problems/longest-even-odd-subarray-with-threshold/description/
// O(n) time, O(1) auxiliary space; preserve nums.
function solve(nums, threshold) {
  let length = 0;
  let longest = 0;
  for (let index = 0; index < nums.length; index++) {
    const value = nums[index];
    if (value > threshold) {
      length = 0;
    } else if (length > 0 && value % 2 !== nums[index - 1] % 2) {
      length++;
    } else {
      length = value % 2 === 0 ? 1 : 0;
    }
    longest = Math.max(longest, length);
  }
  return longest;
}

const longestAlternatingSubarray = solve;
class Solution {
  longestAlternatingSubarray(nums, threshold) { return solve(nums, threshold); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestAlternatingSubarray };
