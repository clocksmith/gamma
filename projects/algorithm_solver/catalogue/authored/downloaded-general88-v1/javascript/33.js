'use strict';

// 33. Search in Rotated Sorted Array (Medium).
// Specification: https://leetcode.com/problems/search-in-rotated-sorted-array/description/
function solve(nums, target) {
  let left = 0; let right = nums.length - 1;
  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    if (nums[mid] === target) return mid;
    if (nums[left] <= nums[mid]) {
      if (nums[left] <= target && target < nums[mid]) right = mid - 1; else left = mid + 1;
    } else {
      if (nums[mid] < target && target <= nums[right]) left = mid + 1; else right = mid - 1;
    }
  }
  return -1;
}
const search = solve;
class Solution { search(nums, target) { return solve(nums, target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, search };
