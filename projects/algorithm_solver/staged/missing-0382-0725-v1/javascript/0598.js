'use strict';

// 598. Range Addition II.

function solve(m, n, ops) {
  for (const [rows, cols] of ops) { m = Math.min(m, rows); n = Math.min(n, cols); }
  return m * n;
}

const maxCount = solve;
class Solution {
  maxCount(m, n, ops) { return solve(m, n, ops); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxCount };
