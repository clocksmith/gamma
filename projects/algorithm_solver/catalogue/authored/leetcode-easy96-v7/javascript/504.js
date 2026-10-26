'use strict';

// 504. Base 7 (Easy).
// Specification: https://leetcode.com/problems/base-7/description/
// O(log(abs(num) + 1)) time and output space; preserve the sign and handle zero explicitly.
function solve(num) {
  if (num === 0) return '0';
  let remaining = Math.abs(num);
  const digits = [];
  while (remaining > 0) {
    digits.push(String(remaining % 7));
    remaining = Math.floor(remaining / 7);
  }
  return (num < 0 ? '-' : '') + digits.reverse().join('');
}

const convertToBase7 = solve;
class Solution {
  convertToBase7(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, convertToBase7 };
