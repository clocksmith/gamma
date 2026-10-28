'use strict';

// 1837. Sum of Digits in Base K (Easy).
// Specification: https://leetcode.com/problems/sum-of-digits-in-base-k/description/
function solve(n, k) {
  let total = 0;
  let value = n;
  while (value > 0) { total += value % k; value = Math.floor(value / k); }
  return total;
}
const sumBase = solve;
class Solution { sumBase(n, k) { return solve(n, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumBase };
