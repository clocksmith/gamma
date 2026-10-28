'use strict';

// 89. Gray Code (Medium).
// Specification: https://leetcode.com/problems/gray-code/description/
function solve(n) {
  const result = [];
  for (let i = 0; i < (1 << n); i++) result.push(i ^ (i >> 1));
  return result;
}
const grayCode = solve;
class Solution { grayCode(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, grayCode };
