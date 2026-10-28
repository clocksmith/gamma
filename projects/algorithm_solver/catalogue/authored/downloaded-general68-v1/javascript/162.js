'use strict';

// 162. Find Peak Element (Medium).
// Specification: https://leetcode.com/problems/find-peak-element/description/
function solve(nums) {
  let left = 0; let right = nums.length - 1;
  while (left < right) {
    const mid = Math.floor((left + right) / 2);
    if (nums[mid] < nums[mid + 1]) left = mid + 1;
    else right = mid;
  }
  return left;
}
const findPeakElement = solve;
class Solution { findPeakElement(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findPeakElement };
