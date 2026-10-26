'use strict';

// 405. Convert a Number to Hexadecimal (Easy).
// Specification: https://leetcode.com/problems/convert-a-number-to-hexadecimal/description/
// O(1) bounded 32-bit conversion; use lowercase hexadecimal and two's complement.
function solve(num) {
  let value = num >>> 0;
  if (value === 0) return '0';
  const digits = '0123456789abcdef';
  const result = [];
  while (value > 0) {
    result.push(digits[value % 16]);
    value = Math.floor(value / 16);
  }
  return result.reverse().join('');
}

const toHex = solve;
class Solution {
  toHex(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, toHex };
