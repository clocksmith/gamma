'use strict';

// 693. Binary Number with Alternating Bits (Easy).
// Specification: https://leetcode.com/problems/binary-number-with-alternating-bits/description/
function solve(n) {
  const combined = n ^ (n >> 1);
  return (combined & (combined + 1)) === 0;
}

const hasAlternatingBits = solve;
class Solution {
  hasAlternatingBits(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, hasAlternatingBits };
