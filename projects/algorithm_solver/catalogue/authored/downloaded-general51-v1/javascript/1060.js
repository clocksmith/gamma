'use strict';

// 1060. Missing Element in Sorted Array (Medium).
// Specification: https://leetcode.com/problems/missing-element-in-sorted-array/description/
function solve(nums, k) {
  for (let i = 0; i < nums.length - 1; i++) {
    const missing = nums[i + 1] - nums[i] - 1;
    if (k <= missing) return nums[i] + k;
    k -= missing;
  }
  return nums[nums.length - 1] + k;
}
const missingElement = solve;
class Solution { missingElement(nums, k) { return solve(nums, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, missingElement };
