'use strict';

// 371. Sum of Two Integers (Medium).
// Specification: https://leetcode.com/problems/sum-of-two-integers/description/
function solve(a, b) {
  let x = a; let y = b;
  while (y !== 0) { const carry = (x & y) << 1; x = x ^ y; y = carry; }
  return x;
}
const getSum = solve;
class Solution { getSum(a, b) { return solve(a, b); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, getSum };
