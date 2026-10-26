'use strict';

// 2303. Calculate Amount Paid in Taxes (Easy).
// Specification: https://leetcode.com/problems/calculate-amount-paid-in-taxes/description/
// O(n) time, O(1) space; accumulate integer percentage-units then divide once; preserve brackets.
function solve(brackets, income) {
  let previous = 0;
  let percentageUnits = 0;
  for (const [upper, percent] of brackets) {
    const taxable = Math.min(income, upper) - previous;
    if (taxable > 0) percentageUnits += taxable * percent;
    if (income <= upper) break;
    previous = upper;
  }
  return percentageUnits / 100;
}

const calculateTax = solve;
class Solution {
  calculateTax(brackets, income) { return solve(brackets, income); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, calculateTax };
