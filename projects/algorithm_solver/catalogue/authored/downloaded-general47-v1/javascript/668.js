'use strict';

// 668. Kth Smallest Number in Multiplication Table (Hard).
// Specification: https://leetcode.com/problems/kth-smallest-number-in-multiplication-table/description/
function solve(m, n, k) {
  let left = 1; let right = m * n;
  while (left < right) {
    const mid = Math.floor((left + right) / 2);
    let count = 0;
    for (let i = 1; i <= m; i++) count += Math.min(Math.floor(mid / i), n);
    if (count < k) left = mid + 1;
    else right = mid;
  }
  return left;
}
const findKthNumber = solve;
class Solution { findKthNumber(m, n, k) { return solve(m, n, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findKthNumber };
