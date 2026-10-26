'use strict';

// 3697. Compute Decimal Representation (Easy).
// Specification: https://leetcode.com/problems/compute-decimal-representation/description/
// O(d) time and output space; emit nonzero place values in descending order.
function solve(n) {
  const result = [];
  let remaining = n;
  let place = 1;
  while (remaining > 0) {
    const digit = remaining % 10;
    if (digit !== 0) result.push(digit * place);
    place *= 10;
    remaining = Math.floor(remaining / 10);
  }
  result.reverse();
  return result;
}

const decimalRepresentation = solve;
class Solution {
  decimalRepresentation(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, decimalRepresentation };
