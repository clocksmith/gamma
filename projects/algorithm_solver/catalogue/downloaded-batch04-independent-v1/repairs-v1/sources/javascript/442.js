'use strict';

// 442. Find All Duplicates in an Array (Medium).
// Specification: https://leetcode.com/problems/find-all-duplicates-in-an-array/description/
function solve(nums) {
  const result = [];
  try {
    for (let i = 0; i < nums.length; i++) {
      const position = Math.abs(nums[i]) - 1;
      if (nums[position] < 0) result.push(position + 1);
      else nums[position] = -nums[position];
    }
  } finally {
    for (let i = 0; i < nums.length; i++) nums[i] = Math.abs(nums[i]);
  }
  return result;
}
const findDuplicates = solve;
class Solution { findDuplicates(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findDuplicates };
