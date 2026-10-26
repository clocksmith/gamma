'use strict';

// 2595. Number of Even and Odd Bits (Easy).
// Specification: https://leetcode.com/problems/number-of-even-and-odd-bits/description/
// O(log(n + 1)) time, O(1) space; bit positions start at zero.
function solve(n) {
  const result = [0, 0];
  let remaining = n;
  let parity = 0;
  while (remaining > 0) {
    result[parity] += remaining % 2;
    remaining = Math.floor(remaining / 2);
    parity = 1 - parity;
  }
  return result;
}

const evenOddBit = solve;
class Solution {
  evenOddBit(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, evenOddBit };
