'use strict';

// 2089. Find Target Indices After Sorting Array (Easy).
// Specification: https://leetcode.com/problems/find-target-indices-after-sorting-array/description/
// O(n) time, O(r) result space; count smaller and equal values instead of sorting nums.
function solve(nums, target) {
  let smaller = 0;
  let equal = 0;
  for (const value of nums) {
    if (value < target) smaller++;
    else if (value === target) equal++;
  }
  return Array.from({ length: equal }, (_, offset) => smaller + offset);
}

const targetIndices = solve;
class Solution {
  targetIndices(nums, target) { return solve(nums, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, targetIndices };
