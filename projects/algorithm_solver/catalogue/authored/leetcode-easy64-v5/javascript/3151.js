'use strict';

// 3151. Special Array I (Easy).
// Specification: https://leetcode.com/problems/special-array-i/description/
// O(n) time, O(1) auxiliary space; preserve nums.
function solve(nums) {
  for (let index = 1; index < nums.length; index++) {
    if (nums[index] % 2 === nums[index - 1] % 2) return false;
  }
  return true;
}

const isArraySpecial = solve;
class Solution {
  isArraySpecial(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isArraySpecial };
