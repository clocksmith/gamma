'use strict';

// 3959. Check Good Integer.
// Specification: https://leetcode.com/problems/check-good-integer/description/
// O(log n) time and O(1) space. Inputs are preserved.
function solve(n) {
  let difference = 0;
  while (n > 0) {
    const digit = n % 10;
    difference += digit * (digit - 1);
    n = Math.floor(n / 10);
  }
  return difference >= 50;
}

if (typeof module !== 'undefined') module.exports = { solve };
