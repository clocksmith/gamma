'use strict';

// 1389. Create Target Array in the Given Order (Easy).
// Specification: https://leetcode.com/problems/create-target-array-in-the-given-order/description/
// O(n^2) time, O(n) space; insert each value at its specified current index.
function solve(nums, index) {
  const result = [];
  for (let position = 0; position < nums.length; position++) result.splice(index[position], 0, nums[position]);
  return result;
}

const createTargetArray = solve;
class Solution {
  createTargetArray(nums, index) { return solve(nums, index); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, createTargetArray };
