'use strict';

// 191. Number of 1 Bits (Easy).
// Specification: https://leetcode.com/problems/number-of-1-bits/description/
// O(32) time, O(1) space; count set bits in the unsigned 32-bit representation.
function solve(n) {
  let remaining = n >>> 0;
  let count = 0;
  while (remaining !== 0) {
    remaining = (remaining & (remaining - 1)) >>> 0;
    count++;
  }
  return count;
}

const hammingWeight = solve;
class Solution {
  hammingWeight(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, hammingWeight };
