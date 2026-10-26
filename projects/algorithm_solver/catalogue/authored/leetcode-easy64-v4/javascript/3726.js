'use strict';

// 3726. Remove Zeros in Decimal Representation (Easy).
// Specification: https://leetcode.com/problems/remove-zeros-in-decimal-representation/description/
// O(d) time, O(1) space; n <= 10^15 stays within exact JavaScript integer range.
function solve(n) {
  let remaining = n;
  let result = 0;
  let place = 1;
  while (remaining > 0) {
    const digit = remaining % 10;
    if (digit !== 0) {
      result += digit * place;
      place *= 10;
    }
    remaining = Math.floor(remaining / 10);
  }
  return result;
}

const removeZeros = solve;
class Solution {
  removeZeros(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeZeros };
