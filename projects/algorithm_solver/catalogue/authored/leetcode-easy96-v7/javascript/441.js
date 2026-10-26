'use strict';

// 441. Arranging Coins (Easy).
// Specification: https://leetcode.com/problems/arranging-coins/description/
// O(log n) time, O(1) space; the 32-bit input bound permits an exact 65536-row upper bound.
function solve(n) {
  let low = 0;
  let high = Math.min(n, 65536);
  while (low < high) {
    const middle = low + Math.floor((high - low + 1) / 2);
    const required = middle * (middle + 1) / 2;
    if (required <= n) low = middle;
    else high = middle - 1;
  }
  return low;
}

const arrangeCoins = solve;
class Solution {
  arrangeCoins(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, arrangeCoins };
