'use strict';

// 1486. XOR Operation in an Array (Easy).
// Specification: https://leetcode.com/problems/xor-operation-in-an-array/description/
// O(n) time, O(1) space; all operands fit signed int32 in the public domain.
function solve(n, start) {
  let result = 0;
  for (let index = 0; index < n; index++) result ^= start + 2 * index;
  return result;
}

const xorOperation = solve;
class Solution {
  xorOperation(n, start) { return solve(n, start); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, xorOperation };
