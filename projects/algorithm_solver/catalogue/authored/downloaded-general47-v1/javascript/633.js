'use strict';

// 633. Sum of Square Numbers (Medium).
// Specification: https://leetcode.com/problems/sum-of-square-numbers/description/
function solve(c) {
  let left = 0; let right = Math.floor(Math.sqrt(c));
  while (left <= right) {
    const total = left * left + right * right;
    if (total === c) return true;
    if (total < c) left++;
    else right--;
  }
  return false;
}
const judgeSquareSum = solve;
class Solution { judgeSquareSum(c) { return solve(c); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, judgeSquareSum };
