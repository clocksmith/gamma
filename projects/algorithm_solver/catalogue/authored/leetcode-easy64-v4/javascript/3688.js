'use strict';

// 3688. Bitwise OR of Even Numbers in an Array (Easy).
// Specification: https://leetcode.com/problems/bitwise-or-of-even-numbers-in-an-array/description/
// O(n) time, O(1) space; values in [1, 100] make bitwise arithmetic safe.
function solve(nums) {
  let result = 0;
  for (const value of nums) {
    if (value % 2 === 0) result |= value;
  }
  return result;
}

const evenNumberBitwiseORs = solve;
class Solution {
  evenNumberBitwiseORs(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, evenNumberBitwiseORs };
