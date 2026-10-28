'use strict';

// 27. Remove Element (Easy).
// Specification: https://leetcode.com/problems/remove-element/description/
function solve(nums, val) {
  return nums.filter((value) => value !== val);
}
const removeElement = solve;
class Solution { removeElement(nums, val) { return solve(nums, val); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeElement };
