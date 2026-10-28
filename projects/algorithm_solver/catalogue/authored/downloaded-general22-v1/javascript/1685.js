'use strict';

// 1685. Sum of Absolute Differences in a Sorted Array (Medium).
// Specification: https://leetcode.com/problems/sum-of-absolute-differences-in-a-sorted-array/description/
function solve(nums) {
  const total = nums.reduce((sum, value) => sum + value, 0);
  let prefix = 0;
  const result = [];
  for (let i = 0; i < nums.length; i++) {
    const left = i * nums[i] - prefix;
    const right = (total - prefix - nums[i]) - (nums.length - 1 - i) * nums[i];
    result.push(left + right);
    prefix += nums[i];
  }
  return result;
}
const getSumAbsoluteDifferences = solve;
class Solution { getSumAbsoluteDifferences(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, getSumAbsoluteDifferences };
