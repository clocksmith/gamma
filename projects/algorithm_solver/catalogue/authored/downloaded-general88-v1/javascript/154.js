'use strict';

// 154. Find Minimum in Rotated Sorted Array II (Hard).
// Specification: https://leetcode.com/problems/find-minimum-in-rotated-sorted-array-ii/description/
function solve(nums) {
  let left = 0; let right = nums.length - 1;
  while (left < right) {
    const mid = Math.floor((left + right) / 2);
    if (nums[mid] > nums[right]) left = mid + 1;
    else if (nums[mid] < nums[right]) right = mid;
    else right--;
  }
  return nums[left];
}
const findMin = solve;
class Solution { findMin(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMin };
