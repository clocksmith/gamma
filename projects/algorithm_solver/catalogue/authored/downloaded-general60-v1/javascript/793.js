'use strict';

// 793. Preimage Size of Factorial Zeroes Function (Hard).
// Specification: https://leetcode.com/problems/preimage-size-of-factorial-zeroes-function/description/
function trailingZeroes(n) {
  let count = 0;
  while (n > 0) { n = Math.floor(n / 5); count += n; }
  return count;
}
function solve(k) {
  let left = 0; let right = 5000000000;
  while (left < right) {
    const mid = Math.floor((left + right) / 2);
    if (trailingZeroes(mid) < k) left = mid + 1;
    else right = mid;
  }
  return trailingZeroes(left) === k ? 5 : 0;
}
const preimageSizeFZF = solve;
class Solution { preimageSizeFZF(k) { return solve(k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, preimageSizeFZF };
