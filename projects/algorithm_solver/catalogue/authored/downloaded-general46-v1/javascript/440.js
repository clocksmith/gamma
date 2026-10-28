'use strict';

// 440. K-th Smallest in Lexicographical Order (Hard).
// Specification: https://leetcode.com/problems/k-th-smallest-in-lexicographical-order/description/
function countSteps(n, prefix) {
  let steps = 0; let first = prefix; let last = prefix + 1;
  while (first <= n) { steps += Math.min(last, n + 1) - first; first *= 10; last *= 10; }
  return steps;
}
function solve(n, k) {
  let current = 1; let remaining = k - 1;
  while (remaining > 0) {
    const steps = countSteps(n, current);
    if (steps <= remaining) { current++; remaining -= steps; } else { current *= 10; remaining--; }
  }
  return current;
}
const findKthNumber = solve;
class Solution { findKthNumber(n, k) { return solve(n, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findKthNumber };
