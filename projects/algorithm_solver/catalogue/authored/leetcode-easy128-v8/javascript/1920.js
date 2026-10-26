'use strict';

// 1920. Build Array from Permutation (Easy).
// Specification: https://leetcode.com/problems/build-array-from-permutation/description/
// O(n) time and space; read each composed index from the unchanged input permutation.
function solve(nums) {
  return nums.map(value => nums[value]);
}

const buildArray = solve;
class Solution {
  buildArray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, buildArray };
