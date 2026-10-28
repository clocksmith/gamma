'use strict';

// 1492. The kth Factor of n (Medium).
// Specification: https://leetcode.com/problems/the-kth-factor-of-n/description/
function solve(n, k) {
  let count = 0;
  for (let value = 1; value <= n; value++) {
    if (n % value === 0) { count++; if (count === k) return value; }
  }
  return -1;
}
const kthFactor = solve;
class Solution { kthFactor(n, k) { return solve(n, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, kthFactor };
