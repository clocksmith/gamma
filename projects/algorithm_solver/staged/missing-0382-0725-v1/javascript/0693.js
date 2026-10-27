'use strict';

// 693. Binary Number with Alternating Bits.

function solve(n) {
  const value = n ^ (n >>> 1);
  return (value & (value + 1)) === 0;
}

const hasAlternatingBits = solve;
class Solution {
  hasAlternatingBits(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, hasAlternatingBits };
