'use strict';

// 2733. Neither Minimum nor Maximum (Easy).
// Specification: https://leetcode.com/problems/neither-minimum-nor-maximum/description/
// O(1) time and space; return the median of the first three distinct values.
function solve(nums) {
  if (nums.length < 3) return -1;
  const first = nums[0];
  const second = nums[1];
  const third = nums[2];
  return first + second + third - Math.min(first, second, third) - Math.max(first, second, third);
}

const findNonMinOrMax = solve;
class Solution {
  findNonMinOrMax(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findNonMinOrMax };
