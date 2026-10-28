'use strict';

// 724. Find Pivot Index (Easy).
// Specification: https://leetcode.com/problems/find-pivot-index/description/
function solve(nums) {
  const total = nums.reduce((sum, value) => sum + value, 0);
  let left = 0;
  for (let index = 0; index < nums.length; index++) {
    if (left === total - left - nums[index]) return index;
    left += nums[index];
  }
  return -1;
}

const pivotIndex = solve;
class Solution {
  pivotIndex(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, pivotIndex };
