'use strict';

// 26. Remove Duplicates from Sorted Array (Easy).
// Specification: https://leetcode.com/problems/remove-duplicates-from-sorted-array/description/
function solve(nums) {
  if (nums.length === 0) return [];
  const result = [nums[0]];
  for (let i = 1; i < nums.length; i++) { if (nums[i] !== nums[i - 1]) result.push(nums[i]); }
  return result;
}
const removeDuplicates = solve;
class Solution { removeDuplicates(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeDuplicates };
