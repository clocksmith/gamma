'use strict';

// 190. Reverse Bits (Easy).
// Specification: https://leetcode.com/problems/reverse-bits/description/
// O(32) time, O(1) space; reverse exactly 32 bits and return an unsigned integer.
function solve(n) {
  let remaining = n >>> 0;
  let result = 0;
  for (let bit = 0; bit < 32; bit++) {
    result = result * 2 + (remaining & 1);
    remaining >>>= 1;
  }
  return result;
}

const reverseBits = solve;
class Solution {
  reverseBits(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseBits };
