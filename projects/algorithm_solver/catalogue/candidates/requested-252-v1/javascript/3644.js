'use strict';

// 3644. Maximum K to Sort a Permutation.
// Specification: https://leetcode.com/problems/maximum-k-to-sort-a-permutation/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(n) time, O(1) space; bitwise AND of all misplaced permutation values.
// Inputs are not modified.

function solve(nums) {
  let answer = null;
  for (let index = 0; index < nums.length; index++) {
    if (nums[index] !== index) answer = answer === null ? nums[index] : answer & nums[index];
  }
  return answer === null ? 0 : answer;
}

const sortPermutation = solve;
class Solution {
  sortPermutation(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sortPermutation };
