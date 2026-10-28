'use strict';

// 1281. Subtract the Product and Sum of Digits of an Integer (Easy).
// Specification: https://leetcode.com/problems/subtract-the-product-and-sum-of-digits-of-an-integer/description/
function solve(n) {
  let product = 1; let sum = 0; let value = n;
  while (value > 0) { const digit = value % 10; product *= digit; sum += digit; value = Math.floor(value / 10); }
  return product - sum;
}
const subtractProductAndSum = solve;
class Solution { subtractProductAndSum(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, subtractProductAndSum };
