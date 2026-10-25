'use strict';

// 1716. Calculate Money in Leetcode Bank (Easy).
// Specification: https://leetcode.com/problems/calculate-money-in-leetcode-bank/description/
// O(1) time and space. Arithmetic is exact within the declared n <= 1000.
function solve(n) {
  const weeks = Math.floor(n / 7);
  const days = n % 7;
  const completeWeeks = 28 * weeks + 7 * weeks * (weeks - 1) / 2;
  const remainingDays = days * (weeks + 1) + days * (days - 1) / 2;
  return completeWeeks + remainingDays;
}

const totalMoney = solve;
class Solution {
  totalMoney(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, totalMoney };
