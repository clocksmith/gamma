'use strict';

// 3622. Check Divisibility by Digit Sum and Product (Easy).
// Specification: https://leetcode.com/problems/check-divisibility-by-digit-sum-and-product/description/
// O(d) time, O(1) space; d is the decimal digit count.
function solve(n) {
  let remaining = n;
  let digitSum = 0;
  let digitProduct = 1;
  while (remaining > 0) {
    const digit = remaining % 10;
    digitSum += digit;
    digitProduct *= digit;
    remaining = Math.floor(remaining / 10);
  }
  return n % (digitSum + digitProduct) === 0;
}

const checkDivisibility = solve;
class Solution {
  checkDivisibility(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkDivisibility };
