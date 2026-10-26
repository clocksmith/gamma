'use strict';

// 3345. Smallest Divisible Digit Product I (Easy).
// Specification: https://leetcode.com/problems/smallest-divisible-digit-product-i/description/
// O(log n) time, O(1) space; at most ten candidates reach a multiple of ten.
function solve(n, t) {
  let candidate = n;
  while (true) {
    let remaining = candidate;
    let product = 1;
    while (remaining > 0) {
      product *= remaining % 10;
      remaining = Math.floor(remaining / 10);
    }
    if (product % t === 0) return candidate;
    candidate++;
  }
}

const smallestNumber = solve;
class Solution {
  smallestNumber(n, t) { return solve(n, t); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestNumber };
