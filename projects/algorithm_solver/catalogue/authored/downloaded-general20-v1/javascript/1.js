'use strict';

// 1. Two Sum (Easy).
// Specification: https://leetcode.com/problems/two-sum/description/
function solve(nums, target) {
  const indexByValue = new Map();
  for (let index = 0; index < nums.length; index++) {
    const needed = target - nums[index];
    if (indexByValue.has(needed)) return [indexByValue.get(needed), index];
    indexByValue.set(nums[index], index);
  }
  return [];
}

const twoSum = solve;
class Solution {
  twoSum(nums, target) { return solve(nums, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, twoSum };
