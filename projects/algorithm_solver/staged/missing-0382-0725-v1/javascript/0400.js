'use strict';

// 400. Nth Digit.

function solve(n) {
  let digits = 1, first = 1, count = 9;
  while (n > digits * count) {
    n -= digits * count; digits += 1; first *= 10; count *= 10;
  }
  const number = first + Math.floor((n - 1) / digits);
  return Number(String(number)[(n - 1) % digits]);
}

const findNthDigit = solve;
class Solution {
  findNthDigit(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findNthDigit };
