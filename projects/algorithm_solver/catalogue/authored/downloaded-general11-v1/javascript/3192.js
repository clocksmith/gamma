'use strict';

// 3192. Minimum Operations to Make Binary Array Elements Equal to One II (Medium).
// Specification: https://leetcode.com/problems/minimum-operations-to-make-binary-array-elements-equal-to-one-ii/description/
function solve(nums) {
  let flips = 0; let ans = 0;
  for (const v of nums) {
    if ((v ^ flips) === 0) { flips ^= 1; ans++; }
  }
  return ans;
}
const minOperations = solve;
class Solution { minOperations(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
