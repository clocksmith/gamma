'use strict';

// 35. Search Insert Position (Easy).
// Specification: https://leetcode.com/problems/search-insert-position/description/
// O(log n) time, O(1) space; lower-bound search on a half-open interval.
function solve(nums, target) {
  let left = 0;
  let right = nums.length;
  while (left < right) {
    const middle = left + Math.floor((right - left) / 2);
    if (nums[middle] < target) left = middle + 1;
    else right = middle;
  }
  return left;
}

const searchInsert = solve;
class Solution {
  searchInsert(nums, target) { return solve(nums, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, searchInsert };
