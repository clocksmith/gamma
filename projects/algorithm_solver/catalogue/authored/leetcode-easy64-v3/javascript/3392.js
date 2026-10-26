'use strict';

// 3392. Count Subarrays of Length Three With a Condition (Easy).
// Specification: https://leetcode.com/problems/count-subarrays-of-length-three-with-a-condition/description/
// O(n) time, O(1) space; multiply the outer sum by two to avoid fractional division.
function solve(nums) {
  let result = 0;
  for (let index = 1; index + 1 < nums.length; index++) {
    if (2 * (nums[index - 1] + nums[index + 1]) === nums[index]) result++;
  }
  return result;
}

const countSubarrays = solve;
class Solution {
  countSubarrays(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSubarrays };
