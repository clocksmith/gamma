'use strict';

// 2717. Semi-Ordered Permutation (Easy).
// Specification: https://leetcode.com/problems/semi-ordered-permutation/description/
// O(n) time, O(1) auxiliary space; preserve the permutation.
function solve(nums) {
  const first = nums.indexOf(1);
  const last = nums.indexOf(nums.length);
  return first + nums.length - 1 - last - (first > last ? 1 : 0);
}

const semiOrderedPermutation = solve;
class Solution {
  semiOrderedPermutation(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, semiOrderedPermutation };
