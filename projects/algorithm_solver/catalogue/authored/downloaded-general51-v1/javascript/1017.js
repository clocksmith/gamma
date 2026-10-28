'use strict';

// 1017. Convert to Base -2 (Medium).
// Specification: https://leetcode.com/problems/convert-to-base-2/description/
function solve(n) {
  if (n === 0) return '0';
  let result = '';
  let value = n;
  while (value !== 0) {
    const remainder = ((value % 2) + 2) % 2;
    result = String(remainder) + result;
    value = (value - remainder) / -2;
  }
  return result;
}
const baseNeg2 = solve;
class Solution { baseNeg2(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, baseNeg2 };
