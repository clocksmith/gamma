'use strict';

// 268. Missing Number (Easy).
// Specification: https://leetcode.com/problems/missing-number/description/
// O(n) time, O(1) space; sums are exact in the stated n <= 10000 domain; preserve nums.
function solve(nums) {
  let missing = nums.length;
  for (let index = 0; index < nums.length; index++) {
    missing += index - nums[index];
  }
  return missing;
}

const missingNumber = solve;
class Solution {
  missingNumber(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, missingNumber };
