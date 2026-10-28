'use strict';

// 80. Remove Duplicates from Sorted Array II (Medium).
// Specification: https://leetcode.com/problems/remove-duplicates-from-sorted-array-ii/description/
function solve(nums) {
  const result = [];
  for (const value of nums) {
    if (result.length < 2 || value !== result[result.length - 2]) result.push(value);
  }
  return result;
}
const removeDuplicates = solve;
class Solution { removeDuplicates(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeDuplicates };
