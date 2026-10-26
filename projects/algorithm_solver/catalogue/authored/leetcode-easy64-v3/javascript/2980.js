'use strict';

// 2980. Check if Bitwise OR Has Trailing Zeros (Easy).
// Specification: https://leetcode.com/problems/check-if-bitwise-or-has-trailing-zeros/description/
// O(n) time, O(1) space; at least two even operands are necessary and sufficient.
function solve(nums) {
  let evens = 0;
  for (const value of nums) {
    if (value % 2 === 0) evens++;
    if (evens >= 2) return true;
  }
  return false;
}

const hasTrailingZeros = solve;
class Solution {
  hasTrailingZeros(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, hasTrailingZeros };
